from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Product, Category, Order, ProductOrder, ProductCategory
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, get_jwt_identity
from datetime import datetime, timezone
from sqlalchemy import and_, asc

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def validateSearchRequest():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return "Missing Authorization Header", 401
    return "", 0


def getSearchResult():
    resultDictionary = {"categories": [], "products": []}
    searchResults = database.session.query(
        Product.id.label("ProductId"),
        Product.productName.label("ProductName"),
        Product.productPrice.label("ProductPrice"),
        Category.categoryName.label("CategoryName")
    ).join(
        ProductCategory, Product.id == ProductCategory.productId
    ).join(
        Category, ProductCategory.categoryId == Category.id
    ).filter(
        and_(
            Product.productName.like(f"%{request.args.get('name', '')}%"),
            Category.categoryName.like(f"%{request.args.get('category', '')}%")
        )
    ).all()

    for searchResult in searchResults:
        if searchResult.CategoryName not in resultDictionary["categories"]:
            resultDictionary["categories"].append(searchResult.CategoryName)
        productAlreadyAdded = False
        for product in resultDictionary["products"]:
            if product["id"] == searchResult.ProductId:
                productAlreadyAdded = True
                product["categories"].append(searchResult.CategoryName)
                break
        if not productAlreadyAdded:
            resultDictionary["products"].append({
                "categories": [searchResult.CategoryName],
                "id": searchResult.ProductId,
                "name": searchResult.ProductName,
                "price": searchResult.ProductPrice
            })
    return resultDictionary


def validateOrderRequest():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return None, "Missing Authorization Header", 401

    requests = request.json.get("requests", "null")
    if requests == "null":
        return None, "Field requests is missing.", 400

    requestNumber = 0
    allProductIds = [product.id for product in Product.query.all()]
    for currentRequest in requests:
        if "id" not in currentRequest:
            return None, f"Product id is missing for request number {requestNumber}.", 400
        if "quantity" not in currentRequest:
            return None, f"Product quantity is missing for request number {requestNumber}.", 400
        if type(currentRequest["id"]) is not int or currentRequest["id"] <= 0:
            return None, f"Invalid product id for request number {requestNumber}.", 400
        if type(currentRequest["quantity"]) is not int or currentRequest["quantity"] <= 0:
            return None, f"Invalid product quantity for request number {requestNumber}.", 400
        if currentRequest["id"] not in allProductIds:
            return None, f"Invalid product for request number {requestNumber}.", 400
        requestNumber += 1

    return requests, "", 0


def getNewOrderData(requests):
    requests = sorted(requests, key=lambda x: x["id"])
    orderedProductIds = [currentRequest["id"] for currentRequest in requests]
    orderedProductPrices = database.session.query(
        Product.productPrice.label("ProductPrice")
    ).filter(
        Product.id.in_(orderedProductIds)
    ).order_by(
        asc(Product.id)
    ).all()

    totalOrderPrice = 0
    for currentRequest, orderedProductPrice in zip(requests, orderedProductPrices):
        totalOrderPrice += currentRequest["quantity"] * orderedProductPrice.ProductPrice
    orderCreationTime = datetime.now(timezone.utc).isoformat()

    return totalOrderPrice, "CREATED", orderCreationTime, get_jwt_identity()


def insertOrder(requests):
    totalOrderPrice, orderStatus, orderCreationTime, buyerEmail = getNewOrderData(requests)
    newOrder = Order(
        totalOrderPrice=totalOrderPrice,
        orderStatus=orderStatus,
        orderCreationTime=orderCreationTime,
        buyerEmail=buyerEmail
    )
    database.session.add(newOrder)
    database.session.commit()
    return newOrder


def insertProductOrder(requests, newOrder):
    newProductOrders = []
    for currentRequest in requests:
        newProductOrders.append(
            ProductOrder(
                productId=currentRequest["id"],
                orderId=newOrder.id,
                quantity=currentRequest["quantity"]
            )
        )
    database.session.bulk_save_objects(newProductOrders)
    database.session.commit()
    return {"id": newOrder.id}


def validateStatusRequest():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return "Missing Authorization Header", 401
    return "", 0


