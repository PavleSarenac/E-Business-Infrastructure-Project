import os
from datetime import timedelta


class Configuration:
    HOST = "0.0.0.0" if "PRODUCTION" in os.environ else "localhost"
    OWNER_APPLICATION_PORT = 5001
    CUSTOMER_APPLICATION_PORT = 5002
    COURIER_APPLICATION_PORT = 5003

    DATABASE_URL = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else "localhost"
    DATABASE_USERNAME = os.environ["DATABASE_USERNAME"] if "DATABASE_USERNAME" in os.environ else "root"
    DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"] if "DATABASE_PASSWORD" in os.environ else "root"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/store"

    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
