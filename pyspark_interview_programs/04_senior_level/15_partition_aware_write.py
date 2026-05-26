"""Partitioned write with file size control via repartition."""
from pyspark.sql import SparkSession


def main() -> None:
    spark = SparkSession.builder.appName("partition-write").master("local[*]").getOrCreate()
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    df = spark.createDataFrame(
        [(i, f"name_{i}", f"2026-01-{(i % 5) + 1:02d}") for i in range(1, 101)],
        ["id", "name", "order_date"],
    )
    (df.repartition("order_date")
       .write.mode("overwrite")
       .partitionBy("order_date")
       .parquet("output/partitioned_orders"))
    spark.read.parquet("output/partitioned_orders").groupBy("order_date").count().show()
    spark.stop()


if __name__ == "__main__":
    main()
