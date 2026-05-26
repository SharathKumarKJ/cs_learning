# Apache Kafka Interview Questions (Detailed)

### 1. What is Kafka?
A distributed, partitioned, replicated commit log used as the backbone for event streaming. Producers append events to topics; consumers read them at their own pace. Designed for very high throughput, durability, and horizontal scale.

### 2. Topic, partition, offset.
A **topic** is a named log. Each topic is split into **partitions** for parallelism; partitions are ordered, append-only logs of messages. Each message has an **offset**, its position within its partition — offsets are unique only within a partition.

### 3. Brokers.
Servers that store partitions and serve producers/consumers. A Kafka cluster has multiple brokers; one is elected controller. Each partition has one leader broker (handles all reads/writes) and replicas on other brokers for fault tolerance.

### 4. Replication factor.
Number of copies of each partition across brokers (e.g. RF=3 → one leader + two followers). Tolerates RF-1 broker failures. Production minimum is usually 3.

### 5. ISR (In-Sync Replicas).
The subset of replicas caught up with the leader. Writes with `acks=all` wait for all ISRs. If ISR shrinks below `min.insync.replicas`, producers configured with `acks=all` get errors — a safety mechanism preventing data loss.

### 6. Producer `acks` setting.
**`acks=0`**: fire and forget — fastest, no durability. **`acks=1`**: leader ack only — possible loss on leader failure. **`acks=all`**: leader + all ISRs ack — strongest guarantee, slightly higher latency. Use `acks=all` for any data you care about.

### 7. Consumer groups.
A set of consumers sharing a `group.id` cooperate to read a topic — Kafka assigns each partition to exactly one consumer in the group. Adding consumers scales out reads up to the partition count; more consumers than partitions sit idle.

### 8. Rebalance.
When a consumer joins/leaves the group or partition count changes, partitions are re-assigned to consumers. During rebalance, consumption pauses. Modern cooperative rebalance protocols (CooperativeStickyAssignor) minimize disruption.

### 9. Exactly-once semantics.
Achieved with: (a) **idempotent producer** (`enable.idempotence=true`) preventing duplicates on retries within a partition; (b) **transactions** spanning multiple partitions/topics committed atomically (`transactional.id`); (c) end-to-end EOS using Kafka Streams or Kafka Connect with transactional sinks.

### 10. Compaction.
A retention strategy that keeps only the latest value per key per topic (in addition to or instead of time-based retention). Used for changelog topics, KTables in Kafka Streams, and lookup-like data where you want a complete current snapshot.

### 11. Kafka Connect.
A framework for connecting Kafka to other systems via reusable **source** (DB → Kafka) and **sink** (Kafka → S3/JDBC/Elastic) connectors. Runs in distributed mode with workers; configurable for exactly-once on supported sinks. Avoid writing custom ingest code when a connector exists.

### 12. Kafka Streams vs ksqlDB vs Flink.
**Kafka Streams**: JVM library, embeds in your app, simple stateful processing with RocksDB local state. **ksqlDB**: SQL on Kafka, easy for simple aggregations and joins. **Flink**: full distributed stream processor, far richer windowing/state/exactly-once, separate cluster — preferred for complex streaming.

---

## Intermediate Kafka

### I1. Anatomy of a Kafka message (record).
Each record has: **key** (optional, drives partitioning), **value** (payload), **timestamp** (create time or log-append time), **headers** (custom key/value metadata — trace IDs, schema IDs), **offset** (assigned by broker per partition), **partition**. The key/value are arbitrary bytes — serialization is the producer/consumer's job.

### I2. Producer flow internals.
`send()` → serialize → partitioner picks partition → record batched per partition in the **accumulator** → sender thread groups batches per broker → request sent → broker writes to leader's log → replicates → response. Tuned by `batch.size`, `linger.ms`, `compression.type`, `buffer.memory`.

### I3. Consumer poll loop.
`poll(timeout)` fetches records from assigned partitions, returns them, manages heartbeats. Records are deserialized client-side. Processing happens between polls. If processing exceeds `max.poll.interval.ms`, the consumer is kicked from the group (rebalance). Always design idempotent processing.

