# Airflow Scheduling Questions (Detailed)

### 1. How does scheduling work in Airflow?
A DAG has a `schedule` (cron, preset, timedelta, dataset, or custom timetable) and a `start_date`. Airflow advances a logical clock in fixed **data intervals**; a DAG run for interval `[start, end)` is queued **at the end** of that interval. The `data_interval_start`/`data_interval_end` context variables tell the task which window it is processing — use them, not `datetime.now()`.

### 2. `schedule` vs the old `schedule_interval`.
`schedule_interval` was the original parameter; `schedule` (2.4+) is the unified, more flexible replacement that accepts cron strings (`"0 6 * * *"`), presets (`"@daily"`), `timedelta`, datasets (`[Dataset("s3://...")]`), or `Timetable` instances. New code should use `schedule`.

### 3. Difference between logical date and run time.
**Logical date / data_interval_start**: the start of the data window the run represents (yesterday for a daily job running today). **Run time**: when Airflow actually executes it (end of interval + scheduler/queue latency). Always use the logical date for partition filters; using wall-clock time causes off-by-one errors and non-idempotent runs.

### 4. What is `catchup`?
If `catchup=True` (legacy default), Airflow backfills every missed interval between `start_date` and now. Set `catchup=False` for most production DAGs so a paused-then-resumed DAG does not suddenly run 200 historical runs. Use `airflow dags backfill` explicitly when you need history.

### 5. `max_active_runs` and `max_active_tasks`.
**`max_active_runs`** caps concurrent DAG runs (default 16); essential when consecutive intervals must not overlap (e.g. SCD2 writes to the same partition). **`max_active_tasks`** (per DAG) and **pools** cap concurrent task instances; use pools to throttle access to shared external systems (a DB, an API).

### 6. Custom timetables.
For schedules cron cannot express — business-day-only, last-friday-of-month, market trading hours, fiscal calendars — implement `Timetable` with `next_dagrun_info()` and `infer_manual_data_interval()`. They replace the old `schedule_interval` for complex business calendars.

### 7. Dataset-aware scheduling.
Producers declare `outlets=[Dataset("s3://lake/orders")]` on their final task; consumers set `schedule=[Dataset("s3://lake/orders")]` and trigger automatically when the producer updates the dataset. Eliminates the need for cross-DAG sensors and decouples producers from consumers.

### 8. SLA misses vs SLA callbacks.
An **SLA** is the maximum allowed time from `data_interval_start` to task completion. Misses are logged and an optional `sla_miss_callback` fires. SLAs in Airflow have known limitations (only on tasks, not full DAGs; not always reliable) — many teams instead use freshness checks on the output data (dbt `source freshness`, Soda, Great Expectations) and alert from there.

### 9. Backfilling.
`airflow dags backfill -s 2026-01-01 -e 2026-01-31 my_dag` re-runs intervals in that range. Make tasks idempotent (writes go to date-partitioned targets, MERGE not INSERT) so backfill is safe. For huge backfills, throttle with `max_active_runs` to avoid hammering downstream systems.

### 10. How does the scheduler decide the next run?
At each scheduler heartbeat it asks each DAG's timetable for the next data interval, compares to the latest run in the metadata DB, checks `catchup`/`depends_on_past`/`max_active_runs`, and queues a DAG run when conditions are met. Understanding this loop is critical when debugging "why isn't my DAG running" issues.
