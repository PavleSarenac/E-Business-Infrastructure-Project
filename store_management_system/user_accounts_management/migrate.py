from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import database, Role, User
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, database)

if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"])

database.init_app(application)

with application.app_context() as context:
    init()
    migrate(message="Initial production migration.")
    upgrade()

    customerRole = Role(roleDescription="customer")
    storeOwnerRole = Role(roleDescription="storeOwner")
    courierRole = Role(roleDescription="courier")

    database.session.add(customerRole)
    database.session.add(storeOwnerRole)
    database.session.add(courierRole)
    database.session.commit()

    storeOwner1 = User(
        email="storeOwner1@gmail.com",
        password="storeOwner1Password",
        forename="storeOwner1Forename",
        surname="storeOwner1Surname",
        roleId=2
    )
    storeOwner2 = User(
        email="storeOwner2@gmail.com",
        password="storeOwner2Password",
        forename="storeOwner2Forename",
        surname="storeOwner2Surname",
        roleId=2
    )
    storeOwner3 = User(
        email="storeOwner3@gmail.com",
        password="storeOwner3Password",
        forename="storeOwner3Forename",
        surname="storeOwner3Surname",
        roleId=2
    )

    database.session.add(storeOwner1)
    database.session.add(storeOwner2)
    database.session.add(storeOwner3)
    database.session.commit()
