"""Streaming example reading from rate source writing parquet sink (Kafka->Delta pattern template)."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr


def main() -> None:
    spark = SparkSession.builder.appName("kafka-template").master("local[*]").getOrCreate()
    stream = spark.readStream.format("rate").option("rowsPerSecond", 10).load()
    enriched = stream.withColumn("tier", expr("CASE WHEN value % 2 = 0 THEN 'EVEN' ELSE 'ODD' END"))
    query = (enriched.writeStream
             .format("console")
             .option("truncate", False)
             .outputMode("append")
             .option("checkpointLocation", "output/_chk_stream")
             .start())
    query.awaitTermination(15)


if __name__ == "__main__":
    main()
