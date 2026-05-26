"""Sessionize user events with 30-minute inactivity gap."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, sum as spark_sum, unix_timestamp, when
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("session").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [("u1", "2026-01-01 10:00:00"), ("u1", "2026-01-01 10:10:00"),
         ("u1", "2026-01-01 11:00:00"), ("u2", "2026-01-01 10:00:00")],
        ["user_id", "event_time"],
    ).withColumn("event_time", col("event_time").cast("timestamp"))
    w = Window.partitionBy("user_id").orderBy("event_time")
    diff = unix_timestamp("event_time") - unix_timestamp(lag("event_time").over(w))
    df = df.withColumn("is_new", when((diff > 1800) | diff.isNull(), 1).otherwise(0))
    df = df.withColumn("session_id", spark_sum("is_new").over(w))
    df.show()
    spark.stop()


if __name__ == "__main__":
    main()
