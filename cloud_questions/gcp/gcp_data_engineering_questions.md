# GCP Data Engineering Interview Questions (Detailed)

## Core services

### 1. What is BigQuery?
A fully managed, serverless, columnar MPP data warehouse with separated storage and compute (the Dremel engine). You write standard SQL; Google handles infrastructure. Pricing: per-TB scanned (on-demand) or per-slot (flat-rate/editions).

### 2. Storage vs compute separation in BigQuery.
Data is stored in Colossus (Google's distributed FS) in columnar Capacitor format. Compute is allocated as "slots" on demand. You can scale either independently — store cheap petabytes long-term while only paying for compute when queries run.

### 3. Partitioned tables in BigQuery.
Tables can be partitioned by ingestion time, a DATE/TIMESTAMP column, or an integer range. The optimizer prunes partitions when the query filters on the partition column. Set `require_partition_filter=true` to prevent accidental full scans.

### 4. Clustering in BigQuery.
Up to 4 columns by which data within each partition is sorted/clustered. Filters and joins on clustering columns benefit from block pruning (no need to read all blocks). Unlike partitions, clustering is automatic and continuous.

### 5. Partitioning vs clustering.
**Partitioning** is a coarse, explicit, top-level filter (one folder per partition value). **Clustering** is a fine-grained, automatic in-partition sort. Use partitioning for the primary time dimension and clustering for secondary high-cardinality filter columns (customer_id, product_id).

### 6. What is Dataproc?
Managed Hadoop and Spark on GCE/GKE. Lets you lift-and-shift on-prem Hadoop workloads or run open-source Spark with full control. Comes in **Standard** (clusters you manage) and **Serverless** (jobs only, no cluster) flavors.

### 7. What is Dataflow?
Managed Apache Beam runner for both batch and streaming. Auto-scales workers, handles windowing/watermarking. Great for streaming ETL from Pub/Sub to BigQuery with exactly-once semantics, or large batch transforms with one programming model.

### 8. What is Pub/Sub?
A globally distributed managed messaging service. Publishers send messages to topics; subscribers receive via push or pull subscriptions. Used as the streaming backbone, often paired with Dataflow → BigQuery or Dataflow → GCS.

### 9. What is GCS?
Google Cloud Storage — object storage equivalent to S3/ADLS. Used as the data lake substrate, staging area for BigQuery loads, and archive. Supports lifecycle policies, versioning, and signed URLs.

### 10. GCS storage classes.
**Standard**: hot data, no minimum duration. **Nearline**: ≥ 30-day minimum, infrequent access. **Coldline**: ≥ 90-day. **Archive**: ≥ 365-day, cheapest storage but highest retrieval cost. Lifecycle policies transition automatically.

## BigQuery deep

### 11. Slots vs on-demand pricing.
**On-demand**: $/TB scanned, no capacity to manage but unpredictable cost. **Slots (flat-rate / editions)**: reserved compute capacity (e.g. Enterprise edition, autoscale slots) with predictable cost, ideal for high steady utilization.

### 12. Flat-rate vs editions pricing.
The newer "Editions" model (Standard / Enterprise / Enterprise Plus) replaces legacy flat-rate. You commit baseline slots and autoscale up; features (column-level security, BI Engine, etc.) vary by edition.

### 13. How to optimize BigQuery cost?
Avoid `SELECT *` (pay per column scanned), partition + cluster tables, use `LIMIT` for previews via the `tabledata.list` API (not within SQL — it still scans), materialize repeated heavy queries into MVs/tables, set query and project quotas, and prefer flat-rate for predictable workloads.

### 14. Materialized views.
Precomputed and **incrementally** maintained query results. BigQuery auto-routes matching queries to the MV (smart tuning) — users do not need to know it exists. Great for hot aggregations; has limitations on supported SQL.

### 15. What is BI Engine?
An in-memory columnar cache that accelerates dashboard queries (Looker/Looker Studio/Tableau via ODBC) by orders of magnitude. You allocate GB; BigQuery transparently uses it for matching queries.

### 16. Streaming inserts vs batch loads.
**Batch load** (`bq load` / Storage Write API in batch mode): free, eventual minutes, ideal for periodic ingestion. **Streaming insert** (legacy tabledata.insertAll or Storage Write API): per-row cost, second-level latency, used for real-time. Storage Write API is the modern unified replacement.

### 17. External tables / BigLake.
Query data sitting in GCS, S3, ADLS, Bigtable, or Cloud SQL without loading into BigQuery. BigLake adds fine-grained security on top of external tables (row-level filtering, column masking) and unifies governance across formats and clouds.

### 18. Authorized views.
A view in dataset A authorized to read a table in dataset B, exposed to a consumer who has no direct access to dataset B. Pattern for sharing curated subsets while protecting the source. Authorized datasets and routines extend the same idea.

### 19. Row-level and column-level security.
**Column-level**: tag columns with policy tags and grant access via Data Catalog taxonomies. **Row-level**: define row access policies with a SQL predicate per principal. Combine for fine-grained governance.

### 20. Time travel and snapshots.
BigQuery retains every change to a table for **7 days** (configurable up to 7 days), queryable with `FOR SYSTEM_TIME AS OF`. **Table snapshots** are cheap point-in-time copies for longer retention. **Failsafe** adds another 7 days for recovery via support.

## Pipelines

### 21. Cloud Composer.
Managed Apache Airflow on GKE. Use it for cross-service orchestration of BigQuery, Dataflow, Dataproc, Pub/Sub jobs. Native operators exist for most GCP services.

### 22. Cloud Functions vs Cloud Run for ETL.
**Cloud Functions**: lightweight, event-driven (Pub/Sub, GCS object), per-language runtimes — good for small glue/enrichment. **Cloud Run**: any container, longer requests, autoscaling to zero, better for medium services, custom dependencies, and HTTP APIs.

### 23. Dataform vs dbt.
Both transform data in BigQuery using SQL with tests, refs, and docs. **Dataform** is built into GCP, free, with native scheduling. **dbt** is more mature, larger ecosystem (adapters, packages), and cloud-agnostic. Most teams pick dbt unless they want a fully GCP-native experience.

### 24. Workflows vs Composer.
**Workflows**: lightweight, YAML-based, low-cost orchestration for HTTP/serverless service calls — great for simple pipelines. **Composer (Airflow)**: heavier, Python DAGs, retries, sensors, dynamic mapping — required for complex data pipelines.

## Scenarios

### 25. Design a GCP data lake.
GCS for raw landing with lifecycle policies, external/BigLake tables for in-place query, BigQuery for curated layers, dbt/Dataform for transformations, Composer for orchestration, Pub/Sub + Dataflow for streaming, Data Catalog for governance, IAM + VPC-SC for security boundary.

### 26. Stream Pub/Sub to BigQuery with Dataflow.
Standard pattern: Pub/Sub topic → Dataflow streaming pipeline (Beam) doing parsing/validation → Storage Write API into a partitioned + clustered BigQuery table. Add a dead-letter table for invalid records and a windowed dedup keyed by event_id with watermark.

### 27. CDC from Cloud SQL via Datastream.
Datastream is a serverless CDC service. It reads MySQL/Postgres/Oracle WAL/binlog, writes change events to GCS or BigQuery (auto-merge supported into BigQuery). Pair with dbt for downstream silver/gold models.

### 28. Cross-project data sharing.
Use authorized datasets/views to expose curated data, or **BigQuery Analytics Hub** to publish/subscribe shared datasets across organizations. Both avoid data movement and copies.

### 29. Cost optimization in BigQuery.
Partition + cluster, materialize hot queries, prefer columnar projections, kill abandoned queries with custom quotas, monitor `INFORMATION_SCHEMA.JOBS_BY_PROJECT` for top-scanning queries and users, mix on-demand + slots intelligently, and set table expiration on staging datasets.

### 30. Disaster recovery in BigQuery.
Multi-region datasets (`US`, `EU`) provide cross-region replication by default. Add scheduled table snapshots for longer point-in-time recovery, export critical datasets to GCS in another region, and document RPO/RTO. Manage failover with infrastructure as code so the platform is repeatable.
