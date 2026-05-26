"""Pandas UDF (vectorized) example - far faster than row-wise Python UDFs."""
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import DoubleType


@pandas_udf(DoubleType())
def add_tax(amount: pd.Series) -> pd.Series:
    return amount * 1.18


def main() -> None:
    spark = SparkSession.builder.appName("pandas-udf").master("local[*]").getOrCreate()
    df = spark.createDataFrame([(1, 100.0), (2, 250.0)], ["id", "amount"])
    df.withColumn("with_tax", add_tax("amount")).show()
    spark.stop()


if __name__ == "__main__":
    main()
