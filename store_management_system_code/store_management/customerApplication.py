from flask import Flask, request, jsonify
from configuration import Configuration
from models import database, Product, Category
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

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


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.CUSTOMER_APPLICATION_PORT)
