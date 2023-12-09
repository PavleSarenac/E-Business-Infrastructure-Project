from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Product, Category, ProductCategory, Order, ProductOrder
from sqlalchemy import and_, func
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

OWNER_ROLE_ID_STRING = "2"

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


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
    allCategorieNamesFromDatabase = [category.categoryName for category in Category.query.all()]
    newCategoryNames = set()
    newCategoryObjects = []
    for categoryObjects in productCategoriesDictionary.values():
        for categoryObject in categoryObjects:
            if categoryObject.categoryName not in allCategorieNamesFromDatabase \
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
    return productCategoriesDictionary


def getNewProductCategoryObjects(productCategoriesDictionary):
    allProductCategoriesFromDatabase = \
        [(productCategory.productId, productCategory.categoryId) for productCategory in ProductCategory.query.all()]
    newProductCategoriesTuples = set()
    newProductCategoriesObjects = []
    for productObject, categoryObjects in productCategoriesDictionary.items():
        for categoryObject in categoryObjects:
            currentTuple = (productObject.id, categoryObject.id)
            if currentTuple not in allProductCategoriesFromDatabase \
                    and currentTuple not in newProductCategoriesTuples:
                newProductCategoriesTuples.add(currentTuple)
                newProductCategoriesObjects.append(
                    ProductCategory(
                        productId=currentTuple[0],
                        categoryId=currentTuple[1]
                    )
                )
    return newProductCategoriesObjects


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


@application.route("/update", methods=["POST"])
@jwt_required()
def update():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != OWNER_ROLE_ID_STRING:
        return jsonify(msg="Missing Authorization Header"), 401
    if "file" not in request.files:
        return jsonify(message="Field file missing."), 400

    productCategoriesDictionary, errorMessage, errorCode = processFile(request)
    if len(errorMessage) > 0:
        return jsonify(message=errorMessage), errorCode

    productCategoriesDictionary = insertProducts(productCategoriesDictionary)
    productCategoriesDictionary = insertCategories(productCategoriesDictionary)
    insertProductCategories(productCategoriesDictionary)

    return Response(status=200)


@application.route("/product_statistics", methods=["GET"])
@jwt_required()
def product_statistics():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != OWNER_ROLE_ID_STRING:
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
    if jwtToken["roleId"] != OWNER_ROLE_ID_STRING:
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
