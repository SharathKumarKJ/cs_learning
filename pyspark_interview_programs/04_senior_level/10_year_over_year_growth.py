"""Year-over-year monthly revenue growth."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_format, lag, sum as spark_sum
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("yoy").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [("2025-01-15", 100), ("2025-02-15", 200), ("2026-01-10", 150), ("2026-02-10", 250)],
        ["order_date", "amount"],
    ).withColumn("order_date", col("order_date").cast("date"))
    monthly = df.groupBy(date_format("order_date", "yyyy-MM").alias("ym")).agg(spark_sum("amount").alias("rev"))
    w = Window.orderBy("ym")
    monthly.withColumn("rev_prev_year", lag("rev", 12).over(w)).show()
    spark.stop()


if __name__ == "__main__":
    main()
