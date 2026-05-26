# ClickHouse Interview Questions — Basic to Advanced (Detailed)

A comprehensive question bank covering ClickHouse fundamentals, table engines, query language extensions, performance tuning, replication, sharding, and production operations.

---

## 1. Basics

### 1. What is ClickHouse?
A column-oriented OLAP database open-sourced by Yandex in 2016, designed for sub-second analytical queries over billions to trillions of rows. Uses columnar storage, vectorized execution, aggressive compression, and massively parallel query execution. SQL-like dialect with many extensions.

### 2. Why is ClickHouse so fast?
**Columnar storage** (read only needed columns), **data compression** (LZ4/ZSTD per column with codecs like Delta, DoubleDelta, T64), **vectorized engine** (SIMD over chunks of column data, not row-by-row), **sparse primary index** (granules of ~8192 rows, index fits in RAM), **massively parallel** execution per CPU core and per shard, and **locality** of data on disk.

### 3. OLAP vs OLTP — where does ClickHouse fit?
**OLAP** (Online Analytical Processing): few writes, many reads, big aggregations over wide tables — ClickHouse is built for this. **OLTP** (PostgreSQL, MySQL): many small read/writes, row-by-row updates, strong transactions — ClickHouse is *not* a good fit (no per-row updates/deletes by default, eventual consistency, weaker transactional guarantees).

### 4. ClickHouse vs other OLAP systems.
**vs Snowflake/BigQuery**: ClickHouse is open source, self-hostable, much cheaper at scale, but requires more ops. **vs Redshift**: faster and more flexible, more complex to operate. **vs Druid/Pinot**: similar real-time analytics but ClickHouse has richer SQL, simpler model. **vs DuckDB**: DuckDB is single-process embedded; ClickHouse is a distributed server.

### 5. Row-oriented vs column-oriented.
Row store keeps all columns of one row together (good for reading whole rows). Column store keeps each column together on disk (good for scanning few columns over many rows). Analytics typically reads a few columns out of hundreds — columnar wins, often by orders of magnitude.

### 6. Installing & running ClickHouse.
`curl https://clickhouse.com/ | sh` or via Docker (`clickhouse/clickhouse-server`), apt/yum repos, or managed offerings (ClickHouse Cloud, Altinity, Aiven). Two main binaries: `clickhouse-server` (the daemon) and `clickhouse-client` (CLI/SQL client).

### 7. Basic SQL — CREATE / INSERT / SELECT.
```sql
CREATE TABLE events (
    event_time DateTime,
    user_id UInt64,
    event_type LowCardinality(String),
    payload String
) ENGINE = MergeTree
ORDER BY (event_time, user_id);

INSERT INTO events VALUES (now(), 1, 'click', '{}');
SELECT event_type, count() FROM events GROUP BY event_type;
```

### 8. Data types.
Numeric: `Int8/16/32/64`, `UInt*`, `Float32/64`, `Decimal(P,S)`. String: `String`, `FixedString(N)`, `LowCardinality(String)` (dictionary-encoded). Date: `Date`, `Date32`, `DateTime`, `DateTime64(precision, tz)`. Composite: `Array(T)`, `Tuple`, `Map(K,V)`, `Nested(...)`, `Nullable(T)`, `Enum8/16`. Specialized: `UUID`, `IPv4`, `IPv6`, `JSON` (newer).

### 9. `Nullable` — when to use.
`Nullable(T)` adds a per-row null mask — extra storage and slightly slower queries. Avoid unless you need NULL semantics. Idiomatic ClickHouse uses sentinel values or empty strings/zeros and saves the overhead. Same for nested nullables.

### 10. `LowCardinality`.
Dictionary encoding for columns with few distinct values (typically <10k). Dramatically reduces storage and speeds up filtering/grouping. Standard for `String` columns like country codes, event types, status flags. Don't use for high-cardinality data — wastes effort.

