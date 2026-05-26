"""Running total and 7-day moving average."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, sum as spark_sum
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("running").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [("2026-01-01", 100), ("2026-01-02", 150), ("2026-01-03", 200), ("2026-01-04", 50), ("2026-01-05", 80)],
        ["order_date", "amount"],
    )
    w_running = Window.orderBy("order_date").rowsBetween(Window.unboundedPreceding, Window.currentRow)
    w_7d = Window.orderBy("order_date").rowsBetween(-6, 0)
    df.withColumn("running_total", spark_sum("amount").over(w_running)) \
      .withColumn("ma_7d", avg("amount").over(w_7d)) \
      .show()
    spark.stop()


if __name__ == "__main__":
    main()
