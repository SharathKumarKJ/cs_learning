"""Classic word count interview problem."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split, lower, regexp_replace


def main() -> None:
    spark = SparkSession.builder.appName("wordcount").master("local[*]").getOrCreate()
    df = spark.createDataFrame([("hello world hello spark",), ("data engineer spark world",)], ["line"])
    words = df.withColumn("line", lower(regexp_replace("line", "[^a-zA-Z ]", ""))).withColumn("word", explode(split("line", " ")))
    words.groupBy("word").count().orderBy("count", ascending=False).show()
    spark.stop()


if __name__ == "__main__":
    main()
