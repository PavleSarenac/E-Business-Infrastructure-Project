from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps
from flask import jsonify


def roleCheck(roleId):
    def decorator(function):
        @jwt_required()
        @wraps(function)
        def wrapper(*args, **kwargs):
            jwtToken = get_jwt()
            if jwtToken["roleId"] == roleId:
                return function(*args, **kwargs)
            else:
                return jsonify(msg="Missing Authorization Header"), 401

        return wrapper

    return decorator
