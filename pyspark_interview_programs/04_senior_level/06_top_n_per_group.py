"""Top N products per category by revenue."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number, sum as spark_sum
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("topn").master("local[*]").getOrCreate()
    df = spark.createDataFrame(
        [("Electronics", "P1", 100), ("Electronics", "P2", 200), ("Electronics", "P3", 150),
         ("Books", "P4", 50), ("Books", "P5", 90), ("Books", "P6", 30)],
        ["category", "product", "revenue"],
    )
    agg = df.groupBy("category", "product").agg(spark_sum("revenue").alias("revenue"))
    w = Window.partitionBy("category").orderBy(col("revenue").desc())
    agg.withColumn("rn", row_number().over(w)).filter(col("rn") <= 2).show()
    spark.stop()


if __name__ == "__main__":
    main()
