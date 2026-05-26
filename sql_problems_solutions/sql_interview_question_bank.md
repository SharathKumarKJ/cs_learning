# SQL Interview Question Bank (Detailed)

## Basics

### 1. Difference between WHERE and HAVING?
`WHERE` filters rows *before* aggregation; `HAVING` filters *after* aggregation. You can use aggregate functions only in `HAVING` (or by referencing aliases in some dialects). Filtering with `WHERE` when possible is faster because fewer rows reach the aggregation step.

### 2. Difference between DELETE, TRUNCATE, DROP?
`DELETE` removes rows, supports `WHERE`, is logged row-by-row, fires triggers, and can be rolled back. `TRUNCATE` removes all rows quickly by deallocating data pages, usually cannot be rolled back, resets identity, and is DDL-like. `DROP` removes the entire table object including schema, constraints, and indexes.

### 3. Difference between UNION and UNION ALL?
`UNION` combines results and removes duplicates, which requires a sort/hash and is slower. `UNION ALL` just concatenates results, keeping duplicates, and is much faster. Use `UNION ALL` unless deduplication is genuinely required.

### 4. Primary key vs unique key?
Both enforce uniqueness. A primary key additionally enforces NOT NULL and there can be only one per table; it is the canonical row identifier. A unique constraint can allow NULLs (one or many depending on dialect) and multiple per table.

### 5. What is a foreign key?
A foreign key is a column (or set) in a child table that references the primary key of a parent table, enforcing referential integrity. Options include `ON DELETE CASCADE`, `SET NULL`, `RESTRICT`. In analytical warehouses (Snowflake, BigQuery), FKs often exist for documentation only and are not enforced.

### 6. What are SQL constraints?
NOT NULL, UNIQUE, PRIMARY KEY, FOREIGN KEY, CHECK (e.g. `CHECK (amount >= 0)`), and DEFAULT. They enforce data integrity at the database level so bad data never lands.

### 7. CHAR vs VARCHAR?
`CHAR(n)` is fixed-length, padded with spaces. `VARCHAR(n)` is variable-length up to n. VARCHAR is preferred for most use cases because it saves storage; CHAR is only marginally useful for truly fixed-width codes.

### 8. NULL vs empty string?
NULL means "unknown/absent" — it is not equal to anything, including itself (`NULL = NULL` is unknown). An empty string `''` is a known value of length 0. Be very careful in joins and `NOT IN` clauses where NULLs cause silent row loss.

### 9. Order of execution of a SQL query.
Logical order: FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT/OFFSET. This is why column aliases defined in SELECT cannot be used in WHERE in most dialects, but can be used in ORDER BY.

### 10. View vs materialized view?
A view is a stored SQL query — re-runs on every reference, always fresh, no storage. A materialized view stores the result physically; reads are fast but the data is as stale as the last refresh (manual, scheduled, or incremental).

## Joins

### 11. Types of joins?
INNER (matching rows on both sides), LEFT/RIGHT/FULL OUTER (keep unmatched on one or both sides with NULLs), CROSS (Cartesian product), SELF (table joined to itself), SEMI (keep left rows that match, no right columns), ANTI (keep left rows with no match). Lateral/APPLY joins allow correlated subqueries per row.

### 12. Self join use cases?
Hierarchies (employee → manager), comparisons between rows in the same table (price changes), finding pairs (products bought together), and gap/island detection.

### 13. Anti join in SQL?
Implemented via `NOT EXISTS` (NULL-safe, preferred), `LEFT JOIN ... WHERE right.key IS NULL`, or `NOT IN` (broken if right side has NULL). Use to find customers without orders, products never sold, etc.

### 14. Cross join?
Returns the Cartesian product of two tables — every left row paired with every right row. Useful for generating date dimensions, salt buckets for skew handling, or test combinations. Dangerous on large tables without filtering.

### 15. Cartesian product problem?
An accidental cross join, usually caused by a missing or wrong join condition, that explodes row counts (M × N rows). Detect with EXPLAIN showing `Nested Loop` over two large tables without a key.

## Aggregations

### 16. GROUP BY rules with non-aggregated columns.
Every column in SELECT must either appear in GROUP BY or be inside an aggregate function. Some dialects (MySQL with relaxed mode) allow exceptions but produce non-deterministic results. ANSI-compliant engines (Postgres, BigQuery, Snowflake) enforce strictly.

