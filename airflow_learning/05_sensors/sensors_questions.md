# Airflow Sensors Questions (Detailed)

### 1. What is a sensor?
A sensor is a special operator that **waits** for a condition to become true (file exists, partition is loaded, external DAG completed, API returns a value). It calls a `poke()` method on an interval until success, timeout, or failure. Use sensors at the boundaries of pipelines that depend on external/upstream systems.

### 2. `poke` vs `reschedule` mode.
**poke** (default): the sensor occupies a worker slot for the entire wait — fine for short waits (seconds to a few minutes). **reschedule**: the sensor releases the worker slot between pokes and returns to the queue — drastically reduces slot pressure for long waits (hours). Always set `mode="reschedule"` for sensors waiting more than a few minutes.

### 3. Deferrable (async) sensors.
Built on Airflow's **triggerer** process. The sensor submits a small async coroutine to the triggerer and frees the worker completely. The triggerer can handle thousands of concurrent waits cheaply. Examples: `TimeDeltaSensorAsync`, `ExternalTaskSensor(deferrable=True)`, async S3/HTTP sensors. Strongly preferred for long waits at scale.

### 4. Common sensor types.
**S3KeySensor** / **GCSObjectExistenceSensor** / **WasbBlobSensor**: file landed. **ExternalTaskSensor**: upstream DAG/task completed. **SqlSensor**: row count or condition true. **HttpSensor**: endpoint healthy. **TimeDeltaSensor / TimeSensor**: wait until a wall-clock time. **FileSensor**: local/NFS file exists.

### 5. ExternalTaskSensor pitfalls.
It waits for a specific task in another DAG **for a specific logical date** — by default the same `execution_date` as the current run. If the two DAGs run on different schedules, you must supply `execution_date_fn` to map between them. Prefer **datasets** (Airflow 2.4+) for new cross-DAG dependencies — they avoid this entire class of bug.

### 6. Timeout and `soft_fail`.
Always set a `timeout` (in seconds) so a stuck sensor doesn't block the DAG forever. With `soft_fail=True`, timeout marks the sensor SKIPPED instead of FAILED — useful when "no data today" is a valid outcome that should not page the on-call.

### 7. Smart sensors (deprecated) vs deferrable.
Smart sensors batched many sensors into a single long-running task to save slots; they were deprecated in 2.4 in favor of **deferrable operators**, which solve the same problem more robustly via the triggerer. Migrate any remaining smart sensors to deferrable.

### 8. When NOT to use a sensor.
If the producer can simply notify you (event-driven via S3→SQS→Lambda→Airflow REST API, or a Dataset trigger), avoid sensors entirely — they cost compute and add latency. Use sensors only when polling is the only option.
