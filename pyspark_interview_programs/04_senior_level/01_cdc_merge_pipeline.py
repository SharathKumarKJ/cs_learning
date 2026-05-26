"""CDC merge pattern using PySpark DataFrame logic."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("cdc").master("local[*]").getOrCreate()
    target = spark.createDataFrame([(1, "Asha", "Pune"), (2, "Ravi", "Delhi")], ["id", "name", "city"])
    cdc = spark.createDataFrame(
        [(1, "Asha", "Bengaluru", "UPDATE", "2026-01-02"), (3, "Meera", "Mumbai", "INSERT", "2026-01-02"), (2, "Ravi", "Delhi", "DELETE", "2026-01-02")],
        ["id", "name", "city", "op", "ts"],
    )
    latest = cdc.withColumn("rn", row_number().over(Window.partitionBy("id").orderBy(col("ts").desc()))).where("rn = 1").drop("rn")
    deletes = latest.filter("op = 'DELETE'").select("id")
    upserts = latest.filter("op <> 'DELETE'").select("id", "name", "city")
    merged = target.join(deletes, "id", "left_anti").join(upserts, "id", "left_anti").unionByName(upserts)
    merged.orderBy("id").show()
    spark.stop()


if __name__ == "__main__":
    main()