### I4. Default partitioner behavior.
**With key**: `murmur2(key) % numPartitions` — same key → same partition → ordering per key. **Without key**: **Sticky Partitioner** (Kafka 2.4+) — sends a whole batch to one partition, then switches; better batching than old round-robin. **Custom**: implement `Partitioner` to route by tenant_id, geography, etc.

### I5. Why partition count matters.
Partition count caps consumer parallelism (one consumer per partition per group), determines per-partition throughput (a partition is single-threaded write-side), and is **expensive to increase** later (rehashes keys → ordering breaks for existing keys). Start with 3–10× expected consumers; rarely > 100 per topic.

### I6. Log segment files.
Each partition is a sequence of **segments** on disk: `00000000000000000000.log`, `.index`, `.timeindex`, `.snapshot`. Rolled by size (`log.segment.bytes`) or time (`log.roll.ms`). Old segments are deleted (retention) or compacted. Indexes are sparse — one entry per N KB — fit in OS page cache.

### I7. Zero-copy reads.
Kafka uses `sendfile()` on Linux to ship log segments straight from the page cache to the network socket without copying through user space — the key reason Kafka brokers can serve gigabytes/sec per node with modest CPU. Disabled when SSL is on (re-encryption needed).

### I8. Page cache role.
Kafka relies on the OS page cache as its read cache — no JVM heap caching of message data. Give the broker JVM modest heap (6–8 GB) and leave the rest of RAM to the OS. Consumers tailing live data hit the cache and pay almost no disk IO.

### I9. Retention configs.
`retention.ms` / `retention.bytes` — drop old segments by time/size. `cleanup.policy=delete|compact|compact,delete`. `delete.retention.ms` — how long tombstones live in compacted topics. `min.cleanable.dirty.ratio` — when compaction kicks in. `segment.ms` — force-roll segment so retention can act.

### I10. Producer batching trade-offs.
`linger.ms=0` → fire ASAP, small batches, low latency, high overhead. `linger.ms=5-20`, `batch.size=64-256KB` → wait briefly, big batches, much higher throughput, slight latency. Compression amplifies the benefit. Tune to your SLA.

### I11. Compression options.
**none** (fastest CPU), **gzip** (high ratio, slow), **snappy** (balanced), **lz4** (fast, decent ratio), **zstd** (best ratio + fast — modern default). Set per-topic or per-producer. Compressing a whole batch (not message) is what makes Kafka network-efficient.

### I12. Acks vs durability matrix.
| Config | Producer waits for | Loss possible? |
|---|---|---|
| `acks=0` | nothing | yes (broker crash mid-send) |
| `acks=1` | leader | yes (leader crash before replication) |
| `acks=all` + `min.insync.replicas=2` | leader + 1 follower | only if all ISRs die simultaneously |
| `acks=all` + `min.insync.replicas=RF` | all replicas | virtually no loss but lower availability |

### I13. Consumer offset commit strategies.
1. **Auto commit** (`enable.auto.commit=true`): every `auto.commit.interval.ms` — easy, can lose or duplicate.
2. **Sync manual** (`commitSync()` after processing): safe, blocking.
3. **Async manual** (`commitAsync()` + occasional sync): fast, retries on the next commit.
4. **Commit per record** (in stateful sinks): fine-grained but slow.
For at-least-once: process *then* commit.

### I14. Consumer group rebalance protocols.
**Eager (legacy)**: stop-the-world — all consumers revoke partitions, then re-assign. Long pauses.
**Cooperative Sticky (KIP-429, default since 2.4)**: incremental — only partitions that need to move are revoked. Much less disruption. Always prefer.

### I15. Static membership.
`group.instance.id=my-instance-1` makes a consumer survive short disconnects without triggering a rebalance — coordinator waits `session.timeout.ms` for it to come back. Saves big rebalances on rolling restarts of stateful consumers.

