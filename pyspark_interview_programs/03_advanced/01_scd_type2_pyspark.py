from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_date, lit, when


def main() -> None:
    spark = SparkSession.builder.appName("scd-type-2").master("local[*]").getOrCreate()
    current = spark.createDataFrame(
        [(1, "Asha", "Pune", "2026-01-01", None, True), (2, "Ravi", "Delhi", "2026-01-01", None, True)],
        ["customer_id", "name", "city", "valid_from", "valid_to", "is_current"],
    )
    incoming = spark.createDataFrame([(1, "Asha", "Bengaluru"), (3, "Meera", "Mumbai")], ["customer_id", "name", "city"])
    joined = current.alias("c").join(incoming.alias("i"), "customer_id", "full_outer")
    expired = joined.where((col("c.is_current") == True) & (col("i.city").isNotNull()) & (col("c.city") != col("i.city"))).select(
        col("customer_id"), col("c.name").alias("name"), col("c.city").alias("city"), col("c.valid_from"), current_date().alias("valid_to"), lit(False).alias("is_current")
    )
    new_rows = joined.where(col("i.city").isNotNull() & ((col("c.city").isNull()) | (col("c.city") != col("i.city")))).select(
        col("customer_id"), col("i.name").alias("name"), col("i.city").alias("city"), current_date().alias("valid_from"), lit(None).cast("date").alias("valid_to"), lit(True).alias("is_current")
    )
    unchanged = current.join(expired.select("customer_id"), "customer_id", "left_anti")
    unchanged.unionByName(expired).unionByName(new_rows).show(truncate=False)
    spark.stop()


if __name__ == "__main__":
    main()
