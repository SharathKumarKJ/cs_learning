# Structured Streaming Questions (Detailed)

### 1. What is Structured Streaming?
Spark's stream processing engine built on the same DataFrame API as batch. It treats a stream as an unbounded table that grows over time; the same query you write for batch runs incrementally as new data arrives. Supports micro-batch and continuous (experimental) modes.

### 2. Difference between processing time and event time?
Processing time is when Spark sees the record (clock on the cluster). Event time is when the event actually happened (timestamp inside the record). Aggregations on event time are correct even when data arrives late or out of order; processing time can produce wrong analytics.

### 3. What is watermarking?
A watermark tells Spark how late data can arrive before it is considered lost. Set with `withWatermark("event_time", "10 minutes")`. Spark uses it to expire state for windows older than `(max_event_time - watermark)` so memory does not grow unbounded.

### 4. What output modes exist?
**Append**: only new rows added since last trigger (no updates to past output) — works with windows + watermark. **Update**: rows that changed since last trigger — good for sinks that support upsert. **Complete**: full result table — only practical for small aggregated outputs.

### 5. What is checkpointing in streaming?
Checkpointing persists query progress (source offsets, schema, state store snapshots) so the query can resume exactly where it left off after a restart. Set via `option("checkpointLocation", "<path>")`. Without it, you cannot guarantee at-least-once delivery.

### 6. Why is the checkpoint location critical?
It is the single source of truth for stream progress and state. Deleting it forces reprocessing; sharing it between two queries causes corruption. Each query must have its own checkpoint folder on durable storage (HDFS/S3/ADLS/GCS).

### 7. How do you handle duplicates?
Use `dropDuplicates(["event_id", "event_time"])` with a watermark so Spark can drop state for old IDs. Pair with idempotent sinks (transactional writes, MERGE) so retries do not produce duplicates downstream.

### 8. What is exactly-once processing?
End-to-end exactly-once requires three properties together: (a) replayable source with offsets (Kafka, Kinesis); (b) Spark checkpointing for stateful progress; (c) idempotent or transactional sink (Delta, file sink with `_committed_` markers, foreachBatch with MERGE). Without any one, you only get at-least-once.

### 9. How do you join streams?
Stream-stream joins require watermarks on both sides and a time constraint on the join (`leftTime BETWEEN rightTime - INTERVAL X AND rightTime + INTERVAL Y`) so Spark can bound state. Inner, left outer, and right outer joins are supported under these conditions.

### 10. What causes streaming state to grow too large?
Missing or too-loose watermark, very wide time windows, high-cardinality `groupBy` keys, unbounded `dropDuplicates`, or stream-stream join without time constraint. Monitor `numRowsTotalStateRows` in `StreamingQueryProgress` and tune state store (RocksDB) on Databricks/OSS Spark 3.2+.

### 11. How do you monitor streaming jobs?
Watch the `StreamingQueryProgress` metrics: input/processing rate, batch duration, event-time watermark, state size, sink commit time. Export to Prometheus/Datadog/CloudWatch. Alert when processing rate < input rate (falling behind) or watermark lag grows.

### 12. What is `trigger(availableNow=True)`?
Runs as a streaming query but processes all currently available data in one or a few batches, then stops. Combines streaming's checkpointed offsets with batch-style scheduling — perfect for hourly/daily incremental jobs orchestrated by Airflow.

---

## Advanced Structured Streaming

### 13. Micro-batch vs continuous processing.
**Micro-batch** (default): Spark schedules a job per trigger, processes new offsets, commits. Throughput-oriented, ~100 ms–seconds latency. **Continuous** (experimental, Spark 2.3+): long-running tasks read one record at a time, ms latency, very few operations supported (no aggregations). Production uses micro-batch.

### 14. Trigger modes summary.
- `Trigger.ProcessingTime("30 seconds")`: fixed cadence.
- `Trigger.Once()` (deprecated): one batch then stop.
- `Trigger.AvailableNow()`: process all current data in possibly multiple batches, then stop — supersedes `Once` for big backlogs.
- `Trigger.Continuous("1 second")`: continuous processing mode.
Default = micro-batch as fast as possible.