### 11. Codecs.
Per-column compression codecs: `Delta` + `LZ4` for sorted timestamps, `DoubleDelta` for monotonic counters, `Gorilla` for floats, `T64` for sorted integers, `ZSTD(level)` for cold data. Combine in chain: `CODEC(Delta, ZSTD(3))`. Massive impact on size and scan speed.

### 12. `system.*` tables.
Built-in introspection: `system.parts`, `system.tables`, `system.columns`, `system.processes` (running queries), `system.query_log`, `system.metrics`, `system.replicas`, `system.merges`. Indispensable for ops; query them like normal tables.

---

## 2. Table Engines

### 13. The MergeTree family — overview.
**MergeTree** is the workhorse — sorted by primary key, splits data into immutable parts that background processes merge. Variants: **ReplacingMergeTree** (deduplicates by sort key during merge), **SummingMergeTree** (sums numeric columns on merge), **AggregatingMergeTree** (stores intermediate aggregate states), **CollapsingMergeTree**/**VersionedCollapsing** (handle row updates via +1/-1 sign columns), **GraphiteMergeTree** (time-series rollups).

### 14. How MergeTree stores data.
Inserts go to a new part (sorted by primary key, compressed). Background merges combine small parts into bigger ones (similar to LSM compaction). Each part has its own primary-key index (sparse, one entry per granule of 8192 rows by default). Reads merge results from all parts.

### 15. Primary key vs ORDER BY.
ORDER BY defines the on-disk sort order **and** the default primary key. Primary key can be a prefix of ORDER BY (e.g., `ORDER BY (a,b,c) PRIMARY KEY (a,b)`). It is **sparse** (index ~1 entry per 8192 rows) — fits in memory even for huge tables. Not a uniqueness constraint.

### 16. Partitioning vs ordering.
`PARTITION BY toYYYYMM(event_time)` splits parts into folders by month — used for pruning, TTL, and `ALTER ... DROP PARTITION`. **ORDER BY** controls on-disk sort within a part. Common pitfall: too many partitions (e.g., daily for 10 years) → many small parts, slow startup. Aim for tens to a few hundred partitions per table.

### 17. ReplacingMergeTree.
Deduplicates rows with the same sort key during merges, keeping the latest by an optional version column: `ReplacingMergeTree(version)`. Useful for upserts. **Caveat**: dedup happens only during merge — until then, duplicates are visible. Use `FINAL` keyword in SELECT (slow) or `OPTIMIZE TABLE ... FINAL` (manual) to force.

### 18. SummingMergeTree / AggregatingMergeTree.
**SummingMergeTree** sums numeric columns on merge for rows with same sort key (e.g., pre-aggregating event counts). **AggregatingMergeTree** stores `AggregateFunction(...)` intermediate states (`sumState`, `uniqState`) — finalized in queries via `sumMerge`, `uniqMerge`. Powers materialized views for OLAP cubes.

### 19. CollapsingMergeTree.
Rows have a `Sign` column (+1 = state, -1 = cancel). On merge, equal sort-key rows with opposite signs are dropped. Lets you "undo" old rows by inserting their negation. **VersionedCollapsingMergeTree** adds a version column for correct ordering.

### 20. Log family engines.
**TinyLog**, **Log**, **StripeLog** — append-only, no indexes, no concurrent reads/writes, no replication. Useful only for tiny temp tables. Production tables almost always use MergeTree.

### 21. Memory engine.
Holds data in RAM only; lost on restart. Fast for small lookups, but use `Dictionary` (below) instead — dictionaries are reload-safe and explicitly cached.

### 22. Integration engines.
**Kafka**, **RabbitMQ**, **PostgreSQL/MySQL** (read external tables), **S3**, **HDFS**, **URL**, **MongoDB**. Read or stream from external sources directly via SQL. Often combined with a materialized view: Kafka engine table → MV → MergeTree.

### 23. Distributed engine.
A virtual table sitting on top of multiple shards: `ENGINE = Distributed(cluster, db, local_table, sharding_key)`. Queries fan out to all shards in parallel and merge results. Inserts route to shards by `sharding_key`. The shard's actual data lives in a local `ReplicatedMergeTree` table.

### 24. ReplicatedMergeTree.
Variant of MergeTree that replicates data via ZooKeeper or **ClickHouse Keeper** (recommended now). Each replica pulls parts from peers; inserts are quorum-checked. Combine with `Distributed` to get a sharded + replicated cluster.

### 25. Dictionary.
External or internal lookup tables loaded into RAM (or cached) for fast `dictGet('dict_name', 'attr', key)` lookups in queries. Sources: ClickHouse table, MySQL/PG, HTTP, file, executable. Use for slow-changing dimensions (geo lookups, user attributes). Refresh policies: `LIFETIME`.

### 26. Materialized views.
A trigger on inserts: when rows land in the source table, the MV runs its SELECT and writes results into a target table (often AggregatingMergeTree). Use for pre-aggregating real-time data, downsampling, format conversion. Note: MV runs on each insert block — not over the whole table.

### 27. Live view / Refreshable MV.
**Live view** (experimental) re-computes on every insert. **Refreshable Materialized View** (2024+) re-runs full SELECT on a schedule, replacing the target table — better choice for periodic snapshots / heavy joins.

### 28. Projections.
Per-table alternative materialized layouts ("indexes on steroids"). A projection rewrites your data with a different sort key / aggregation so queries that match its definition use it transparently. Maintained automatically on insert. Great for accelerating known query patterns without separate MVs.

---

## 3. Query Language Features

### 29. SQL dialect — what's special.
Standard SQL plus: array functions, higher-order functions (`arrayMap`, `arrayFilter`), URL/IP/geo functions, statistical/ML functions, sampling (`SAMPLE 0.1`), `GROUP BY WITH ROLLUP/CUBE/TOTALS`, `LIMIT BY`, `ANY`/`ASOF` joins, table functions (`numbers()`, `s3()`, `url()`), and CTEs.

### 30. Arrays and `arrayJoin`.
`Array(T)` first-class. `arrayJoin(arr)` is like SQL `UNNEST` — explodes one row into N. Higher-order: `arrayMap(x -> x*2, arr)`, `arrayFilter`, `arraySum`, `arrayDistinct`. Used heavily for event analytics (each event has tag arrays, user properties).

### 31. `GROUP BY` extensions.
`WITH ROLLUP` adds subtotals per prefix, `WITH CUBE` adds all subsets, `WITH TOTALS` appends a grand-total row. `LIMIT N BY column` returns top N rows per group (e.g., top 3 events per user) — a common analytics pattern.

### 32. Sampling.
`SELECT ... FROM t SAMPLE 0.1` reads ~10% via the sampling key (declared in `ORDER BY` or `SAMPLE BY`). Used for fast approximate queries on huge tables. Sampling key must be reasonably uniform (e.g., `cityHash64(user_id)`).

### 33. Approximate aggregations.
`uniq`, `uniqExact`, `uniqHLL12`, `uniqCombined` for cardinality (HyperLogLog variants). `quantile`, `quantileTDigest`, `quantileExactWeighted` for percentiles. `topK(N)(col)` for most frequent values. Hugely faster than exact for big data.

### 34. JOINs in ClickHouse.
Supports `INNER`, `LEFT/RIGHT/FULL OUTER`, `CROSS`, `ANY` (any matching row), `ASOF` (nearest match by time), `SEMI/ANTI`. **Important**: right side is loaded into memory (hash join) — keep small. For huge-huge joins, denormalize or use dictionaries. Distributed joins follow specific patterns (see Q56).

### 35. ASOF join.
Joins on inequality of time: `t1 ASOF LEFT JOIN t2 ON t1.id = t2.id AND t1.ts >= t2.ts`. For each row in t1, finds the latest t2 row with `ts <= t1.ts`. Perfect for time-series enrichment (latest price at the time of each event).

### 36. Window functions.
Supported since 21.x: `row_number() OVER (PARTITION BY ... ORDER BY ...)`, `lag`, `lead`, `sum() OVER (...)`. Reasonable performance but typically slower than equivalent ClickHouse-native approaches (`LIMIT BY`, `arrayMap` over array states) — use whichever is clearer.

### 37. CTEs.
`WITH cte AS (SELECT ...) SELECT ...`. Inline by default (re-evaluated each use). Use parameter-style CTEs for constants: `WITH 0.95 AS conf SELECT ... WHERE val > conf`. Recursive CTEs not supported as of mid-2024 (check current version).

### 38. Subqueries vs JOINs vs dictionaries.
Three ways to enrich: subquery `IN (SELECT id FROM small)`, JOIN (right side in memory), or dictionary (`dictGet`). For small dimension lookups, **dictionaries** are usually fastest and clearest. For ad-hoc analytics with small sets, IN/JOIN is fine.

### 39. `argMax` / `argMin`.
Returns the value of one column corresponding to the max/min of another: `argMax(user_name, login_time) GROUP BY user_id` — get the name at the last login per user. Replaces row-number-then-filter patterns common in row stores.

### 40. `groupArray`, `groupBitmap`, `groupUniqArray`.
Aggregate functions that build arrays/bitmaps per group. Useful for cohort analysis, sequence analytics: `groupArray(event_type ORDER BY event_time)` reconstructs a user's session.

### 41. Funnel and sequence analytics.
`windowFunnel(window)(timestamp, cond1, cond2, ...)` returns max number of conditions hit in order within `window`. `sequenceMatch('(?1).*(?2)')(timestamp, cond1, cond2)` does regex over event sequences. Designed for product/user analytics.

### 42. Time functions.
`toYYYYMMDD`, `toStartOfHour/Day/Week/Month`, `dateDiff`, `addDays/Months`, `formatDateTime`, `parseDateTimeBestEffort`. Huge collection. Combine with `toTimezone` to handle multi-region data.

### 43. `FORMAT` clause.
`SELECT * FROM t FORMAT JSONEachRow|CSV|TSV|Parquet|Arrow|Native|Pretty|Vertical`. Lets you stream query output in many formats — great for ingestion, exports, and one-off analytics piping into other tools.

### 44. Table functions.
`numbers(100)`, `numbers_mt(1e9)` for generating data. `s3('s3://...', 'fmt')`, `url(...)`, `file(...)`, `cluster('...')`, `remote(...)` for reading without creating tables. Powerful for ad-hoc queries across systems.

---

## 4. Inserts, Updates, Deletes

### 45. How inserts work.
Insert creates a new immutable part (sorted, compressed, indexed). High-frequency tiny inserts → many tiny parts → merge pressure → `too many parts` errors. Best practice: **batch** inserts (≥ a few thousand rows or several MB) at the client, or buffer via **Async Inserts** or **Buffer Table** or a Kafka engine.

### 46. Async inserts.
Server-side buffer (`async_insert = 1`). Multiple small INSERTs from many clients are merged into one larger insert before flushing. Great for OLTP-like sources writing events one by one. Configure `async_insert_max_data_size` and `async_insert_busy_timeout_ms`.

### 47. Buffer table.
`ENGINE = Buffer(db, target, num_layers, min_time, max_time, min_rows, max_rows, ...)` — in-memory layer in front of a MergeTree that flushes when thresholds hit. Older mechanism; async inserts mostly replace it but Buffer is still useful when you must absolutely keep latency low and can tolerate data loss on crash.

### 48. Updates and deletes.
ClickHouse historically had **mutations**: `ALTER TABLE t UPDATE col=... WHERE ...` rewrites affected parts in the background — heavy. Modern alternatives: **lightweight DELETE** (`DELETE FROM t WHERE ...` marks rows deleted), **lightweight UPDATE** (newer, similar marking approach), **ReplacingMergeTree** with upserts, or `ALTER ... DROP PARTITION` for big bulk deletes.

### 49. Mutations.
Asynchronous. Watch `system.mutations` for progress. Expensive: rewrites whole parts touched by the WHERE clause. Try to design schema so you don't need them (immutable event tables + materialized views). When you must, batch them.

### 50. Idempotent inserts.
ClickHouse de-duplicates **identical** insert blocks via `insert_deduplication_token` or by content hash within a window (configured by `replicated_deduplication_window`). Send the same batch twice → second is no-op. Critical for safe retries from Kafka consumers.

### 51. TTL.
Per-table or per-column TTL: `TTL event_time + INTERVAL 90 DAY`, `TTL ... TO VOLUME 'cold'`, `TTL ... DELETE WHERE condition`, `TTL ... GROUP BY ... SET col = sum(col)` for rollup-on-aging. Drives data tiering and retention automatically.

---

## 5. Performance & Optimization

### 52. Choosing primary / sort key.
Sort by **filters first, then group-by columns, then high-cardinality columns last**. Common pattern: `(tenant_id, event_time, user_id)`. The leftmost columns prune most. Wrong key → full scans even with the "right" filter.

### 53. Skipping indexes.
Secondary indexes for skipping granules: `minmax`, `set(N)`, `bloom_filter`, `tokenbf_v1`, `ngrambf_v1`. Declared as `INDEX name (expr) TYPE bloom_filter GRANULARITY 4`. Help when sort key alone can't prune (e.g., filter on a non-sort column).

### 54. Reading the EXPLAIN plan.
`EXPLAIN PLAN`, `EXPLAIN PIPELINE`, `EXPLAIN AST`, `EXPLAIN SYNTAX`, `EXPLAIN INDEXES = 1`. The Indexes section shows how many granules were pruned by primary key / skipping indexes. `EXPLAIN ESTIMATE` shows estimated rows/marks. Use to verify your index actually helps.

### 55. Materialized views for performance.
Pre-aggregate frequent rollups (daily user count, hourly revenue) into AggregatingMergeTree via MV. Queries hit the small MV instead of scanning raw events. Watch out: MV operates on inserted blocks, so JOINs to dimensions must be carefully designed (use dictionaries).

### 56. Distributed JOIN patterns.
- **GLOBAL JOIN**: right side computed once on initiator, broadcast to all shards. Best when right is small/medium.
- Local JOIN: each shard joins with its local right (works only if data is co-sharded by join key).
- **Distributed product mode** (`distributed_product_mode = 'allow'|'deny'|'local'|'global'`) controls subquery behavior.

### 57. Query profiling.
`SET send_logs_level='trace'`, query log in `system.query_log`, `system.query_thread_log` for per-thread breakdown. `clickhouse-benchmark` for load testing. `EXPLAIN PIPELINE` for operator-level concurrency. The `Settings` block in query_log shows what config a slow query ran with.

### 58. Common slow-query causes.
Wrong sort key, scanning all parts (no partition pruning), large right side in JOIN, `Nullable` everywhere, missing `LowCardinality`, too many small parts, `FINAL` in selects (forces merge on read), missing skipping indexes, network bottleneck during distributed query merge, too high parallelism on small data.

### 59. Settings to know.
`max_memory_usage`, `max_threads`, `max_execution_time`, `max_rows_to_read`, `max_bytes_to_read` (query guard rails); `optimize_read_in_order`, `optimize_aggregation_in_order` (use sort order to skip work); `prefer_localhost_replica`, `load_balancing` (distributed routing); `max_insert_block_size`. Tune per-user/per-query profile.

### 60. Sampling for performance.
Declared at table level. Speeds up exploratory queries on huge tables. Trade accuracy for speed: `SELECT count() * 10 FROM t SAMPLE 0.1` estimates total. Note: not all aggregations sample-friendly — `uniq` works well, `quantile` mostly works, `max/min` won't be accurate.

### 61. Vectorized execution & SIMD.
ClickHouse processes data in **blocks** of typically tens of thousands of rows. Operators are implemented as tight loops over column arrays, often with SIMD intrinsics. This is why simple aggregations on billions of rows run in seconds on a single node — you're effectively doing hardware-accelerated math.

### 62. Memory management.
Each query has a memory tracker; OOM throws clearly. Knobs: `max_memory_usage` (per query), `max_memory_usage_for_user`, `max_server_memory_usage`. Big joins/group-bys may spill to disk if `max_bytes_before_external_group_by`/`...sort` are set.

### 63. Caching.
**Query cache** (since 23.x): caches query results in memory by hash. **Uncompressed cache**: cached uncompressed columns. **Mark cache**: cached index marks (primary keys). **Filesystem cache**: cached object-storage reads (S3/GCS). Inspect via `system.metrics` and `system.events`.

---

## 6. Replication & Sharding

### 64. ReplicatedMergeTree internals.
Coordinated via ZooKeeper / ClickHouse Keeper. Each insert writes a log entry; replicas tail the log and pull parts from peers over HTTP. `insert_quorum` requires N replicas to ack before INSERT returns. Conflict resolution: parts are immutable; merges decided by leader.

### 65. ClickHouse Keeper vs ZooKeeper.
Keeper is a drop-in replacement written in C++, embedded in ClickHouse or run standalone. Lighter, faster, easier to operate. Use Keeper for new clusters; existing ZK can be migrated.

### 66. Designing a shard layout.
Decide: number of shards (parallelism upper bound), replicas per shard (HA + read scaling), sharding key (must distribute evenly and ideally co-locate joined data). Configure in `config.xml` `<remote_servers>` or `clusters` element. Treat the topology as long-lived — resharding is expensive.

### 67. Sharding key choice.
Want: high cardinality, uniform distribution, joined keys co-located when possible. Common: `rand()` (uniform but no locality), `cityHash64(user_id)` (uniform + co-location for per-user queries), explicit ranges (rare). Sharding by time is **bad** — creates hot shards.

### 68. Distributed inserts.
Two modes: (a) insert directly into the per-shard local replicated table via your own routing (best for big batches); (b) insert into the `Distributed` table, which buffers and forwards to shards by sharding key (`internal_replication` controls whether replica or distributed handles HA). The first scales better at high volume.

### 69. Rebalancing & resharding.
ClickHouse has no built-in online resharding. To grow: add shards, dual-write (or replay) to the new topology, swap reads. Use partitions + `MOVE PARTITION` between clusters for offline rebalancing. Plan capacity ahead so resharding is rare.

### 70. Multi-master vs leader.
ReplicatedMergeTree is leaderless for writes — any replica accepts inserts and they replicate to peers. Merges are coordinated; one replica is elected to perform a given merge to avoid duplicate work. Reads can hit any replica.

### 71. Cross-region replication.
Two patterns: (a) one logical cluster with replicas across regions — high replication latency but a single SQL endpoint; (b) two clusters with async logical replication (custom or via Kafka). Most production setups treat each region as an independent cluster + global ingestion fan-out.

---

## 7. Storage, Tiering, Object Storage

### 72. Storage policies.
Define volumes (e.g., `hot=NVMe`, `cold=S3`) and policies that move parts between volumes based on age or size. Combine with TTL `TO VOLUME 'cold'`. Lets you keep recent data on fast disks and old data on cheap object storage transparently.

### 73. S3 / GCS / Azure backed tables.
`storage_policy = 's3'` puts MergeTree parts on object storage. Reads cached locally via filesystem cache. Decouples storage from compute and is the basis of "shared storage" architectures.

### 74. Shared storage / `SharedMergeTree`.
ClickHouse Cloud's `SharedMergeTree` (and OSS analogues being explored) keeps part metadata in a coordination service and data in object storage — replicas are stateless, scale on demand, no part replication between nodes. Operationally simpler at the cost of object-storage latency.

### 75. Compression and codec stacking.
`CODEC(Delta(8), ZSTD(3))` first deltas then compresses — perfect for sorted ints. `CODEC(DoubleDelta, LZ4)` for time series. Choose codecs per column based on distribution; can yield 5–10× extra compression vs default LZ4 alone.

### 76. Disk and memory sizing rules of thumb.
- Aim for ~64–256 GB RAM per node depending on workload.
- NVMe SSDs (or object storage + cache) for hot data.
- Plan 1 vCPU per ~50–200 MB/s of scan throughput needed.
- Keep table parts < ~100,000 per node (split across tables/partitions).
- Active query memory should fit in RAM; spill is supported but slow.

---

## 8. Ingestion Patterns

### 77. Kafka engine.
`ENGINE = Kafka` reads from a topic; pair with an MV that writes to a MergeTree. Consumer group is `kafka_group_name`. Offsets are committed after writing to the MV's target. Tune `kafka_max_block_size`, `kafka_num_consumers`, `kafka_thread_per_consumer`. Handle bad rows via `kafka_handle_error_mode='stream'` to capture parse errors.

### 78. CDC into ClickHouse.
**Debezium → Kafka → Kafka engine → MV → ReplacingMergeTree** keyed by primary key with a version (LSN/timestamp). Use `FINAL` or `argMax(... , version)` in queries to see the latest state. For deletes, use a tombstone column.

### 79. Bulk loading.
For huge bulk loads, write Parquet/CSV to S3, then `INSERT INTO t SELECT * FROM s3(...)`. ClickHouse parallelizes the read. Adjust `max_insert_block_size`, disable `optimize_on_insert` during bulk load and run `OPTIMIZE` afterwards.

### 80. Backfill strategy.
Land into a staging table (raw format), validate, then `INSERT INTO target SELECT ... FROM staging` in batches. For idempotency, use `insert_deduplication_token` keyed by your batch ID. Avoid running mutations during backfill — they fight for IO.

### 81. Real-time ingestion patterns.
- App → HTTP/JSON → ClickHouse (with `async_insert`).
- App → Kafka → Kafka engine → MV → MergeTree (most common at scale).
- Vector / Fluent Bit → ClickHouse over HTTP / native protocol (logs/metrics).
- Spark / Flink batch → S3 → S3 table function → MergeTree.

### 82. Error handling on ingestion.
Configure `input_format_skip_unknown_fields`, `input_format_null_as_default`, error mode for Kafka. Route bad rows to a `system.errors` table or a parallel dead-letter table. Always alert on growing error rates rather than silently dropping data.

---

## 9. Operations, Observability, Reliability

### 83. Monitoring metrics.
`system.metrics` (current state), `system.events` (cumulative counters), `system.asynchronous_metrics` (sampled), `system.query_log`, `system.part_log`, `system.merge_log`, `system.replicas`, `system.replication_queue`. Scrape via the built-in Prometheus endpoint (`/metrics`) or Datadog agent.

### 84. Key health metrics to alert on.
Replication lag (`absolute_delay` per replica), `ReadonlyReplica`, growing `replication_queue`, parts count per table, queries failed rate, memory rejections, ZK/Keeper session loss, disk space < 20%, merges stuck, mutation backlog.

### 85. Backups.
**`BACKUP TABLE ... TO Disk('backups', 'name.zip')` / `RESTORE`** since 22.x — built-in physical-ish backups. Targets: local disk, S3, Azure. Test restore regularly. Alternative: snapshot underlying volumes, but harder to make consistent.

### 86. Upgrades.
Rolling upgrade replica-by-replica. Always read the changelog — major versions can introduce breaking SQL/config changes. Pin client driver versions in apps. Have a rollback plan and tested backups before any upgrade.

### 87. Schema migrations.
`ALTER TABLE ... ADD/DROP/MODIFY COLUMN` — most are O(1) metadata changes; some (`MODIFY COLUMN` changing type, ordering changes) trigger mutations that rewrite parts. For replicated tables, ALTERs flow through ZK/Keeper and apply on all replicas. Use migration tooling (`golang-migrate`, custom, `dbt` macros) for versioning.

### 88. Multi-tenancy.
Approaches: one cluster per big tenant (best isolation), schema/database per tenant (medium), or shared tables with `tenant_id` as the leading sort key (cheapest but noisy-neighbor risk). Use **row-level security via grants and views** or `WHERE tenant_id = currentUser()`-style middleware filters.

### 89. Security.
Auth: native passwords, LDAP, Kerberos, OAuth (via proxy), or HTTPS + client certs. Authorization: SQL-standard GRANT/REVOKE, role-based, with row-level (`<filter>`) and column-level grants. Encrypt at rest via disk encryption; TLS for client and inter-node traffic.

### 90. Quotas & resource management.
**Quotas**: limit rows/queries/duration/exceptions per user per interval. **Settings profiles**: cap `max_memory_usage`, `max_threads`, `max_execution_time` per user/query. **Workload management** (newer): named workloads with priorities, akin to Snowflake warehouse routing.

### 91. Common production issues.
"Too many parts" (raise insert batch size / use async inserts), "Memory limit exceeded" (cap concurrency / increase memory / fix query), replication queue stuck (broken part — `SYSTEM RESTART REPLICA`), ZK session expired (Keeper instability), `Code: 252` (insert quorum failed), disk full (drop old partitions, add cold storage).

### 92. Debugging a stuck query.
`SELECT * FROM system.processes` — find query, get `query_id`. `KILL QUERY WHERE query_id='...'` to cancel. `system.query_log` after the fact for full picture. `EXPLAIN` to understand plan. `clickhouse-client --send_logs_level=trace` for verbose runs.

---

## 10. Patterns, Anti-Patterns, Real-World

### 93. When ClickHouse is the right tool.
Event analytics, observability/logs/metrics at scale, ad-tech reporting, real-time dashboards, product analytics (Mixpanel/Amplitude-style), time-series (with caveats), feature store offline scoring. Anywhere you have huge append-only data and want sub-second analytical queries on it.

### 94. When it's the wrong tool.
Heavy row-level OLTP, frequent in-place updates/deletes, strict ACID multi-row transactions, < 1 ms key/value lookups (use Redis), full-text search at scale (use Elastic/OpenSearch — though CH has some FTS), tiny datasets (Postgres is fine).

### 95. Common anti-patterns.
Per-row INSERTs without batching; using `Nullable` everywhere; partitioning by day for 5-year tables; making sort key end with timestamp (gives bad pruning for partial timestamp filters); using mutations for upserts when ReplacingMergeTree fits; joining huge fact-fact tables; running `FINAL` on every query.

### 96. Modeling event tables.
Wide, denormalized, columnar: pull in dimension attributes at write time (or via dictionaries at query time). Heavy `LowCardinality` use, sensible sort key (`(tenant_id, event_date, user_id)`), partition by month, TTL for raw retention, materialized views for rollups.

### 97. Observability use case.
ClickHouse is heavily used for logs/metrics/traces: OpenTelemetry exporter writes to a wide events table with `LowCardinality` service/operation columns + JSON attributes. Bloom-filter indexes on attribute keys. Skipping indexes on trace_id. Cheaper and faster than Elasticsearch for high-volume observability.

### 98. Feature store / ML offline use case.
Store event-level data in ClickHouse; compute features via SQL with `argMax`, time windows, and AggregatingMergeTree MVs. Export training datasets via `INTO OUTFILE` or `s3()` table function. Online store is separate (Redis, DynamoDB) — ClickHouse is the offline + analytics layer.

### 99. Time series patterns.
Sort by `(metric, timestamp)`. Use Delta+DoubleDelta+Gorilla codecs for ts/value. AggregatingMergeTree for downsampling (per-minute, per-hour rollups via MVs). Be careful with retention — partition monthly, TTL by age, move cold to object storage.

### 100. Migrating from another OLAP system.
From Redshift / BigQuery / Snowflake: replicate schemas with ClickHouse-native types (LowCardinality, codecs), decide on sharding/replication topology, write a parallel-write or shadow-read phase for validation, dual-query to compare correctness, then cut over reads. Beware of SQL-dialect differences (functions, window semantics, JOIN strictness).
