# Production Airflow Questions (Detailed)

### 1. How do you deploy Airflow DAGs?
Two main patterns: (a) **Git-sync** sidecar that pulls DAGs from a repo into the scheduler/worker pods on every interval; (b) **bake into image**: DAGs are baked into a custom Airflow Docker image deployed via Helm/ArgoCD. Managed Airflow (MWAA / Cloud Composer / Astronomer) usually provides a sync mechanism (S3/GCS bucket).

### 2. How do you test DAGs?
Three layers: **import test** (Python parses without errors), **structure test** (assert task IDs, dependencies, retries), and **unit tests** for the business logic that tasks call (treat DAG files as wiring, keep logic outside). Use `airflow dags test` for end-to-end local runs.

### 3. How do you store credentials?
Use **Airflow Connections** (encrypted with the Fernet key in metadata DB) or — better — a **secrets backend** (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, HashiCorp Vault). Never hardcode in DAG files or commit to git.

### 4. How do you monitor production DAGs?
Combine: Airflow UI/REST API for state, `on_failure_callback` to ship alerts to Slack/PagerDuty, SLA misses for late tasks, metrics export via StatsD/Prometheus, structured logging to ELK/Datadog/CloudWatch, and a data-quality layer (Great Expectations) for output-level monitoring.

### 5. How do you handle retries?
Set `retries` and `retry_delay` (preferably exponential via `retry_exponential_backoff=True` and `max_retry_delay`). Only retry idempotent tasks. For non-idempotent operations, design the task to be idempotent first (use unique run IDs, MERGE upserts, partition overwrites).

### 6. How do you avoid scheduler overload?
Keep top-level DAG-file imports light: no DB calls, no S3 listing, no HTTP requests at parse time. Reduce `dag_parsing_interval`, increase `parsing_processes`. Avoid generating thousands of DAGs dynamically; use dynamic task mapping instead.

### 7. How do you version pipeline code?
Keep business logic in a separately versioned Python package (or container image) installed alongside Airflow; DAGs just call into versioned functions or trigger versioned images. This separates pipeline definition from execution logic.

### 8. What should not be stored in XCom?
Large data (DataFrames, files, blobs) — XCom lives in the metadata DB and bloats it quickly. Also avoid secrets. Pass references (S3 paths, table names, IDs) and store payloads externally; or configure a custom XCom backend (S3) for large objects.

### 9. How do you handle task dependencies across DAGs?
Options: **Datasets** (Airflow 2.4+): one DAG produces a dataset URI, another DAG triggers when datasets are updated — declarative and recommended. **ExternalTaskSensor** with reschedule mode. **TriggerDagRunOperator** for explicit fan-out. Avoid coupling DAGs tightly when possible.

### 10. Production-ready DAG checklist.
Idempotent tasks; explicit `start_date` and `catchup=False`; retries + exponential backoff; `on_failure_callback`/SLAs; tagged owner; resource limits (pools, queues, `max_active_runs`); secrets via backend; tested in CI; documentation in the DAG `doc_md`; alerting wired up; clear data SLAs.
