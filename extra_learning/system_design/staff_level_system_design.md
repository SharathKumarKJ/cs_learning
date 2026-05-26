# Staff-Level System Design Questions (Detailed)

Staff/Principal interviews go beyond "can you design X" into trade-offs at scale, organizational impact, multi-year evolution, and failure modes. Use the framework: **requirements → capacity → API/data model → architecture → deep-dives → failure modes → operability → trade-offs → what changes at 10×**.

## Distributed systems classics

### 1. Design a globally distributed URL shortener handling 100k req/sec.
**Capacity**: 100k writes/sec peak, 10× reads, 5-year retention → ~15 PB if naive. Compress URLs, dedupe identical originals. **ID generation**: base62 of a 64-bit ID — pick Snowflake-style (timestamp + machine ID + sequence) for global ordering, or Twitter K-sortable. **Storage**: shard by hash(short_id) over a wide-column store (Cassandra/Scylla) or sharded MySQL with Vitess. **Read path**: edge CDN + Redis cache → DB. **Write path**: regional primary with async cross-region replication, accept eventual consistency. **Trade-offs**: strong consistency for ID uniqueness (use centralized ID service or Snowflake) vs read availability.

### 2. Design a multi-tenant logging platform like Datadog Logs.
**Pipeline**: agents → regional Kafka → stream processor (Flink) doing parsing, enrichment, PII redaction, indexing → tiered storage (hot: ClickHouse/Elastic, warm: S3+Parquet via DuckDB/Trino, cold: S3 Glacier). **Query**: federated planner routes by time range + tenant + filter, pushes predicates down to each tier. **Quotas**: per-tenant ingest rate, retention, query CPU; enforce in Kafka producers and at query planner. **Cost**: most spend is storage and queries on hot tier — push aggressively to columnar warm storage with smart indexes.

### 3. Design a payment processing system.
**Constraints**: strong consistency, exactly-once charges, regulatory audit, PCI scope minimization. **Architecture**: API gateway → idempotency-keyed payment service (Postgres with optimistic locking) → saga orchestrator coordinating fraud check → tokenization → bank rail → ledger. **Ledger**: double-entry, append-only, separate service (immutable Kafka log + materialized view in Postgres). **Failure**: every step has compensation; reconciliation jobs run nightly against bank statements. **Idempotency key + outbox** are non-negotiable. Discuss how to handle webhooks (rail callbacks) reliably.

