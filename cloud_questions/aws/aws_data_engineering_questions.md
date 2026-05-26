# AWS Data Engineering Interview Questions (Detailed)

## Core services

### 1. What is S3 used for in data engineering?
Amazon S3 is the de facto data lake storage on AWS — durable (11 nines), elastic, and cheap object storage. It separates storage from compute, letting Athena, Glue, EMR, Redshift Spectrum, and Databricks query the same data. Standard layout: raw → curated → consumption "zones" or bronze/silver/gold.

### 2. S3 storage classes.
**Standard**: frequent access. **Standard-IA / One-Zone-IA**: infrequent access, cheaper storage, higher retrieval cost. **Intelligent-Tiering**: auto-moves objects between tiers based on access patterns. **Glacier Instant / Flexible / Deep Archive**: archive tiers with milliseconds to hours retrieval. Use lifecycle policies to transition automatically.

### 3. What is AWS Glue?
A serverless data-integration suite with three main parts: **Glue Crawlers** that infer schemas and register tables in the **Glue Data Catalog**, and **Glue ETL Jobs** running PySpark or Python shell. Glue Studio gives a visual editor; Glue Workflows orchestrate jobs and triggers.

### 4. What is the Glue Data Catalog?
A managed, Hive-compatible metastore that stores table schemas, partitions, and S3 locations. Athena, EMR, Redshift Spectrum, and Lake Formation all read from it. Treat it as your central metadata layer — keep partition columns, formats, and locations consistent.

### 5. What is Athena?
Serverless interactive SQL on S3 via the Presto/Trino engine, pay-per-TB-scanned. Use it for ad-hoc analytics on Parquet/ORC partitioned data; it leverages the Glue Catalog for schemas. Cost optimization = columnar formats + partitioning + filtering + column pruning.

### 6. What is Redshift?
A cloud MPP data warehouse. Two flavors: **Provisioned** (you pick node types) and **Serverless** (compute auto-scales). Uses columnar storage and zone maps; query performance depends heavily on distribution and sort keys. Best for large structured analytical workloads with predictable SQL patterns.

### 7. Redshift sort key vs distribution key?
**Distribution key (DISTKEY)** controls which node holds each row — choose it to co-locate rows that join together so joins do not shuffle. **Sort key (SORTKEY)** controls physical order within each node so zone maps can skip blocks during range scans. Together they determine 80% of query performance.

### 8. What is EMR?
Managed Hadoop/Spark/Hive/Presto/Flink/HBase clusters on EC2 (or EKS or Serverless). You control instance types, autoscaling, and bootstrap actions. Use for custom Spark/big-data workloads, large ad-hoc jobs, or migrations from on-prem Hadoop.

### 9. Glue vs EMR?
**Glue**: serverless, fast startup, lower ops, ideal for scheduled Spark ETL up to ~moderate scale. **EMR**: more control, supports more engines (Hive, HBase, Flink, Presto), better for very large clusters, custom configs, and persistent jobs. Glue is faster to deliver; EMR is cheaper at scale with proper tuning.

### 10. What is Kinesis?
A family of streaming services: **Kinesis Data Streams** (Kafka-like shards, low-latency ingest), **Kinesis Firehose** (managed delivery to S3/Redshift/OpenSearch with buffering and format conversion), **Kinesis Data Analytics** (Flink). Use Streams + Firehose for typical real-time-to-lake pipelines.

## Architecture

### 11. How do you design a data lake on AWS?
Land raw data in S3 (date-partitioned, immutable), register in Glue Catalog, transform with Glue/EMR/Spark into silver (cleaned, conformed) and gold (business-ready) Parquet/Delta/Iceberg layers. Secure with Lake Formation row/column policies, query via Athena/Redshift Spectrum/EMR, orchestrate with MWAA (Airflow) or Step Functions.

### 12. Bronze/silver/gold layers.
**Bronze**: raw, immutable, schema-on-read; preserves source fidelity for replay. **Silver**: cleaned, deduplicated, schema-enforced, conformed to a canonical model. **Gold**: business aggregates, denormalized marts, KPIs ready for BI and ML features.

### 13. How do you secure S3 data?
Layered: IAM identity-based policies, S3 bucket policies, block public access settings, encryption at rest (SSE-S3, SSE-KMS with CMKs), encryption in transit (TLS), VPC endpoints (S3 Gateway endpoint) to keep traffic private, access logs + CloudTrail for audit, and Lake Formation/Glue permissions for fine-grained column/row access.

### 14. How do you optimize Athena cost?
Convert CSV/JSON to Parquet (10-50× cheaper queries), partition by query-filter columns (date), compact small files (>= 128 MB), select only needed columns, use partition projection for very-large partitioned tables (no MSCK REPAIR needed), and set per-query data limits.

### 15. How do you handle schema evolution?
Prefer additive changes; never rename or narrow types. For Glue + Athena, set `parquet.column.index.access=true` so column ordering changes do not break reads. For transactional tables, use Iceberg/Delta with explicit `ALTER TABLE` and schema validation in CI.

## Senior scenarios

### 16. How do you process CDC from RDS to a lake?
Use AWS DMS or Database Migration Service to capture full load + ongoing changes; land into S3 as Parquet (DMS task format) or stream to Kinesis. In the lake, deduplicate by primary key keeping the latest LSN/timestamp, then MERGE into Iceberg/Delta silver tables. Use Glue/EMR Spark for the merge step.

### 17. How do you design cross-account data sharing?
Options: (a) Lake Formation cross-account grants on Glue databases/tables — most secure, fine-grained; (b) Redshift datashare for warehouse-to-warehouse; (c) S3 bucket policy + IAM role assumption — simplest but coarse; (d) Resource Access Manager (RAM) to share Glue resources at the AWS account level.

### 18. How do you monitor Glue jobs?
Enable continuous CloudWatch logs and metrics, use Glue job bookmarks for incremental processing, configure retries with exponential backoff, capture custom metrics (rows in/out, bad rows) via the Glue Metrics API, and route failures to SNS/PagerDuty. For data quality, add Glue Data Quality rules.

### 19. How do you reduce Redshift query time?
Inspect `EXPLAIN` and SVL_QUERY_REPORT for steps. Levers: choose better DISTKEY/SORTKEY, run `ANALYZE` and `VACUUM`/`VACUUM REINDEX`, use compression (`COPY` auto-encodes), use materialized views, manage WLM/queues by workload, prefer Redshift Spectrum for cold data, and consider RA3 nodes with managed storage for hot/cold separation.

### 20. How do you design disaster recovery?
Versioned + replicated S3 (Cross-Region Replication), Glue Catalog backups (export DDL or use AWS Backup), Redshift snapshots + cross-region copy, infrastructure as code (Terraform/CloudFormation) so the platform can be redeployed, and quarterly tested runbooks. Define RPO/RTO and choose strategy (pilot light, warm standby, multi-region active-active) accordingly.
