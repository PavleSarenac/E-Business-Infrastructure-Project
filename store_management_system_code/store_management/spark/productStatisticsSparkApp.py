from pyspark.sql import SparkSession
from pyspark.sql import functions as func

import os
import json

PRODUCTION = True if "PRODUCTION" in os.environ else False
DATABASE_URL = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else "localhost"
DATABASE_USERNAME = os.environ["DATABASE_USERNAME"] if "DATABASE_USERNAME" in os.environ else "root"
DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"] if "DATABASE_PASSWORD" in os.environ else "root"

builder = SparkSession.builder.appName("Product statistics spark app.")

# local[*] means "utilize all available processor cores"
if not PRODUCTION:
    builder = builder.master("local[*]").config("spark.driver.extraClassPath",
                                                "/app/store_management/spark/mysql-connector-j-8.0.33.jar")

spark = builder.getOrCreate()

productDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.products") \
    .option("user", DATABASE_USERNAME) \
    .option("password", DATABASE_PASSWORD) \
    .load()

productOrderDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.productorder") \
    .option("user", DATABASE_USERNAME) \
    .option("password", DATABASE_PASSWORD) \
    .load()

orderDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.orders") \
    .option("user", DATABASE_USERNAME) \
    .option("password", DATABASE_PASSWORD) \
    .load()

productStatistics = productDataFrame.join(
    productOrderDataFrame, productDataFrame["id"] == productOrderDataFrame["productId"]
).join(
    orderDataFrame, productOrderDataFrame["orderId"] == orderDataFrame["id"]
).groupBy(
    productDataFrame["productName"].alias("ProductName")
).agg(
    func.sum(
        func.when(orderDataFrame["orderStatus"] == "COMPLETE", productOrderDataFrame["quantity"]).otherwise(0)
    ).alias("Sold"),
    func.sum(
        func.when(orderDataFrame["orderStatus"] != "COMPLETE", productOrderDataFrame["quantity"]).otherwise(0)
    ).alias("Waiting")
).collect()

productStatisticsResponse = {"statistics": []}
for row in productStatistics:
    productStatisticsResponse["statistics"].append({
        "name": row["ProductName"],
        "sold": int(row["Sold"]),
        "waiting": int(row["Waiting"])
    })

print(json.dumps(productStatisticsResponse), end="", flush=True)

spark.stop()
