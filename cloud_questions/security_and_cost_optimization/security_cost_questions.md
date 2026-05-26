# Security and Cost Optimization Questions (Detailed)

## Security

### 1. How do you secure data at rest?
Enable encryption with **provider-managed keys** by default and upgrade to **customer-managed keys (CMK)** in KMS/Key Vault/Cloud KMS when compliance or BYOK is required. Encrypt every layer: object storage (S3/ADLS/GCS), warehouse storage, snapshots, backups, and intermediate scratch volumes. Rotate keys on a schedule and log all key operations.

### 2. How do you secure data in transit?
Enforce TLS 1.2+ on every endpoint; reject plaintext via bucket/account policies. Use private endpoints / VPC endpoints / Private Link so traffic between services stays on the cloud backbone, not the public internet. For cross-cloud or hybrid links, use VPN/Direct Connect/ExpressRoute/Interconnect.

### 3. IAM least-privilege patterns.
Grant the minimum permissions needed for each role and audit them with access analyzers (AWS IAM Access Analyzer, Azure PIM access reviews, GCP Policy Analyzer). Prefer roles/managed identities over static credentials, use short-lived tokens (STS/Workload Identity), and separate identities per environment so a dev key can never touch prod.

### 4. Network isolation.
Put data services in private subnets with no public IP, route through NAT/Private Endpoints for outbound, and restrict service-to-service traffic with security groups / NSGs / VPC firewall rules. For cross-account access, use IAM role assumption rather than opening networks.

### 5. PII handling.
Classify columns (catalog tags), encrypt or tokenize PII at ingestion if downstream consumers do not need the raw value, mask in non-prod, restrict access via column/row policies, and log every access for audit. Build deletion workflows so "right to be forgotten" works across raw, curated, backups, and BI extracts.

### 6. Secrets management.
Never store credentials in code, env vars in plaintext, or DAG Variables. Use **AWS Secrets Manager / Azure Key Vault / GCP Secret Manager / HashiCorp Vault**, accessed via managed identity. Rotate automatically; alert on long-lived static credentials.

### 7. Audit logging.
Enable CloudTrail / Azure Activity + Diagnostic / Cloud Audit Logs and ship to a centralized SIEM (Splunk, Datadog, Sentinel, Chronicle). Retain per regulation (often 1-7 years). Build alerts for anomalous patterns: bulk downloads, unusual geographies, privilege escalation, key disablement.

### 8. Securing data sharing.
Prefer governed share mechanisms (Snowflake Secure Data Sharing, BigQuery Authorized Datasets / Analytics Hub, Lake Formation cross-account grants, Delta Sharing) over copying data. These keep the source under your control and revoke cleanly.

## Cost

### 9. Compute cost levers.
Auto-suspend idle warehouses and clusters; right-size (don't run 4XL when XL finishes in time); use Spot/preemptible for stateless workloads; commit to reserved capacity for steady baselines; separate workloads (ETL vs BI) onto distinct warehouses so heavy ETL doesn't push BI users into bigger clusters.

### 10. Storage cost levers.
Lifecycle policies move cold data to cheaper tiers (S3 IA/Glacier, ADLS Cool/Archive, GCS Nearline/Coldline); expire temp/scratch buckets; compact small files (read cost is metadata-heavy); delete unused snapshots/AMIs; remove unused dev clones (`zero-copy clones` still consume divergent storage over time).

### 11. Query cost levers.
Partition and cluster/Z-ORDER on common filters; avoid `SELECT *` and project only needed columns; materialize hot aggregates; pre-aggregate before joins; set query quotas per user/role; review top-cost queries weekly from system tables (`INFORMATION_SCHEMA.JOBS` in BigQuery, `QUERY_HISTORY` in Snowflake, `SVL_QUERY_REPORT` in Redshift).

### 12. Data transfer cost.
Egress between regions and out to the internet is often the most surprising bill. Co-locate compute with storage; use VPC endpoints / Private Link to avoid NAT and internet egress; cache or replicate hot data into consumer regions; avoid round-tripping through the public internet for service-to-service calls.

### 13. Tagging and chargeback.
Tag every resource with `env`, `team`, `project`, `cost_center`. Use AWS Cost Categories / Azure Cost Management / GCP Labels to slice spend by tag. Show teams their own spend in dashboards — visibility drives behavior more than any policy.

### 14. Cost anomaly detection.
Use built-in anomaly detection (AWS Cost Anomaly Detection, Azure Cost alerts, GCP Budgets) and custom alerts on sudden warehouse credit jumps. Catch a runaway query the same hour, not at month end.

### 15. Cost optimization checklist.
Auto-suspend everything that supports it; lifecycle on object storage; right-size and review quarterly; reserved/committed use for steady workloads; column pruning and partitioning enforced in CI; materialized views for hot dashboards; tag and chargeback; cost dashboards per team; monthly review with FinOps; budget alerts at 50/80/100%.