### I16. Reading from a specific point.
`seek(partition, offset)` for exact offset; `seekToBeginning` / `seekToEnd`; `offsetsForTimes({tp: ts})` to start from a timestamp. Used for replay, debugging, time-bounded reprocessing. Combine with a fresh `group.id` to not affect production.

### I17. Internal topics.
`__consumer_offsets` (offset storage, compacted). `__transaction_state` (transaction coordinator state). `__cluster_metadata` (KRaft metadata log). Connect uses `connect-offsets`, `connect-configs`, `connect-status`. Streams creates `<app>-<store>-changelog` / `-repartition` topics.

### I18. Replication mechanics.
Each partition has a **leader** (handles reads/writes) and **followers** (fetch from leader). Followers' `LEO` (Log End Offset) chases the leader; **HW** (High Watermark) = min LEO across ISRs and is what consumers see. Only committed (≤ HW) messages are exposed to consumers.

### I19. Leader election.
Controller (KRaft quorum or ZK-elected broker) picks the new leader from ISRs when the current leader fails. `unclean.leader.election.enable=false` (default since 2.0) prevents picking out-of-sync replicas → safer at cost of brief unavailability.

### I20. min.insync.replicas vs replication factor.
`replication.factor=3, min.insync.replicas=2` is the prod sweet spot: tolerate 1 failure with full durability; refuse writes if 2 brokers down (preserving safety). Setting `min.insync.replicas = RF` is fragile — any single broker outage halts writes.

### I21. Producer idempotence in detail.
`enable.idempotence=true` (default in modern Kafka) attaches a producer ID + per-partition sequence number to each batch. The broker rejects duplicates and out-of-order batches → exactly-once *per partition* within a producer session. Adds almost no overhead.

### I22. Transactional producer.
For atomic writes across partitions/topics:
```java
producer.initTransactions();
producer.beginTransaction();
producer.send(record1); producer.send(record2);
producer.sendOffsetsToTransaction(offsets, consumerGroup);
producer.commitTransaction();
```
Consumers with `isolation.level=read_committed` skip uncommitted/aborted txns. Foundation of EOS in Streams.

### I23. Headers.
Custom metadata per record (`Headers headers = record.headers()`). Standard uses: schema ID (Confluent), trace IDs (OpenTelemetry W3C `traceparent`), tenant ID, source system. Cheap to add; powerful for routing and observability.

### I24. Schema management with Schema Registry.
Producer registers schema (Avro/Protobuf/JSON Schema) → gets ID → prepends ID + serialized payload. Consumer reads ID → fetches schema → deserializes. Registry enforces compatibility rules (`BACKWARD`, `FORWARD`, `FULL`) preventing breaking changes. Common reg: Confluent, Apicurio, AWS Glue.

### I25. Kafka Connect modes.
**Standalone**: one process, single config file, dev only. **Distributed**: cluster of workers, REST API, fault-tolerant, balances connector tasks. Producers/consumers internally; you just configure connectors via JSON. Many open-source + Confluent Hub connectors (JDBC, S3, Elastic, Debezium, etc.).

### I26. CDC with Debezium.
A source connector that reads database WAL/binlog and produces change events (`op: c/u/d/r`, `before`, `after`, `source` metadata) to Kafka. Powers near-real-time replication from OLTP to lake/warehouse. Snapshots + ongoing log tailing; resumes via stored offsets.

### I27. Kafka Streams essentials.
JVM library: KStream (record stream), KTable (changelog, latest per key), GlobalKTable (replicated per instance). DSL: `mapValues`, `filter`, `groupByKey`, `aggregate`, `join`, `windowedBy`. Stateful ops use RocksDB locally + changelog topics for fault tolerance.

### I28. KSQLDB / ksqlDB.
SQL on top of Kafka Streams. Define streams/tables, write continuous queries, push-and-pull queries, materialized state. Great for simple aggregations and ETL without writing JVM code. Limitations for complex windowing → Flink fits better.

