# Advanced PostgreSQL Interview Questions (Detailed)

A focused question bank on advanced PostgreSQL topics for data, backend, and platform engineers: architecture, MVCC, indexing, query planner, performance tuning, replication, partitioning, JSONB, full-text, extensions, security, and operations.

> Note: Examples assume Postgres 14+ unless mentioned. Many features (`MERGE`, `GENERATED ALWAYS AS IDENTITY`, `pg_stat_io`, logical replication enhancements) ship in newer versions — verify against your target version.

---

## 1. Architecture & Process Model

### 1. What is PostgreSQL's process model?
Postgres uses a **process-per-connection** model: the `postmaster` forks a backend per client. Helper processes: `walwriter`, `bgwriter` (background writer), `checkpointer`, `autovacuum launcher` + workers, `archiver`, `walreceiver`/`walsender` (replication), `logical replication launcher`. This makes per-connection memory the dominant overhead — heavy concurrency demands a connection pooler (PgBouncer).

### 2. Shared memory layout.
Configured by `shared_buffers`, `wal_buffers`, lock tables, the proc array, and shared catalog cache. `shared_buffers` is Postgres's own page cache (typically 25% of RAM); the OS page cache holds the rest. A page is 8 KB.

### 3. WAL — Write-Ahead Log.
Every change is written to WAL before the heap/index pages are flushed. Recovery replays WAL from the last checkpoint. WAL records are the foundation of crash recovery, PITR, physical replication, and logical decoding. Files in `pg_wal/`, default 16 MB each.

### 4. Checkpoints.
Periodic event that flushes all dirty buffers to disk and marks a "safe" recovery starting point. Triggered by `checkpoint_timeout` (default 5 min) or `max_wal_size` (1 GB default). Tune `checkpoint_completion_target` (default 0.9) to spread I/O. Too-frequent checkpoints = write storm; too-rare = long recovery.

### 5. Background writer vs checkpointer.
**bgwriter** continuously trickles dirty buffers out to smooth I/O. **checkpointer** does the full flush at a checkpoint. Together they reduce the burst that checkpointing alone would cause.

### 6. Connection pooler — why mandatory.
Each connection costs ~10 MB and a backend process. 1000 idle connections = 10 GB + scheduler overhead. **PgBouncer** in `transaction` mode multiplexes thousands of client conns onto a small pool of server conns. Pgcat / Odyssey are alternatives. Use a pooler in any non-trivial app.

### 7. work_mem vs maintenance_work_mem vs shared_buffers.
- `shared_buffers`: page cache, all backends share.
- `work_mem`: per-operation memory (sort, hash, etc.) — multiplied by concurrent ops × nodes in the plan.
- `maintenance_work_mem`: used by `VACUUM`, `CREATE INDEX`, `ALTER TABLE` — set generously, only one runs at a time per session.
Set `work_mem` modestly (e.g., 16–64 MB) and override per session for heavy analytics.

---

## 2. MVCC, Vacuum, Bloat

### 8. How does MVCC work in Postgres?
Each tuple has hidden columns: `xmin` (creator xid), `xmax` (deleter xid). Updates write a new tuple version and mark the old one with `xmax`. Readers see only tuples visible to their snapshot. No read locks for read-write conflicts; high concurrency is the headline benefit.

### 9. Why does Postgres need VACUUM?
Updates and deletes leave **dead tuples**. VACUUM reclaims space (within the page) and updates the **visibility map** so index-only scans work. Without it, tables bloat and queries slow.

### 10. VACUUM vs VACUUM FULL.
- `VACUUM`: non-blocking, reuses freed space inside existing pages; no exclusive lock.
- `VACUUM FULL`: rewrites the whole table, takes `ACCESS EXCLUSIVE` lock, reclaims space back to OS — rarely used in prod; prefer `pg_repack` for online table rewrite.

### 11. Autovacuum.
Background process that auto-vacuums + auto-analyzes tables based on dead-tuple thresholds. Key settings: `autovacuum_vacuum_scale_factor` (default 0.2 → vacuum when 20% dead), `autovacuum_naptime`, `autovacuum_max_workers`. Tune per table on hot tables (`ALTER TABLE ... SET (autovacuum_vacuum_scale_factor = 0.02)`).