### 4. Design Twitter's home timeline.
**Read-heavy** (100:1). Two strategies: **fan-out on write** (push tweets to each follower's timeline cache — fast reads, expensive for celebrity accounts) and **fan-out on read** (compute timeline at read time — cheap writes, slow reads). Hybrid: push for normal users, pull for celebrities (>1M followers). **Storage**: Redis sorted sets keyed by user, sharded by user_id. **Tweet store**: append-only, sharded by tweet_id. **Discuss** ranking (chronological vs ranked), backfill, abuse mitigation, hot keys.

### 5. Design YouTube/Netflix video streaming.
**Upload pipeline**: chunked upload → transcoding farm (multiple bitrates/codecs) → DRM packaging → push to CDN. **Playback**: adaptive bitrate (HLS/DASH), manifest fetched from origin, segments from nearest CDN POP. **Metadata DB**: sharded by video_id, hot views in Memcached/Redis. **Recommendations**: offline batch (Spark) + online retrieval (vector store) + real-time ranker. **Failures**: CDN miss → origin shield; transcoder failures retry idempotently keyed by chunk hash.

### 6. Design a globally distributed key-value store like DynamoDB.
**Partitioning**: consistent hashing by key (with virtual nodes for balanced distribution). **Replication**: N replicas, quorum reads/writes (R + W > N for strong consistency on a single key). **Conflict resolution**: vector clocks or last-write-wins with synchronized clocks. **Hot partition handling**: adaptive partitioning (split hot ranges). **Failures**: hinted handoff for temporarily-down replicas, Merkle-tree anti-entropy for long absences. **Discuss**: tunable consistency (eventual vs strong), gossip protocols for membership, fencing on partition splits.

### 7. Design a real-time collaborative document editor (Google Docs).
**Concurrency model**: operational transformation (OT) or CRDTs (more modern, simpler in distributed settings). **Architecture**: each doc has a session server holding the canonical state; clients send ops, server transforms and broadcasts to other clients. **Persistence**: snapshot every N ops + op log. **Scale**: shard by document; presence via Redis pub/sub. **Discuss**: offline editing, merge conflicts on long offline sessions, end-to-end encryption challenges.

### 8. Design a search engine for a large e-commerce catalog (1B products).
**Indexing**: ingest from product DB via CDC → enrich (synonyms, embeddings) → write to inverted index (Elasticsearch/OpenSearch/Vespa). **Sharding**: by product_id with replicas for read scale. **Ranking**: BM25 baseline + learning-to-rank model on top, with features like CTR, recency, conversion rate. **Hybrid retrieval**: keyword + vector (ANN like HNSW/FAISS) for semantic search. **Freshness**: near-real-time index (sub-minute) for new listings and price changes. **A/B testing** infra for ranking experiments.

### 9. Design a feature store serving ML models at 1M req/sec.
**Two-store architecture**: offline (Delta/Iceberg in S3) for training point-in-time joins; online (DynamoDB/Bigtable/Redis) for serving with <10 ms p99. **Registry**: features defined once (Feast), pipelines write to both stores. **Backfill jobs** populate offline history. **Streaming features** (Flink) write to both stores. **Consistency**: same logic for online and offline to avoid training-serving skew. **Governance**: feature versioning, freshness SLAs, drift monitoring.

### 10. Design a notification system (push/SMS/email) at scale.
**Architecture**: API → priority queues per channel (Kafka topics) → channel-specific workers calling external providers (FCM/APNS/Twilio/SES). **Idempotency** per (user, template, dedup_key). **User preferences** service (do-not-disturb, frequency caps). **Templating** service. **Failure handling**: provider retries with exponential backoff, fall back to alternate providers, dead-letter queue. **Observability**: delivery, open, click metrics shipped to analytics.

## Data/ML platform problems

### 11. Design a self-serve data platform for 200+ analysts.
**Components**: catalog (lineage, ownership, freshness — Unity/Purview/DataHub), semantic layer (Cube/LookML/dbt Semantic Layer) so metrics are defined once, governed access (Lake Formation/Unity Catalog row-level policies), workspace per team with cost attribution, golden datasets curated by central team. **Tooling**: standardized dbt + Airflow templates, Jupyter on managed clusters, BI tool integration. **Adoption**: tech, but mostly social — office hours, docs, golden paths.

### 12. Design a real-time fraud detection platform.
**Ingest**: transactions → Kafka. **Online features**: Flink stateful job computing rolling counts, distinct counters (HLL), velocity features → Redis (10 ms reads). **Offline features**: batch in Spark/dbt → Delta. **Model serving**: ONNX/TensorRT, A/B routed via feature flags, shadow mode for new models. **Decisioning**: rules engine (Drools-like) + ML score → block/review/allow. **Feedback loop**: chargebacks update training labels; retrain weekly. **Audit**: every decision (features, model version, output) logged for regulatory review.

### 13. Design a multi-region active-active data platform.
**Tier 1 (sources of truth)**: regional Postgres with logical replication, or globally consistent DB (CockroachDB/Spanner) for shared dimensions. **Tier 2 (lake)**: each region writes locally, cross-region replication for global tables, partition by region for local-first reads. **Conflict resolution**: idempotent writes keyed by deterministic IDs; CRDT-style merges for counters. **Failure**: region down → DNS/Global Load Balancer fails over; lagging replica accepts reads with staleness warning. **Discuss**: latency vs consistency trade-offs, write amplification, cost of cross-region egress.

### 14. Design a query optimizer / cost-based planner for a SQL engine.
**Stages**: parse → bind → logical plan (relational algebra) → rewrite rules (predicate pushdown, projection pruning, join reordering) → cost-based optimizer using statistics → physical plan (operators with chosen algorithms) → execution. **Stats**: histograms, distinct counts, correlation. **Plan caching** for repeated queries. **Adaptive execution** (re-plan during execution based on actual cardinality). **Calcite, Catalyst, Trino** are real-world reference implementations to mention.

### 15. Design a centralized data quality / observability platform.
**Sources**: row counts, schema drifts, freshness, distributions emitted from every pipeline + warehouse metadata. **Storage**: time-series of dataset metrics in a warehouse table. **Detection**: anomaly detection (rolling stats, Prophet, isolation forest), explicit assertions (Soda/Great Expectations). **Alerting**: routed by ownership from the catalog. **Lineage**: column-level so impact analysis can highlight affected dashboards. **UI**: per-dataset health score and SLA compliance. Emphasize automation — manual checks don't scale.

## Operational and organizational

### 16. How do you migrate a 5-year-old monolith to microservices safely?
**Don't blindly split**. Identify bounded contexts via DDD; pull out one context at a time (strangler fig pattern). Each extraction: introduce an API in the monolith, build the new service behind a feature flag with dual writes, shadow read to verify, cut over reads, eventually retire the monolith path. **Anti-patterns**: distributed monolith (services tightly coupled by DB), over-decomposition (more services than team can operate). Discuss data ownership, deployment cadence, observability.

### 17. How do you design for a 10× growth in 12 months?
Quantify current bottlenecks (DB, queues, cache, network), forecast which break first at 10×. Capacity plan per layer with utilization curves. Identify hard limits (single-master DB, sticky sessions, manual ops). Define a north-star architecture and a stepwise migration. Build cost forecast — at 10× scale, naïve cost can break the business. Run game days simulating 5× load to find failure modes.

### 18. How do you design for graceful degradation?
Define **criticality tiers** per feature; degrade lowest tier first under stress. Examples: timeline shows cached results when ranking is slow, recommendations fall back to popular, search returns BM25 results when LTR model is down. Use **load shedding** (drop low-priority requests), **circuit breakers** (skip slow downstreams), **bulkheads** (isolate resources). Test degradation paths regularly — silent fallbacks rot.

### 19. How do you roll out a breaking schema change across many services?
**Expand-then-contract**: (1) add new field/table; (2) backfill historical data; (3) update writers to write both old and new; (4) update readers to prefer new with fallback to old; (5) verify metrics show new path used; (6) remove writers of old; (7) remove readers of old; (8) drop old. Each step is independently deployable and revertible. Coordinate with consumers via contracts and CI checks; never break consumers without prior notice.

### 20. How do you design on-call and incident response?
Define **severity levels** with measurable triggers (S1: customer-impacting, S2: degraded, S3: internal). Page only on S1/S2; everything else into a queue for business hours. **Runbooks** per known failure mode, kept fresh by post-mortems. **Blameless post-mortems** with action items and owners. **Error budgets** (SRE-style): too many incidents → feature freeze until reliability recovers. Rotate on-call so no one burns out; reward operability work, not just features.

## Hard trade-offs senior interviewers love

### 21. CP vs AP in CAP theorem — when to pick which?
Choose **CP** when consistency is the business contract: financial ledgers, inventory of unique items (last seat on a flight), uniqueness constraints. Choose **AP** when availability beats freshness: social feeds, product catalogs, analytics. Most systems are a mix per dataset — be explicit about which choice you're making for each table/topic.

### 22. SQL vs NoSQL — when to pick which?
**SQL** for structured data with rich query patterns, joins, transactions, and consistent schema (Postgres handles enormous scale). **NoSQL** for one of: extreme write scale with simple access patterns (DynamoDB, Cassandra), schema-less document workloads (MongoDB), graph queries (Neo4j), full-text (Elastic), or time-series (Influx, Timescale). Default to SQL until you have a concrete reason; "schema flexibility" is rarely a good reason at scale.

### 23. Sync vs async APIs.
**Sync** for request/response with low latency and tight coupling (payments, login). **Async** for long-running work, fan-out, or weak coupling between teams (event-driven). Hybrid: sync API accepts the request, queues work, returns a job ID; client polls or receives webhook. Don't make everything async — it adds debugging complexity and observability burden.

### 24. Choosing between batch and streaming.
Streaming is necessary when **business value depends on minutes-fresh data** (fraud, real-time personalization, alerting). For most analytics, **batch with 1-hour or daily SLA** is cheaper, simpler, easier to test, and more accurate (full-data corrections). A hybrid (Lambda-style or Kappa-style) is often a sign of unclear requirements — push to clarify before architecting both.

### 25. Build vs buy.
**Buy** when the capability is undifferentiated infrastructure (auth, payments rails, observability, identity, email delivery) and the vendor's failure mode is acceptable. **Build** when the capability is your competitive edge or you can't accept vendor lock-in (search ranking at Google, recommendation at Netflix). Total cost of ownership (engineering + ops + opportunity cost) almost always favors buy for non-core; revisit yearly because the buy/build line moves.

### 26. Read-your-writes consistency in eventually-consistent systems.
Patterns: route the same user's reads to the same replica (session affinity), read from the primary briefly after writing, version the response and have the client wait until the version is visible, or use causal consistency tokens. Each adds cost; pick based on user perception (most "read-your-writes" pain is in the UI immediately after submit — solve it there).

### 27. How do you handle hot partitions?
**Detection**: per-partition QPS and latency dashboards. **Mitigation**: salt the key (append random suffix on writes, scatter-gather on reads), split the hot range (adaptive sharding), cache in front, batch writes, redirect to a per-key queue with a dedicated worker. Long term: redesign the access pattern that creates the hotspot.

### 28. How do you scale a stateful service horizontally?
**Sharding**: deterministic mapping from key to shard, often via consistent hashing. **Replication** within shard for HA. **Coordination**: a control plane (etcd/ZooKeeper) tracks shard membership; clients route via a router service or smart client. **Rebalance**: design for online shard moves with no downtime. The hard part is **stateful failover** — see how Kafka, Cassandra, and Spanner handle it for inspiration.
