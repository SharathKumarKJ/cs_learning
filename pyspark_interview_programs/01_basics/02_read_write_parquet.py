"""Read CSV, write Parquet partitioned."""
from pyspark.sql import SparkSession


def main() -> None:
    spark = SparkSession.builder.appName("read-write").master("local[*]").getOrCreate()
    data = [(1, "Asha", "2026-01-01"), (2, "Ravi", "2026-01-01"), (3, "Meera", "2026-01-02")]
    df = spark.createDataFrame(data, ["id", "name", "order_date"])
    df.write.mode("overwrite").partitionBy("order_date").parquet("output/orders_parquet")
    spark.read.parquet("output/orders_parquet").show()
    spark.stop()


if __name__ == "__main__":
    main()