### I29. Quotas.
Producer/consumer/connector rate limits per client ID, user, or IP. Configured dynamically:
```
kafka-configs --alter --add-config 'producer_byte_rate=10485760' --entity-type clients --entity-name app1
```
Prevents one noisy tenant saturating the cluster.

### I30. Multi-tenancy.
ACLs per user/topic/group, quotas per client, naming conventions (`team.app.entity`), separate Connect clusters per team, Schema Registry per env. Use OAuth/SASL with central IdP. Big orgs run multiple clusters partitioned by criticality + region.

### I31. Reading Kafka logs and metrics.
`kafka-topics --describe`, `kafka-consumer-groups --describe` (lag!), `kafka-log-dirs --describe` (disk), `kafka-configs --describe`. JMX metrics: `BytesIn/OutPerSec`, `MessagesInPerSec`, `UnderReplicatedPartitions`, `RequestQueueSize`, `RequestHandlerAvgIdlePercent`, `OfflinePartitionsCount`, `IsrShrinksPerSec`. Scrape with Prometheus JMX exporter.

### I32. Tools you should know.
**CLI**: `kafka-console-producer/consumer`, `kafka-topics`, `kafka-consumer-groups`, `kafka-configs`, `kafka-dump-log`, `kafka-reassign-partitions`. **UIs**: AKHQ, Conduktor, Kafka UI (Provectus), Confluent Control Center. **Tools**: `kcat` (formerly `kafkacat`) for everything CLI; `kminion`/`Burrow` for lag.

### I33. Common intermediate gotchas.
- Increasing partition count rehashes — ordering for old keys silently breaks.
- Default `auto.offset.reset=latest` skips data after consumer restart with no committed offset.
- Long GC pauses cause session timeouts → rebalance storms.
- Sending a huge message → broker rejects (`message.max.bytes`); update producer + broker + consumer.
- Compacted topic with no key → no-op compaction, log grows unbounded.

---

## Advanced Kafka

### 13. KRaft vs ZooKeeper.
Classic Kafka used ZooKeeper for metadata and controller election. **KRaft** (Kafka Raft, KIP-500) replaces ZooKeeper with an internal Raft quorum of controller nodes — simpler ops, faster failover, higher partition counts. Production default in Kafka 3.5+; ZK fully removed in 4.0.

### 14. Partitioning strategies.
Producer decides partition: (a) explicit partition number, (b) key hash (default `murmur2` — same key → same partition → ordering), (c) round-robin / sticky for null-key messages. Choose key carefully: too coarse → hot partitions; too fine → no co-location for stateful ops.

### 15. Log retention vs compaction.
**Time/size retention** (`retention.ms`, `retention.bytes`) deletes old segments. **Compaction** (`cleanup.policy=compact`) keeps latest value per key. Combine `compact,delete` for "keep latest per key, but drop tombstones older than X". Tombstone = null value, marks key for deletion.

### 16. Consumer offsets.
Stored in internal `__consumer_offsets` topic (compacted). Commit modes: **auto-commit** (every `auto.commit.interval.ms` — risk of skipping/redelivering), **manual sync** (`commitSync()` — slow, safe), **manual async** (`commitAsync()` — fast, may lose on crash). Commit *after* processing for at-least-once.

### 17. Delivery semantics in practice.
**At-most-once**: commit before processing → loss on crash. **At-least-once**: process then commit → duplicates on retry — make consumer idempotent. **Exactly-once**: idempotent producer + transactions + `read_committed` isolation + `isolation.level=read_committed` consumer + atomic offset commit within transaction.

### 18. Transactions internals.
`initTransactions()` → `beginTransaction()` → produce + `sendOffsetsToTransaction()` → `commitTransaction()`. Transaction coordinator writes markers to participating partitions; consumers with `read_committed` skip uncommitted. Required for EOS in Streams and Connect sinks.

### 19. Producer tuning for throughput.
`batch.size` (16KB default → 64–256KB), `linger.ms` (0 → 5–20ms to batch), `compression.type` (`lz4`/`zstd`), `buffer.memory`, `max.in.flight.requests.per.connection=5` (still safe with idempotence). Trade latency for throughput; benchmark with `kafka-producer-perf-test.sh`.

