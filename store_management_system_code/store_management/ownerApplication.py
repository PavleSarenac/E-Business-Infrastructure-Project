from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Product, Category, ProductCategory
from sqlalchemy import and_
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


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.OWNER_APPLICATION_PORT)