### 12. Transaction ID wraparound.
Postgres uses 32-bit xids; if not vacuumed, the cluster halts to prevent data loss when xids approach wraparound (~2 billion). Autovacuum's "freeze" phase rewrites old tuples with `FrozenXID`. Monitor `age(datfrozenxid)`; modern versions added xid-aware autovacuum, but the rule remains: **never disable autovacuum**.

### 13. Bloat — diagnosing and fixing.
Use `pgstattuple` extension or `pg_stat_user_tables` + `pg_class` size queries; tools: `pgstatbloat`, `check_postgres.pl`. Fix: aggressive autovacuum, `pg_repack` (online rebuild), or partitioning by time so old partitions can be dropped instead of vacuumed.

### 14. HOT updates.
**Heap-Only Tuple** updates: if the new tuple fits on the same page and no indexed column changed, Postgres updates in place without touching indexes. Massive write win on hot tables — leave 10–20% `fillfactor` to enable it (`ALTER TABLE ... SET (fillfactor = 80)`).

### 15. Visibility map and index-only scans.
The visibility map tracks pages where all tuples are visible to all transactions. An index-only scan returns a tuple from the index if the page is "all-visible" — no heap fetch needed. VACUUM updates the map; without recent VACUUM, index-only scans degrade.

---

## 3. Indexes

### 16. Index types in Postgres.
- **B-tree** (default): equality, range, sort, `LIKE 'prefix%'`.
- **Hash**: equality only; rarely needed (B-tree handles equality well).
- **GiST**: geometric, ranges, custom indexable predicates.
- **SP-GiST**: space-partitioned trees (quadtree, k-d tree).
- **GIN**: inverted indexes — arrays, full-text, JSONB containment, trigrams.
- **BRIN**: block range indexes — tiny, summarize ranges over physically clustered data (time-series).
- **Bloom**: cheap multi-column filter for low-selectivity equality (extension).

### 17. When is a B-tree index NOT used?
Functions wrap the column (`WHERE LOWER(email) = ...` → make a functional index). Implicit type cast. `LIKE '%foo%'` (leading wildcard — use `pg_trgm` GIN). `OR` patterns the planner can't decompose. Low selectivity where seq scan is cheaper. Stale stats giving wrong cardinality. `EXPLAIN` reveals which.

### 18. Functional / expression index.
```sql
CREATE INDEX idx_users_lower_email ON users (LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'a@b.com'; -- uses it
```
Index any expression; the planner matches predicates expression-wise.

### 19. Partial index.
Indexes only rows matching a predicate; smaller and faster.
```sql
CREATE INDEX idx_orders_open ON orders (created_at) WHERE status = 'open';
```
Great for status flags where one value dominates.

### 20. Covering / INCLUDE index.
```sql
CREATE INDEX idx_orders_user_inc ON orders (user_id) INCLUDE (total, created_at);
```
`total` and `created_at` are stored in the leaf pages but not part of the key — enables index-only scans without bloating the B-tree.

### 21. Multicolumn index ordering.
Order matters: index `(a, b)` supports `WHERE a = ?`, `WHERE a = ? AND b = ?`, `WHERE a = ? ORDER BY b`. It does NOT efficiently handle `WHERE b = ?` alone. Put the most selective / most filtered column first.

### 22. GIN vs GiST for full-text.
**GIN**: faster queries, slower inserts, larger size — default for full-text.
**GiST**: faster updates, slower queries — for fast-changing data.
Trigram (`pg_trgm`) → GIN for fuzzy `LIKE '%term%'`.

### 23. BRIN — when it shines.
Tiny indexes that summarize min/max per block range (default 128 pages). Perfect for time-series tables where rows are physically ordered by time:
```sql
CREATE INDEX idx_logs_ts_brin ON logs USING brin (ts);
```
Index size ~thousand-fold smaller than a B-tree; range scans fast.

### 24. CREATE INDEX CONCURRENTLY.
Builds the index without taking a long write lock. Slower, two table scans, but no downtime. Always use in production. Caveats: cannot be inside a transaction; on failure leaves an invalid index — drop and retry.

### 25. REINDEX CONCURRENTLY.
Postgres 12+. Rebuilds index online to reclaim bloat. Pair with monitoring of bloat to do it proactively. `pg_repack` is an alternative.

### 26. Index bloat — what causes it.
Updates + non-HOT writes accumulate dead entries in B-trees until pages split / merge. Symptoms: index larger than the table. Fix: `REINDEX CONCURRENTLY` or `pg_repack`. Postgres 13+ has much improved B-tree deduplication, reducing bloat for low-cardinality keys.

