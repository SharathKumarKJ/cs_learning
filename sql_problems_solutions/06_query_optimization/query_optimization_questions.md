# SQL Query Optimization Questions (Detailed)

### 1. How do you optimize a slow query?
Start by reading the **execution plan** (`EXPLAIN` / `EXPLAIN ANALYZE`) to see where the time goes. Common levers in order of impact: reduce scanned data (filters pushed down, partition pruning, column projection), choose the right join algorithm, ensure relevant indexes are usable (no functions on indexed columns), refresh statistics so the optimizer makes good choices, and break very large queries into staged CTEs/materializations. Always measure before and after — "optimizations" without measurement often regress performance.

### 2. What is an index?
A secondary data structure (usually a B-tree, sometimes hash, bitmap, or GiST/GIN) that maps key values to row locations so the engine can find matches without scanning the whole table. Indexes speed up reads but slow down writes (every insert/update/delete must maintain them) and consume storage. Use indexes on columns frequently used in `WHERE`, `JOIN`, and `ORDER BY`, and avoid indexing low-selectivity columns in OLTP.

### 3. When can an index be ignored by the optimizer?
When **selectivity is low** (the optimizer estimates a full scan will be cheaper than many random index lookups), when **functions wrap the indexed column** (`WHERE LOWER(email) = ...` — use a functional/expression index instead), when **implicit type casts** prevent index use (string vs int), when **statistics are stale** so the optimizer mis-estimates cardinality, or when `OR`/`NOT IN` patterns defeat index access. `EXPLAIN` will reveal the actual access path.

### 4. What is partition pruning?
A physical optimization where the engine skips entire partitions (folders, ranges, or hash buckets) based on `WHERE` predicates on the partition column. It is the cheapest possible filter because no I/O happens for skipped partitions. Always partition by the column most queries filter on (typically a date), and use `EXPLAIN` to confirm pruning is actually occurring — a wrapped expression like `WHERE DATE(ts) = '2026-01-01'` often defeats it.

### 5. Why avoid `SELECT *`?
It forces the engine to read every column (huge I/O on wide tables and columnar stores), breaks projection pushdown in lake engines, ships unneeded bytes over the network, and couples consumers to the producer's schema so adding a column may break code. Always list the columns you need — your future self and your warehouse bill will thank you.

### 6. How do you optimize joins?
Filter and project as early as possible on both sides so less data reaches the join. Choose the right strategy: **broadcast** for one small side, **hash** for medium, **sort-merge** for two large sorted/clustered sides. Co-locate data on the join key when possible (Redshift DISTKEY, Spark bucketing, Snowflake clustering). Make sure join keys have the same data type (no implicit casts) and statistics are current so the optimizer picks the right join order.

### 7. What is a covering index?
An index that contains **all columns referenced by a query** (key + included columns), so the engine can satisfy the query from the index alone without touching the base table ("index-only scan"). Massively reduces I/O for hot read paths. In Postgres use `INCLUDE`; SQL Server has the same; MySQL has implicit covering with secondary indexes.

### 8. What is query cardinality?
The estimated number of rows produced at each step of the plan. The optimizer uses cardinality estimates to choose join order, join algorithm, and access path — if estimates are wrong by an order of magnitude, the plan can be catastrophically bad. Keep statistics fresh (`ANALYZE` / auto-stats) and watch for skewed data where uniform-distribution assumptions break.

### 9. Why are statistics important?
The optimizer's cost model depends on statistics (row counts, distinct values, histograms, null fractions). Stale stats cause it to under- or over-estimate cardinality and pick the wrong plan — using nested-loop on millions of rows, hash-joining the wrong side, missing partition pruning, etc. After large loads, run `ANALYZE` (or rely on auto-stats) before running heavy queries.

### 10. Difference between `WHERE` and `HAVING`?
`WHERE` filters rows **before aggregation**, so fewer rows enter `GROUP BY` — generally faster and pushable down to the storage layer. `HAVING` filters **after aggregation** and can reference aggregate functions (`HAVING SUM(amount) > 1000`). Use `WHERE` whenever the predicate does not depend on aggregates; reserve `HAVING` for true post-aggregation filters.

### 11. Why can `OR` conditions be slow?
The optimizer may not be able to use an index for both sides of an `OR`, so it falls back to a full scan. Rewriting `WHERE a = 1 OR b = 2` as `... WHERE a = 1 UNION ALL ... WHERE b = 2 AND a <> 1` often lets each branch use its own index. In some engines, `IN (...)` is also more index-friendly than equivalent `OR` chains.

### 12. How do you optimize window functions?
Reduce the input rows with `WHERE` before the window step (windows process every row that survives `WHERE`). Align partition/order keys with existing indexes or table sort order to avoid extra sorts. Avoid multiple windows over different specs in one query — each becomes a separate sort. Select only columns the window actually needs, and remember `QUALIFY` (Snowflake/BigQuery/Teradata) avoids the extra subquery wrapper for filtering on window results.

### 13. What is predicate pushdown?
Moving filter expressions down to the data source so unmatched rows are never read. In Parquet/ORC, statistics in each row group enable block-level pruning. In JDBC sources, the predicate becomes part of the remote `WHERE`. Critical to leverage — write filters on raw columns (not functions of them) and prefer column-equality on partition/cluster keys.

### 14. What is column pruning?
Reading only columns the query references, skipping the rest entirely on columnar formats (Parquet, ORC, Capacitor in BigQuery, micro-partitions in Snowflake). Often the single biggest win on wide tables. Defeated by `SELECT *` and by reading into an intermediate DataFrame before projecting.

### 15. When should you use a materialized view?
When the same expensive query runs frequently against data that changes slowly (heavy aggregations, complex joins powering dashboards). The MV stores results physically and is refreshed manually, scheduled, or incrementally. Trade-offs: extra storage, staleness, refresh cost — but read latency drops from minutes to milliseconds.

### 16. How do you tune queries scanning huge tables?
Layered approach: partition by the primary filter column; cluster/sort by secondary filter columns (Snowflake clustering, Redshift SORTKEY, Delta Z-ORDER, BigQuery clustering); compact small files; project only needed columns; push filters to the source; pre-aggregate into a smaller table or MV for dashboards. Always look at bytes scanned, not just elapsed time, as the primary cost metric in modern warehouses.
