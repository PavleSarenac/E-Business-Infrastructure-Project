import os

DATABASE_URL = "CHANGE THIS !!!!!!!!!" if ("PRODUCTION" in os.environ) else "localhost"


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{DATABASE_URL}/authentication"
