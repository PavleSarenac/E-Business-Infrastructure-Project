from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User
import re

application = Flask(__name__)
application.config.from_object(Configuration)


def registration(userRole):
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    isForenameEmpty = len(forename) == 0
    isSurnameEmpty = len(surname) == 0
    isEmailEmpty = len(email) == 0
    isPasswordEmpty = len(password) == 0

    if isForenameEmpty:
        return jsonify(message="Field forename is missing."), 400
    if isSurnameEmpty:
        return jsonify(message="Field surname is missing."), 400
    if isEmailEmpty:
        return jsonify(message="Field email is missing."), 400
    if isPasswordEmpty:
        return jsonify(message="Field password is missing."), 400

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+'
    if not re.match(email_pattern, email):
        return jsonify(message="Invalid email."), 400

    if len(password) < 8:
        return jsonify(message="Invalid password."), 400

    userWithSameEmailAddress = User.query.filter(User.email == email).first()
    if userWithSameEmailAddress:
        return jsonify(message="Email already exists."), 400

    userRoleId = 1 if (userRole == "customer") else 3
    user = User(email=email, password=password, forename=forename, surname=surname, roleId=userRoleId)
    database.session.add(user)
    database.session.commit()

    return Response(status=200)


@application.route("/register_customer", methods=["POST"])
def registerCustomer():
    return registration("customer")


@application.route("/register_courier", methods=["POST"])
def registerCourier():
    return registration("courier")


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)
