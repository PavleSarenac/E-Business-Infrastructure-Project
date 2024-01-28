from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps


def roleCheck(roleId):
    def decorator(function):
        @jwt_required()
        @wraps(function)
        def wrapper(*args, **kwargs):
            jwtToken = get_jwt()
            if jwtToken["roleId"] == roleId:
                return function(*args, **kwargs)
            else:
                return "Missing Authorization Header", 401

        return wrapper

    return decorator
