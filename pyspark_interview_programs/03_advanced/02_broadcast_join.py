"""Broadcast join example."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast


def main() -> None:
    spark = SparkSession.builder.appName("broadcast").master("local[*]").getOrCreate()
    big = spark.createDataFrame([(i, i % 10) for i in range(100)], ["id", "lookup_id"])
    small = spark.createDataFrame([(i, f"name_{i}") for i in range(10)], ["lookup_id", "name"])
    big.join(broadcast(small), "lookup_id").show(5)
    spark.stop()


if __name__ == "__main__":
    main()
