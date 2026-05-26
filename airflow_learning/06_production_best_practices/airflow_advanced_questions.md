# Airflow Advanced Questions (Detailed)

### 1. How does the scheduler determine the next run?
On each loop, the scheduler reads each DAG's timetable, asks for `next_dagrun_info()` given the latest completed interval, applies guard rails (`catchup`, `max_active_runs`, `depends_on_past`), and creates a DAG run row in the metadata DB. It then queues runnable task instances whose dependencies (upstream success, pool slots, trigger rules) are met. Scheduler throughput is gated by DB latency and DAG-parsing time.

### 2. `schedule_interval` vs custom timetable.
`schedule_interval` (now `schedule`) accepts cron, presets, or `timedelta`. For business-specific calendars (workdays only, fiscal months, market hours), implement `Timetable` with `next_dagrun_info` and `infer_manual_data_interval` — gives full control while still letting the scheduler reason about intervals.

### 3. DAG parsing performance.
The scheduler re-parses each DAG file periodically. Slow imports (Spark client init, large config loads, network calls) at file scope freeze the scheduler. Keep top-level lightweight, defer heavy work to task callables. Use `airflow info` and the `dag_processing` metrics to find slow parses; raise `parsing_processes` and lower `min_file_process_interval` carefully.

### 4. What is the triggerer?
A separate, async process that runs deferrable operators' triggers (lightweight coroutines). It enables a single Python process to wait on thousands of conditions concurrently without consuming worker slots. Required for deferrable operators; deploy as its own pod/process alongside scheduler and workers.

### 5. Dataset-aware scheduling.
A producer declares `outlets=[Dataset("s3://lake/orders")]`. The scheduler treats updates to a dataset as a trigger event; consumer DAGs with `schedule=[Dataset(...)]` start automatically. Replaces brittle cross-DAG `ExternalTaskSensor` patterns and decouples producers and consumers in time.

### 6. Sharing data between tasks.
**XCom** for tiny values (<48 KB recommended). **Datasets** for declarative producer→consumer signaling. **External storage** (S3/GCS/ADLS) for large payloads with a path returned via XCom. **Custom XCom backend** to transparently spill large XComs to S3. Avoid the temptation to push DataFrames through XCom.

### 7. Custom XCom backend.
Subclass `BaseXCom` and override `serialize_value`/`deserialize_value` to push values to S3/GCS keyed by run/task. Tasks continue to write/read XCom normally, but large objects bypass the metadata DB. Critical when teams routinely pass medium-sized payloads.

### 8. Multi-environment deployment.
Maintain dev/stage/prod Airflow instances with the same DAG code but environment-specific Connections, Variables, and resource configs (pools, queues, cluster sizes). Use Git tags or environment-specific branches with CI deploying the right artifact. Parameterize cluster targets so the same DAG runs against the right warehouse per environment.

### 9. CI/CD for DAGs.
On PR: parse all DAGs (`pytest` + import test), structure tests (assert `task_ids`, retries, owners), lint, security scans. On merge: deploy DAGs to dev (auto), promote to stage/prod via tags or manual approval. Use git-sync or image builds for distribution.

### 10. Testing DAGs offline.
Layered: `pytest` import test, structure assertions on `DagBag()`, unit tests for task callables (kept in a separate package), and end-to-end with `airflow dags test <dag_id> <date>` against fixtures. For provider operators, mock the hook in tests.

### 11. Secrets at scale.
Use a **secrets backend** (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, HashiCorp Vault). Airflow looks up `Connection`/`Variable` keys there transparently. Combine with cloud-managed identities so Airflow itself authenticates to the secrets backend without static credentials.

### 12. Controlling parallelism.
**`parallelism`** (cluster-wide max tasks), **`dag_concurrency` / `max_active_tasks_per_dag`**, **`max_active_runs`** (per DAG), **`pools`** (named slot buckets shared across DAGs), **`task_concurrency`** (per task across runs). Use pools to throttle access to fragile external systems (a DB, a vendor API).

### 13. SLA misses vs callbacks.
SLA misses log a row and optionally call `sla_miss_callback`; they have known limitations (task-level only, depend on DAG completion timing). Many teams instead alert on output freshness (dbt `source freshness`, Soda, custom checks) — closer to what stakeholders actually care about.

### 14. `on_failure_callback` patterns.
A function called when a task fails; common uses: Slack/PagerDuty alert, write to an incidents table, attempt cleanup, kick off a rollback DAG. Keep callbacks simple and idempotent — they run in the worker's context and a failure inside the callback can mask the real error.

### 15. Custom operator development.
Subclass `BaseOperator`, set `template_fields` (which fields support Jinja), implement `execute(self, context)`, log clearly, raise `AirflowException` on failure. Reuse hooks for external systems rather than re-implementing connection logic.

### 16. Custom hook for a new system.
Subclass `BaseHook`, accept a `conn_id`, implement `get_conn()` returning a client/session, and add helper methods (`run_query`, `upload_file`). A good hook is reusable across operators and CLIs.

### 17. KubernetesPodOperator vs DockerOperator.
**KubernetesPodOperator**: launches a pod per task in the K8s cluster — isolation, custom images, per-task resources, scales naturally. **DockerOperator**: runs on the worker's local Docker daemon — fine for dev, awkward for production. K8s-native deployments almost always use KubernetesPodOperator.

### 18. Celery vs Kubernetes vs Local executor.
**LocalExecutor**: same machine, simplest for small setups. **CeleryExecutor**: distributed workers via Celery + Redis/RabbitMQ — predictable throughput, persistent workers. **KubernetesExecutor**: each task in its own pod — perfect isolation, slower task startup, scales infinitely. **CeleryKubernetesExecutor**: hybrid — small tasks on Celery for speed, heavy tasks on K8s for isolation.

### 19. Best practices summary.
Idempotent tasks; explicit `start_date` + `catchup=False`; retries with exponential backoff; alerts via callbacks; secrets via backend; lightweight top-level DAG code; structured logging; documentation in `doc_md`; tests in CI; clear ownership; resource limits via pools; data SLAs measured on output, not just task duration.

### 20. Common production pitfalls.
`datetime.now()` in `start_date`; heavy imports at DAG-file scope; non-idempotent writes; missing `catchup=False`; sensors in poke mode for long waits; large XCom payloads; no alerting on failure; no SLA on freshness; no version control of Connections/Variables; running schedule and worker as root with full cloud admin permissions.
