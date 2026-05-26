# Data Engineering System Design (Detailed)

A system-design interview at senior DE level usually asks you to design an end-to-end pipeline. Walk through: **requirements → high-level architecture → component deep-dives → scale/perf → reliability → security → cost → trade-offs**.

## Framework to use in every answer

1. **Clarify requirements**: data volume per day, peak vs steady, latency SLA (batch hourly / near-real-time / strict streaming), retention, query patterns, consumers (BI, ML, services), regulatory constraints, budget.
2. **Bound the problem**: estimate rows/sec, GB/day, storage growth/year, peak concurrent queries.
3. **High-level diagram**: ingestion → storage → processing → serving → orchestration → observability.
4. **Pick technologies per layer** and justify against alternatives.
5. **Deep-dive** on hardest part (often schema evolution, exactly-once, skew, or cost).
6. **Failure modes** and recovery: what if a source goes down, what if Kafka is behind, what if a transformation produces NaNs.
7. **Trade-offs and what you'd change at 10× scale.**

## Common problems

### 1. Design a real-time clickstream analytics pipeline.
**Volume**: ~50k events/sec peak, 100 GB/day. **Latency**: dashboards within 1 minute. **Architecture**: JS SDK → load balancer → collector service (stateless, autoscaled) → Kafka (partitioned by user_id for ordering, RF=3) → two consumers: (a) Spark Structured Streaming with 30-second micro-batches landing partitioned Parquet in S3 (bronze), then enriching with user dim broadcast join into silver Delta tables; (b) Flink job computing real-time rollups into Redis/ClickHouse for the live dashboard. **Exactly-once** via Kafka transactional producer + Delta idempotent MERGE. **Schema** in Confluent Schema Registry (Avro). **Replay** by re-reading Kafka with a new consumer group. **Cost** controlled by tiering raw data to S3 IA after 30 days.

### 2. Design a CDC pipeline from OLTP to warehouse.
**Source**: 200-table Postgres OLTP, ~5M changes/day. **Latency**: < 5 min. **Architecture**: Debezium reads WAL → Kafka topic per table → Kafka Connect S3 sink lands JSON to bronze, dedupes by `(pk, lsn)` and MERGEs into silver Iceberg tables via a 1-min Spark micro-batch. dbt builds gold marts hourly. **Schema evolution** via Schema Registry with backward-compatible rules; alerts on incompatible changes block downstream until reviewed. **Tombstones** flagged with `op_type = DELETE` propagate to MERGE WHEN MATCHED THEN DELETE. **Reconciliation** job nightly compares source row counts to silver.

### 3. Design a batch ETL pipeline for daily revenue reporting.
**Volume**: 10 TB/day input, 200 source files. **SLA**: ready by 7 am. **Architecture**: S3 landing → Airflow DAG triggered by file arrival → Spark on EMR/Databricks for bronze→silver (clean, dedupe, conform) → dbt on Snowflake for silver→gold star schema → Tableau/Looker. **Idempotency** via dynamic partition overwrite and MERGE. **Backfill** runs the same DAG with `--start-date` flags. **Alerting** on freshness via Soda + Slack; runbook for each known failure mode. **Cost** controlled by sizing Snowflake warehouse per workload and auto-suspending in 60 s.

### 4. Design a feature store for ML.
**Offline store** (training): Delta tables in S3 with point-in-time joins and full history. **Online store** (serving): DynamoDB / Bigtable / Redis keyed by entity ID, < 10 ms reads. **Registry** (Feast): declares features once; ingestion jobs write to both stores from the same Spark logic. **Backfill** writes historical features to offline only; **streaming** features (Flink/Spark) write to both. **Governance**: feature ownership, versioning, freshness SLA, drift monitoring on training-serving skew.

### 5. Design a multi-region data lake with DR.
**Primary region** hosts S3 + Glue/Lake Formation + EMR + Snowflake. **Secondary region** receives async CRR replication on S3, replicated Glue catalog (script-based or via AWS Backup), and a Snowflake replication group. **RPO** ~15 min (S3 CRR lag); **RTO** ~1 h (manual failover). **DR drill** quarterly: fail over, run a known query, fail back. **IaC** (Terraform) makes the whole stack reproducible; **state** stored in a multi-region backend.

### 6. Design a streaming aggregation with exactly-once semantics.
End-to-end EOS needs (a) replayable source (Kafka with offsets), (b) checkpointed processor (Spark/Flink state store), (c) idempotent or transactional sink (Delta/Iceberg MERGE on `(window_start, key)`). Use event-time windowing with a watermark (`10 min`) to bound state and handle late data; emit results in **append** mode with **update**-aware downstream sinks. Test by killing the job mid-batch and verifying no duplicates after recovery.

### 7. Design a schema-evolution-safe pipeline.
Schema registry (Avro/Protobuf) enforces backward-compatible producer changes; consumers pin a reader schema. Bronze ingests permissively (extra fields stored as JSON); silver enforces a strict contract and routes contract violations to a quarantine table. Add CI gates: a producer PR triggers compatibility checks against all registered consumers. Document the contract per dataset in the catalog with owner, freshness SLA, breaking-change policy.

### 8. Design data quality monitoring.
Layered checks: (a) **schema** validation at every load (column count/types); (b) **volume** anomaly detection (row count vs 7-day avg); (c) **business rules** (sum(revenue) ≥ 0, no orphan FKs, primary-key uniqueness); (d) **freshness** SLAs alerting on stale tables; (e) **drift** detection on key distributions over time. Tools: Great Expectations / Soda / dbt tests for checks, a small Postgres or warehouse table to record results, Grafana/Datadog for dashboards, PagerDuty for criticals.

### 9. Design a cost-optimized data platform for a startup.
Use **serverless or pay-per-use** wherever possible (BigQuery on-demand, Snowflake auto-suspend XS, Lambda/Cloud Run for glue) to avoid idle cost. Lake-first: land in cheap object storage, query with Athena/BigQuery external tables until volumes justify a warehouse. dbt for transformations, Airflow on a single small instance (or Cloud Composer / Astronomer). Tag everything; set strict per-team budgets. Re-evaluate at each 5× growth — premature optimization wastes more than over-provisioned compute.

### 10. Design a near-real-time fraud detection pipeline.
Transactions → Kafka → Flink stateful job evaluating rules + scoring with a small online model (ONNX/TFLite). Hot features from a feature store (Redis); cold features from Iceberg. Decisions sub-100 ms; flagged transactions write to a review queue and to Kafka for downstream auditing. Shadow mode for new models, A/B routing for production. Full lineage (transaction → features used → model version → decision) stored for regulatory audit.

## Tips for senior interviews
- **Drive the conversation**: state assumptions, ask 2-3 clarifying questions, then move on.
- **Quantify everything**: rows/sec, GB/day, $/month — back-of-envelope is fine.
- **Show breadth and depth**: pick one layer to deep-dive (often storage layout or exactly-once).
- **Acknowledge trade-offs** explicitly — there is no perfect answer.
- **Discuss observability and on-call** — senior engineers always think about who pages whom at 3 am.
