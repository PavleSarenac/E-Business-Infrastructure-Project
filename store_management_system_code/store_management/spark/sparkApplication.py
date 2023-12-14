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
    subprocess.check_output(["/template.sh"])
    with open("/app/store_management/spark/productStatisticsTempFile.txt", "r") as productStatisticsFile:
        productStatistics = productStatisticsFile.read()
    return productStatistics


@application.route("/category_statistics", methods=["GET"])
def category_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/store_management/spark/categoryStatisticsSparkApp.py"
    os.environ["SPARK_SUBMIT_ARGS"] = \
        "--driver-class-path /app/store_management/spark/mysql-connector-j-8.0.33.jar" \
        " --jars /app/store_management/spark/mysql-connector-j-8.0.33.jar"
    subprocess.check_output(["/template.sh"])
    with open("/app/store_management/spark/categoryStatisticsTempFile.txt", "r") as categoryStatisticsFile:
        categoryStatistics = categoryStatisticsFile.read()
    return categoryStatistics


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5004)
