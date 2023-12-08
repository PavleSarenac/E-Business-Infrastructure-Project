from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User
import re
from sqlalchemy import and_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

CUSTOMER_ROLE_ID = 1
COURIER_ROLE_ID = 3

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


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

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.(com|org|net|edu|gov|mil|io|co\.uk)$'
    if not re.match(email_pattern, email):
        return jsonify(message="Invalid email."), 400

    if len(password) < 8:
        return jsonify(message="Invalid password."), 400

    userWithSameEmailAddress = User.query.filter(User.email == email).first()
    if userWithSameEmailAddress:
        return jsonify(message="Email already exists."), 400

    userRoleId = CUSTOMER_ROLE_ID if userRole == "customer" else COURIER_ROLE_ID
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


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    isEmailEmpty = len(email) == 0
    isPasswordEmpty = len(password) == 0

    if isEmailEmpty:
        return jsonify(message="Field email is missing."), 400
    if isPasswordEmpty:
        return jsonify(message="Field password is missing."), 400

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.(com|org|net|edu|gov|mil|io|co\.uk)$'
    if not re.match(email_pattern, email):
        return jsonify(message="Invalid email."), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if not user:
        return jsonify(message="Invalid credentials."), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "password": user.password,
        "roleId": str(user.roleId)
    }
    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    return jsonify(accessToken=accessToken), 200


@application.route("/delete", methods=["POST"])
@jwt_required()
def deleteUser():
    userAccessTokenIdentity = get_jwt_identity()
    user = User.query.filter(User.email == userAccessTokenIdentity).first()
    if not user:
        return jsonify(message="Unknown user."), 400
    database.session.delete(user)
    database.session.commit()
    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.AUTHENTICATION_APPLICATION_PORT)