### 15. Sources and sinks.
**Sources**: Kafka (most common), Kinesis, file sources (S3/HDFS), Delta/Iceberg CDF, socket/rate (testing). **Sinks**: Kafka, file (Parquet/JSON/ORC), Delta/Iceberg, `foreach`, `foreachBatch`, console/memory (testing).

### 16. `foreachBatch` for arbitrary sinks.
```python
def upsert(batch_df, batch_id):
    batch_df.write.format("jdbc").mode("append").save()
stream.writeStream.foreachBatch(upsert).start()
```
Each micro-batch's DataFrame is passed to your function. Used for MERGE into Delta, JDBC sinks, multi-sink fan-out. Must be idempotent — Spark can retry the same `batch_id`.

### 17. Stateful operations & state store.
Aggregations, joins, deduplication, `mapGroupsWithState`/`flatMapGroupsWithState` keep state across batches in a **state store**. Default: HDFS state store. **RocksDB state store** (Spark 3.2+, default in Databricks) handles much larger state by spilling to local disk. Set via `spark.sql.streaming.stateStore.providerClass`.

### 18. `mapGroupsWithState` vs `flatMapGroupsWithState`.
Arbitrary stateful processing: UDF gets `(key, new_inputs, current_state)` and returns updated state + outputs. `map` returns one output per key per batch; `flatMap` returns zero or more. Use for sessionization, complex state machines, custom dedupe with timeouts.

### 19. Sessionization.
Group events by user, close session after N minutes of inactivity. Build with `flatMapGroupsWithState` (custom timeouts via `state.setTimeoutDuration`) or with `session_window` (Spark 3.2+): `groupBy(session_window("ts", "30 minutes"))`.

### 20. Watermark mechanics in detail.
`withWatermark("event_time", "10 minutes")` declares "we'll wait up to 10 min for late events". Spark drops state for windows older than `max(event_time) - 10 min` and **drops late records** entirely in append mode. Too-tight watermark → data loss; too-loose → state explosion. Always set it for any windowed aggregation.

### 21. Late data handling per output mode.
- **Append**: late events past watermark are silently dropped; results emit only after window closes.
- **Update**: rows that change since last batch are re-emitted; late events update previous results until watermark passes.
- **Complete**: full result every batch; expensive but late updates always reflected.

### 22. Window types.
- **Tumbling**: fixed, non-overlapping (`window("ts", "5 minutes")`).
- **Sliding**: fixed size, slides by step (`window("ts", "5 minutes", "1 minute")` — 5-min window every 1 min).
- **Session**: variable, closed by inactivity gap.
Sliding windows multiply state — use sparingly.

### 23. Stream-static join.
Joining a stream with a static DataFrame (dimension lookup). The static side is broadcast each batch — refresh by re-reading inside `foreachBatch` or with periodic restart. Useful for enrichment with slowly-changing dimensions.

### 24. Stream-stream join.
Both sides streaming. Requires watermarks on both + time-bound condition. Inner join can emit late inners after watermark; outer joins emit nulls only after watermark on the missing side. State held until both watermarks pass.

### 25. Backpressure & rate limiting.
Kafka source: `maxOffsetsPerTrigger` caps records per batch — prevents huge first batch on a backlog. File source: `maxFilesPerTrigger`, `maxBytesPerTrigger`. Without these, you can OOM after downtime when the queue is huge.

### 26. End-to-end exactly-once.
Requires (a) replayable source with offsets (Kafka, Kinesis, file), (b) checkpointed processing (Spark state + offset commits), (c) idempotent or transactional sink. Delta/Iceberg `foreachBatch` with MERGE on a deterministic key — best in practice. File sink with `_committed_` markers — exactly-once for files.

### 27. Idempotent sinks pattern.
For non-transactional sinks (JDBC, REST), use `batch_id` as part of the idempotency key. Upsert by `(natural_key, batch_id)` and de-duplicate downstream. Or write to a staging table and MERGE on commit.