### 27. INCLUDE vs additional key columns.
INCLUDE columns are stored only in leaves — no sort order, no impact on uniqueness. Putting them in the key forces sorting, increases comparison cost. Use INCLUDE for payload, key for predicates / ordering.

---

## 4. Query Planner

### 28. `EXPLAIN` vs `EXPLAIN ANALYZE`.
`EXPLAIN` shows estimated plan. `EXPLAIN ANALYZE` actually runs the query and shows real times + row counts. Add `BUFFERS` to see I/O: `EXPLAIN (ANALYZE, BUFFERS) SELECT ...`. Compare estimated vs actual rows — large divergence = bad stats.

### 29. Plan nodes.
- **Seq Scan**: full table scan.
- **Index Scan**: walk index, fetch heap.
- **Index Only Scan**: index has all needed columns AND visibility map says page is all-visible.
- **Bitmap Index Scan + Bitmap Heap Scan**: build bitmap of matching pages, then read heap in disk order.
- **Nested Loop / Hash Join / Merge Join**: join algorithms.
- **Sort**, **HashAggregate**, **GroupAggregate**, **WindowAgg**, **Materialize**, **Gather** (parallel).

### 30. Join algorithms.
- **Nested loop**: good when outer side is tiny.
- **Hash join**: hash the smaller side in memory, probe with the bigger; default for equi-joins on medium/big data.
- **Merge join**: both sides sorted on join key; great when sort comes "for free" from indexes.
The planner chooses based on cost; bad stats → wrong choice. Disable temporarily with `SET enable_nestloop=off` to test.

### 31. Statistics: `ANALYZE` and `pg_stats`.
`ANALYZE` samples the table and updates `pg_statistic`: row counts, distinct values, MCVs (most-common values), histograms, correlation. Stale stats = wrong cost estimates = wrong plan. After bulk loads, run `ANALYZE`.

### 32. Extended statistics.
Postgres 10+: `CREATE STATISTICS` to capture **multi-column dependencies / correlations** that single-column stats miss.
```sql
CREATE STATISTICS s_zip_city (dependencies, ndistinct) ON zip, city FROM addresses;
ANALYZE addresses;
```
Cures bad estimates on correlated columns (zip determines city).

### 33. Parallel query.
Postgres parallelizes seq scans, index scans, hash joins, aggregations. Tunables: `max_parallel_workers_per_gather` (default 2), `parallel_setup_cost`, `parallel_tuple_cost`. Disable per query with `SET max_parallel_workers_per_gather=0;`. Not a magic 10× — overhead matters for small queries.

### 34. Why is my query not using parallel workers?
Reasons: table too small (`min_parallel_table_scan_size`), function marked `VOLATILE` or `PARALLEL UNSAFE`, settings disabled, plan picked non-parallel for cost reasons. Check with `EXPLAIN` — look for `Gather` node.

### 35. Genetic Query Optimizer (GEQO).
For queries with more than `geqo_threshold` (default 12) tables, Postgres switches from exhaustive search to a genetic algorithm — non-deterministic plans. Reduce by raising `from_collapse_limit` / `join_collapse_limit`, or restructuring big OR-heavy joins.

### 36. CTEs — are they optimization fences?
Pre-12: yes, materialized always. Postgres 12+: `WITH ... AS MATERIALIZED` to force, `NOT MATERIALIZED` to inline. By default, simple non-recursive CTEs may inline. If your CTE got slower after upgrade, force `MATERIALIZED`.

### 37. Lateral joins.
`LEFT JOIN LATERAL` lets the right-side subquery reference the left side — used for top-N per group, dependent subqueries.
```sql
SELECT u.id, recent.*
FROM users u
LEFT JOIN LATERAL (
    SELECT * FROM events e WHERE e.user_id = u.id ORDER BY ts DESC LIMIT 3
) recent ON true;
```

### 38. Window functions internals.
Window functions execute *after* WHERE/GROUP/HAVING. `PARTITION BY` creates groups; `ORDER BY` orders within. **Frame clause** (`ROWS BETWEEN ... AND ...`) controls visible rows. Beware: `rank()` vs `dense_rank()` vs `row_number()` differ on ties; `lag/lead` vs `first_value/last_value` differ on frames.

