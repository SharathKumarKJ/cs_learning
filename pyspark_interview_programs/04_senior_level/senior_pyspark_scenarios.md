# Senior PySpark Scenario Questions (Detailed)

### 1. You join a 5 TB fact table with a 200 MB dim table and the job is slow — how do you fix it?
Force a **broadcast join**: `from pyspark.sql.functions import broadcast; fact.join(broadcast(dim), "id")` — this ships the 200 MB dim to every executor and avoids shuffling 5 TB of facts. Verify with `df.explain()` that the plan shows `BroadcastHashJoin`, not `SortMergeJoin`. Also raise `spark.sql.autoBroadcastJoinThreshold` if Spark estimated the dim as bigger than it actually is, and project only the dim columns you need to keep the broadcast small.

### 2. Your Spark job has 1000 partitions but 3 tasks take 10× longer than the rest. What is happening and how do you fix it?
Classic **data skew**: a few keys hold most of the rows. Confirm in Spark UI by looking at the task duration histogram and per-task shuffle read size — a huge gap between median and max is skew. Fix order: (a) enable AQE skew join handling (`spark.sql.adaptive.enabled=true`, `spark.sql.adaptive.skewJoin.enabled=true`); (b) broadcast if one side is small; (c) **salt** the hot key by adding `concat(key, rand(0..N))` on the large side and exploding the small side across N salts to spread the load; (d) split the heavy keys into a separate job.

### 3. A streaming job's state size keeps growing and eventually OOMs. Why?
The watermark is missing or too loose, so old state never expires. Add `withWatermark("event_time", "10 minutes")` before any windowed aggregation or stream-stream join, choose a window/grace based on actual lateness, and verify `numRowsTotalStateRows` plateaus in `StreamingQueryProgress`. For very large state, switch the state store to RocksDB (`spark.sql.streaming.stateStore.providerClass=...RocksDBStateStoreProvider`) so state spills to disk.

### 4. Reading a folder of 500k tiny JSON files takes hours. How do you fix it?
That is the **small file problem** — listing and per-file overhead dominate. Run a one-time compaction job that reads the folder with `wholeTextFiles` or controlled partitions and writes consolidated Parquet (~128 MB-1 GB per file). For ongoing ingestion, batch writers to produce larger files, use **Auto Loader** or **Structured Streaming** with `trigger(availableNow)` and compaction, or land in a table format (Delta/Iceberg) and run `OPTIMIZE`/`rewrite_data_files` regularly.

### 5. The same Spark job produces different row counts on different runs. What's wrong?
Likely a **non-deterministic transformation**: `rand()` without a fixed seed, `current_timestamp()` used as a key, unordered window functions with ties broken arbitrarily, or non-deterministic UDFs. Lock down each source of randomness — fix seeds, use ingestion timestamps captured once and propagated, add deterministic tiebreakers (`orderBy(col, row_id)`), and mark UDFs `asNondeterministic()` only when truly necessary so Catalyst optimizes correctly.

### 6. How do you implement SCD2 in Spark on a Delta table?
Read incoming source rows, compute a hash of tracked columns, and identify changed/new records by joining against the current rows of the dim. Then do a single `MERGE`: `WHEN MATCHED AND current.hash <> source.hash THEN UPDATE SET valid_to = today, is_current = false`, then a second `MERGE` (or `WHEN NOT MATCHED` branch with a union trick) to `INSERT` the new version with `valid_from = today`, `valid_to = NULL`, `is_current = true`. Always use a stable business key + surrogate key strategy and write tests for "no overlapping valid ranges per business key."

### 7. Your pipeline must be idempotent — how do you guarantee it?
Pick deterministic logic (no random/now keys), make writes target-replace-safe (dynamic partition overwrite, MERGE with primary key, or transactional table formats), and store the run ID/data interval in the output so re-runs are recognizable. For streaming, use checkpointing + idempotent sinks. Test idempotency explicitly: run the job twice on the same interval and assert row counts and content are identical.

### 8. A `groupBy(country).agg(...)` job spills heavily to disk. How do you tune it?
Spill means partitions are too large to fit in executor memory. Options: increase `spark.sql.shuffle.partitions` so each partition is smaller; pre-aggregate before the wide shuffle (`reduceByKey`-style — combine before shuffle); ensure AQE is on so it can coalesce/skew-split partitions; reduce columns flowing into the aggregation; increase executor memory only as a last resort. Always check Spark UI's spill-to-disk and spill-to-memory metrics before and after.

### 9. How do you handle CDC events that arrive out of order in Spark?
Land raw events with their LSN/sequence/timestamp in bronze. In silver, deduplicate by primary key keeping the **maximum sequence** with a window: `row_number() OVER (PARTITION BY pk ORDER BY seq DESC) = 1`. Then MERGE with logic on `op_type` (INSERT/UPDATE/DELETE) — late events with smaller sequence are naturally ignored. Watermark + dedup window for streaming so state stays bounded.

### 10. You need to process a 50 GB Parquet file with very wide rows (2000 columns). What do you do?
Don't read all columns. Project only the columns the job actually needs at the source: `spark.read.parquet(path).select(needed_cols)` enables Parquet column pruning so most data is never read. Also push filters down (`.filter(...)`) so row-groups are skipped via Parquet statistics. If the schema is genuinely wide, consider splitting it into multiple narrower tables aligned with consumer queries — wide tables are usually a modeling smell.
