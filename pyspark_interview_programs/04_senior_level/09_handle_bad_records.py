"""Reading CSV with bad-record handling and corrupt column."""
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType


def main() -> None:
    spark = SparkSession.builder.appName("bad-records").master("local[*]").getOrCreate()
    path = Path("output/bad.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("id,name,age\n1,Asha,30\n2,Ravi,abc\n3,Meera,25\n")
    schema = StructType([
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("age", IntegerType()),
        StructField("_corrupt", StringType()),
    ])
    df = spark.read.option("header", "true").option("mode", "PERMISSIVE") \
        .option("columnNameOfCorruptRecord", "_corrupt").schema(schema).csv(str(path))
    df.show()
    spark.stop()


if __name__ == "__main__":
    main()
