# Airflow DAG Design Questions (Detailed)

### 1. What makes a good DAG design?
A good DAG is **idempotent** (re-running produces the same result), **deterministic** (no hidden state from `datetime.now()` or random seeds without fixing them), **decoupled** (business logic lives in a Python package, the DAG just wires tasks together), **small in scope** (one DAG per business pipeline, not a mega-DAG), and **observable** (clear task IDs, owners, SLAs, alerts). Aim for tasks that each do one thing and complete in minutes, not hours.

### 2. How do you avoid putting heavy logic in the DAG file?
The DAG file is parsed every `min_file_process_interval` (default 30 s) by the scheduler — any top-level imports, DB calls, HTTP requests, or S3 listings run on every parse and tank scheduler performance. Move logic into functions/classes inside an installed Python package, then call them from `PythonOperator` or `@task` callables. Top-level code should only construct the DAG object.

### 3. How do you parameterize a DAG?
Use **`params`** for run-time overrides via the UI/REST API, **Variables** (`Variable.get("name", default_var=...)`) for environment-level config (rarely changing), **Connections** for credentials, and **Jinja templating** (`{{ ds }}`, `{{ params.x }}`) inside operator fields to inject values at runtime. For multi-environment configs, prefer a YAML file shipped with the code over Variables.

### 4. How do you pass data between tasks?
**XCom** is the built-in mechanism — return a value from one task and `task_instance.xcom_pull(task_ids="...")` (or just receive it as a parameter in TaskFlow). Keep XCom payloads tiny (IDs, paths, counts) because they live in the metadata DB. For large data, write to S3/GCS/ADLS and pass the path through XCom, or configure a custom XCom backend (S3) so large objects bypass the DB.

### 5. When should you split into multiple DAGs?
Split when pipelines have **different schedules**, **different owners**, **different SLAs**, or **different failure isolation** requirements. Don't split tasks that always run together — that just adds inter-DAG coordination overhead. Use **Datasets** (Airflow 2.4+) to declaratively connect producer and consumer DAGs by data, not by schedule.

### 6. What is dynamic task mapping?
Introduced in 2.3, it lets a single task definition expand into N parallel task instances at runtime based on the output of another task: `process.expand(file=list_files())`. Replaces the older pattern of generating tasks at parse time with Python loops, which was bad for scheduler performance. Use it for fan-out work like "process each file in a folder."

### 7. What are TaskGroups?
A purely visual grouping of related tasks in the UI (no runtime semantics). They make large DAGs readable: e.g. an `extract` group, `transform` group, `load` group. Unlike SubDAGs (deprecated), TaskGroups have no scheduling overhead.

### 8. How do you handle branching logic?
Use `BranchPythonOperator` or `@task.branch` — the callable returns the `task_id` (or list) of downstream tasks to run; others are skipped. Pair with a `trigger_rule="none_failed_min_one_success"` join task so the DAG can converge cleanly after the branch.