### 28. Schema evolution in streams.
Kafka: source schema fetched on stream start; new producer fields are ignored unless you re-read. For file sources, set `cloudFiles.schemaEvolutionMode` (Auto Loader) to `addNewColumns`. Plan column drops/renames as breaking changes — typically requires restarting the query against a new checkpoint.

### 29. Checkpoint internals.
Stored under `checkpointLocation`: `offsets/` (source progress), `commits/` (sink confirmations), `state/` (state store snapshots + deltas), `metadata` (query metadata). Corrupting these = data loss or duplication. Back up checkpoints for disaster recovery.

### 30. Restarting with code changes.
Some changes are checkpoint-compatible (adding new columns, expanding filters); others break (changing aggregation key, watermark column, output schema). Spark validates on start and fails loudly. For breaking changes, drain via `availableNow`, archive checkpoint, start fresh with a new path.

### 31. Multiple queries in one app.
Each `start()` returns a `StreamingQuery`. Manage with `spark.streams.active`. Use independent checkpoints. Beware shared resources (executor memory, sink connections). For many small queries, prefer multiple apps for isolation.

### 32. Async progress logging.
`spark.streams.addListener(StreamingQueryListener)` emits events: `onQueryStarted`, `onQueryProgress`, `onQueryTerminated`. Export to Kafka / metrics endpoint for centralized monitoring. Databricks has built-in dashboards; OSS Spark needs custom wiring.

### 33. Auto Loader (Databricks).
Optimized file source for cloud storage using SNS+SQS / EventGrid notifications instead of expensive directory listing. Handles schema evolution, dead-letter quarantine. Outperforms vanilla file source by orders of magnitude on big buckets.

### 34. Delta Live Tables / Pipelines.
Declarative streaming framework on Databricks: define expectations (constraints), lineage, retries. Handles infrastructure (clusters, checkpoints, restarts) and quality gates. Equivalent OSS approaches: dbt + Spark streaming, but DLT is more integrated.

### 35. Tuning RocksDB state store.
Set `spark.sql.streaming.stateStore.rocksdb.compactOnCommit=true` for predictable size, tune block cache memory, watch `numRowsDroppedByWatermark` and `stateMemoryUsedBytes`. For huge state (100M+ keys), partition keys evenly and consider scaling executors.

### 36. Performance pitfalls.
Too-small batch interval (overhead dominates), unbounded state (no watermark or wrong key), shuffles per batch (re-partition needed), serialization overhead from Python UDFs (use built-ins or Pandas UDFs), sink commit slowness blocking next batch, Kafka source partition count < executor cores (under-parallel).

### 37. Spark Streaming vs Flink vs Kafka Streams.
- **Spark Structured Streaming**: same API as batch, micro-batch (mostly), great for SQL-heavy stateful workloads, Delta/Iceberg integration.
- **Flink**: true event-at-a-time, lowest latency, richest windowing, native exactly-once with two-phase commit.
- **Kafka Streams**: JVM library, simplest deploy (no cluster), tightly coupled to Kafka, great for stateless transforms and KTables.
Choose Flink for ms-latency complex events; Spark for SQL/ETL/ML on streams; Kafka Streams for in-app processing.

### 38. Failure recovery.
On restart, Spark reads checkpoint, replays uncommitted batches, rebuilds state from snapshots. Sink idempotency ensures no duplicates. Common failure modes: poison messages (handle in `foreachBatch` with try/except and DLQ), schema mismatch (validate and quarantine), state corruption (very rare — restore checkpoint).

### 39. Testing streaming jobs.
Use `MemoryStream` or `rate` source for unit tests; assert on `processAllAvailable()` + collected results. Integration: spin up Kafka in testcontainers, run small end-to-end. CI: golden offsets + expected outputs. Always test schema evolution and watermark behavior explicitly.

### 40. Real-world stream architecture.
Kafka (events) → Spark Structured Streaming (`availableNow` every minute or continuous micro-batch) → Delta bronze (append all) → Delta silver (`foreachBatch` MERGE for dedupe/CDC) → Delta gold (aggregations) → BI / ML. Add Auto Loader for files, dataset-aware Airflow for orchestration of `availableNow` jobs, Prometheus for monitoring.
