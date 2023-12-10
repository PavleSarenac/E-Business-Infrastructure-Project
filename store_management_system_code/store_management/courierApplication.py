from flask import Flask, request, jsonify, Response
from configuration import Configuration
from models import database, Order
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def validateOrdersToDeliverRequest():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "3":
        return "Missing Authorization Header", 401
    return "", 0


def getUndeliveredOrders():
    undeliveredOrders = {"orders": []}
    for order in Order.query.filter(Order.orderStatus == "CREATED").all():
        undeliveredOrders["orders"].append({
            "id": order.id,
            "email": order.buyerEmail
        })
    return undeliveredOrders


def validatePickUpOrderRequest():
    jwtToken = get_jwt()
    if jwtToken["roleId"] != "3":
        return "Missing Authorization Header", 401, None

    orderId = request.json.get("id", None)
    if orderId is None:
        return "Missing order id.", 400, None
    if type(orderId) is not int or orderId <= 0:
        return "Invalid order id.", 400, None
    orderForPickUp = Order.query.filter(Order.id == orderId).first()
    if not orderForPickUp:
        return "Invalid order id.", 400, None
    if orderForPickUp.orderStatus == "PENDING" or orderForPickUp.orderStatus == "COMPLETE":
        return "Invalid order id.", 400, None

    return "", 0, orderForPickUp


def confirmOrderPickUp(orderForPickUp):
    orderForPickUp.orderStatus = "PENDING"
    database.session.commit()


@application.route("/orders_to_deliver", methods=["GET"])
@jwt_required()
def orders_to_deliver():
    errorMessage, errorCode = validateOrdersToDeliverRequest()
    if len(errorMessage) > 0:
        return jsonify(msg=errorMessage), errorCode

    return jsonify(getUndeliveredOrders()), 200


@application.route("/pick_up_order", methods=["POST"])
@jwt_required()
def pick_up_order():
    errorMessage, errorCode, orderForPickUp = validatePickUpOrderRequest()
    if errorCode == 401:
        return jsonify(msg=errorMessage), errorCode
    if len(errorMessage) > 0:
        return jsonify(message=errorMessage), errorCode

    confirmOrderPickUp(orderForPickUp)

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.COURIER_APPLICATION_PORT)
