from pyspark.sql import SparkSession
from pyspark.sql import functions as func

import os

PRODUCTION = True if "PRODUCTION" in os.environ else False
DATABASE_URL = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else "localhost"
DATABASE_USERNAME = os.environ["DATABASE_USERNAME"] if "DATABASE_USERNAME" in os.environ else "root"
DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"] if "DATABASE_PASSWORD" in os.environ else "root"

builder = SparkSession.builder.appName("PySpark Database example")

if not PRODUCTION:
    builder = builder.master("local[*]")

builder = builder.config("spark.driver.extraClassPath", "/app/store_management/spark/mysql-connector-j-8.0.33.jar")

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

categoryDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.categories") \
    .option("user", DATABASE_USERNAME) \
    .option("password", DATABASE_PASSWORD) \
    .load()

productCategoryDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_URL}:3306/store") \
    .option("dbtable", "store.productcategory") \
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

print(productStatisticsResponse)

categoryStatistics = categoryDataFrame.join(
    productCategoryDataFrame, categoryDataFrame["id"] == productCategoryDataFrame["categoryId"], "left_outer"
).join(
    productOrderDataFrame, productCategoryDataFrame["productId"] == productOrderDataFrame["productId"], "left_outer"
).join(
    orderDataFrame, productOrderDataFrame["orderId"] == orderDataFrame["id"], "left_outer"
).groupBy(
    categoryDataFrame["categoryName"].alias("CategoryName")
).agg(
    func.sum(
        func.when(orderDataFrame["orderStatus"] == "COMPLETE", productOrderDataFrame["quantity"]).otherwise(0)
    ).alias("Quantity")
).orderBy(
    func.desc("Quantity"), func.asc("CategoryName")
).collect()

categoryStatisticsResponse = {"statistics": []}
for row in categoryStatistics:
    categoryStatisticsResponse["statistics"].append(row["CategoryName"])

print(categoryStatisticsResponse)

spark.stop()
