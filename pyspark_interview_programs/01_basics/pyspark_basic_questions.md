# PySpark Basic Interview Questions (Detailed)

### 1. What is PySpark?
PySpark is the Python API for Apache Spark, a distributed in-memory compute engine. It lets you process large datasets in parallel across a cluster using Python while Spark runs on the JVM. It supports batch, streaming, SQL, ML, and graph workloads.

### 2. What is a SparkSession?
`SparkSession` is the unified entry point for DataFrame, SQL, Catalog, and streaming APIs (introduced in Spark 2.0, replacing `SQLContext` and `HiveContext`). It manages configuration, the underlying `SparkContext`, and the metastore connection. You create one with `SparkSession.builder.appName(...).getOrCreate()`.

### 3. What is a DataFrame?
A DataFrame is a distributed collection of rows organized into named columns with a schema, similar to a table or a pandas DataFrame. Internally it is a logical plan over RDDs of `Row` objects, optimized by Catalyst. It supports SQL-like operations and is the recommended API over raw RDDs.

### 4. What is lazy evaluation?
Spark builds a logical plan as you chain transformations but does not run anything until an action is called. This lets Catalyst optimize the entire pipeline (predicate pushdown, column pruning, join reordering) before execution. Examples: `.filter()` is lazy; `.count()` triggers execution.

### 5. Examples of transformations.
Transformations return a new DataFrame and are lazy: `select`, `filter`/`where`, `withColumn`, `drop`, `join`, `groupBy`, `agg`, `union`, `repartition`, `coalesce`, `orderBy`, `distinct`, `dropDuplicates`. They are categorized as narrow (no shuffle) or wide (shuffle).

### 6. Examples of actions.
Actions trigger execution and return results to the driver or write data: `count`, `collect`, `show`, `take`, `first`, `head`, `write`, `toPandas`, `foreach`, `save`. Use them sparingly on large data because they materialize results.

### 7. Difference between `select` and `withColumn`?
`select` projects a chosen list of columns or expressions, returning only those columns. `withColumn` returns all existing columns plus one new/replaced column. Chaining many `withColumn` calls is slower than a single `select` because each call creates a new projection node in the plan.

### 8. Difference between `filter` and `where`?
They are exact aliases for the same operation; pick whichever reads better. Both accept a SQL string (`"amount > 100"`) or a Column expression (`col("amount") > 100`).

### 9. What is a schema?
A schema describes column names, types, and nullability via `StructType` and `StructField`. Defining it explicitly avoids costly schema inference, prevents type drift, and catches bad data early. Always set schema for production reads.

### 10. Why avoid `collect` on large data?
`collect` brings every row to the driver JVM as a Python list. On large data this causes driver out-of-memory and network bottlenecks. Use `take(n)`, `show()`, or write to storage instead; use `toLocalIterator()` for streaming small batches to driver.

### 11. What is partitioning?
Spark splits a DataFrame into partitions, each processed by one task on one executor core. Good partitioning balances data volume and parallelism (typically 2-4 tasks per core). Bad partitioning causes skew, OOM, or wasted cores.

### 12. What is `repartition`?
`repartition(n)` or `repartition(col)` does a full shuffle to create `n` evenly distributed partitions or hash-partition by column. Use it before wide operations, joins on a key, or to balance skewed data. It is expensive but produces uniform partitions.

### 13. What is `coalesce`?
`coalesce(n)` reduces partition count by combining existing partitions without a full shuffle. It is much cheaper than `repartition` for shrinking, but can leave uneven partitions and limit parallelism. Common use: reduce output file count before write.

### 14. Common file formats in Spark.
Parquet (columnar, default for analytics), ORC (columnar, common in Hive), Delta/Iceberg/Hudi (transactional table formats), Avro (row-based, schema-evolution friendly for streaming), CSV/JSON (slow, text, for ingestion only).

### 15. Why is Parquet preferred?
Parquet is columnar, splittable, compressed (snappy/zstd), and stores statistics/min-max per row group. This enables predicate pushdown, column pruning, and partition pruning, which slash I/O. It is the default for almost all analytical workloads.

### 16. What is the Catalyst optimizer?
Catalyst is Spark SQL's rule-based + cost-based optimizer that transforms a parsed logical plan into an optimized physical plan. Optimizations include constant folding, predicate pushdown, projection pruning, join reordering, and selecting join strategies (broadcast vs sort-merge vs shuffle-hash).

### 17. What is Tungsten?
Tungsten is Spark's execution engine that uses off-heap memory management, cache-aware computation, and whole-stage code generation (compiling multiple operators into a single JVM method) to dramatically improve CPU and memory efficiency.

### 18. What is a narrow transformation?
A narrow transformation produces each output partition from exactly one input partition — no shuffle. Examples: `map`, `filter`, `select`, `withColumn`. These pipeline efficiently and recover quickly on failure.

### 19. What is a wide transformation?
A wide transformation requires data movement across the network (shuffle) because output partitions depend on multiple input partitions. Examples: `groupBy`, `join`, `distinct`, `repartition`, `orderBy`. Shuffles are the main cost in Spark jobs.

### 20. What is a shuffle?
A shuffle is the redistribution of data between executors triggered by wide transformations. It writes intermediate files to local disk on the map side, then fetches them on the reduce side. Shuffles cause network I/O, disk I/O, and serialization cost — minimizing them is the core of Spark tuning.
