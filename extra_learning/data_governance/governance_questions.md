# Data Governance and Quality Questions (Detailed)

### 1. What is data governance?
The collection of policies, roles, and processes ensuring data is accurate, secure, available, and used appropriately. It covers ownership, classification, lineage, quality, access, retention, and compliance. Without it, lakes turn into swamps.

### 2. Key roles.
**Data owner**: business accountable, defines what the data means and who can use it. **Data steward**: day-to-day enforcement, quality, glossary. **Data custodian**: IT/engineering, manages the platform that stores it. Clarifying these prevents the classic "no one owns this" problem.

### 3. Data catalogs.
Tools that crawl your data systems and present searchable inventories with descriptions, owners, lineage, and quality scores. Examples: **Microsoft Purview**, **Collibra**, **Alation**, **Atlan**, **DataHub** (open source), **Amundsen** (open source), **Unity Catalog** (Databricks).

### 4. Column-level lineage.
Tracks how each column in a target was derived from source columns, through all transformations. Critical for impact analysis ("what breaks if I drop this column?") and root-cause investigation. Tools parse SQL/Spark logs to produce it.

### 5. Data quality dimensions.
**Accuracy** (matches reality), **Completeness** (no missing values where expected), **Consistency** (same value across systems), **Timeliness** (fresh enough), **Uniqueness** (no duplicates on key), **Validity** (matches format/range/domain). Define SLAs per dimension per table.

### 6. Great Expectations vs Soda vs dbt tests.
**GE**: rich Python framework, profiling, docs sites — heavyweight but powerful. **Soda**: simple YAML checks, fast onboarding, SaaS observability. **dbt tests**: SQL-native, lightweight, perfect if you already use dbt. Many teams use dbt tests for in-warehouse + Soda/GE for ingest/external.

### 7. GDPR core principles.
Lawfulness/fairness/transparency, purpose limitation, data minimization, accuracy, storage limitation, integrity/confidentiality, accountability. Practical asks on you: right to access, right to be forgotten (deletion across systems and backups), and breach notification.

### 8. CCPA basics.
California consumer privacy: right to know what is collected, right to delete, right to opt-out of sale, right to non-discrimination. Similar engineering implications: track PII, support per-subject deletion across the lake/warehouse.

### 9. PII classification.
Tag columns with sensitivity tiers (Public, Internal, Confidential, Restricted) and PII categories (name, email, SSN, phone, address, financial, health). Automate detection (Purview, Macie, BigQuery DLP) and enforce policies based on tags.

### 10. Masking vs tokenization vs encryption.
**Masking**: replace with fake-but-realistic values (irreversible) — for non-prod environments. **Tokenization**: reversible mapping via a token vault — for limited downstream use cases. **Encryption**: reversible with key — for storage and transit. Pick by who needs the original value when.

### 11. Data retention policies.
Per dataset/sensitivity, define how long you keep raw and curated data. Drives lifecycle policies (S3/GCS/ADLS tiers and deletes), warehouse table expirations, and backup retention. Required for GDPR Article 5 ("storage limitation").

### 12. Data contracts.
Formal agreement between producer and consumer: schema, semantics, freshness SLA, ownership, breaking-change policy. Enforced via CI checks (schema diff, contract tests). Prevents the "the upstream renamed a column at 3am" failure mode.

### 13. Schema registry.
Centralized service holding versioned schemas (Avro, Protobuf, JSON Schema) for streams. Producers and consumers fetch by ID; enforced backward/forward compatibility prevents pipeline breaks. Used heavily with Kafka.

### 14. RBAC vs ABAC.
**RBAC**: permissions granted to roles, users assigned to roles. Simple, common (Snowflake, Databricks Unity Catalog). **ABAC**: permissions evaluated from attributes of user + resource + context (department, tag, time). More flexible, more complex (Lake Formation, IAM with conditions).

### 15. Audit and lineage for compliance.
Log every access and change with who/what/when/why. Combine with lineage to demonstrate that data flows comply with policies (e.g. EU data never leaves EU systems). Centralize logs to SIEM (Splunk/Datadog) and retain per regulation.
