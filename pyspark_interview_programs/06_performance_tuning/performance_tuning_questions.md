# PySpark Performance Tuning Questions (Detailed)

### 1. How do you choose partition count?
Aim for partition size of 100-200 MB and tasks of 10-30 seconds. Total partitions ≈ data_size / target_partition_size. Also align with cluster: at least 2-4 partitions per executor core for good parallelism. For shuffles, set `spark.sql.shuffle.partitions` accordingly (default 200 is often wrong).

### 2. What is a good output file size?
For Parquet/ORC on object storage, 128 MB to 1 GB per file is the sweet spot. Smaller files cause listing/metadata overhead; larger files reduce parallelism on reads. Control via `repartition(n)` before write or `maxRecordsPerFile` option.

### 3. When should you repartition?
Before a wide operation when current partitioning is poor (skewed or too few/many), to redistribute by a join key for co-located joins, or to control the number of output files on write. It is expensive (full shuffle) — do it once strategically, not repeatedly.

### 4. When should you coalesce?
To reduce partition count after a heavy filter or before write, without triggering a shuffle. Coalesce is cheap but can produce uneven partitions and reduce parallelism — never use it to *increase* partitions, and avoid it before another wide operation.

### 5. How do you reduce shuffle?
Filter and project columns early, pre-aggregate before joins, broadcast small lookup tables, partition the source on join/filter keys, use bucketing for repeated joins on the same key, and enable AQE to coalesce small shuffle partitions automatically.

### 6. How do you detect skew?
In Spark UI Stages tab, look at the task duration histogram and "Summary Metrics for completed tasks" — large gap between median and max indicates skew. Also check shuffle read size per task; if one task reads GBs while others read MBs, you have skew.

### 7. What is salting?
Salting breaks a skewed key into multiple keys by appending a random suffix (`key_0`, `key_1`, ..., `key_N`). The large side gets a single salt per row; the small side is exploded across all N salts. This distributes the hot key across N tasks at the cost of N× the small side.

### 8. How do you optimize joins?
Choose the right strategy: broadcast if small (<100 MB), sort-merge for two large sorted tables, shuffle-hash for medium. Project only required columns before the join. Filter both sides early. Match partition keys to avoid extra shuffles. Enable AQE for runtime adjustments.

### 9. Why prefer built-in functions over UDFs?
Built-ins (`col`, `when`, `regexp_extract`, `array_*`, etc.) are visible to Catalyst, run inside Tungsten code-generated JVM code, and avoid Python<->JVM serialization. They are typically 10-100× faster than equivalent Python UDFs.

### 10. How do you tune `spark.sql.shuffle.partitions`?
Default 200 is wrong for most workloads. Set so each shuffle partition holds ~128-200 MB. For 100 GB shuffle data and 200 MB target, set to ~500. With AQE enabled, set a higher upper bound (e.g. 1000-2000) and let AQE coalesce dynamically.

### 11. How can AQE help?
AQE (enabled by default in Spark 3.2+) coalesces small post-shuffle partitions into larger ones, switches sort-merge join to broadcast join if runtime stats show one side is small, and splits skewed partitions for skew joins. It removes much of the manual tuning burden.

### 12. How do you optimize reads?
Prefer columnar formats (Parquet/ORC/Delta), define explicit schema, leverage predicate and projection pushdown, use partition pruning, and avoid recursive scans of huge directory trees. Use Delta/Iceberg statistics and Z-ORDER/clustering for selective filters.

### 13. How do you optimize writes?
Pre-shuffle with `repartition(partition_cols)` to write one task per partition (avoids small files), choose appropriate compression (snappy default, zstd for better ratio), enable optimized writes/auto-compaction if using Delta, and avoid partitioning by high-cardinality columns.

### 14. What should you check in Spark UI?
Jobs/Stages tab for slow stages and skewed tasks; SQL tab for the optimized plan and shuffle sizes; Storage tab for cache health; Executors tab for memory, GC time, shuffle read/write, and failures; Environment tab for actual config in effect.

### 15. What is data spill?
When a task's working set exceeds executor memory, Spark spills to local disk. Spill bytes are visible in Spark UI stage metrics. Heavy spill kills performance; reduce it by increasing executor memory, increasing partition count (smaller tasks), reducing aggregation cardinality, or removing unnecessary columns.
