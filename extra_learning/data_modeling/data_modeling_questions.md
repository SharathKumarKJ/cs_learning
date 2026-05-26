# Data Modeling Interview Questions (Detailed)

### 1. OLTP vs OLAP modeling.
**OLTP**: highly normalized (3NF), optimized for many small writes, primary-key lookups, and referential integrity (banking, e-commerce backends). **OLAP**: denormalized stars/snowflakes, optimized for large aggregations over wide scans (analytics warehouses). Don't try to use one model for both — replicate OLTP → OLAP.

### 2. What is the star schema?
A central **fact table** (events/measures) surrounded by **dimension tables** (descriptive attributes) joined by foreign keys. Few joins, intuitive for BI users, fast scans. Dominant pattern for Kimball-style warehousing.

### 3. Star vs snowflake schema.
**Star**: dimensions are denormalized into single tables. **Snowflake**: dimensions are normalized into multiple sub-tables. Star wins for simplicity and query performance; snowflake saves storage for very large hierarchies but adds joins.

### 4. Fact table types.
**Transactional**: one row per event (most common). **Periodic snapshot**: one row per entity per period (daily account balance). **Accumulating snapshot**: one row per workflow instance updated as steps complete (order lifecycle). **Factless**: events with no measures, used for coverage/eligibility.

### 5. Grain of a fact table.
The grain is the meaning of one row — define it first and stick to it. Examples: "one row per order item", "one row per customer per day". Mixing grains in one table is a top modeling mistake.

### 6. Slowly Changing Dimensions (SCD).
**Type 0**: never changes. **Type 1**: overwrite (no history). **Type 2**: keep history with `valid_from`/`valid_to`/`is_current` columns or surrogate keys. **Type 3**: keep limited history in extra columns. **Type 4**: separate history table. **Type 6**: hybrid 1+2+3. Type 2 is the workhorse.

### 7. Surrogate vs natural keys.
**Natural key**: from the source system (e.g. customer_id from CRM). **Surrogate key**: warehouse-generated integer/UUID independent of source. Use surrogates as PK in dim tables — they are stable across source changes, support SCD2 versioning, and keep joins fast.

### 8. Conformed dimensions.
Dimensions shared across multiple fact tables/data marts so analytics across business processes is consistent. The classic example is a single shared `dim_date` and `dim_customer`. Without conformed dimensions, you get conflicting metrics across reports.

### 9. Bridge tables.
Resolve many-to-many relationships, like many products in many categories or many doctors per patient. Often paired with weighting factors to allow either correct counts or allocations.

### 10. Data Vault basics.
A modeling approach for raw, auditable, source-agnostic warehouses. Three structures: **Hubs** (business keys), **Links** (relationships between hubs), **Satellites** (descriptive attributes with full history). Highly insert-only and source-traceable; downstream marts often present a Kimball star to consumers.
