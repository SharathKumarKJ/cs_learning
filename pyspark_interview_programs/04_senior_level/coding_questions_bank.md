# PySpark Coding Questions Bank (Detailed)

For each problem: **what's asked**, **approach**, and **key PySpark constructs**. Solutions exist in the numbered files in this folder.

### 1. Find latest record per customer.
Use a window partitioned by `customer_id` ordered by `updated_at DESC`; keep `row_number() = 1`. Add a deterministic tiebreaker (e.g. `, id DESC`) to avoid non-determinism when timestamps collide. Constructs: `Window.partitionBy().orderBy()`, `row_number()`.

### 2. Find Nth highest salary per department.
Use `dense_rank()` (not `row_number`) over a window partitioned by `department_id` ordered by `salary DESC`, then filter `rank = N`. `dense_rank` handles ties correctly — three people tied for top salary all rank 1, and the next salary ranks 2.

### 3. Detect duplicates and keep only one occurrence.
Two flavors: (a) exact duplicates — use `dropDuplicates(subset_cols)`; (b) keep the latest — use `row_number()` window ordered by timestamp DESC and filter `= 1`. Discuss `distinct()` vs `dropDuplicates()` (the former dedupes on all columns).

### 4. Calculate running total of sales.
`sum(amount).over(Window.partitionBy(customer).orderBy(date).rowsBetween(Window.unboundedPreceding, Window.currentRow))`. Be **explicit** about the frame; the default frame with `orderBy` is `RANGE` which behaves differently on ties.

### 5. Calculate 7-day moving average.
`avg(amount).over(Window.orderBy(date).rowsBetween(-6, 0))` for a 7-row window. For a calendar 7-day window with gaps in dates, you'd need `RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW` — supported in Spark SQL but not in DataFrame API directly; switch to SQL or generate a continuous date dimension.

### 6. Sessionize events using inactivity window.
Compute the gap between consecutive events per user (`lag(event_time)`), flag rows where the gap > 30 min as new sessions, then cumulative-sum the flags to assign a session_id. Aggregate by `(user, session_id)` for session-level stats. Identical pattern to SQL islands.

### 7. Pivot monthly sales by product.
`df.groupBy("product").pivot("month", ["Jan","Feb","Mar"]).agg(sum("amount"))`. Always specify the pivot value list — without it, Spark scans the data to discover values, which costs an extra job.

### 8. Unpivot wide table to long format.
Use `selectExpr` with `stack()`: `df.selectExpr("product", "stack(3, 'Jan', jan, 'Feb', feb, 'Mar', mar) as (month, amount)")`. The first arg is the number of groups; pairs follow as (literal label, column).

### 9. CDC merge: apply inserts/updates/deletes to target.
Land changes in bronze; deduplicate by primary key keeping latest sequence with a window; then `DeltaTable.merge(...)` (or Iceberg/Hudi equivalent) with `whenMatchedDelete` on tombstones, `whenMatchedUpdateAll` on updates, `whenNotMatchedInsertAll` on inserts. Test idempotency by running the same batch twice.

### 10. Word count from text data.
`spark.read.text(path).selectExpr("explode(split(value, ' ')) as word").groupBy("word").count()`. The canonical Spark example — discuss combiner behavior, partitioning by hash(word), and skew for very common words.

### 11. Implement SCD Type 2.
Compare incoming rows to current rows of the dim by a hash of tracked columns. For changed rows: `MERGE` to set `valid_to = today, is_current = false` on current versions. For changed + new rows: insert new versions with `valid_from = today, valid_to = NULL, is_current = true`. Test for "no overlapping valid ranges per business key."

### 12. Join two large tables with skew handling.
Identify hot keys via Spark UI or a sample-based query. Salt the large side by appending `concat(key, lit('_'), (rand()*N).cast('int'))`; explode the small side across all N salts. Join on the salted key. Alternative: enable AQE skew-join (`spark.sql.adaptive.skewJoin.enabled=true`).

### 13. Broadcast small lookup tables.
`from pyspark.sql.functions import broadcast; big.join(broadcast(small), "id")`. Verify with `df.explain()` that the plan shows `BroadcastHashJoin`. Tune `spark.sql.autoBroadcastJoinThreshold` if Spark mis-estimates the small side as too big.

