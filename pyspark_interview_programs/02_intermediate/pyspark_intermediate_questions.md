# PySpark Intermediate Interview Questions (Detailed)

## Joins

### 1. What join types does Spark support?
Inner, left/right/full outer, left_semi (keeps left rows that match), left_anti (keeps left rows with no match), and cross. Spark also supports special hints: broadcast (BHJ), shuffle hash (SHJ), sort-merge (SMJ), and shuffle replicate NL.

### 2. When should you use a broadcast join?
When one side is small enough to fit in each executor's memory (default threshold `spark.sql.autoBroadcastJoinThreshold = 10 MB`, often raised to 100 MB for production). Spark ships the small DataFrame to every executor, eliminating shuffle on the large side. Use `broadcast(df)` hint to force it.

### 3. What is a left semi join?
Returns rows from the left side that have at least one match on the right side, but no columns from the right are returned. It is logically equivalent to `WHERE EXISTS (...)` and is often faster than inner join + distinct.

### 4. What is a left anti join?
Returns rows from the left side that have no match on the right side. Equivalent to `WHERE NOT EXISTS (...)`. Common use: find customers without orders, products never sold.

### 5. How do you handle duplicate column names after joins?
Either join with a column name string (`df1.join(df2, "id")` returns one `id`), or alias DataFrames (`df1.alias("a").join(df2.alias("b"), ...)`) and select explicitly. Renaming with `withColumnRenamed` before the join is also clean.

## Windows

### 6. Difference between `row_number`, `rank`, and `dense_rank`?
`row_number` assigns a unique sequential number with no ties broken arbitrarily. `rank` gives ties the same value and leaves gaps (1,1,3). `dense_rank` gives ties the same value with no gaps (1,1,2). Use `row_number` for "pick one row per group", `dense_rank` for "Nth distinct salary".

### 7. How do you get latest record per key?
Use a window partitioned by key and ordered by timestamp descending, then keep `row_number() = 1`. This handles ties deterministically by adding a tiebreaker like a sequence column to the `orderBy`.

### 8. How do you calculate running total?
`sum(amount).over(Window.partitionBy(key).orderBy(date).rowsBetween(Window.unboundedPreceding, Window.currentRow))`. Be explicit about the frame; the default frame depends on whether you have an `orderBy`, which is a common source of bugs.

## Data quality

### 9. How do you remove duplicates?
`dropDuplicates(subset)` removes exact duplicates over the subset of columns and keeps an arbitrary row. To keep a *specific* row (e.g. latest), use a window with `row_number()` and filter `= 1`. `distinct()` removes only fully-identical rows.

### 10. How do you handle nulls?
Inspect with `df.summary()` and per-column null counts. Use `fillna({"col": default})`, `dropna(subset, how, thresh)`, or `coalesce(col1, col2, lit(default))`. For joins, remember nulls never match in equi-joins; use null-safe equality `<=>` when needed.

### 11. How do you validate schema?
Define an expected `StructType` and either pass it to `spark.read.schema(...)` or compare with the read schema (set/diff of fields). For production, run a contract check at the start of the job and fail fast if columns or types drift.

## File processing

### 12. How do you read multiple files?
Pass a directory path, a glob (`s3://bucket/orders/2026-01-*/`), a comma-separated string, or a list of paths. Spark reads them in parallel; combine with `recursiveFileLookup=true` and `pathGlobFilter` for nested layouts.

### 13. How do you add input file name?
Use `from pyspark.sql.functions import input_file_name` and `df.withColumn("source_file", input_file_name())`. Useful for lineage, debugging, and partition recovery.

### 14. How do you write partitioned output?
Use `df.write.partitionBy("col1", "col2").parquet(path)`. Choose partition columns with low-to-moderate cardinality (date works well). Pair with `repartition(*partition_cols)` before write to avoid tiny files per partition per task.

### 15. What is the small file problem?
Many tiny files (KBs each) overwhelm the driver with metadata, slow down listing on object stores, and reduce read throughput. Causes: too many output partitions, over-partitioning by high-cardinality columns, frequent small streaming writes. Fix with compaction jobs, `coalesce`/`repartition` before write, or table format auto-optimize.
