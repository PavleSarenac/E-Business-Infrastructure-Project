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
        if searchResult[3] not in resultDictionary["categories"]:
            resultDictionary["categories"].append(searchResult[3])
        productAlreadyAdded = False
        for product in resultDictionary["products"]:
            if product["id"] == searchResult[0]:
                productAlreadyAdded = True
                product["categories"].append(searchResult[3])
                break
        if not productAlreadyAdded:
            resultDictionary["products"].append({
                "categories": [searchResult[3]],
                "id": searchResult[0],
                "name": searchResult[1],
                "price": searchResult[2]
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
        totalOrderPrice += currentRequest["quantity"] * orderedProductPrice[0]
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
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return jsonify(msg="Missing Authorization Header"), 401

    response = {
        "orders": []
    }
    allOrders = Order.query.all()
    for currentOrder in allOrders:
        newOrder = dict()
        newOrder["products"] = []
        for product in currentOrder.products:
            newProduct = dict()
            newProduct["categories"] = [category.categoryName for category in product.categories]
            newProduct["name"] = product.productName
            newProduct["price"] = product.productPrice
            newProduct["quantity"] = ProductOrder.query.filter(
                and_(ProductOrder.productId == product.id, ProductOrder.orderId == currentOrder.id)
            ).first().quantity
            newOrder["products"].append(newProduct)
        newOrder["price"] = currentOrder.totalOrderPrice
        newOrder["status"] = currentOrder.orderStatus
        newOrder["timestamp"] = currentOrder.orderCreationTime
        response["orders"].append(newOrder)
    return jsonify(response), 200


@application.route("/delivered", methods=["POST"])
@jwt_required()
def delivered():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return jsonify(msg="Missing Authorization Header"), 401

    orderId = request.json.get("id", "null")
    if orderId == "null":
        return jsonify(message="Missing order id."), 400
    if type(orderId) is not int or orderId <= 0:
        return jsonify(message="Invalid order id."), 400
    if not Order.query.filter(Order.id == orderId).first():
        return jsonify(message="Invalid order id."), 400
    orderStatus = Order.query.filter(Order.id == orderId).first().orderStatus
    if orderStatus != "PENDING":
        return jsonify(message="Invalid order id."), 400
    _order = Order.query.filter(Order.id == orderId).first()
    _order.orderStatus = "COMPLETE"
    database.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.CUSTOMER_APPLICATION_PORT)
