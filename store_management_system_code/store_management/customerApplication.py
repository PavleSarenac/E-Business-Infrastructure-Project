from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Product, Category, Order, ProductOrder
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from datetime import datetime, timezone
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/search", methods=["GET"])
@jwt_required()
def search():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return jsonify(msg="Missing Authorization Header"), 401
    resultDictionary = {
        "categories": [],
        "products": []
    }
    if "name" in request.args:
        searchedProducts = Product.query.filter(Product.productName.like(f"%{request.args['name']}%")).all()
    else:
        searchedProducts = Product.query.all()
    if "category" in request.args:
        searchedCategories = Category.query.filter(Category.categoryName.like(f"%{request.args['category']}%")).all()
    else:
        searchedCategories = Category.query.all()
    for product in searchedProducts:
        categoryFound = False
        for category in product.categories:
            for searchedCategory in searchedCategories:
                if category.categoryName == searchedCategory.categoryName:
                    if category.categoryName not in resultDictionary["categories"]:
                        resultDictionary["categories"].append(category.categoryName)
                    categoryFound = True
        if categoryFound:
            resultDictionary["products"].append({
                "categories": [currentCategory.categoryName for currentCategory in product.categories],
                "id": product.id,
                "name": product.productName,
                "price": product.productPrice
            })
    return jsonify(resultDictionary), 200


@application.route("/order", methods=["POST"])
@jwt_required()
def order():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "1":
        return jsonify(msg="Missing Authorization Header"), 401

    requests = request.json.get("requests", "null")
    if requests == "null":
        return jsonify(message="Field requests is missing."), 400
    requestNumber = 0
    for currentRequest in requests:
        if "id" not in currentRequest:
            return jsonify(message="Product id is missing for request number " + str(requestNumber) + "."), 400
        if "quantity" not in currentRequest:
            return jsonify(message="Product quantity is missing for request number " + str(requestNumber) + "."), 400
        if type(currentRequest["id"]) is not int or currentRequest["id"] <= 0:
            return jsonify(message="Invalid product id for request number " + str(requestNumber) + "."), 400
        if type(currentRequest["quantity"]) is not int or currentRequest["quantity"] <= 0:
            return jsonify(message="Invalid product quantity for request number " + str(requestNumber) + "."), 400
        if not Product.query.filter(Product.id == currentRequest["id"]).first():
            return jsonify(message="Invalid product for request number " + str(requestNumber) + "."), 400
        requestNumber += 1

    totalOrderPrice = 0
    for currentRequest in requests:
        currentProduct = Product.query.filter(Product.id == currentRequest["id"]).first()
        totalOrderPrice += currentRequest["quantity"] * currentProduct.productPrice
    orderCreationTime = datetime.now(timezone.utc).isoformat()
    newOrder = Order(
        totalOrderPrice=totalOrderPrice,
        orderStatus="CREATED",
        orderCreationTime=orderCreationTime,
        buyerEmail=jwtToken["email"]
    )
    database.session.add(newOrder)
    database.session.commit()

    for currentRequest in requests:
        newProductOrder = ProductOrder(
            productId=currentRequest["id"],
            orderId=newOrder.id,
            quantity=currentRequest["quantity"]
        )
        database.session.add(newProductOrder)
        database.session.commit()

    return jsonify({"id": newOrder.id}), 200


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
