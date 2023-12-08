from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Product, Category, ProductCategory, Order, ProductOrder
from sqlalchemy import and_, func
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def isFloat(stringRepresentation):
    try:
        float(stringRepresentation)
        return True
    except ValueError:
        return False


@application.route("/update", methods=["POST"])
@jwt_required()
def update():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "2":
        return jsonify(msg="Missing Authorization Header"), 401
    if "file" not in request.files:
        return jsonify(message="Field file missing."), 400
    productsFileContent = request.files["file"].stream.read().decode()
    lineNumber = 0
    productCategoriesDictionary = dict()

    for line in productsFileContent.split("\n"):
        splittedLine = line.split(",")
        if len(splittedLine) != 3:
            return jsonify(message=f"Incorrect number of values on line {lineNumber}."), 400
        productCategories, productName, productPrice = splittedLine[0], splittedLine[1], splittedLine[2]
        if not (isFloat(productPrice) and float(productPrice) > 0.0):
            return jsonify(message=f"Incorrect price on line {lineNumber}."), 400
        if Product.query.filter(Product.productName == productName).first():
            return jsonify(message=f"Product {productName} already exists."), 400
        productObject = Product(productName=productName, productPrice=productPrice)
        productCategoriesDictionary[productObject] = []
        for categoryName in productCategories.split("|"):
            productCategoriesDictionary[productObject].append(categoryName)
        lineNumber += 1

    for productObject, categoriesNames in productCategoriesDictionary.items():
        database.session.add(productObject)
        database.session.commit()
        for categoryName in categoriesNames:
            categoryObject = Category.query.filter(Category.categoryName == categoryName).first()
            if not categoryObject:
                categoryObject = Category(categoryName=categoryName)
                database.session.add(categoryObject)
                database.session.commit()
            if not ProductCategory.query.filter(
                    and_(ProductCategory.productId == productObject.id,
                         ProductCategory.categoryId == categoryObject.id)).first():
                productCategoryObject = ProductCategory(productId=productObject.id, categoryId=categoryObject.id)
                database.session.add(productCategoryObject)
                database.session.commit()

    return Response(status=200)


@application.route("/product_statistics", methods=["GET"])
@jwt_required()
def product_statistics():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "2":
        return jsonify(msg="Missing Authorization Header"), 401

    products = dict()
    allOrders = Order.query.all()
    for order in allOrders:
        for product in order.products:
            productName = product.productName
            productQuantity = ProductOrder.query.filter(and_(
                ProductOrder.productId == product.id,
                ProductOrder.orderId == order.id
            )).first().quantity
            if productName not in products.keys():
                products[productName] = {"sold": 0, "waiting": 0}
            if order.orderStatus == "COMPLETE":
                products[productName]["sold"] += productQuantity
            else:
                products[productName]["waiting"] += productQuantity
    response = {
        "statistics": []
    }
    for productName, statistics in products.items():
        response["statistics"].append({
            "name": productName,
            "sold": statistics["sold"],
            "waiting": statistics["waiting"]
        })
    return jsonify(response), 200


@application.route("/category_statistics", methods=["GET"])
@jwt_required()
def category_statistics():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "2":
        return jsonify(msg="Missing Authorization Header"), 401

    categories = dict()
    allCategories = Category.query.all()
    for category in allCategories:
        if category.categoryName not in categories:
            categories[category.categoryName] = 0
        quantity = database.session.query(
            func.sum(ProductOrder.quantity)
        ).join(
            ProductCategory, ProductOrder.productId == ProductCategory.productId
        ).join(
            Order, ProductOrder.orderId == Order.id
        ).filter(
            and_(
                ProductCategory.categoryId == category.id,
                Order.orderStatus == "COMPLETE"
            )
        ).group_by(
            ProductCategory.categoryId
        ).scalar()
        if quantity:
            categories[category.categoryName] += quantity
    sortedCategories = dict(sorted(categories.items(), key=lambda item: (-item[1], item[0])))
    response = {
        "statistics": []
    }
    for categoryName in sortedCategories:
        response["statistics"].append(categoryName)

    return jsonify(response), 200


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.OWNER_APPLICATION_PORT)