### 39. ROLLUP, CUBE, GROUPING SETS.
Multi-level aggregations in one query:
```sql
SELECT region, product, SUM(amount)
FROM sales
GROUP BY ROLLUP(region, product);
```
Produces subtotals + grand total. `GROUPING(col)` distinguishes real NULLs from grouping NULLs.

### 40. Sub-plans, init-plans.
`EXPLAIN` shows `SubPlan` (executed per row) vs `InitPlan` (executed once, value reused). Bad correlated subqueries become `SubPlan` and run N times. Rewriting as `JOIN` or `LATERAL` often beats correlated subqueries.

---

## 5. JSON / JSONB

### 41. JSON vs JSONB.
**JSON**: stored as text, preserves whitespace and key order, slower to query.
**JSONB**: binary, deduped keys, indexable, faster query, slightly slower insert. **Use JSONB**. JSON only when you must preserve exact textual form.

### 42. JSONB operators.
- `->` / `->>`: get field as JSONB / as text.
- `#>` / `#>>`: get at path.
- `@>` / `<@`: containment.
- `?`, `?|`, `?&`: key existence.
- `||`: concatenate / merge.
- `-`, `#-`: remove key / path.
- `jsonb_set`, `jsonb_insert`: targeted updates.

### 43. Indexing JSONB.
Default GIN index over the whole JSONB covers `@>` containment:
```sql
CREATE INDEX idx_doc_gin ON documents USING gin (doc);
```
For specific paths use `jsonb_path_ops` (smaller, faster, containment-only):
```sql
CREATE INDEX idx_doc_gin_ops ON documents USING gin (doc jsonb_path_ops);
```
Or expression index for a hot path: `CREATE INDEX ON documents ((doc->>'tenant_id'))`.

### 44. JSONPath (`@? @@`, `jsonb_path_query`).
Postgres 12+ supports SQL/JSON path:
```sql
SELECT jsonb_path_query(doc, '$.items[*] ? (@.price > 100)') FROM documents;
WHERE doc @@ '$.tenant == "acme"';
```
Path expressions can use filters, methods (`.size()`, `.keyvalue()`).

### 45. JSONB anti-patterns.
- Storing relational data as JSONB just to "avoid schema". Costs: no FKs, weak typing, slower joins, bigger storage.
- Updating a single field in huge JSONB — Postgres rewrites the whole value.
- Querying nested arrays without indexes — full scans.
Use JSONB for **truly schema-less or sparse** data, not as a normal-table substitute.

---

## 6. Full-Text Search

### 46. Building blocks.
`to_tsvector(config, text)` produces a normalized lexeme vector. `to_tsquery` / `plainto_tsquery` / `websearch_to_tsquery` parse the query. Match with `@@`:
```sql
SELECT * FROM docs WHERE to_tsvector('english', body) @@ websearch_to_tsquery('english', '"data engineer" -intern');
```

### 47. Indexing FTS.
Persist the tsvector as a generated column for fast lookup:
```sql
ALTER TABLE docs ADD COLUMN tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', body)) STORED;
CREATE INDEX idx_docs_tsv ON docs USING gin (tsv);
```

### 48. Ranking.
`ts_rank` / `ts_rank_cd`:
```sql
SELECT id, ts_rank(tsv, q) AS r
FROM docs, websearch_to_tsquery('english', 'machine learning') q
WHERE tsv @@ q
ORDER BY r DESC LIMIT 10;
```
Use `ts_headline` to extract highlighted snippets.

### 49. Trigram / fuzzy search.
`pg_trgm` extension provides `LIKE '%foo%'` GIN indexes and similarity:
```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_name_trgm ON users USING gin (name gin_trgm_ops);
SELECT * FROM users WHERE name % 'jhon'; -- similarity
```
Combine with FTS where typos matter.

### 50. When to use Elastic instead.
FTS is great for simple ranked search co-located with transactions, no extra infra. Use a dedicated engine (Elasticsearch/OpenSearch, Meilisearch) when you need: language-specific analyzers at scale, faceting, ML re-rankers, vector + lexical hybrid, billions of docs.

---

## 7. Concurrency, Transactions, Isolation

### 51. Isolation levels.
- **Read Committed** (default): each statement sees committed data; non-repeatable reads possible.
- **Repeatable Read**: snapshot at txn start; in Postgres equals "Snapshot Isolation" — no non-repeatable reads, allows **write skew**.
- **Serializable**: SSI (Serializable Snapshot Isolation) — detects dependencies and aborts conflicting txns to give true serializability.

