"""All join types in PySpark."""
from pyspark.sql import SparkSession


def main() -> None:
    spark = SparkSession.builder.appName("joins").master("local[*]").getOrCreate()
    customers = spark.createDataFrame([(1, "Asha"), (2, "Ravi"), (3, "Meera")], ["id", "name"])
    orders = spark.createDataFrame([(1, 100), (1, 200), (2, 150), (4, 80)], ["customer_id", "amount"])
    print("INNER")
    customers.join(orders, customers.id == orders.customer_id, "inner").show()
    print("LEFT")
    customers.join(orders, customers.id == orders.customer_id, "left").show()
    print("LEFT_ANTI")
    customers.join(orders, customers.id == orders.customer_id, "left_anti").show()
    print("LEFT_SEMI")
    customers.join(orders, customers.id == orders.customer_id, "left_semi").show()
    spark.stop()


if __name__ == "__main__":
    main()
