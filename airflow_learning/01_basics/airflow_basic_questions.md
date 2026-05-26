# Airflow Basic Interview Questions (Detailed)

### 1. What is Airflow?
Apache Airflow is an open-source workflow orchestration platform where pipelines are defined as Python code (DAGs). It schedules, executes, monitors, retries, and alerts on tasks. The web UI provides visibility into runs, logs, and dependencies.

### 2. What is a DAG?
A **Directed Acyclic Graph** of tasks: directed edges define order, and no cycles are allowed (no task can depend on itself directly or indirectly). A DAG file is a Python module that constructs a `DAG` object with tasks and dependencies.

### 3. What is a task?
A single unit of work in a DAG, an instance of an operator (or `@task`-decorated function). A "task instance" is the execution of a task for a specific DAG run / data interval.

### 4. What is an operator?
A template that defines what a task does. Examples: `PythonOperator`, `BashOperator`, `KubernetesPodOperator`, provider-specific operators like `S3ToRedshiftOperator`. With the TaskFlow API (`@task`), you mostly write functions and Airflow handles the operator under the hood.

### 5. What is the scheduler?
The component that parses DAG files, determines which task instances are ready to run based on schedule, dependencies, and triggers, and queues them for execution. It is the heart of Airflow — its performance limits the platform's throughput.

### 6. What is an executor?
Decides how queued task instances are executed. **LocalExecutor**: same machine, parallel via subprocesses. **CeleryExecutor**: distributed workers via Celery + broker (Redis/RabbitMQ). **KubernetesExecutor**: each task runs as a pod. **CeleryKubernetesExecutor**: mix of both.

### 7. What is a worker?
A process (or pod) that actually executes tasks. In Celery setup it polls the queue and runs tasks; in Kubernetes setup it is a transient pod per task. Workers must have access to the same DAG code and connection metadata as the scheduler.

### 8. What is `start_date`?
The earliest logical date for which Airflow can schedule a run of this DAG. Airflow does not run anything before this date. A common pitfall is setting `start_date=datetime.now()` — use a fixed date (e.g. `datetime(2026,1,1)`) so behavior is reproducible.

### 9. What is `catchup`?
If `catchup=True` (default until you change it), Airflow backfills every missed schedule interval between `start_date` and now. Set `catchup=False` for most production DAGs so it only runs the latest interval; backfill explicitly when needed.

### 10. What is XCom?
"Cross-communication": a small key-value store in the metadata DB that tasks use to pass return values between each other. Default backend stores in the DB — keep payloads tiny (IDs, paths, counts). For large data, use S3/GCS/ADLS as the medium and pass the path through XCom, or configure a custom XCom backend.

---

## Intermediate Airflow

### 11. TaskFlow API vs classic operators.
**Classic**: instantiate operators (`PythonOperator(task_id="t", python_callable=fn)`) and wire with `>>`. **TaskFlow** (`@task`): decorate a Python function; Airflow infers task ID, handles XCom return/args, makes code feel like normal Python. Use TaskFlow for new code; mix freely with operators (Bash, KubernetesPod, providers).

### 12. Connections and how they're used.
A `Connection` stores credentials/host/port/extras for an external system (Postgres, S3, Snowflake). Operators/hooks load by `conn_id`. Stored in metadata DB by default; better to back with a **secrets backend** (AWS Secrets Manager, Vault). Never hard-code creds in DAG files.

### 13. Variables.
Key-value strings in the metadata DB, accessed via `Variable.get("name")` or Jinja `{{ var.value.name }}` / `{{ var.json.name }}`. Use for environment toggles, not secrets. Avoid `Variable.get` at the top of a DAG file — it runs on every parse. Prefer env vars or a config file for values needed at parse time.

### 14. Jinja templating.
Operator fields listed in `template_fields` are rendered with Jinja at execution time. Built-in vars: `{{ ds }}` (logical date YYYY-MM-DD), `{{ ts }}`, `{{ data_interval_start/end }}`, `{{ params.x }}`, `{{ var.value.x }}`, `{{ conn.my_conn.host }}`. Lets one DAG run idempotently for any interval.

### 15. Logical date vs execution date.
Older Airflow used "execution_date" = start of the interval. Airflow 2 introduced **`logical_date`** + **`data_interval_start` / `data_interval_end`** to clarify: a DAG runs *after* its interval, processing data *from* `data_interval_start` *up to* `data_interval_end`. Use the interval vars in SQL templates.

### 16. Trigger rules.
Per-task rule for when it runs based on upstream state:
- `all_success` (default), `all_failed`, `all_done`.
- `one_success`, `one_failed`, `one_done`.
- `none_failed`, `none_failed_min_one_success`, `none_skipped`.
- `always`.
Use `none_failed_min_one_success` as the join after a branch.

### 17. Sensors.
Tasks that wait for a condition (file arrives, partition exists, external DAG done). Three modes:
- **poke** (default): occupies a worker slot — bad for long waits.
- **reschedule**: releases the slot between checks — preferred for polls > a few min.
- **deferrable** (async, requires triggerer): essentially free during the wait — best for any sensor at scale.

