# Snowflake Interview Questions (Detailed)

### 1. Snowflake architecture.
Three layers: **Storage** (compressed, columnar micro-partitions on cloud object storage), **Compute** (independent virtual warehouses), **Cloud services** (metadata, query optimization, security, transactions). Compute and storage scale independently, and multiple warehouses can query the same data without contention.

### 2. What is a virtual warehouse?
A cluster of compute resources sized T-shirt-style (XS → 6XL). It runs queries against the shared storage layer. Auto-suspend/auto-resume make it pay-per-use. Different warehouses can target different workloads (ETL, BI, ad-hoc) without interfering.

### 3. Multi-cluster warehouses.
A warehouse that can spin up additional clusters automatically to handle concurrency spikes (Enterprise edition). Use for BI workloads with many simultaneous users; ETL usually does not need it.

### 4. Micro-partitions.
Immutable ~50-500 MB columnar files Snowflake creates automatically as data is loaded. Each carries metadata (min/max, distinct count, nulls) used for pruning. You never manage them directly.

### 5. Clustering keys.
Optional declaration that tells Snowflake to maintain a sort order on certain columns so micro-partition pruning is more effective. Background auto-clustering rewrites micro-partitions. Use only on very large tables (TB+) where queries filter on those columns; check `SYSTEM$CLUSTERING_INFORMATION`.

### 6. Time travel.
Query past versions of a table with `AT (OFFSET => -3600)` or `BEFORE (STATEMENT => ...)`. Retention: 1 day (Standard) up to 90 days (Enterprise+). Use to recover from accidental DML and for snapshot consistency.

### 7. Fail-safe.
A 7-day non-configurable period after time-travel retention ends, accessible only via Snowflake support, for disaster recovery of historical data. Not part of normal SLA.

### 8. Zero-copy cloning.
`CREATE TABLE ... CLONE source` (also for schemas and databases) creates a new object pointing to the same underlying micro-partitions instantly — no data copy, no extra storage until divergence. Perfect for dev/test environments, what-if scenarios, and snapshots.

### 9. Streams (CDC).
A stream is a "change table" that records inserts/updates/deletes on a source table since the last consumption point. Read with normal SQL, then `COMMIT` advances the offset. Pair with **Tasks** to build incremental pipelines without external tools.

### 10. Tasks.
Server-side scheduled SQL units that can run on a cron or after another task (forming DAGs). Combined with streams, you build pure-Snowflake incremental ELT (no external orchestrator) — though most teams still prefer Airflow/dbt Cloud for complex flows.

### 11. Stored procedures.
Server-side procedural logic in JavaScript, Python, Scala, or SQL Scripting. Used for control flow, dynamic SQL, multi-statement transactions. Python procedures (Snowpark) let you write data engineering jobs in Python that execute inside Snowflake.

### 12. UDFs and UDTFs.
**UDF**: scalar or aggregate function in SQL, JavaScript, Python, Java. **UDTF** (Table function): returns a table, useful for parsing/flattening. Prefer SQL UDFs for performance; Python UDFs use Snowpark and run in Snowflake's sandbox.

### 13. External tables.
Tables defined over files in cloud storage (S3/Azure/GCS) with metadata in Snowflake. Schema-on-read; partition by manual partition keys. **Iceberg tables** are the modern replacement, offering full DML and time travel over open formats.

### 14. Snowpipe and auto-ingest.
Continuous serverless ingestion: as new files land in a stage (S3/Azure/GCS), event notifications trigger Snowpipe to COPY them into a target table. Pay per file/bytes loaded. Best for steady drip-feed file ingestion.

### 15. Stages: internal vs external.
**Internal stage**: Snowflake-managed area within your account (user/table/named). **External stage**: pointer to S3/Azure/GCS with credentials/storage integration. Files in stages are loaded via `COPY INTO`.

### 16. File formats.
Reusable definitions for CSV/JSON/Parquet/ORC/Avro/XML with options like delimiter, compression, header. Referenced from `COPY INTO` and stages. Always centralize file formats; don't repeat the options inline.

### 17. COPY INTO command.
Bulk-load files from stages into tables (and reverse: unload tables to stages). Supports schema inference for Parquet, error handling (`ON_ERROR`), column transformations, validation mode, and load history dedup so you cannot accidentally load the same file twice.

### 18. Caching layers.
**Result cache** (24 h): identical query returns instantly from services layer. **Local disk cache** on each warehouse: hot data stays warm; suspending evicts. **Remote storage**: source of truth. Result and disk cache are why repeated queries feel free.

### 19. Warehouse sizing and auto-suspend.
Right-size by workload: ETL usually L/XL bursts, BI XS-M with multi-cluster. Auto-suspend (e.g. 60 s) saves cost; auto-resume on query arrival. Each size doubles credits per hour, but also roughly halves runtime — pick by total credits, not size.

### 20. Resource monitors.
Set monthly credit quotas on warehouses with actions (notify, suspend, suspend immediately). Essential to prevent runaway queries or developer mistakes from generating huge bills.

### 21. RBAC model.
Role-based, hierarchical, with grants on objects. Best practice: separate **access roles** (per-object grants) from **functional roles** (assigned to users), and assemble functional roles from access roles. SYSADMIN, SECURITYADMIN, ACCOUNTADMIN are the system roles.

### 22. Secure data sharing.
Share live, read-only access to selected objects with consumers in other Snowflake accounts — zero copy, zero ETL. **Listings** publish to the Snowflake Marketplace. Reader accounts let you share with consumers who do not have Snowflake.

### 23. Materialized views.
Precomputed and incrementally maintained views (Enterprise+). Snowflake auto-routes matching queries. Limitations: single base table, restricted SQL. Use for high-frequency aggregations on huge fact tables.

### 24. Search optimization service.
Adds a secondary index on point-lookup columns (high-cardinality equality predicates, substrings, geospatial). Background maintenance. Costs credits; enable only on columns that get repeated point queries.

### 25. Query profile.
The graphical execution plan in the UI showing each operator, rows produced, bytes scanned, time spent, and pruning effectiveness. Always check it when tuning: red bars are bottlenecks.

### 26. Clustering depth.
A measure of how well a table is clustered (lower is better). `SYSTEM$CLUSTERING_DEPTH('table', 'cols')` reports it. If it grows, consider declaring a clustering key or rewriting the table.

### 27. Snowpark for Python.
A DataFrame-style Python API that executes inside Snowflake using pushdown to SQL. Lets you write PySpark-like code without a Spark cluster, with optional Python UDFs/stored procs for custom logic.

### 28. Dynamic tables.
A managed, declarative alternative to streams + tasks. You define a SELECT and a target lag (e.g. "1 minute"); Snowflake handles incremental refresh and dependencies. Modern way to build pipelines in pure SQL.

### 29. Iceberg tables in Snowflake.
Snowflake-managed (or externally-managed) Apache Iceberg tables stored in your own cloud storage. Open format, full DML and time travel, queryable by Spark/Trino/Flink. Great for open lakehouses while keeping Snowflake compute.

### 30. Cost optimization in Snowflake.
Right-size warehouses, aggressive auto-suspend, kill long-running queries with resource monitors, materialize repeated heavy queries (MVs, dynamic tables), avoid SELECT * scanning all columns, prune via clustering on large tables, separate workloads (ETL vs BI) into distinct warehouses, and analyze ACCOUNT_USAGE views for top spenders.
