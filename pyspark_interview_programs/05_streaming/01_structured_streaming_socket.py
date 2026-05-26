"""Structured Streaming example reading from rate source."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import window


def main() -> None:
    spark = SparkSession.builder.appName("streaming").master("local[*]").getOrCreate()
    stream = spark.readStream.format("rate").option("rowsPerSecond", 5).load()
    aggregated = stream.groupBy(window("timestamp", "10 seconds")).count()
    query = aggregated.writeStream.outputMode("complete").format("console").start()
    query.awaitTermination(20)


if __name__ == "__main__":
    main()