### 18. Deferrable operators.
An operator that releases its worker, registers a **trigger** (an async coroutine running in the triggerer process), and resumes when the trigger fires. One triggerer process handles thousands of waits. Providers like AWS / GCP / HTTP / time-based ship deferrable variants — use them for sensors and long-running waits.

### 19. Hooks.
The low-level client to an external system, wrapping a Connection. Operators are thin wrappers around hooks. Reuse hooks in custom operators / `@task` functions: `S3Hook().download_file(...)`. Don't write boto3 calls in DAGs — use the hook.

### 20. Pools.
Named buckets of concurrency slots. A task with `pool="my_db"` of size 5 means at most 5 such tasks run at once cluster-wide. Use to throttle access to fragile externals (a database, a vendor API). Independent of DAG-level concurrency settings.

### 21. Priority weight.
Within a pool, tasks ordered by `priority_weight` (default sums upstream weights). Tunable for SLAs — high-priority pipelines preempt low-priority ones for scarce slots.

### 22. Retries and retry behavior.
`retries=3, retry_delay=timedelta(minutes=5)`, `retry_exponential_backoff=True`, `max_retry_delay=timedelta(hours=2)`. Combine with `email_on_retry=False` and an `on_retry_callback` for Slack noise control. Distinguish transient (retry) vs permanent (raise `AirflowFailException` — no retry).

### 23. SLA vs SLO vs freshness.
`sla=timedelta(hours=1)` on a task fires `sla_miss_callback` if the task isn't done by `data_interval_end + sla`. Known to have edge cases (only at DAG completion). Many teams instead alert on **output freshness** (table max(updated_at)) — closer to what stakeholders measure.

### 24. Callbacks.
`on_success_callback`, `on_failure_callback`, `on_retry_callback`, `on_execute_callback`, `sla_miss_callback`. Receive context dict; do small things (alert, log, write metric). Keep idempotent; a failing callback can mask root cause.

### 25. Dynamic task mapping (deeper).
`process.expand(file=list_files())` creates N task instances at runtime. Use `expand_kwargs` for multiple kwargs varying together; use `.partial()` for fixed args. Limit `max_active_tis_per_dag` per mapped task to avoid swamping a downstream system. Mapped tasks have indexes (`task_id=process, map_index=0..N-1`).

### 26. TaskGroups (intermediate use).
Visual grouping; nest them; parameterize via factory functions:
```python
def build_etl_group(source):
    with TaskGroup(f"etl_{source}") as g:
        extract = ...
        load = ...
    return g
```
Cleaner than huge flat DAGs.

### 27. ExternalTaskSensor / ExternalTaskMarker.
Wait for a task in another DAG to finish. Useful but brittle (timing mismatches, schedules drift). **Datasets** (Airflow 2.4+) are the modern, decoupled alternative — emit/consume events instead of polling.

### 28. Datasets (data-aware scheduling).
Producer DAG declares `outlets=[Dataset("s3://lake/orders")]`; consumer DAG sets `schedule=[Dataset(...)]`. When the producer succeeds, Airflow triggers consumers. Replaces cross-DAG sensors. Multi-dataset schedules work as logical AND/OR.

### 29. Backfill.
`airflow dags backfill --start-date X --end-date Y dag_id` runs missed intervals. Combine with `--max-active-runs` and `--reset-dagruns`. Requires `catchup=True` or explicit backfill command. Idempotency of tasks is non-negotiable here.

### 30. Reruns and clears.
**Clear** a task instance to rerun it. **Clear downstream** to rerun all dependents. Useful for fixing a bug then re-processing the affected runs. Use the UI or `airflow tasks clear`. Doesn't change DB rows from the task automatically — must be idempotent.

### 31. Logs in Airflow.
Per-task-instance logs streamed to scheduler/UI. Configure **remote logging** (S3/GCS/Azure/Elasticsearch) so they persist beyond worker lifetime, especially with KubernetesExecutor where pods vanish. UI fetches from remote when local missing.

### 32. Airflow REST API.
Stable since 2.0. Trigger DAGs, list runs, get logs, manage Variables/Connections. Authenticate with token / basic auth (better: OAuth/JWT via plugin). Useful for triggering from upstream systems, CI/CD, custom UIs.

### 33. Plugins.
Drop a Python package into the plugins folder to add Operators, Hooks, Macros, UI views, ExecutorFactory, etc. Most needs are met by providers (PyPI packages) — write a plugin only for organization-specific glue.

### 34. Providers.
Versioned PyPI packages (`apache-airflow-providers-amazon`, `-snowflake`, `-google`, `-microsoft-azure`) shipping Hooks/Operators/Sensors/Connections for an external system. Decoupled from core Airflow upgrades — bump provider versions independently.

### 35. Common intermediate gotchas.
- `Variable.get("x")` at top-level DAG → hits DB every parse.
- Long-running sensor in poke mode → eats slots.
- Storing DataFrames in XCom → metadata DB bloat.
- Using `datetime.now()` in DAG file → non-deterministic `start_date`/schedule.
- Forgetting `catchup=False` → flood of backfill runs on first deploy.
- Trigger rules misuse → branches don't converge correctly.
- Heavy imports in DAG file → slow parsing, scheduler can't keep up.
