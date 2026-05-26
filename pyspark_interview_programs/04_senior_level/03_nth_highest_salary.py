"""Nth highest salary per department using PySpark."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, dense_rank
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("nth-salary").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [("HR", "A", 50000), ("HR", "B", 70000), ("HR", "C", 70000), ("ENG", "D", 90000), ("ENG", "E", 80000)],
        ["dept", "name", "salary"],
    )
    n = 2
    ranked = df.withColumn("rk", dense_rank().over(Window.partitionBy("dept").orderBy(col("salary").desc())))
    ranked.filter(col("rk") == n).show()
    spark.stop()


if __name__ == "__main__":
    main()