### 52. Snapshot Isolation and write skew.
Two txns read overlapping data, write disjoint things, jointly violate an invariant. Example: two doctors going off-call leaves no doctor on-call. SI doesn't catch this; SSI does (will abort one of them with `40001`). For business invariants spanning rows, use `SERIALIZABLE` or `SELECT ... FOR UPDATE` to lock.

### 53. SELECT ... FOR UPDATE / FOR NO KEY UPDATE / FOR SHARE.
Row-level locks. `FOR UPDATE` blocks other writers and other `FOR UPDATE` readers. `FOR NO KEY UPDATE` is lighter (doesn't block FK references). `FOR SHARE` blocks writers only. `SKIP LOCKED` and `NOWAIT` to manage contention — basis for queue-in-Postgres patterns.

### 54. Deadlocks.
Two txns each waiting on a lock the other holds. Postgres detects (default 1 s) and aborts one with error `40P01`. Fix: consistent lock ordering across code, shorter txns, fewer indexes triggering lock escalation, use `advisory locks` for app-level coordination.

### 55. Advisory locks.
Application-defined locks identified by a `bigint` key. Acquired with `pg_advisory_lock(key)` / `pg_try_advisory_lock(key)`. Used for distributed cron leadership, deduplicating workers, etc. Session-scoped or transaction-scoped variants.

### 56. Lock modes (table-level).
`ACCESS SHARE` (SELECT), `ROW SHARE` (FOR SHARE), `ROW EXCLUSIVE` (INSERT/UPDATE/DELETE), `SHARE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, `ACCESS EXCLUSIVE` (DDL, VACUUM FULL). `pg_locks` view shows current locks. Many DDLs need `ACCESS EXCLUSIVE` — use `CONCURRENTLY` variants where available.

### 57. Long-running queries blocking DDL.
A long-running SELECT holds `ACCESS SHARE`; a `DROP/ALTER` needs `ACCESS EXCLUSIVE`. The DDL waits behind the SELECT *and blocks every subsequent SELECT*. Always set `lock_timeout` / `statement_timeout` on DDLs and kill long readers before maintenance.

### 58. Transaction guidelines.
Keep txns short. Don't `SELECT FOR UPDATE` huge sets. Avoid app-side `BEGIN` followed by remote API calls. Set `idle_in_transaction_session_timeout` to kill leaks. Use `SAVEPOINT` for partial rollback inside a long txn.

---

## 8. Partitioning

### 59. Native declarative partitioning.
Postgres 10+. Three flavors:
- **RANGE**: by value range (time, id range) — most common.
- **LIST**: explicit values (region codes).
- **HASH**: even spread (sharding-like).

```sql
CREATE TABLE events (id bigint, ts timestamptz, payload jsonb)
PARTITION BY RANGE (ts);

CREATE TABLE events_2026_01 PARTITION OF events
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

### 60. Partition pruning.
The planner skips partitions that can't match the `WHERE` clause. Check with `EXPLAIN` — you should see only relevant child plans. Don't wrap the partition key in a function (`WHERE date(ts) = ...`) — defeats pruning.

### 61. Sub-partitioning.
A partition can itself be partitioned: range by month → hash by tenant. Use sparingly; complexity grows fast.

### 62. Partition maintenance.
Create future partitions ahead of time (cron / `pg_partman`). Drop old partitions with `DROP TABLE events_2024_06;` — instant, no VACUUM needed.

### 63. pg_partman.
Extension to automate range/time partition creation and retention. Daily / monthly partitions, premake N future, retention to drop old.

### 64. Constraints on partitioned tables.
Primary keys and unique constraints must include the partition key (since partitions are independent indexes). FKs from a partitioned table work (10+); FKs *to* a partitioned table improved in 12+.

### 65. Partition-wise join / aggregate.
When both sides are partitioned identically, Postgres can join partition-by-partition in parallel. Enable: `SET enable_partitionwise_join = on; enable_partitionwise_aggregate = on;` (off by default — costs memory).

### 66. Choosing the partition key.
Pick the column most queries filter on (almost always a timestamp for event tables). Avoid keys with frequent updates — moving a row between partitions = DELETE + INSERT and is expensive.

---

## 9. Replication & HA

### 67. Streaming replication (physical).
Primary ships WAL to standbys; standbys replay WAL. Byte-for-byte copy. Used for read replicas, HA, DR. Configure with `wal_level=replica` (or `logical`), `max_wal_senders`, replication slots.

### 68. Synchronous vs asynchronous replication.
**Async** (default): primary commits without waiting for standby. **Sync** (`synchronous_standby_names = '...'`): primary waits for ACK from at least one standby — zero data loss at the cost of write latency. `synchronous_commit = remote_apply` is the strictest mode.

### 69. Replication slots.
Persistent identifiers ensuring the primary keeps WAL until a standby has consumed it. Physical slots prevent gaps on lagging standbys; logical slots feed logical decoding (CDC). Watch out: an abandoned slot will fill the disk because WAL won't be recycled.

### 70. Hot standby.
A standby that allows read-only queries. Set `hot_standby = on`. Queries can be cancelled if WAL replay needs a conflicting lock; tune `hot_standby_feedback` and `max_standby_streaming_delay`.

### 71. Logical replication.
Replicate selected tables to another Postgres (possibly different version, different schema). Built-in since Postgres 10: `CREATE PUBLICATION`/`CREATE SUBSCRIPTION`. Foundation of CDC, zero-downtime upgrades, multi-region writes. Postgres 16+ adds bidirectional logical replication scaffolding.

### 72. Logical decoding.
Reads WAL and translates to logical changes via output plugins (`pgoutput`, `wal2json`, `decoderbufs`). Powers Debezium and other CDC tooling. Requires `wal_level = logical` and a replication slot.

### 73. Failover and tooling.
Patroni (de facto standard) + etcd/Consul for leader election + HAProxy for routing. Repmgr is an older option. Cloud DBs (RDS, Cloud SQL, Aurora) abstract this. Test failover regularly — recovery time and replication lag are the metrics that matter.

### 74. PITR — Point-in-Time Recovery.
Take base backup + archive WAL continuously (`archive_command` or `pgBackRest`/`barman`/`wal-g`). Restore: extract base, set `recovery_target_time = '2026-05-20 11:00'`, replay WAL up to that timestamp. Tested as part of DR.

### 75. Replication lag — measuring and mitigating.
On primary: `pg_stat_replication.write_lag/flush_lag/replay_lag`. On standby: `now() - pg_last_xact_replay_timestamp()`. Lag causes: heavy DDL on primary, slow disks on standby, single-threaded replay (until parallel apply lands more broadly), conflicting queries on standby. Scale standby IOPS first.

### 76. Connection routing on failover.
Two patterns: (1) **VIP / DNS swap** — clients reconnect to the same address; (2) **HAProxy with pg_isready / Patroni REST API** — proxy picks new leader. Drivers with `target_session_attrs=read-write` (libpq 10+, JDBC) auto-discover among multi-host URLs.

### 77. Read scaling — caveats.
Reads on replicas are eventually consistent (replication lag). For read-your-writes, route the user back to the primary briefly, or use `synchronous_commit=remote_apply` and read from sync standby. Don't blindly use replicas for everything.

---

## 10. Operations, Monitoring, Security

### 78. Key pg_stat views.
- `pg_stat_activity`: current connections, queries, wait events.
- `pg_stat_statements` (extension): aggregated query stats — *enable this everywhere*.
- `pg_stat_user_tables/indexes`: per-table/index stats.
- `pg_stat_replication`, `pg_stat_subscription`: replication.
- `pg_stat_io` (16+): I/O by backend type.
- `pg_locks`: current locks.

### 79. pg_stat_statements.
Records normalized queries with total/avg time, rows, shared block hits/reads. The single most important extension for production. Identify your top queries by total time, by tail latency, by I/O.

### 80. Slow query logging.
`log_min_duration_statement = 500ms` logs every query > 500 ms. Pair with `auto_explain` (load module, set `auto_explain.log_min_duration`) to capture plans of slow queries automatically.

### 81. Wait events.
`pg_stat_activity.wait_event_type` / `wait_event` shows why a backend is blocked: `LWLock`, `Lock`, `IO`, `Client`, `Timeout`. Sampling them frequently builds an "Active Session History" — invaluable for tuning. Tools: `pgsentinel`, `pg_wait_sampling`.

### 82. Vacuum monitoring.
Watch `pg_stat_user_tables` for `n_dead_tup`, `last_autovacuum`, `last_autoanalyze`. Alert on tables with high dead tuples not being vacuumed (autovacuum starved). Tune per-table or raise `autovacuum_max_workers`.

### 83. Common alerts.
- Replication lag > N seconds.
- Long-running queries / long idle-in-transaction.
- Bloat ratio above threshold.
- Connections close to `max_connections`.
- `xid_age` approaching wraparound.
- Disk space, WAL accumulation, slot lag.
- Checkpoint frequency anomalies.

### 84. Roles, privileges, RLS.
Postgres roles unify users/groups. `GRANT SELECT ON ... TO role`. **Row-Level Security**:
```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON invoices
  USING (tenant_id = current_setting('app.tenant_id')::int);
```
The app sets `SET app.tenant_id = ...` per request. Multi-tenant pattern.

### 85. SCRAM, SSL, certs.
Use `password_encryption = scram-sha-256` (default). Require SSL (`hostssl` lines in `pg_hba.conf`). Certificate-based auth (`cert`) for service accounts. Audit `pg_hba.conf` regularly.

### 86. Encryption.
Postgres does not do native data-at-rest encryption (use disk encryption / cloud-managed). Column-level encryption via `pgcrypto`. TLS in transit via SSL. Sensitive logs go to a SIEM with retention policy.

### 87. Backups.
`pg_dump`/`pg_dumpall` for logical (slow, restorable cross-version). `pg_basebackup` + WAL archiving for physical (fast, PITR). Production: `pgBackRest`, `wal-g`, `barman` — incremental, parallel, encrypted, off-site. Test restores monthly.

### 88. Schema migrations.
Tools: Liquibase, Flyway, sqitch, Atlas, golang-migrate, alembic. Best practices: small backwards-compatible steps, online DDL (`CONCURRENTLY` indexes, `NOT VALID` constraints validated later), `lock_timeout`, `statement_timeout` on every migration. Avoid `ALTER TABLE ADD COLUMN ... DEFAULT non-volatile` blowing the disk — Postgres 11+ made `ADD COLUMN ... DEFAULT` fast for constant defaults.

### 89. Online ALTER best practices.
- Add nullable column → free in Postgres 11+.
- Add column with default → fast for constants, slow for `now()` / expressions.
- Add NOT NULL on existing column → rewrites the table (since 12+ can use `CHECK ... NOT VALID` then `VALIDATE`).
- Rename column / change type → rewrite; do via add new + dual-write + backfill + drop old.

### 90. Foreign data wrappers.
`postgres_fdw` for cross-cluster queries; `oracle_fdw`, `mongo_fdw`, `file_fdw`, `parquet_fdw`. Used for federation, gradual migrations, joining Postgres to S3/Parquet. Push-down quality varies — measure with `EXPLAIN VERBOSE`.

---

## 11. Useful Extensions

### 91. Top extensions to know.
- **pg_stat_statements**: query stats (always on).
- **pg_trgm**: trigram fuzzy match + GIN.
- **pgcrypto**: hashing, encryption helpers.
- **citext**: case-insensitive text.
- **hstore**: legacy key-value (use JSONB now).
- **uuid-ossp / pgcrypto**: UUID generation.
- **postgis**: full geospatial stack.
- **pgvector**: vector similarity for embeddings/RAG.
- **timescaledb**: time-series hypertables, continuous aggregates.
- **pg_partman**: partition management.
- **pgrepack / pg_repack**: online table rebuild.
- **pg_cron**: cron inside Postgres.
- **pgaudit**: detailed audit logging.

### 92. pgvector.
Adds `vector` type and ANN indexes (HNSW since 0.5, IVF) for cosine / L2 similarity. Used for embeddings, RAG, semantic search.
```sql
CREATE EXTENSION vector;
CREATE TABLE docs (id int, embedding vector(1536));
CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops);
SELECT id FROM docs ORDER BY embedding <=> '[...]' LIMIT 10;
```

### 93. TimescaleDB.
Extension that adds **hypertables** (auto-partitioned by time), **continuous aggregates** (incrementally refreshed materialized views), **compression**, and time-series functions. Works on plain Postgres; great for metrics, IoT.

---

## 12. Modern Features (recent versions)

### 94. MERGE (15+).
ANSI MERGE finally lands:
```sql
MERGE INTO target t
USING source s ON t.id = s.id
WHEN MATCHED AND s.delete THEN DELETE
WHEN MATCHED THEN UPDATE SET val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);
```
Before 15, use `INSERT ... ON CONFLICT DO UPDATE` (still common — faster for simple upserts).

### 95. INSERT ... ON CONFLICT.
Postgres-specific UPSERT:
```sql
INSERT INTO users (id, email, name) VALUES (1, 'a@b', 'A')
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name, updated_at = now()
WHERE users.name IS DISTINCT FROM EXCLUDED.name;
```
Use `EXCLUDED` to reference the proposed row.

### 96. RETURNING.
```sql
UPDATE orders SET status='shipped' WHERE id=$1 RETURNING id, status, shipped_at;
INSERT INTO ... RETURNING id; -- get autoincrement id back without round-trip
```
Saves a separate SELECT — meaningful at scale.

### 97. Generated columns.
```sql
ALTER TABLE orders ADD COLUMN total numeric
    GENERATED ALWAYS AS (qty * unit_price) STORED;
```
Stored or virtual (only STORED implemented). Useful for derived values used in indexes / filters.

### 98. Identity columns.
```sql
CREATE TABLE t (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, ...);
```
SQL-standard alternative to `SERIAL`. `BY DEFAULT` allows manual overrides; `ALWAYS` forbids.

### 99. GROUPS / FILTER / DISTINCT in aggregates.
```sql
SELECT
  COUNT(*) FILTER (WHERE status='ok') AS ok,
  COUNT(*) FILTER (WHERE status='err') AS err,
  COUNT(DISTINCT user_id) AS uniq_users
FROM events;
```
Cleaner and faster than multiple `CASE WHEN` aggregations.

### 100. SQL/JSON & jsonpath (12+, 15/16+ enhancements).
Full SQL/JSON functions: `JSON_TABLE` (17), `JSON_VALUE`, `JSON_QUERY`, `JSON_EXISTS`, `IS JSON` predicate. Replaces messy operator chains for nested extraction.

---

## 13. Anti-Patterns & Best Practices

### 101. Top anti-patterns.
- `SELECT *` everywhere → wasted I/O, fragile contracts.
- One giant table for everything (events, logs, audit, KV).
- Storing files as `bytea` — use object storage + URL.
- Long-running transactions on the primary.
- Disabling autovacuum.
- Random UUID v4 primary keys on huge tables — destroys cache locality; consider UUID v7 (time-ordered) or `bigint` IDENTITY.
- Many tiny tables joined N ways for a single screen → fix the schema.
- `OFFSET 1000000 LIMIT 20` → use keyset / cursor pagination.

### 102. Keyset pagination.
```sql
SELECT * FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```
Constant time regardless of page depth; needs index on `(created_at, id)`.

### 103. NULL semantics gotchas.
`NULL = NULL` is `NULL` (not true). Use `IS NULL` / `IS DISTINCT FROM`. `NOT IN (subquery with NULL)` returns nothing. Aggregations skip NULLs (except `COUNT(*)`). Be deliberate: NULL means "unknown".

### 104. Boolean / 3-valued logic.
`WHERE flag` works if `flag` is boolean — `IS TRUE` / `IS FALSE` is safer with nullable booleans. In `WHERE`, only **TRUE** rows are returned; **NULL** and **FALSE** are filtered out.

### 105. Time zones.
Always use `timestamptz`. It stores UTC internally and converts at display. `timestamp` (without TZ) silently drops offsets — a frequent source of bugs.

### 106. Money.
Don't use `float`/`double` for money. Use `numeric(20,4)`. Postgres has a `money` type — limited; most apps avoid it.

### 107. UUID v4 vs v7.
Random v4 PKs hurt B-tree locality on huge tables (random inserts → page splits). v7 is time-ordered, behaves like a bigint at the index level. Generate v7 in app code (libraries exist in Go/Python/JS); Postgres lacks a built-in v7 generator (yet).

### 108. Mindset summary.
- Measure before tuning: `EXPLAIN ANALYZE`, `pg_stat_statements`, `pg_stat_io`.
- Statistics are sacred — keep them fresh.
- Connections are expensive — pool them.
- VACUUM is non-negotiable — keep it healthy.
- Index intentionally; every index has a write cost.
- Transactions short, locks small, timeouts everywhere.
- Backups proven by restore. Failover proven by drills.
- Prefer SQL over application-side joins; Postgres can do more than people give it credit for.
