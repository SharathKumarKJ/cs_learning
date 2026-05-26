# Data Warehousing Interview Questions (Detailed)

### 1. Data warehouse vs data lake vs lakehouse.
**Warehouse**: schema-on-write, structured, BI-optimized (Snowflake, Redshift, BigQuery, Synapse). **Lake**: schema-on-read, all formats, cheap object storage (S3/ADLS/GCS). **Lakehouse**: lake + transactional table formats (Delta/Iceberg/Hudi) + governance to get warehouse semantics on lake storage.

### 2. ETL vs ELT.
**ETL**: transform before loading (legacy, Informatica/SSIS era — fits limited warehouse compute). **ELT**: load raw data first, transform inside the warehouse using SQL (Snowflake/BigQuery/Redshift + dbt). ELT dominates modern stacks because cloud warehouse compute is elastic and cheap.

### 3. Kimball vs Inmon.
**Inmon**: enterprise data warehouse in 3NF (normalized), conformed marts built on top — top-down, governance-heavy, slow to deliver. **Kimball**: bus matrix of conformed dimensions feeding star-schema marts — bottom-up, faster delivery. Most teams use Kimball; some use Data Vault as the raw layer with Kimball marts on top.

### 4. Fact vs dimension table.
**Fact**: numeric measures (revenue, quantity) with foreign keys to dimensions; tall and narrow at scale. **Dimension**: descriptive attributes (customer, product, date) used for filtering and grouping; wide and short.

### 5. Galaxy schema.
Also called fact constellation: multiple fact tables sharing conformed dimensions. Reflects a real warehouse with several business processes (orders, shipments, returns) sharing dim_customer, dim_product, dim_date.

### 6. Surrogate key vs natural key.
Surrogate keys are warehouse-generated, decouple history from source IDs, support SCD2, and keep joins on small integers. Natural keys remain as business identifiers stored alongside but not used as PKs.

### 7. Partitioning vs clustering.
**Partitioning**: physical split by low-cardinality column (usually a date) — pruned by query optimizer. **Clustering / Z-ORDER**: in-partition data co-location by additional columns. Combine: partition by date + cluster by customer/product.

### 8. Materialized views.
Precomputed query results stored physically and refreshed (manually, scheduled, or incrementally). Speed up hot aggregations at the cost of storage and refresh complexity. All major warehouses support them with varying refresh capabilities.

### 9. Columnar storage.
Stores values of the same column contiguously (Parquet, ORC, Capacitor, Snowflake micro-partitions). Enables: better compression (similar values together), vectorized execution, predicate/projection pushdown, min-max statistics for block skipping. The single biggest reason cloud warehouses are fast on wide tables.

### 10. SCD Type 2 implementation pattern.
On each load: compare incoming dimension rows to current rows; for changed attributes, set `valid_to = today`, `is_current = false` on the current row, then INSERT a new row with new attributes, `valid_from = today`, `valid_to = NULL`, `is_current = true`. Fact tables reference the surrogate key, not the natural key, so historical facts join to the historically correct dim version.
