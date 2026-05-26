from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum


def main() -> None:
    spark = SparkSession.builder.appName("dataframe-basics").master("local[*]").getOrCreate()
    data = [(1, "Asha", "IN", 1000), (2, "Ravi", "IN", 1500), (3, "John", "US", 800)]
    df = spark.createDataFrame(data, ["id", "name", "country", "amount"])
    df.select("name", "country", "amount").where(col("amount") >= 1000).show()
    df.groupBy("country").agg(spark_sum("amount").alias("total_amount")).show()
    spark.stop()


if __name__ == "__main__":
    main()
