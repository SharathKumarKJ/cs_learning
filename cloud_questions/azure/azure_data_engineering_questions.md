# Azure Data Engineering Interview Questions (Detailed)

### 1. What is ADLS Gen2?
Azure Data Lake Storage Gen2 is Blob Storage with a hierarchical namespace (real folders), POSIX-like ACLs, and analytics-optimized APIs. It is the standard data lake substrate on Azure used by Synapse, Databricks, HDInsight, and Fabric.

### 2. What is Azure Data Factory (ADF)?
A managed cloud orchestration and data movement service. Core concepts: **linked services** (connections), **datasets** (typed references), **pipelines** (workflows of activities), **triggers** (schedule/event/tumbling-window). Use Copy Activity for movement, Mapping Data Flows for transformations, and external compute (Databricks/Synapse) for heavy work.

### 3. What is Mapping Data Flow?
Visual Spark-based transformations inside ADF that run on a managed Spark cluster. Good for low-code users; for complex logic or tight cost control, prefer Databricks notebooks invoked from ADF.

### 4. What is Azure Databricks?
A managed Apache Spark + Delta Lake platform deeply integrated with Azure (AAD, Key Vault, ADLS, Synapse). Provides workspaces, jobs, Delta Live Tables, Unity Catalog (governance), and managed MLflow. The dominant Spark platform on Azure for serious workloads.

### 5. What is Synapse Analytics?
A unified analytics service combining: **Dedicated SQL pools** (MPP warehouse, formerly Azure SQL DW), **Serverless SQL** (T-SQL over ADLS), **Apache Spark pools**, and **Synapse Pipelines** (rebranded ADF). It is being superseded by **Microsoft Fabric** for new deployments.

### 6. Dedicated vs serverless SQL pool?
**Dedicated**: provisioned MPP warehouse with distribution + partitioning, billed by DWU regardless of usage — predictable for steady workloads. **Serverless**: pay-per-TB scanned, queries files directly from ADLS via external tables — perfect for ad-hoc and unpredictable workloads.

### 7. What is Event Hubs?
A high-throughput managed event-ingest service, similar to Kafka. Offers a Kafka-compatible endpoint, partitioning by key, consumer groups, and Capture (auto-archive to ADLS/Blob). Pairs with Stream Analytics or Databricks for processing.

### 8. What is Azure Stream Analytics?
A managed, SQL-like stream processing engine for low-code real-time pipelines. Supports tumbling/hopping/sliding/session windows and writes to many sinks (ADLS, SQL, Event Hubs, Power BI). For complex logic or scale, Databricks Structured Streaming is more flexible.

### 9. What is Key Vault?
A managed service for secrets, keys, and certificates with HSM-backed options. Integrates with ADF (linked services), Databricks (secret scopes), and Azure Functions via Managed Identity — never hardcode credentials.

### 10. What is Managed Identity?
An automatically managed Azure AD identity attached to a service so it can authenticate to other Azure resources without storing credentials. Two types: **system-assigned** (lifecycle tied to the resource) and **user-assigned** (reusable across resources). Always prefer over connection strings.

### 11. How do you secure ADLS?
Layered: AAD RBAC at account/container level + POSIX ACLs on folders/files for fine-grained control; private endpoints to keep traffic off the public internet; storage firewall + VNet rules; encryption with Microsoft-managed or customer-managed keys (CMK in Key Vault); diagnostic logs to Log Analytics.

### 12. How do you design a lakehouse on Azure?
ADLS Gen2 zones (raw/curated/enriched), Delta tables managed by Databricks or Fabric, Unity Catalog or Purview for governance, ADF/Databricks Jobs for orchestration, and Power BI/Fabric for consumption. Streaming via Event Hubs + Structured Streaming.

### 13. How do you optimize Synapse dedicated SQL?
Choose right **distribution** (hash on join key, replicate small dims, round-robin for staging), partition very large tables, keep **statistics** current, use **materialized views** for hot aggregations, manage **workload groups** to isolate queues, and monitor columnstore health (`ALTER INDEX REORGANIZE` to compress open rowgroups).

### 14. How do you handle incremental loads in ADF?
Patterns: (a) high-watermark column (max(updated_at)) stored in a control table; (b) tumbling-window triggers for parameterized date slices; (c) SQL Server Change Tracking / Change Data Capture; (d) Auto Loader (Databricks) for files. Metadata-driven pipelines parameterize source/target so one pipeline handles many tables.

### 15. How do you monitor Azure pipelines?
ADF/Synapse pipeline monitor for run history; emit diagnostic logs to Log Analytics with KQL queries and alerts; Azure Monitor metrics for runtime/SLA; custom logging tables for row counts and data quality; integrate with Teams/PagerDuty via Action Groups.

### 16. How do you implement CI/CD for ADF?
ADF integrates with Git (Azure DevOps Repos / GitHub) in a "collaboration" branch. PRs merge to `main`, then export ARM templates and deploy via Azure DevOps Pipelines / GitHub Actions to dev → test → prod, parameterizing connections per environment. Alternative: deploy with Bicep/Terraform.

### 17. What is Microsoft Purview?
The unified data governance platform: data catalog, automated classification (PII tagging), end-to-end lineage across ADF, Synapse, Databricks, Power BI, and policy management. Use it as the central catalog and lineage layer for the whole estate.

### 18. What are private endpoints?
Network interfaces inside your VNet that map to specific instances of Azure PaaS services. Traffic stays on the Microsoft backbone (not the internet). Critical for production data platforms to prevent data exfiltration and meet compliance.

### 19. How do you manage secrets in Databricks?
Create a **secret scope** backed by Azure Key Vault, then reference via `dbutils.secrets.get(scope, key)`. Never inline secrets in notebooks. Combine with managed identities for passwordless access to ADLS and SQL.

### 20. How do you reduce Azure data platform cost?
Auto-terminate idle Databricks clusters; right-size Synapse DWUs and pause when unused; use Spot/Low-priority for non-critical workloads; lifecycle policies on ADLS (cool/archive tiers); reserved capacity for steady workloads; optimize file sizes and partitioning; review queries scanning unnecessary data.
