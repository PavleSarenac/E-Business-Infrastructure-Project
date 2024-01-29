from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Product, Category, ProductCategory
from flask_jwt_extended import JWTManager, jwt_required
from requests import request as httpRequest
import json
from decorators import roleCheck

OWNER_ROLE_ID_STRING = "2"

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/update", methods=["POST"])
@jwt_required()
@roleCheck(OWNER_ROLE_ID_STRING)
def update():
    errorMessage, errorCode = validateUpdateRequest()
    if len(errorMessage) > 0:
        return jsonify(message=errorMessage), errorCode

    productCategoriesDictionary, errorMessage, errorCode = processFile(request)
    if len(errorMessage) > 0:
        return jsonify(message=errorMessage), errorCode

    productCategoriesDictionary = insertProducts(productCategoriesDictionary)
    productCategoriesDictionary = insertCategories(productCategoriesDictionary)
    insertProductCategories(productCategoriesDictionary)

    return Response(status=200)


@application.route("/product_statistics", methods=["GET"])
@jwt_required()
@roleCheck(OWNER_ROLE_ID_STRING)
def product_statistics():
    response = httpRequest(
        method="get",
        url="http://sparkApplication:5004/product_statistics"
    )
    return jsonify(json.loads(response.text)), 200


@application.route("/category_statistics", methods=["GET"])
@jwt_required()
@roleCheck(OWNER_ROLE_ID_STRING)
def category_statistics():
    response = httpRequest(
        method="get",
        url="http://sparkApplication:5004/category_statistics"
    )
    return jsonify(json.loads(response.text)), 200


def isFloat(stringRepresentation):
    try:
        float(stringRepresentation)
        return True
    except ValueError:
        return False


def insertProducts(productCategoriesDictionary):
    database.session.bulk_save_objects(list(productCategoriesDictionary.keys()))
    database.session.commit()
    addedProducts = Product.query.filter(
        Product.productName.in_([product.productName for product in productCategoriesDictionary.keys()])
    ).all()
    for productObject, addedProduct in zip(productCategoriesDictionary.keys(), addedProducts):
        productObject.id = addedProduct.id
    return productCategoriesDictionary


def getNewCategoryObjects(productCategoriesDictionary):
    allCategoryNamesFromDatabase = [category.categoryName for category in Category.query.all()]
    newCategoryNames = set()
    newCategoryObjects = []
    for categoryObjects in productCategoriesDictionary.values():
        for categoryObject in categoryObjects:
            if categoryObject.categoryName not in allCategoryNamesFromDatabase \
                    and categoryObject.categoryName not in newCategoryNames:
                newCategoryNames.add(categoryObject.categoryName)
                newCategoryObjects.append(categoryObject)
    return newCategoryObjects


def insertCategories(productCategoriesDictionary):
    newCategoryObjects = getNewCategoryObjects(productCategoriesDictionary)
    database.session.bulk_save_objects(newCategoryObjects)
    database.session.commit()
    addedCategories = Category.query.filter(
        Category.categoryName.in_([category.categoryName for category in newCategoryObjects])
    ).all()
    for productObject, categoryObjects in productCategoriesDictionary.items():
        for categoryObject in categoryObjects:
            for addedCategory in addedCategories:
                if categoryObject.categoryName == addedCategory.categoryName:
                    categoryObject.id = addedCategory.id
                    break
    return productCategoriesDictionary


def getNewProductCategoryObjects(productCategoriesDictionary):
    allProductCategoriesFromDatabase = \
        [(productCategory.productId, productCategory.categoryId) for productCategory in ProductCategory.query.all()]
    newProductCategoryTuples = set()
    newProductCategoryObjects = []
    for productObject, categoryObjects in productCategoriesDictionary.items():
        for categoryObject in categoryObjects:
            currentTuple = (productObject.id, categoryObject.id)
            if currentTuple not in allProductCategoriesFromDatabase \
                    and currentTuple not in newProductCategoryTuples:
                newProductCategoryTuples.add(currentTuple)
                newProductCategoryObjects.append(
                    ProductCategory(
                        productId=currentTuple[0],
                        categoryId=currentTuple[1]
                    )
                )
    return newProductCategoryObjects


def insertProductCategories(productCategoriesDictionary):
    newProductCategoryObjects = getNewProductCategoryObjects(productCategoriesDictionary)
    database.session.bulk_save_objects(newProductCategoryObjects)
    database.session.commit()


def processFile(postRequestBody):
    productsFileContent = postRequestBody.files["file"].stream.read().decode()
    productCategoriesDictionary = dict()
    lineNumber = 0
    allProductNamesInDatabase = [product.productName for product in Product.query.all()]

    for line in productsFileContent.split("\n"):
        splittedLine = line.split(",")
        if len(splittedLine) != 3:
            return productCategoriesDictionary, f"Incorrect number of values on line {lineNumber}.", 400
        productCategories, productName, productPrice = splittedLine[0], splittedLine[1], splittedLine[2]
        if not (isFloat(productPrice) and float(productPrice) > 0.0):
            return productCategoriesDictionary, f"Incorrect price on line {lineNumber}.", 400
        if productName in allProductNamesInDatabase \
                or productName in [product.productName for product in productCategoriesDictionary.keys()]:
            return productCategoriesDictionary, f"Product {productName} already exists.", 400
        productObject = Product(productName=productName, productPrice=productPrice)
        productCategoriesDictionary[productObject] = \
            [Category(categoryName=categoryName) for categoryName in productCategories.split("|")]
        lineNumber += 1

    return productCategoriesDictionary, "", 0


def validateUpdateRequest():
    if "file" not in request.files:
        return "Field file missing.", 400
    return "", 0


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.OWNER_APPLICATION_PORT)
