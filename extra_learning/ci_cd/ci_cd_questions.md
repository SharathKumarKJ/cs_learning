# CI/CD for Data Engineering (Detailed)

### 1. What is CI/CD?
**Continuous Integration**: every code change is automatically built, linted, and tested on merge to a shared branch. **Continuous Delivery/Deployment**: every passing build is automatically (or one-click) deployed to environments. The goal is fast, safe, frequent change.

### 2. Popular CI tools.
**GitHub Actions** (YAML, tight Git integration), **GitLab CI**, **Jenkins** (self-hosted, plugin ecosystem), **Azure DevOps**, **CircleCI**, **Buildkite**. Most data teams use GitHub Actions or GitLab CI for new work.

### 3. CI for data pipelines — what to test?
Python lint (ruff/black/mypy), SQL lint (sqlfluff), DAG import + structure tests (Airflow), dbt parse + compile, dbt tests on a CI warehouse, unit tests for transformations, schema/contract validation, and security scans (Trivy on Docker images, secret scanning).

### 4. CD for data — what gets deployed?
DAG files synced to Airflow, dbt project to the warehouse (`dbt run` against a CI/staging schema first), Spark job artifacts/images, Terraform/Bicep infra, and database migrations. Each environment (dev/stage/prod) deploys with separate credentials.

### 5. Environment promotion.
A typical flow: feature branch → dev (auto on PR) → stage (auto on merge to main) → prod (manual approval or canary). Each environment has its own warehouse schema, S3 bucket, and secrets. Promote the same artifact built once, parameterized by environment.

### 6. Infrastructure as Code.
Define cloud resources declaratively: **Terraform** (multi-cloud, most popular), **Pulumi** (real programming languages), **CloudFormation** (AWS-native), **Bicep** (Azure-native). Critical for reproducibility, DR, audit, and least-privilege via code review.

### 7. Secrets in CI/CD.
Never store in plaintext. Use the CI's encrypted secret store (GitHub Actions secrets) for boot-strapping, then **OIDC-based** auth to cloud (AWS/Azure/GCP) — short-lived tokens, no static credentials. For runtime, pipelines pull secrets from Vault/Key Vault/Secrets Manager.

### 8. Blue-green vs canary for data jobs.
**Blue-green**: deploy new version side-by-side, validate, switch traffic — straightforward for APIs, harder for stateful jobs. **Canary**: ramp traffic gradually. For data: shadow the new pipeline writing to a `_v2` table, compare with the old, then cut over.

### 9. Schema migrations.
Use tools like **Alembic** (Python/SQLAlchemy), **Flyway**, **Liquibase**, or dbt's run-operations. Migrations are versioned SQL files applied in order; expand-then-contract pattern: add new column → backfill → swap reads → remove old column.

### 10. Data contracts.
Producer-consumer agreements describing schema, freshness, ownership, quality. Tools: **dbt source contracts**, **Soda Contracts**, **Avro/Protobuf with schema registry**. CI enforces contracts so a producer cannot ship a breaking change without consumer sign-off.

### 11. Pre-commit hooks.
Run linters/formatters before code reaches CI: `ruff`, `black`, `isort`, `sqlfluff`, `yamllint`, `detect-secrets`. Use the `pre-commit` framework with a `.pre-commit-config.yaml` checked into the repo.

### 12. PR-based dbt slim CI.
Only build models that **changed** in the PR plus their downstream — use `dbt run -s state:modified+ --defer --state <prod_manifest>`. Saves time and warehouse cost vs full rebuilds on every PR.

### 13. Testing Airflow DAGs in CI.
At minimum: `python -c "import dag_file"` to catch parse errors and `airflow dags list-import-errors`. For deeper checks: assert task structure, retries, owner, SLA; spin up an Airflow container and run `airflow dags test` on small fixtures.

### 14. Testing Spark jobs in CI.
Build a small fixture DataFrame in a `pytest` fixture with a local `SparkSession`, run the transformation, assert on the resulting DataFrame. Keep tests under 5-10 s; cover edge cases (nulls, duplicates, schema variants). Avoid hitting the cluster in CI.

### 15. Rollback strategies.
For dbt: revert the PR and re-run; use snapshots for SCD2 history. For Airflow: redeploy previous DAG version, mark current run failed. For warehouse migrations: keep backward-compatible changes; for breaking changes, ensure the previous artifact still works on the new schema (expand-contract).
