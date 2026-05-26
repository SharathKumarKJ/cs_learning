"""Pivot and unpivot patterns."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import expr


def main() -> None:
    spark = SparkSession.builder.appName("pivot").master("local[*]").getOrCreate()
    df = spark.createDataFrame([("Asha", "Jan", 100), ("Asha", "Feb", 200), ("Ravi", "Jan", 150)], ["name", "month", "amount"])
    pivoted = df.groupBy("name").pivot("month").sum("amount")
    pivoted.show()
    unpivoted = pivoted.selectExpr("name", "stack(2, 'Jan', Jan, 'Feb', Feb) as (month, amount)").where("amount is not null")
    unpivoted.show()
    spark.stop()


if __name__ == "__main__":
    main()