### 17. ROLLUP vs CUBE vs GROUPING SETS?
`ROLLUP(a, b, c)` produces subtotals along a hierarchy: (a,b,c), (a,b), (a), (). `CUBE` produces all combinations: 2^n subtotals. `GROUPING SETS` lets you list exactly which subtotal groupings you want — most flexible. Use `GROUPING()` function to identify the subtotal rows.

### 18. How to count distinct without DISTINCT?
`COUNT(DISTINCT col)` is the standard way but can be slow on huge data. Alternatives: `COUNT(*)` over a deduplicated CTE, approximate methods like `APPROX_COUNT_DISTINCT` (HyperLogLog) in Snowflake/BigQuery/Spark — 100× faster with ~2% error.

## Window functions

### 19. ROW_NUMBER vs RANK vs DENSE_RANK?
`ROW_NUMBER` is always unique (ties broken by physical order). `RANK` gives ties the same rank then skips (1,1,3). `DENSE_RANK` gives ties the same rank with no gap (1,1,2). Pick `row_number` for "one row per group", `dense_rank` for distinct ordinal positions.

### 20. FIRST_VALUE vs LAST_VALUE pitfalls.
With default frame `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, `LAST_VALUE` returns the current row, not what you expect. Always specify `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` for true last value over the partition.

### 21. NTILE use cases?
Bucket rows into N equal-sized groups for quartiles, deciles, percentiles, A/B test cohorts, top-X% spenders. `NTILE(4)` over an ordering gives quartile labels 1-4.

### 22. LEAD/LAG with default values?
Third argument is the default when the offset is out of bounds: `LAG(amount, 1, 0) OVER (...)` returns 0 instead of NULL for the first row. Useful for computing differences without NULL propagation.

### 23. Running totals.
`SUM(amount) OVER (PARTITION BY key ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`. Be explicit with the frame; the implicit frame with `ORDER BY` is `RANGE`, which behaves differently with ties.

### 24. 7-day moving averages.
`AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` for a row-based window. For a *calendar* 7-day window with gaps in dates, use `RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW` (Postgres) — gives correct results when dates are missing.

### 25. Top N per group.
`ROW_NUMBER() OVER (PARTITION BY group_col ORDER BY metric DESC)` in a CTE, then filter `rn <= N`. Use `DENSE_RANK` when ties should all be included.

## Advanced

### 26. Recursive CTE example.
Used for hierarchies and graph traversal. Anchor query returns starting rows; recursive query joins back to the CTE adding one level. Always include a termination condition or row limit to avoid infinite recursion.

### 27. Pivot/Unpivot.
**Pivot**: turn distinct values of one column into columns — use conditional aggregation (`SUM(CASE WHEN month='Jan' THEN amount END)`) or `PIVOT` operator in SQL Server/Snowflake. **Unpivot**: turn columns into rows — use `UNION ALL` or the `UNPIVOT` operator / `stack()` in Spark SQL.

### 28. MERGE statement.
Atomic upsert/delete from a source into a target by a matching condition. Supports `WHEN MATCHED THEN UPDATE/DELETE` and `WHEN NOT MATCHED THEN INSERT`. Core operation for CDC, SCD Type 1/2, and idempotent loads in Snowflake, BigQuery, Delta, Iceberg.

### 29. Islands and gaps problem.
Find runs of consecutive values (islands) or missing ones (gaps). Classic trick: subtract `ROW_NUMBER()` from the value/date — rows in the same run share the same difference. Group by that difference to collapse into runs.

### 30. Sessionization in SQL.
Mark a "new session" event whenever the gap from the previous event exceeds a threshold (e.g. 30 min), then take a running sum of those flags to assign session IDs. Equivalent to the islands pattern but on time gaps.

### 31. Year-over-year growth.
Aggregate to monthly/yearly totals, then `LAG(metric, 12) OVER (ORDER BY month)` for prior-year comparison. Compute pct with `NULLIF(prev, 0)` to avoid division by zero.

### 32. Cohort analysis.
Assign each customer to a cohort by their first activity month, then compute the % of the cohort active in each subsequent month. Joins cohort → activity → cohort size for retention percentage.

### 33. Funnel conversion.
Use conditional aggregation or a series of CTEs counting users at each step. Compute conversion as `count_at_step_n * 1.0 / count_at_step_(n-1)`.

### 34. Median in SQL without PERCENTILE_CONT?
Use `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY col)` where supported. Without it: order rows, take the middle (or average of two middle) using `ROW_NUMBER` and `COUNT(*) OVER ()`.

### 35. Detect duplicates.
`SELECT key_cols, COUNT(*) FROM t GROUP BY key_cols HAVING COUNT(*) > 1`. To inspect rows themselves use `ROW_NUMBER() OVER (PARTITION BY key_cols ORDER BY ...) > 1`.

## Optimization

### 36. How to read an execution plan?
Look bottom-up: source scans first, then joins, filters, aggregations, final sort. Check estimated vs actual rows (large mismatch = stale stats), join algorithm (Hash/Merge/Nested Loop), index usage (Index Seek vs Table Scan), and presence of explicit Sort/Spill.

### 37. Index types: B-tree, Hash, Bitmap.
**B-tree**: default, supports equality and range. **Hash**: only equality, very fast. **Bitmap**: low-cardinality columns (gender, status), excellent for analytical filters but bad for OLTP because writes lock many rows. **GIN/GiST** (Postgres): for text search, JSON, geometry.

### 38. When does an index hurt performance?
On write-heavy tables (every insert/update/delete must update indexes), when selectivity is low (engine prefers a scan), or when functions on indexed columns prevent index use (`WHERE LOWER(email)` — use a functional index instead).

### 39. Partitioning vs Sharding?
**Partitioning** splits a table within one database by a column (range, list, hash) so the engine can prune partitions. **Sharding** splits data across multiple physical databases for horizontal scale, requiring application-level routing.

### 40. Query rewrite techniques.
Eliminate `SELECT *`, push filters down, replace correlated subqueries with joins, use `EXISTS` instead of `IN` with NULLs, pre-aggregate then join (instead of join then aggregate), and avoid functions on indexed columns.

## Real-world

### 41. Find 2nd highest salary.
`DENSE_RANK() OVER (ORDER BY salary DESC) = 2` (handles ties correctly). Avoid `LIMIT 1 OFFSET 1` which breaks with ties.

### 42. Find users with no orders.
`LEFT JOIN orders ... WHERE orders.id IS NULL` or `NOT EXISTS (SELECT 1 FROM orders WHERE customer_id = c.id)`. Prefer NOT EXISTS to be NULL-safe.

### 43. Find customers with consecutive purchases.
Use `LAG` to get previous order date per customer; flag rows where the gap is exactly 1 day; group consecutive flagged rows using the islands pattern to compute streak lengths.

### 44. Find products bought together.
Self-join `order_items` on `order_id` with `a.product_id < b.product_id` to get unique unordered pairs, then `COUNT(*)` grouped by the pair. Order by count for the strongest associations.

### 45. Find first/last purchase per customer.
`MIN(order_date)`/`MAX(order_date) GROUP BY customer_id` for dates only. For full rows, use `ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date ASC/DESC) = 1`.

### 46. Calculate retention rate.
Cohort users by first activity month, then for each subsequent month count active cohort members divided by cohort size. Display as a cohort triangle.

### 47. Calculate churn.
Define a churn window (e.g. no activity in 90 days). Churned users = users active in period T but not in T+90 days. Churn rate = churned / total at start of period.

### 48. Find duplicates and keep one.
`ROW_NUMBER() OVER (PARTITION BY duplicate_key ORDER BY tiebreaker)` in a CTE, then DELETE/SELECT rows where `rn > 1` or `rn = 1` to keep one.

### 49. Detect fraud patterns.
Examples: more than N transactions per minute (`COUNT(*) OVER (PARTITION BY user ORDER BY ts RANGE INTERVAL '1 minute' PRECEDING)`), distinct locations within short time, transactions just below alert thresholds, sudden change vs historical average.

### 50. SCD Type 2 in SQL.
On each load: (a) UPDATE existing current rows to set `valid_to = today`, `is_current = false` where attributes changed; (b) INSERT new versions with `valid_from = today`, `valid_to = NULL`, `is_current = true`. MERGE with WHEN MATCHED + WHEN NOT MATCHED handles both cleanly.