### 20. Consumer tuning.
`max.poll.records`, `fetch.min.bytes`, `fetch.max.wait.ms` to batch fetches. `max.poll.interval.ms` — if processing exceeds it, consumer is kicked from group. Heartbeat thread separate (`heartbeat.interval.ms`, `session.timeout.ms`). Use `pause()`/`resume()` for backpressure.

### 21. Schema management.
**Confluent Schema Registry** (or Apicurio, AWS Glue Schema Registry) stores Avro/Protobuf/JSON-Schema versions. Producers register schema, get ID, prepend it to messages; consumers fetch by ID. Enforces compatibility rules (BACKWARD, FORWARD, FULL) on register to prevent breaking changes.

### 22. Avro vs Protobuf vs JSON.
**Avro**: compact, schema-required, great Hadoop/Kafka ecosystem, dynamic typing via schema. **Protobuf**: very compact, typed code generation, language-friendly, easier evolution. **JSON Schema**: human-readable, large size, slower — fine for low volume. For Kafka at scale: Avro or Protobuf.

### 23. Mirroring & multi-region.
**MirrorMaker 2** (built on Connect) replicates topics, configs, ACLs, and offsets across clusters — active/passive or active/active. **Confluent Replicator** is the proprietary equivalent. Cluster Linking (Confluent) avoids re-publishing — preserves offsets natively.

### 24. Tiered storage.
Hot data on broker disks, cold segments offloaded to S3/GCS/Azure Blob (Confluent, Apache 3.6+ KIP-405). Decouples storage from compute, enables long retention cheaply. Reads from cold tier are slower — design consumers accordingly.

### 25. Security.
**Authentication**: SASL/PLAIN, SASL/SCRAM, mTLS, OAUTHBEARER. **Authorization**: ACLs per topic/group/cluster, or RBAC in Confluent. **Encryption**: TLS in transit; broker-side encryption at rest via disk encryption or KMS-backed (Confluent). Disable PLAINTEXT in production.

### 26. Common production issues.
**Hot partition** (bad key choice) → uneven load. **Rebalance storms** from frequent consumer joins/leaves or long processing. **Under-replicated partitions** → broker issues; alert on `UnderReplicatedPartitions` JMX. **Disk-full** → broker dies; monitor log dirs. **Lag** → scale consumers or speed processing.

### 27. Monitoring.
JMX metrics scraped via Prometheus JMX exporter or Datadog agent. Key metrics: `MessagesInPerSec`, `BytesIn/OutPerSec`, `UnderReplicatedPartitions`, `ActiveControllerCount=1`, `RequestHandlerAvgIdlePercent`, consumer lag (`kafka-consumer-groups.sh --describe` or Burrow / `kminion`).

### 28. Lag handling strategies.
Scale consumers (up to partition count), increase partitions (irreversible — rehashes keys), parallelize processing inside consumer (careful with ordering), batch downstream writes, use compaction on consumer side, or shed load (DLQ for poison pills).

### 29. Dead letter queues.
A separate topic for messages that fail processing repeatedly. Consumer catches exception → publishes to DLQ with headers (original topic, offset, error, stack), commits offset, moves on. Kafka Connect has built-in DLQ config. Always cap retries to avoid infinite loops.

### 30. Kafka vs Pulsar vs Kinesis vs RabbitMQ.
**Kafka**: throughput king, log semantics, durable replay, partition ordering. **Pulsar**: separates compute/storage (BookKeeper), tiered storage native, multi-tenant. **Kinesis**: AWS-managed Kafka-lite, simpler but limited. **RabbitMQ**: classical message broker, complex routing, lower throughput, no replay.

### 31. When *not* to use Kafka.
Tiny workloads (overhead), low-latency request/reply (use gRPC), workflows needing complex routing (use RabbitMQ), strict FIFO global ordering (Kafka orders only per partition), or when ops cost of a cluster outweighs benefits — managed (MSK, Confluent Cloud) helps.
