from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window


def main() -> None:
    spark = SparkSession.builder.appName("latest-record").master("local[*]").getOrCreate()
    data = [(1, "Asha", "2026-01-01"), (1, "Asha", "2026-01-03"), (2, "Ravi", "2026-01-02")]
    df = spark.createDataFrame(data, ["customer_id", "name", "updated_at"])
    window = Window.partitionBy("customer_id").orderBy(col("updated_at").desc())
    latest = df.withColumn("rn", row_number().over(window)).where(col("rn") == 1).drop("rn")
    latest.show()
    spark.stop()


if __name__ == "__main__":
    main()
