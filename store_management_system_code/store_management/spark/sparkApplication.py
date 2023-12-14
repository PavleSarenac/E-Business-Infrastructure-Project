from flask import Flask
import os
import subprocess

application = Flask(__name__)


@application.route("/product_statistics", methods=["GET"])
def product_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/store_management/spark/productStatisticsSparkApp.py"
    os.environ["SPARK_SUBMIT_ARGS"] = \
        "--driver-class-path /app/store_management/spark/mysql-connector-j-8.0.33.jar" \
        " --jars /app/store_management/spark/mysql-connector-j-8.0.33.jar"
    productStatistics = subprocess.check_output(["/template.sh"])
    print(productStatistics.decode())
    return productStatistics.decode()


@application.route("/category_statistics", methods=["GET"])
def category_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/store_management/spark/categoryStatisticsSparkApp.py"
    os.environ["SPARK_SUBMIT_ARGS"] = \
        "--driver-class-path /app/store_management/spark/mysql-connector-j-8.0.33.jar" \
        " --jars /app/store_management/spark/mysql-connector-j-8.0.33.jar"
    categoryStatistics = subprocess.check_output(["/template.sh"])
    print(categoryStatistics.decode())
    return categoryStatistics.decode()


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5004)
