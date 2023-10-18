import os

DATABASE_URL = "authenticationDatabase" if ("PRODUCTION" in os.environ) else "localhost"


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{DATABASE_URL}/authentication"
