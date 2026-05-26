"""Deduplicate keeping the latest record by timestamp."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("dedup").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [(1, "Asha", "2026-01-01"), (1, "Asha", "2026-01-05"), (2, "Ravi", "2026-01-02")],
        ["id", "name", "ts"],
    )
    w = Window.partitionBy("id").orderBy(col("ts").desc())
    df.withColumn("rn", row_number().over(w)).filter("rn = 1").drop("rn").show()
    spark.stop()


if __name__ == "__main__":
    main()