### 14. Read partitioned parquet and filter only required partitions.
`spark.read.parquet("s3://bucket/orders/").filter("order_date = '2026-01-15'")`. Verify partition pruning in `explain()` (look for `PartitionFilters`). Avoid functions on partition columns that defeat pruning.

### 15. Find top 3 products per category.
`row_number()` over a window partitioned by `category` ordered by revenue DESC, filter `<= 3`. Use `dense_rank` if ties should all be kept.

### 16. Calculate customer churn (no order in last 90 days).
Aggregate per customer the max order_date; filter `max_order_date < current_date() - 90`. Compare against the cohort active at the start of the window for a percentage. Discuss the difference between "churned" and "inactive."

### 17. Find new vs returning customers per month.
For each customer compute first_order_date; for each (customer, order_month) flag `is_new = (order_month == first_order_month)`. Then aggregate counts per month. Classic cohort building block.

### 18. Detect schema drift between two DataFrames.
Compare `df1.schema.fieldNames()` vs `df2.schema.fieldNames()` and per-field type. Print added/removed/type-changed columns. Wrap into a reusable assertion used at the start of every job to fail fast on contract violations.

### 19. Convert nested JSON into flat table.
`select` nested fields with dot notation (`col("address.city")`), `explode` array fields into rows, and rename to flat names. For deeply nested or variable schemas, write a recursive flattening helper that walks the schema and emits column expressions.

### 20. Explode arrays into rows.
`df.withColumn("item", explode("items"))`. Use `explode_outer` to keep rows with empty/null arrays, and `posexplode` when you also need the index within the array.

### 21. Combine multiple files into one DataFrame.
`spark.read.parquet("s3://b/path/*/file.parquet")` accepts globs, comma-separated paths, or directory listings. Add `recursiveFileLookup=true` for nested trees. Use `input_file_name()` to tag each row with its source — essential for lineage and recovery.

### 22. Read CSV with custom schema and bad-record handling.
`spark.read.option("header", "true").option("mode", "PERMISSIVE").option("columnNameOfCorruptRecord", "_corrupt").schema(my_schema).csv(path)`. Other modes: `DROPMALFORMED` (silently drop) and `FAILFAST` (raise). Always define an explicit schema in production to avoid type drift.

### 23. Repartition for write to control file size.
`df.repartition(N).write...` to produce roughly N output files. For partitioned writes, `df.repartition("partition_col")` ensures one task per partition value (avoiding many tiny files). Target 128 MB-1 GB per output file.

### 24. Compute year-over-year growth.
Aggregate to monthly totals; `lag(revenue, 12)` over `Window.orderBy(month)` for last year's value; compute pct change with `NULLIF(prev, 0)` to avoid divide-by-zero. Works analogously for week-over-week, day-over-day with different offsets.

### 25. Find first and last value per partition.
Use `first(col, ignorenulls=True)` and `last(col, ignorenulls=True)` over a window — but **specify the frame** as `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` for `last`, otherwise it returns the current row. Or simpler: `row_number() = 1` and `row_number() = count(*)` patterns.

### 26. Self-join to find pairs of employees with same manager.
`df.alias("a").join(df.alias("b"), (col("a.manager_id") == col("b.manager_id")) & (col("a.employee_id") < col("b.employee_id")))`. The `<` condition avoids self-pairs and duplicate ordered pairs.

### 27. Compute funnel conversion rates.
For each step, count distinct users who reached it (or use boolean flags via conditional aggregation). Ratios between consecutive steps give conversion. For step ordering and time bounds, use windowed lag/lead on event timestamps.

### 28. Detect fraud rules (e.g. >5 transactions in 1 minute).
`count("*").over(Window.partitionBy("customer").orderBy(unix_timestamp("txn_time")).rangeBetween(-60, 0))` to count transactions in the past 60 seconds. Filter rows where the count > 5. Range-based windows are key for time-bounded fraud rules.

### 29. Find products bought together (basket analysis basics).
Self-join `order_items` on `order_id` with `a.product_id < b.product_id`, count pairs, order desc. For very large data, switch to FP-Growth in Spark MLlib for proper market-basket mining.

### 30. Compute median per group using `percentile_approx`.
`groupBy("category").agg(percentile_approx("amount", 0.5).alias("median"))`. Use `percentile_approx` (HyperLogLog/T-Digest-style) instead of exact percentile for large data; configurable accuracy via second argument (default 10000).