def getOrderStatuses():
    orders = database.session.query(
        Order.id.label("OrderId"),
        Order.totalOrderPrice.label("TotalOrderPrice"),
        Order.orderStatus.label("OrderStatus"),
        Order.orderCreationTime.label("OrderCreationTime"),
        Product.id.label("ProductId"),
        Product.productName.label("ProductName"),
        Product.productPrice.label("ProductPrice"),
        ProductOrder.quantity.label("Quantity"),
        Category.categoryName.label("CategoryName")
    ).join(
        ProductOrder, Order.id == ProductOrder.orderId
    ).join(
        Product, ProductOrder.productId == Product.id
    ).join(
        ProductCategory, Product.id == ProductCategory.productId
    ).join(
        Category, ProductCategory.categoryId == Category.id
    ).filter(
        Order.buyerEmail == get_jwt_identity()
    ).order_by(
        asc("OrderId"), asc("ProductId"), asc("CategoryName")
    ).all()

    response = {"orders": []}
    previousOrderId = previousProductId = -1
    currentOrderIndex = currentProductIndex = -1
    for currentOrder in orders:
        currentOrderId = currentOrder.OrderId
        currentProductId = currentOrder.ProductId
        if currentOrderId != previousOrderId:
            currentOrderIndex += 1
            currentProductIndex = 0
            response["orders"].append({
                "products": [
                    {
                        "categories": [currentOrder.CategoryName],
                        "name": currentOrder.ProductName,
                        "price": currentOrder.ProductPrice,
                        "quantity": currentOrder.Quantity
                    }
                ],
                "price": currentOrder.TotalOrderPrice,
                "status": currentOrder.OrderStatus,
                "timestamp": currentOrder.OrderCreationTime
            })
        else:
            if currentProductId != previousProductId:
                response["orders"][currentOrderIndex]["products"].append({
                    "categories": [currentOrder.CategoryName],
                    "name": currentOrder.ProductName,
                    "price": currentOrder.ProductPrice,
                    "quantity": currentOrder.Quantity
                })
                currentProductIndex += 1
            else:
                response["orders"][currentOrderIndex]["products"][currentProductIndex]["categories"].append(
                    currentOrder.CategoryName
                )
        previousOrderId = currentOrderId
        previousProductId = currentProductId
    return response


def validateDeliveredRequest():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return "Missing Authorization Header", 401, None

    orderId = request.json.get("id", None)
    if orderId is None:
        return "Missing order id.", 400, None
    if type(orderId) is not int or orderId <= 0:
        return "Invalid order id.", 400, None
    orderForDeliveryConfirmation = Order.query.filter(Order.id == orderId).first()
    if not orderForDeliveryConfirmation:
        return "Invalid order id.", 400, None
    if orderForDeliveryConfirmation.orderStatus != "PENDING":
        return "Invalid order id.", 400, None

    return "", 0, orderForDeliveryConfirmation


def confirmOrderDelivery(orderForDeliveryConfirmation):
    orderForDeliveryConfirmation.orderStatus = "COMPLETE"
    database.session.commit()


@application.route("/search", methods=["GET"])
@jwt_required()
def search():
    errorMessage, errorCode = validateSearchRequest()
    if len(errorMessage) > 0:
        return jsonify(msg=errorMessage), errorCode

    return jsonify(getSearchResult()), 200


@application.route("/order", methods=["POST"])
@jwt_required()
def order():
    requests, errorMessage, errorCode = validateOrderRequest()
    if errorCode == 401:
        return jsonify(msg=errorMessage), errorCode
    if len(errorMessage) > 0:
        return jsonify(message=errorMessage), errorCode

    newOrder = insertOrder(requests)
    response = insertProductOrder(requests, newOrder)

    return jsonify(response), 200


@application.route("/status", methods=["GET"])
@jwt_required()
def status():
    errorMessage, errorCode = validateStatusRequest()
    if len(errorMessage) > 0:
        return jsonify(msg=errorMessage), errorCode

    return jsonify(getOrderStatuses()), 200


@application.route("/delivered", methods=["POST"])
@jwt_required()
def delivered():
    errorMessage, errorCode, orderForDeliveryConfirmation = validateDeliveredRequest()
    if errorCode == 401:
        return jsonify(msg=errorMessage), errorCode
    if len(errorMessage) > 0:
        return jsonify(message=errorMessage), errorCode

    confirmOrderDelivery(orderForDeliveryConfirmation)

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.CUSTOMER_APPLICATION_PORT)
