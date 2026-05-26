"""Generic data quality checks function."""
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum, when


def quality_report(df: DataFrame, key_col: str) -> None:
    total = df.count()
    nulls = df.select([spark_sum(col(c).isNull().cast("int")).alias(c) for c in df.columns]).collect()[0].asDict()
    duplicates = total - df.select(key_col).distinct().count()
    print({"total_rows": total, "null_counts": nulls, "duplicate_keys": duplicates})


def main() -> None:
    spark = SparkSession.builder.appName("dq").master("local[*]").getOrCreate()
    df = spark.createDataFrame([(1, "Asha", 100), (1, "Asha", 100), (2, None, 200)], ["id", "name", "amount"])
    quality_report(df, "id")
    spark.stop()


if __name__ == "__main__":
    main()
