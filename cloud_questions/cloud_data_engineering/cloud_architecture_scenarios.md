# Cloud Data Engineering Architecture Scenarios (Detailed)

### 1. Design a near-real-time analytics pipeline from a transactional DB.
Capture changes from RDS/Aurora/SQL Server with **CDC**: AWS DMS or Debezium → Kafka/Kinesis/Event Hubs. A streaming consumer (Spark Structured Streaming, Flink, or Dataflow) deduplicates by primary key (window + watermark) and MERGEs into a transactional table format (Delta/Iceberg/Hudi) in S3/ADLS/GCS. BI tools query through Athena/Trino/Databricks SQL with sub-minute freshness. Add a dead-letter table for malformed events and end-to-end exactly-once via Kafka transactions + idempotent MERGE sink.

### 2. Design a data lake with bronze/silver/gold zones.
**Bronze**: raw, immutable, schema-on-read, date-partitioned — preserves source fidelity so you can always replay. **Silver**: cleaned, deduplicated, schema-enforced, conformed dimensions, joined to the canonical model — the layer most engineers query. **Gold**: business marts, denormalized aggregates, KPIs for BI/ML — fewest rows, fastest queries. Use Delta/Iceberg/Hudi for ACID at each layer, dbt or Spark for transforms, and a catalog (Unity, Glue, Polaris) for governance.

### 3. Migrate an on-prem Hadoop warehouse to the cloud.
Phases: (a) inventory tables, sizes, queries, SLAs, lineage; (b) pick target (Snowflake, BigQuery, Databricks, Redshift) based on team skills, SQL dialect, and cost model; (c) lift-and-shift Parquet/ORC to object storage in original layout; (d) re-write SQL into target dialect (use translation tools); (e) port orchestration (Oozie → Airflow); (f) dual-run with reconciliation queries until parity; (g) cut over and decommission. Plan for data gravity — egress is expensive and slow.

### 4. Build a multi-tenant data platform.
Pick an isolation model: separate workspaces/accounts per tenant (strongest, costliest), shared infra with row/column policies (Lake Formation, Unity Catalog row filters), or schema-per-tenant. Enforce IAM with tenant tags; bill back via tag-based cost allocation. Standardize ingestion, modeling, and observability so onboarding a new tenant is config, not code.

### 5. Design an event-driven ingestion pipeline.
Source publishes events → message bus (Kafka/Kinesis/Pub/Sub/Event Hubs) → schema-registered serialization (Avro/Protobuf) → streaming processor or autoloader → bronze lake. Use idempotent producers, partition keys aligned with downstream joins, dead-letter topics for bad data, schema-evolution rules in the registry, and end-to-end tracing (correlation IDs in event headers).

### 6. Choose between Spark and a cloud warehouse for transformations.
Use **Spark/Databricks/EMR** when you have non-SQL logic, very large unstructured data, ML feature engineering, or need engine portability. Use **the warehouse (Snowflake/BigQuery/Redshift)** when transforms are SQL-expressible, latency matters less, and you want zero infra ops. Many teams run dbt **inside the warehouse** for silver/gold and use Spark only for bronze landing and heavy semi-structured work.

### 7. Design disaster recovery for a data platform.
Define **RPO** (acceptable data loss window) and **RTO** (acceptable downtime). Strategies in order of cost: backup-and-restore (cheap, slow), pilot light (core infra warm), warm standby (running but smaller), active-active multi-region. Replicate object storage cross-region (S3 CRR, GCS dual-region, ADLS GRS), snapshot warehouses, store IaC + DAGs in git, and run quarterly DR drills with measured RPO/RTO.

### 8. Design for data residency and compliance (GDPR/HIPAA).
Pin storage and compute to allowed regions; enable encryption at rest with customer-managed keys; restrict cross-region replication; classify and tag PII; implement right-to-be-forgotten via deletion procedures across raw, curated, backups, and downstream BI extracts; audit access via centralized logs (CloudTrail/Audit Logs/Diagnostic Settings) shipped to a SIEM with retention matching the regulation.

### 9. Cost-optimize a cloud lakehouse.
Right-size compute (auto-suspend warehouses, autoscaling Spark clusters, Spot/preemptible for stateless workloads); reduce storage (lifecycle policies to cool/archive tiers, compact small files, prune unused columns); reduce scan (partitioning, clustering/Z-ORDER, column-level pruning, materialized views); kill abandoned queries via quotas; tag every resource for chargeback; review monthly with `INFORMATION_SCHEMA` / Cost Explorer / Cost Management dashboards.

### 10. Build a feature store on cloud.
**Offline store** (Parquet/Delta on lake) for training; **online store** (DynamoDB/Bigtable/Redis) for low-latency serving. A registry (Feast, Tecton, Vertex Feature Store) defines features once and writes to both stores from the same logic. Add point-in-time joins for training correctness and TTLs/versioning for governance.
