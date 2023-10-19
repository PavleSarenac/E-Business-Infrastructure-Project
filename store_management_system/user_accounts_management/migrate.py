from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import database, Role, User
from sqlalchemy_utils import database_exists, create_database

OWNER_ROLE_ID = 2

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

    storeOwner = User(
        email="onlymoney@gmail.com",
        password="evenmoremoney",
        forename="Scrooge",
        surname="McDuck",
        roleId=OWNER_ROLE_ID
    )

    database.session.add(storeOwner)
    database.session.commit()
