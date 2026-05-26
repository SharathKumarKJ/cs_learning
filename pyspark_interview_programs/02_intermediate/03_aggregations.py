"""GroupBy aggregations and pivots."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, sum as spark_sum


def main() -> None:
    spark = SparkSession.builder.appName("aggs").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [("IN", "A", 100), ("IN", "B", 200), ("US", "A", 300), ("US", "B", 50)],
        ["country", "category", "amount"],
    )
    df.groupBy("country").agg(spark_sum("amount").alias("total"), avg("amount").alias("avg"), count("*").alias("orders")).show()
    df.groupBy("country").pivot("category").sum("amount").show()
    spark.stop()


if __name__ == "__main__":
    main()
