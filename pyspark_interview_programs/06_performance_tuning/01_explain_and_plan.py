"""Inspect Spark physical plan."""
from pyspark.sql import SparkSession


def main() -> None:
    spark = SparkSession.builder.appName("plan").master("local[*]").getOrCreate()
    df = spark.createDataFrame([(i, i * 2) for i in range(100)], ["a", "b"])
    df.filter("a > 10").groupBy("b").count().explain("formatted")
    spark.stop()


if __name__ == "__main__":
    main()
