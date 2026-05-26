# Apache Hudi Questions (Detailed)

### 1. Copy-on-Write (CoW) vs Merge-on-Read (MoR).
**CoW**: each update rewrites entire data files containing the affected records — slower writes, fastest reads (plain Parquet). **MoR**: updates are written to delta log files, merged with base files at read time — fast writes, optional async compaction for read speed. Choose CoW for read-heavy analytics, MoR for high-frequency CDC.

### 2. Record key, partition path, precombine key.
**Record key**: primary key for upserts. **Partition path**: how rows are physically partitioned. **Precombine key**: when two updates collide for the same key in one commit, the one with the larger precombine value wins — typically a timestamp or LSN.

### 3. Hudi timeline.
The sequence of "instants" representing actions on the table (commit, deltacommit, compaction, clean, rollback). Each instant is in `requested`, `inflight`, or `completed` state. The timeline is Hudi's transaction log.

### 4. Compaction.
For MoR tables, compaction merges base files + delta log files into new base files asynchronously (scheduled) or synchronously (inline). Tunable to balance write throughput vs query latency.

### 5. Clustering.
Reorganize data files by sort keys to improve query performance without changing partitioning. Similar to Delta Z-ORDER and Iceberg compaction.

### 6. Indexes.
Hudi's killer feature for upserts. **Bloom**: scans Bloom filters per file to find candidates. **Simple**: full match in a join. **HBase**: external index for very large keyspaces. **Bucket**: hash-based, no lookup needed. **Record-level (RLI)**: HFile-backed per-record location index for fastest point lookups.

### 7. Incremental queries.
Read only the rows that changed between two commits via `hoodie.datasource.query.type=incremental` and a begin/end instant range. Enables downstream pipelines to consume changes natively, similar to Delta CDF.

### 8. Snapshot vs read-optimized queries.
**Snapshot**: latest data including pending deltas (slower for MoR). **Read-optimized**: only compacted base files (faster, possibly stale). Same table can be queried both ways depending on freshness vs latency needs.

### 9. DeltaStreamer.
A built-in Hudi utility that continuously ingests from Kafka/DFS sources into Hudi tables with built-in schema, transformer, and checkpointing — useful when you do not want to write custom Spark Structured Streaming code.

### 10. Hudi vs Delta vs Iceberg trade-offs.
Hudi excels at **streaming upserts with record-level indexing** — best fit for high-volume CDC ingestion. Delta is simplest with deepest Databricks integration. Iceberg is the most engine-neutral with best schema/partition evolution. Modern teams converge on Iceberg for openness or Delta for Databricks-heavy stacks; pick Hudi when CDC throughput is the dominant constraint.
