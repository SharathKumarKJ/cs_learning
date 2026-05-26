# Delta Lake Questions (Detailed)

### 1. What is Delta Lake?
An open-source storage layer that brings ACID transactions, schema enforcement, and time travel to Parquet files on object storage. It is the foundation of the Databricks Lakehouse but also runs on OSS Spark.

### 2. What is `_delta_log`?
The transaction log directory next to your data. Each commit writes a JSON file (`000000.json`, `000001.json`, ...) describing add/remove file actions, schema, and metadata. Periodic checkpoints (`*.checkpoint.parquet`) summarize many commits for fast log replay.

### 3. ACID guarantees.
**Atomicity**: a commit either fully succeeds or is invisible. **Consistency**: schema enforcement + constraints. **Isolation**: optimistic concurrency — concurrent writers detect conflicting file changes and retry. **Durability**: object storage durability + committed log entry.

### 4. Time travel.
Query past versions with `VERSION AS OF n` or `TIMESTAMP AS OF '...'`. Driven by the transaction log + retained data files. Useful for audits, rollbacks, and reproducible ML training datasets.

### 5. MERGE INTO.
Atomic upsert/delete from a source into a Delta table with `WHEN MATCHED THEN UPDATE/DELETE` and `WHEN NOT MATCHED THEN INSERT`. The core primitive for CDC, SCD2, idempotent loads. Optimize with file pruning, broadcast hints, and Z-ORDER on the merge key.

### 6. OPTIMIZE and Z-ORDER.
**OPTIMIZE** compacts many small files into fewer ~1 GB files, speeding up reads. **ZORDER BY (col)** additionally co-locates data by those columns within files via space-filling curves, dramatically improving selective filter performance.

### 7. VACUUM and retention.
`VACUUM` deletes files no longer referenced by recent versions. Default retention is **7 days** (`delta.deletedFileRetentionDuration`); shorter retention saves storage but shrinks time-travel window. Never run VACUUM with `RETAIN 0 HOURS` on a table with concurrent readers.

### 8. Schema evolution.
For appends, set `mergeSchema=true` to add new columns automatically. For overwrites, `overwriteSchema=true` replaces the schema entirely. Removing/renaming columns requires explicit DDL and may break readers — treat schema changes as a migration.

### 9. Schema enforcement.
By default, writes that introduce new columns or incompatible types fail. This is a feature, not a bug — it prevents silent data drift. Combine with column constraints (`NOT NULL`, `CHECK`) for stronger data contracts.

### 10. Generated columns.
Columns whose value is derived from an expression (`order_date GENERATED ALWAYS AS (CAST(order_ts AS DATE))`). They are stored, partition pruning works on them, and you cannot insert into them — useful for partition columns derived from raw event timestamps.

### 11. Change Data Feed (CDF).
Enable with `delta.enableChangeDataFeed=true`. Then `SELECT * FROM table_changes('t', start, end)` returns inserts/updates/deletes (with `_change_type`, `_commit_version`, `_commit_timestamp`). Perfect for incremental downstream pipelines without separate CDC infrastructure.

### 12. Liquid clustering.
Newer alternative to partitioning + Z-ORDER. You specify clustering columns and Delta maintains them automatically — no fixed partition boundaries to plan, easier to evolve. Available on Databricks; check OSS Delta support level.

### 13. Delta Sharing.
An open REST protocol for sharing live data across organizations, clouds, or computing platforms. Recipients can be any compatible client (Spark, pandas, BI tools). Zero-copy, governance-controlled.

### 14. Deletion vectors.
Instead of rewriting a file when rows are deleted (merge-on-write), Delta can mark deleted rows in a small side file (merge-on-read). Drastically speeds up DELETE/UPDATE/MERGE on large tables; reads transparently apply the mask.

### 15. Concurrency.
Delta uses optimistic concurrency: writers attempt a commit and detect conflicts based on which files were added/removed. Non-conflicting writers (e.g. different partitions) succeed; conflicting writers retry. Use partition-aware writes to minimize conflicts.

### 16. Compaction and small files.
Streaming writes produce many small files; the small file problem hurts read performance. Fix with periodic `OPTIMIZE`, auto-optimize/auto-compact on Databricks, or explicit `coalesce`/`repartition` before write in batch jobs.

### 17. Streaming with Delta.
Delta is both a streaming source and sink. As source it reads new files committed since the last offset; as sink it provides exactly-once via the transaction log + checkpoints. Combined with CDF, you can stream changes downstream.

### 18. Delta vs Iceberg vs Hudi.
**Delta**: simplest API, deepest integration with Spark/Databricks, Z-ORDER + liquid clustering. **Iceberg**: best schema/partition evolution, broadest engine support (Spark, Trino, Flink, Snowflake, BigQuery). **Hudi**: strongest upsert performance with record-level indexes (Bloom, bucket), best for high-frequency CDC.

### 19. Partition pruning vs Z-ORDER.
**Partitioning** physically splits data into folders by low-cardinality columns (typically date). **Z-ORDER** sorts within files by chosen columns so file-level statistics prune more. Use partitioning for the primary time dimension; Z-ORDER (or liquid clustering) for high-cardinality filter columns.

### 20. Best practices.
Partition by date (day or month), keep file sizes ~128 MB-1 GB, schedule OPTIMIZE + VACUUM, Z-ORDER on hot filter columns, enable CDF where downstream consumers need changes, use schema enforcement always, MERGE for upserts, and pair with Unity Catalog or another governance layer for production.
