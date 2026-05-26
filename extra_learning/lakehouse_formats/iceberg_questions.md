# Apache Iceberg Questions (Detailed)

### 1. What is Iceberg?
An open table format that adds ACID transactions, snapshots, schema/partition evolution, and hidden partitioning on top of Parquet/ORC/Avro files in object storage. Engine-agnostic — Spark, Trino, Flink, Snowflake, BigQuery, and many others read/write it.

### 2. Snapshot isolation and time travel.
Each commit creates a new immutable snapshot in the metadata tree. Queries see one snapshot for their entire run (consistent reads). Time travel via `VERSION AS OF` or snapshot ID; rollback supported via `rollback_to_snapshot`.

### 3. Hidden partitioning.
You declare a partition transform (e.g. `days(event_time)`) once; users do not see or filter on partition columns. The engine automatically applies the transform when filtering on the source column. This decouples physical layout from query syntax — a major Iceberg advantage.

### 4. Partition evolution.
Change partitioning (e.g. from `days(ts)` to `hours(ts)`) without rewriting historical data. New data follows the new spec; queries handle both transparently. Solves a chronic pain point with Hive-style partitioning.

### 5. Schema evolution.
Safe add/drop/rename/reorder columns and type promotions (int → long). Implemented via stable column IDs in metadata, not column names — so renaming a column never breaks readers.

### 6. Metadata files.
**Snapshot** → **Manifest list** → **Manifest files** → **data files**. Each layer is a Parquet/Avro file with min/max statistics. This tree enables efficient pruning at planning time without listing object storage.

### 7. Compaction.
`CALL rewrite_data_files(...)` compacts many small files into fewer larger ones and can re-cluster by columns. Equivalent to Delta OPTIMIZE/Z-ORDER. Periodic compaction is essential for streaming-written tables.

### 8. Catalogs.
Iceberg needs a catalog to track the current table metadata pointer. Options: **Hive Metastore**, **AWS Glue**, **REST catalog** (standard), **Nessie** (git-like with branches/tags), **Polaris** (Snowflake's open catalog). Pick a catalog that matches your platform and supports your engines.

### 9. Position deletes vs equality deletes.
**Copy-on-write**: rewrite files on delete/update — slower writes, faster reads. **Merge-on-read** with position/equality delete files — fast writes, reads apply deletes at scan time. Choose per workload: CoW for read-heavy, MoR for write-heavy CDC.

### 10. Iceberg vs Delta vs Hudi.
**Iceberg**: best schema/partition evolution, broadest engine support, neutral governance (Apache). **Delta**: deepest Spark/Databricks integration, Z-ORDER, liquid clustering. **Hudi**: strongest upsert performance with record-level indexes. Iceberg is becoming the de facto open standard for multi-engine lakehouses.

### 11. Branching and tagging snapshots.
Tag snapshots with names (`v1.0`, `pre-migration`) for stable references; create branches (with Nessie) to do isolated work and merge back. Enables git-like workflows for data — experiment without affecting prod readers.

### 12. Row-level operations.
`MERGE`, `UPDATE`, `DELETE` with full SQL support. Engines (Spark/Trino) translate them into either copy-on-write or merge-on-read depending on table properties (`write.update.mode`).

### 13. Sort order.
Tables can declare a logical sort order; writers cluster data accordingly. Combined with per-file min/max stats, selective filters can skip most files without scanning.

### 14. Streaming support.
Spark Structured Streaming and Flink can both read from and write to Iceberg. Iceberg's snapshots provide a natural stream of new files for downstream consumers.

### 15. Integrations.
Spark (built-in), Trino/Presto, Flink, Hive, Snowflake (Iceberg tables), BigQuery (BigLake Iceberg), AWS Athena/Glue, Dremio, Starburst. One open format readable everywhere is the core value proposition.
