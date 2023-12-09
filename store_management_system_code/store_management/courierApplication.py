from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Order
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/orders_to_deliver", methods=["GET"])
@jwt_required()
def orders_to_deliver():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "3":
        return jsonify(msg="Missing Authorization Header"), 401

    response = {
        "orders": []
    }
    allOrders = Order.query.filter(Order.orderStatus == "CREATED").all()
    for currentOrder in allOrders:
        newDict = dict()
        newDict["id"] = currentOrder.id
        newDict["email"] = currentOrder.buyerEmail
        response["orders"].append(newDict)

    return jsonify(response), 200


@application.route("/pick_up_order", methods=["POST"])
@jwt_required()
def pick_up_order():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "3":
        return jsonify(msg="Missing Authorization Header"), 401

    orderId = request.json.get("id", "null")
    if orderId == "null":
        return jsonify(message="Missing order id."), 400
    if type(orderId) is not int or orderId <= 0:
        return jsonify(message="Invalid order id."), 400
    if not Order.query.filter(Order.id == orderId).first():
        return jsonify(message="Invalid order id."), 400
    orderStatus = Order.query.filter(Order.id == orderId).first().orderStatus
    if orderStatus == "PENDING" or orderStatus == "COMPLETE":
        return jsonify(message="Invalid order id."), 400
    order = Order.query.filter(Order.id == orderId).first()
    order.orderStatus = "PENDING"
    database.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.COURIER_APPLICATION_PORT)
