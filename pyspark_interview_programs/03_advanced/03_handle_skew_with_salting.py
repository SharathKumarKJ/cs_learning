"""Skew handling using salting technique."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, expr, lit


def main() -> None:
    spark = SparkSession.builder.appName("salting").master("local[*]").getOrCreate()
    skewed = spark.createDataFrame([("A", i) for i in range(1000)] + [("B", 1), ("C", 1)], ["key", "value"])
    lookup = spark.createDataFrame([("A", "x"), ("B", "y"), ("C", "z")], ["key", "meta"])
    salt_count = 5
    skewed_salted = skewed.withColumn("salt", (col("value") % lit(salt_count))).withColumn("salted_key", concat_ws("_", col("key"), col("salt")))
    lookup_salted = lookup.withColumn("salt", expr(f"explode(sequence(0, {salt_count - 1}))")).withColumn("salted_key", concat_ws("_", col("key"), col("salt")))
    skewed_salted.join(lookup_salted, "salted_key").show(5)
    spark.stop()


if __name__ == "__main__":
    main()
