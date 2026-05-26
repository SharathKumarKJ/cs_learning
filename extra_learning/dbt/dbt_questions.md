# dbt Interview Questions (Detailed)

### 1. What is dbt?
**Data Build Tool**: a SQL-first transformation framework that compiles Jinja-templated SQL into warehouse-executed DDL/DML, manages a DAG of models, generates docs, and runs tests. dbt does the **T** in ELT.

### 2. Models, sources, seeds.
**Source**: a declaration of an existing raw table the warehouse already contains. **Model**: a `SELECT` saved as a `.sql` file that dbt materializes (view, table, incremental, ephemeral). **Seed**: a small CSV checked into the repo and loaded as a table.

### 3. Materializations.
**view**: re-runs on every query. **table**: drop & recreate full table on every dbt run. **incremental**: append/merge only new rows based on a filter — used for large fact tables. **ephemeral**: inlined CTE in downstream models, never materialized.

### 4. Incremental models.
Use `is_incremental()` to filter incoming rows by a high watermark, then dbt runs `MERGE` or `INSERT` only those rows. Critical strategies: `append`, `merge` (default on many warehouses), `delete+insert`. Configure unique_key for merge.

### 5. dbt tests.
**Generic tests**: `unique`, `not_null`, `accepted_values`, `relationships` defined in YAML. **Singular tests**: bespoke SQL returning rows that should be empty. **dbt-utils** package adds many more. Tests run with `dbt test` and gate CI deployments.

### 6. `ref()` and `source()`.
`{{ ref('model_x') }}` and `{{ source('schema', 'table') }}` are the central abstractions — they let dbt build the DAG, swap schemas across environments, and generate lineage. Never hardcode table names.

### 7. Snapshots (SCD2).
`{% snapshot %}` blocks let dbt capture point-in-time history of dimension tables using check or timestamp strategies, producing SCD Type 2 outputs with `dbt_valid_from` / `dbt_valid_to`.

### 8. Macros.
Jinja functions written in SQL that you can reuse across models. Combined with packages (`dbt_utils`, `dbt_expectations`, `audit_helper`), they make complex transformations DRY.

### 9. Tests + docs + exposures.
`dbt docs generate` produces a static site with models, columns, descriptions, lineage. Exposures declare downstream consumers (BI dashboards, ML models) so lineage extends beyond dbt.

### 10. dbt Core vs dbt Cloud.
**Core**: open-source CLI, runs anywhere (CI, Airflow, K8s CronJob). **Cloud**: managed scheduler, IDE, CI, semantic layer, and observability around Core. Most teams use Core inside Airflow/GitHub Actions; Cloud is convenient for smaller teams or teams that want the IDE/semantic layer.
