from flask import Flask
from configuration import Configuration
from models import database

application = Flask(__name__)
application.config.from_object(Configuration)


@application.route("/update", methods=["POST"])
def update():
    pass


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host=Configuration.HOST, port=Configuration.OWNER_APPLICATION_PORT)
