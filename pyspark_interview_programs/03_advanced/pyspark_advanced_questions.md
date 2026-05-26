# PySpark Advanced Interview Questions (Detailed)

### 1. What is Adaptive Query Execution (AQE)?
AQE re-optimizes the physical plan at runtime using actual shuffle statistics instead of the initial estimates. Enabled by default since Spark 3.2 via `spark.sql.adaptive.enabled=true`. It can coalesce small shuffle partitions, convert sort-merge joins to broadcast joins, and split skewed partitions.

### 2. What can AQE optimize?
Three main things: (a) coalesce post-shuffle partitions into larger ones to reduce small-task overhead; (b) dynamic switch from sort-merge to broadcast join when one side turns out smaller than expected; (c) skew join handling by splitting the skewed partitions of the large side and replicating the matching small side.

### 3. What is data skew?
Skew is uneven distribution of data across partitions where a few keys (or a single key) hold the bulk of the data. Symptoms: a few tasks run for hours while the rest finish in minutes, executor OOM, stage that "looks done" but never finishes. Common in joins on country, customer_id, or default/null keys.

### 4. How do you fix skewed joins?
Strategies in order of preference: (1) broadcast the small side if possible; (2) enable AQE skew join handling; (3) salt the skewed key by adding a random suffix on the large side and exploding the small side across all salt values; (4) split heavy keys into a separate job; (5) pre-aggregate before the join.

### 5. What is predicate pushdown?
Predicate pushdown moves filter expressions down to the data source so only matching rows are read from disk. Parquet, ORC, Delta, and JDBC sources support it. It dramatically reduces I/O — always filter as early and as specifically as possible.

### 6. What is partition pruning?
When a table is physically partitioned (e.g. `partitionBy("order_date")`) and a query filters on the partition column, Spark reads only matching partition folders. It is the cheapest possible filter — your data layout should match common query predicates.

### 7. Why avoid Python UDFs?
Python UDFs serialize each row, send it to a Python worker process, run the UDF, and serialize back to JVM. This crosses the JVM-Python boundary per row, is opaque to Catalyst (no pushdown, no codegen), and is 10-100x slower than built-in functions or pandas UDFs.

### 8. When are pandas UDFs useful?
Pandas UDFs (Arrow-backed) process a batch of rows as a pandas Series/DataFrame, eliminating per-row overhead. Use them when business logic genuinely needs Python libraries (numpy, scikit-learn) and cannot be expressed in built-in functions. They are much faster than regular Python UDFs but still slower than native expressions.

### 9. Difference between cache and persist?
`cache()` is shorthand for `persist(StorageLevel.MEMORY_AND_DISK)`. `persist()` lets you choose storage level: MEMORY_ONLY, MEMORY_AND_DISK, DISK_ONLY, plus serialized or replicated variants. Both mark the DataFrame for caching; the first action triggers it.

### 10. When should you cache?
Cache only when the same DataFrame is reused multiple times AND fits in available executor memory. Avoid caching for one-shot pipelines — it adds overhead. Always `unpersist()` after the dependent stages complete.

### 11. What is lineage?
Lineage is the DAG of transformations Spark records to recompute any partition from source data on failure. It provides fault tolerance without replication. Very long lineage (e.g. iterative ML) can be expensive to recompute — use checkpointing to truncate it.

### 12. What is checkpointing?
Checkpointing writes a DataFrame/RDD to reliable storage (HDFS/S3) and cuts the lineage at that point. Use `df.checkpoint()` (requires `sc.setCheckpointDir`) for batch and `option("checkpointLocation", ...)` for Structured Streaming (where it stores offsets and state).

### 13. How do you inspect a physical plan?
`df.explain()` shows the physical plan; `df.explain("formatted")` is the most readable; `df.explain("extended")` shows parsed, analyzed, optimized, and physical plans. Look for `Exchange` (shuffle), `BroadcastExchange`, `Scan parquet` with `PushedFilters`, and `WholeStageCodegen` boundaries.

### 14. What causes executor OOM?
Common causes: collect/toPandas on large data, skewed shuffle partitions, large broadcast variables, too many concurrent tasks per executor, Python UDFs holding state, memory-heavy aggregations without spill, cache eviction churn. Inspect the Spark UI stage/executor tab for shuffle and spill metrics.

### 15. How do you design idempotent Spark jobs?
Use deterministic logic (no random seeds without a fixed seed, no `current_timestamp()` as a key), write to versioned or partitioned paths overwritten dynamically, use transactional table formats (Delta/Iceberg/Hudi) with MERGE for upserts, and store run metadata so re-runs reconcile rather than duplicate.

### 16. How do you process CDC data?
Land raw CDC events (with op_type INSERT/UPDATE/DELETE and sequence/timestamp) in bronze. In silver, deduplicate by primary key keeping the latest sequence with a window, then MERGE into the target Delta/Iceberg table applying inserts, updates, and deletes accordingly.

### 17. How do you handle schema evolution?
Prefer additive changes (new columns); avoid renames/type narrowing. Use a schema registry (Avro/Protobuf) for streaming, Delta's `mergeSchema` for batch additions, and explicit migration scripts for breaking changes. Validate schema contracts at the entry of each pipeline stage.

### 18. What is dynamic partition overwrite?
With `spark.sql.sources.partitionOverwriteMode=dynamic`, `mode("overwrite") + partitionBy` only replaces partitions that exist in the incoming DataFrame, leaving other partitions intact. Critical for incremental jobs that re-process specific date ranges.

### 19. What is bucketing?
Bucketing pre-shuffles data by hashing a column into a fixed number of buckets, persisted with the table. Two tables bucketed on the same column with the same bucket count can be joined without a shuffle. Works well in Hive/Spark managed tables; less common in cloud lakehouses today, replaced by Z-ORDER / liquid clustering.

### 20. How do you improve Spark write performance?
Right-size output files (128 MB-1 GB), control output partitions with `repartition`/`coalesce`, choose columnar formats (Parquet/ORC/Delta), partition by common query filters, avoid high-cardinality partition columns, enable AQE, and use OPTIMIZE/compaction for transactional table formats.
