"""Flatten nested JSON into a flat DataFrame."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode


def main() -> None:
    spark = SparkSession.builder.appName("flatten").master("local[*]").getOrCreate()
    data = [{"id": 1, "name": "Asha", "address": {"city": "Pune", "zip": "411001"},
             "orders": [{"order_id": 100, "amount": 50}, {"order_id": 101, "amount": 70}]}]
    df = spark.createDataFrame(data)
    flat = (df
            .withColumn("city", col("address.city"))
            .withColumn("zip", col("address.zip"))
            .withColumn("order", explode("orders"))
            .select("id", "name", "city", "zip",
                    col("order.order_id").alias("order_id"),
                    col("order.amount").alias("amount")))
    flat.show()
    spark.stop()


if __name__ == "__main__":
    main()
