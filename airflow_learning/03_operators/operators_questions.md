# Airflow Operators Questions (Detailed)

### 1. What is an operator?
An operator is a template describing a single unit of work. Instantiating it inside a DAG creates a **task**; at runtime that task becomes a **task instance**. Airflow ships dozens of built-in and provider operators; you can also write your own by subclassing `BaseOperator` and implementing `execute(self, context)`.

### 2. PythonOperator vs TaskFlow `@task`.
**`PythonOperator`**: classic, explicit — pass `python_callable=fn`, `op_kwargs={...}`. **`@task` decorator** (TaskFlow API, 2.0+): cleaner — just write `@task def fn(x): ...; fn(value)`. TaskFlow handles XCom plumbing automatically (return value becomes XCom, function arguments come from upstream returns). Prefer TaskFlow for Python work in new code.

### 3. BashOperator.
Runs a Bash command on the worker. Supports Jinja templating in `bash_command`, env vars via `env`. Useful for invoking CLIs (gsutil, aws, dbt), but lacks structured error handling — prefer Python or Kubernetes operators for non-trivial work.

### 4. KubernetesPodOperator.
Launches a pod in a Kubernetes cluster for each task, isolated from the worker. Each task can have its own image, resources (CPU/memory/GPU), and dependencies — perfect for heterogeneous workloads and resource isolation. Common choice for production Airflow on K8s.

### 5. DockerOperator.
Runs a Docker container on the worker host. Simpler than K8s for local/dev but requires Docker daemon access on workers and does not scale per-task across a cluster. Largely superseded by `KubernetesPodOperator`.

### 6. SqlOperator family (SnowflakeOperator, BigQueryInsertJobOperator, etc.).
Provider operators that run SQL on a target system using a configured Airflow Connection. They support templated SQL files, parameter substitution, and return useful metadata (job IDs, query stats). For dbt, use `BashOperator`/`DbtCloudRunJobOperator` or the `astronomer-cosmos` library.

### 7. Sensors (overview).
A special class of operator that **waits** for an external condition (file in S3, partition in Hive, row in DB, time of day). Sensors run in either `poke` mode (occupies a worker slot for the whole wait) or `reschedule` mode (releases the slot between checks — preferred for long waits). Async/deferrable sensors are even cheaper because they free the worker entirely.

### 8. Custom operators.
Subclass `BaseOperator`, define `template_fields` (which params support Jinja), implement `execute(self, context)`, and use hooks for external systems. Write a custom operator when you have repeated logic across many DAGs; otherwise a regular Python function called from `@task` is simpler.
