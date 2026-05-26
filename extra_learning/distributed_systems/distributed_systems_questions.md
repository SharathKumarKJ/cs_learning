# Distributed Systems Interview Questions — Basic to Advanced (Detailed)

A focused question bank for data and backend engineers covering distributed-systems theory, consistency models, consensus, replication, partitioning, fault tolerance, and real-world patterns.

---

## 1. Fundamentals

### 1. What is a distributed system?
A collection of independent computers that appear as one coherent system to users. Communicate via messages over a network. Characterized by partial failure (any subset of nodes/links can fail), concurrency, and lack of a global clock.

### 2. Why is distributed computing hard?
Networks can drop, delay, duplicate, reorder messages. Nodes can crash, slow down, or lie. Clocks drift. Partial failures are the norm. Most "obvious" assumptions from single-machine programming break — see "Fallacies of Distributed Computing" (Peter Deutsch).

### 3. The 8 fallacies of distributed computing.
1) The network is reliable. 2) Latency is zero. 3) Bandwidth is infinite. 4) The network is secure. 5) Topology doesn't change. 6) There is one administrator. 7) Transport cost is zero. 8) The network is homogeneous. Every production outage involves believing at least one.

### 4. Scalability — vertical vs horizontal.
**Vertical**: bigger machine (more CPU/RAM). Limited, expensive, single point of failure. **Horizontal**: add more machines. Cheaper per unit, fault-tolerant, but introduces distributed-systems problems. Modern systems scale horizontally; ClickHouse, Kafka, Cassandra, Spark, Snowflake all do.

### 5. Throughput vs latency.
**Throughput** = work done per unit time (req/sec, MB/sec). **Latency** = time per individual request. Optimizations often trade them: batching ↑ throughput ↓ latency; smaller batches ↓ latency ↑ overhead. Always quote p50/p95/p99/p999 — averages hide tail latency.

### 6. Concurrency vs parallelism.
**Concurrency**: dealing with multiple things at once (structure). **Parallelism**: doing multiple things at once (execution). A single-core async server is concurrent but not parallel; a multi-core data-parallel Spark job is both.

---

## 2. CAP, PACELC, Consistency

### 7. CAP theorem.
In the presence of a network **P**artition, you must choose between **C**onsistency and **A**vailability. **CP** systems (HBase, ZooKeeper, Spanner): refuse requests during partition to stay consistent. **AP** systems (Cassandra, Dynamo, Riak): keep serving, may return stale data. *Cannot* have all three; without partitions you can have both C and A.

### 8. PACELC.
Refinement of CAP: if **P**artition, choose **A** or **C**; **E**lse (normal ops), choose **L**atency or **C**onsistency. Dynamo is **PA/EL**, Spanner is **PC/EC**, MongoDB is **PA/EC** by default. More honest description of real systems.

### 9. Consistency models.
From strongest to weakest:
1. **Strict / Linearizable**: looks like single copy executing ops in real-time order.
2. **Sequential**: all nodes see same order, may not match real time.
3. **Causal**: causally-related ops seen in order; concurrent may reorder.
4. **Read-your-writes / Monotonic / Session** guarantees: convenient subsets.
5. **Eventual**: replicas converge if writes stop.

### 10. Linearizability.
The "single up-to-date copy" illusion. Each op appears to take effect atomically at some point between its start and end. ZooKeeper reads aren't linearizable by default (`sync` makes them so); Spanner reads are; many key-value stores are CAS-linearizable for single-key ops.

### 11. Eventual consistency.
Given no new writes, all replicas eventually return the same value. In practice useful only with conflict resolution (last-writer-wins by timestamp, CRDTs, vector clocks, application-level merges). DynamoDB, S3 (now strongly consistent), Cassandra default behavior.

### 12. Causal consistency.
If write A happens-before write B, every reader observes A before B. Concurrent writes may be observed in any order. Often enough for collaborative apps; cheaper than linearizability. COPS, Bayou, AntidoteDB implement it.

### 13. Strong vs strong eventual consistency.
**Strong**: linearizable / sequential — needs coordination, hurts availability and latency. **Strong eventual** (CRDTs): replicas with the same set of updates *deterministically* converge without coordination. Trade-off: limited to operations that commute.

### 14. Read repair / hinted handoff / anti-entropy.
Mechanisms in eventually consistent stores to converge replicas:
- **Hinted handoff**: a temporarily-down replica's writes are buffered by a peer and forwarded later.
- **Read repair**: on a read, mismatches between replicas are reconciled.
- **Anti-entropy**: background process (Merkle-tree exchange) catches what live repair missed.

---

## 3. Time, Order, Clocks

### 15. Why is "now" hard in distributed systems?
Physical clocks drift, NTP only gives ms-precision, machines crash and restart. Two events on two machines can't be reliably ordered by wall clock. We use **logical clocks** or **causal clocks** instead — except when you have GPS+atomic clocks (Spanner's TrueTime).

### 16. Lamport timestamps.
Each process keeps counter `c`; on local event `c++`; on send, attach `c`; on receive, set `c = max(local, received) + 1`. Property: if A causally precedes B, `c(A) < c(B)`. Establishes a partial order; ties broken by process ID give total order (but loses causality info).

### 17. Vector clocks.
Each node keeps a vector of counters, one per node. On local event, increment own slot; on send/receive, merge by element-wise max. Two events are concurrent iff neither vector dominates the other — captures concurrency precisely. Used by Dynamo, Riak for detecting conflicting writes.

### 18. TrueTime (Spanner).
Google Spanner exposes time as an interval `[earliest, latest]` of size ~ms, backed by GPS + atomic clocks. Transactions wait out the uncertainty (`commit_wait`) so external consistency is preserved across data centers. Enables globally-consistent transactions.

### 19. Hybrid Logical Clocks (HLC).
Combine wall clock (for human-readable ordering) with logical counter (to preserve happened-before). Used by CockroachDB, YugabyteDB, MongoDB. Tolerates clock drift up to bounded skew.

---

## 4. Replication

### 20. Why replicate?
- **Fault tolerance** — survive node failures.
- **Latency** — serve from a nearby replica.
- **Throughput** — scale reads.
- **Disaster recovery** — survive a region loss.
Trade-offs in write cost, consistency, and operational complexity.

### 21. Single-leader vs multi-leader vs leaderless.
- **Single-leader** (Postgres replicas, MySQL): simple, linearizable writes, leader is bottleneck and SPoF.
- **Multi-leader** (BDR, CouchDB): write anywhere, but conflicting writes need resolution; useful for multi-region.
- **Leaderless** (Dynamo, Cassandra): any replica accepts writes; reads/writes go to a quorum; conflicts resolved on read.

### 22. Synchronous vs asynchronous replication.
**Sync**: write returns only after follower acks — strong durability, slow tail latency. **Async**: returns immediately, follower catches up — fast, may lose data on leader failure. **Semi-sync** (MySQL): at least one follower must ack — common pragmatic choice.

### 23. Quorum reads/writes (R + W > N).
With N replicas, write to W, read from R; if `R + W > N`, every read sees the latest write — strong consistency for that key. Common: `N=3, W=2, R=2`. Tunable: `W=N, R=1` (read-fast), `W=1, R=N` (write-fast). Dynamo-style.

### 24. Sloppy quorum & hinted handoff.
If a node is down, write to other available nodes (the "sloppy" part) and hint that the write should be forwarded later. Trades consistency for availability; pure quorum would refuse the write.

### 25. Replication lag problems.
**Read-your-writes**: route user to leader after a write. **Monotonic reads**: stick to one replica per session. **Consistent prefix**: ensure causal writes are visible together. Cure: stickiness + careful routing or use synchronous replication for the writes you care about.

### 26. Conflict resolution.
Strategies: **last-writer-wins** (by timestamp — lossy), **multi-value** (return all conflicting versions, let app resolve), **CRDTs** (deterministic merge), **operational transformation** (Google Docs), **application-level** (custom merge functions). LWW is easy and dangerous; CRDTs are correct but constrained.

---

## 5. Partitioning / Sharding

### 27. Why partition?
Single node can't hold all data or handle all traffic. Split data across nodes ("shards") so each handles a subset. Combined with replication for HA. Required for any system above a few TB or a few thousand ops/sec sustained.

### 28. Partitioning strategies.
- **Hash partitioning**: `hash(key) % N` → uniform distribution, no range queries.
- **Range partitioning**: ordered by key range → fast range scans, risk of hot spots.
- **Composite**: hash on tenant, range on time within tenant.
- **Random**: uniform but no locality.
Choose based on query patterns.

### 29. Consistent hashing.
Map keys and nodes onto a ring; key goes to next node clockwise. Adding/removing a node moves only `1/N` keys (vs almost all keys with `mod N`). Used by Dynamo, Cassandra, memcached clients, Envoy, many caches and CDNs.

### 30. Virtual nodes (vnodes).
Each physical node owns many small ring positions. Smoothens skew and makes rebalancing easier (small chunks move). Cassandra, ScyllaDB, Riak all use vnodes (commonly 256/node).

### 31. Rebalancing.
Adding/removing capacity = moving shards/vnodes between nodes. Done online while serving traffic. Key challenges: throttle to avoid overwhelming network, maintain correctness during the move (forwarding / dual-read), update routing tables. Pathological case: rebalancing during a partial outage → death spiral.

### 32. Hot partitions.
A single shard receives disproportionate traffic — bad key choice (sharding by `tenant_id` when one tenant is 80% of load), bad temporal locality (sharding by date, today's date is hot), celebrity problem. Fixes: choose better key, add a salt prefix, cache the hot key, replicate the hot shard.

### 33. Routing requests to partitions.
Three common designs:
1. **Client-side** routing: client knows topology, picks shard.
2. **Routing tier** (proxy / coordinator): client hits any node, it forwards.
3. **Gossip-based** discovery: cluster shares membership; client cache + retry on miss.
Cassandra uses gossip + client; HDFS uses NameNode (proxy); Vitess uses vtgate.

---

## 6. Consensus & Coordination

### 34. Consensus problem.
Multiple nodes must agree on a single value even if some fail. Solved by **Paxos**, **Raft**, **Multi-Paxos**, **Viewstamped Replication**, **PBFT** (Byzantine). Underpins leader election, replicated state machines, distributed locks, configuration management.

### 35. FLP impossibility.
Fischer-Lynch-Paterson (1985): no deterministic consensus algorithm guarantees termination in an asynchronous network with even one faulty process. Real systems work around it with **randomization** or **partial synchrony** assumptions (timeouts).

### 36. Paxos.
Two-phase: (Prepare → Promise) elects a proposal number, (Accept → Accepted) commits a value. Notoriously hard to understand and implement. Multi-Paxos optimizes the common case by keeping a stable leader. Used in Chubby, Spanner.

### 37. Raft.
Designed to be understandable. Strong leader handles all writes; replicates a log to followers; commits when majority ack. Three sub-problems clearly separated: leader election, log replication, safety. Used by etcd, Consul, TiKV, CockroachDB, MongoDB (oplog-based), ClickHouse Keeper.

### 38. Quorum & majority.
N nodes can tolerate `floor((N-1)/2)` failures while preserving majority quorum `(N/2)+1`. N=3 tolerates 1; N=5 tolerates 2. Even numbers add cost without proportional fault tolerance — clusters are typically 3 or 5.

### 39. Leader election.
A subproblem of consensus. Raft uses randomized election timeouts to avoid split votes. ZK uses Zab. Bully algorithm and ring-based approaches exist but are mostly historical. In production, lean on etcd / ZK / Keeper.

### 40. ZooKeeper / etcd / Consul.
General-purpose coordination services. Provide linearizable key-value, watches, ephemeral nodes (sessions), distributed locks (with TTL), leader election primitives. Different APIs but same conceptual building blocks. Don't store large data — they're for metadata only.

### 41. Distributed locks — pitfalls.
Locks acquired via leases; if the holder pauses (GC, network glitch) past the TTL, another acquires it — two holders simultaneously. Solution: **fencing tokens** — monotonically increasing token returned with the lock; downstream rejects writes with older tokens. Without fencing, Redlock / ZK locks alone are not safe (Kleppmann's critique).

---

## 7. Failure Detection & Resilience

### 42. Failure detectors.
A "perfect" detector that distinguishes crashed from slow is impossible in async networks. Real systems use **heartbeats** with timeouts (φ-accrual is a refined variant). False positives (marking a slow node dead) destabilize; false negatives delay recovery. Tune carefully.

### 43. Network partitions.
Subset of nodes can't talk to another subset. May be asymmetric (A can reach B but not back). Cluster must avoid **split-brain** (both halves act as leader) — solved by quorum requirements. Test with chaos tools (Toxiproxy, Chaos Mesh, Jepsen).

### 44. Gray failures.
Failure modes that aren't crashes: slow disk, partial packet loss, GC pause, kernel bug, half-open TCP connections. The most damaging because metrics still look "up". Detect via end-to-end probes, percentile latency alerts, application-level health checks, not just process liveness.

### 45. Timeouts.
Every network call must have a timeout. Without it, a hung dependency stalls your thread pool / goroutines, cascading the failure. Layered timeouts: connect, read, total deadline (use context). Set based on dependency's p99 + slack — not generous "minutes" defaults.

### 46. Retries — when and how.
Only retry **safe (idempotent)** operations. Use **exponential backoff with jitter** to avoid synchronized retries (thundering herd). Cap retries; classify errors: retry on transient (5xx, timeout), not on permanent (4xx, validation). Track retry budget per dependency.

### 47. Circuit breakers.
After N consecutive failures, stop calling a dependency for a cooldown period; periodically try a probe ("half-open"). Protects the caller and the failing dependency from cascading collapse. Libraries: Hystrix (legacy), resilience4j, sony/gobreaker.

### 48. Bulkheads.
Isolate resources so a failure in one part doesn't sink the whole. E.g., separate connection pools per downstream, separate thread pools per critical/non-critical work, separate K8s nodes per latency-sensitive workload. Ship analogy: a leak in one compartment doesn't sink the ship.

### 49. Backpressure.
When a consumer can't keep up, signal producers to slow down rather than collapse under load. Implementations: bounded queues that block (or drop), TCP-level (`flow control`), reactive streams, Kafka pause/resume, HTTP 429 + `Retry-After`. Unbounded queues hide the problem until OOM.

### 50. Idempotency.
Same request applied N times = applied once. Critical for safe retries. Implementations: idempotency keys (client-generated UUID), natural primary keys (`order_id`), conditional writes (`If-Match: etag`), deduplication tables / TTLs. Without it, retries cause duplicates.

### 51. Graceful degradation.
When subsystems fail, degrade rather than collapse: serve cached data, skip personalization, disable non-essential features, return partial results. Better than 500. Tag features with criticality and design fallback paths up front.

### 52. Chaos engineering.
Continuously inject failures (kill pods, drop packets, slow disks) in production-like envs to verify resilience. Tools: Chaos Mesh, Litmus, Gremlin, Netflix's Chaos Monkey, AWS Fault Injection Simulator. Couple with game days and runbooks.

---

## 8. Messaging & Streaming

### 53. Delivery semantics.
**At-most-once**: send and forget — may lose. **At-least-once**: retry on failure — may duplicate. **Exactly-once**: complex, requires idempotent producer + transactional commits + idempotent consumer. Most pragmatic prod systems do at-least-once + idempotent consumers.

### 54. Ordering.
Per-partition / per-queue ordering is common (Kafka, Kinesis). Global ordering requires a single partition or transactional engine — bottleneck. Choose partition key so order-sensitive events land in the same partition (`user_id` typically).

### 55. Pub-sub vs queue.
**Queue** (SQS, RabbitMQ direct): each message goes to one consumer. **Pub-sub** (Kafka, SNS, Pulsar): each subscriber gets a copy. Kafka with consumer groups acts like both: across groups it's pub-sub, within a group it's a queue.

### 56. Outbox pattern.
To reliably publish events after a DB write, in the same transaction insert the event into an `outbox` table; a separate process reads outbox and publishes to Kafka, marking sent rows. Avoids the dual-write problem (DB commits, Kafka send fails, or vice versa).

### 57. Saga pattern.
Long-running multi-service transaction modeled as a sequence of local transactions + compensating actions. Two flavors: **orchestrated** (central coordinator) or **choreographed** (event-driven). Trades ACID for eventual consistency across services.

### 58. Two-phase commit (2PC) — and why we avoid it.
Coordinator asks all participants to "prepare", then "commit" if all ready. Provides atomicity but blocks indefinitely if coordinator crashes after prepare. Hurts availability and latency. In microservices, sagas + idempotency are preferred.

### 59. Event sourcing.
Persist every state change as an immutable event; current state = fold over events. Benefits: full audit log, easy temporal queries, replayability. Costs: event schema versioning, snapshotting for performance, more complex querying (use CQRS).

### 60. CQRS.
Command Query Responsibility Segregation: separate write model (commands → events) from read model (denormalized views). Often paired with event sourcing. Reads can be optimized for queries; writes for consistency.

---

## 9. Storage, Transactions, Isolation

### 61. ACID — definitions.
**Atomicity** (all or nothing), **Consistency** (invariants preserved), **Isolation** (concurrent txns don't interfere), **Durability** (committed survives crash). Distributed ACID across services is hard; ACID within a single DB is standard.

### 62. Isolation levels.
**Read Uncommitted** (dirty reads), **Read Committed** (default in PG/Oracle), **Repeatable Read** (snapshot in MySQL InnoDB), **Snapshot Isolation** (no write skew protection), **Serializable** (strongest). Each level prevents specific anomalies. Pick based on the anomalies your app can tolerate.

### 63. Snapshot isolation & write skew.
SI gives each txn a consistent snapshot at start time. Avoids dirty reads, non-repeatable reads, phantoms — but allows **write skew**: two txns read overlapping data, write disjoint things, jointly violate an invariant. Postgres "Serializable Snapshot Isolation" (SSI) detects and aborts such txns.

### 64. MVCC.
Multi-Version Concurrency Control: writes create new row versions; readers see the version visible at their snapshot. Avoids read-write locks, scales reads. Implemented by Postgres, MySQL InnoDB, Oracle, CockroachDB, etc. Trade-off: garbage collection of dead versions (VACUUM in Postgres).

### 65. Distributed transactions in NewSQL.
Spanner, CockroachDB, YugabyteDB, TiDB provide ACID across shards via Raft/Paxos + 2PC or variations. CockroachDB uses **parallel commits** to reduce latency. Spanner uses **TrueTime** for external consistency. Performance significantly worse than single-shard txns — design for locality.

### 66. WAL (Write-Ahead Log).
All changes go to the log before mutating the data files. Recovery replays the log. Foundation of durability for most DBs (Postgres, MySQL, RocksDB, Kafka segments). Replication often = shipping the WAL.

### 67. LSM trees vs B-trees.
**B-tree**: in-place updates; balanced reads and writes (PG, MySQL, SQL Server). **LSM (Log-Structured Merge)**: writes go to memory, flushed to sorted runs on disk, compacted in background; write-optimized (Cassandra, RocksDB, ClickHouse). LSMs have write/read/space amplification trade-offs.

---

## 10. Caching, CDNs, Load Balancing

### 68. Cache patterns.
**Cache-aside (lazy)**: app reads cache, on miss reads DB and populates cache. **Read-through / Write-through**: cache library reads/writes DB on app's behalf. **Write-back**: writes to cache, async to DB (risk of loss). **Write-around**: writes bypass cache. Most apps: cache-aside.

### 69. Cache invalidation.
"There are only two hard things in CS: cache invalidation and naming things." Strategies: TTL + jitter (simplest, lets stale data exist for TTL), explicit invalidation on write (race conditions), event-driven invalidation (CDC → cache), versioned cache keys (avoid invalidation entirely).

### 70. Thundering herd.
Many clients miss cache simultaneously and all hit DB. Fixes: **singleflight** (one in-flight request per key, others wait), TTL jitter, probabilistic early refresh ("refresh ahead"), request coalescing at the edge.

### 71. Load balancing algorithms.
**Round-robin** (simple, ignores load), **least-connections** (good for long-lived conns), **weighted** (heterogeneous servers), **consistent hashing** (stickiness for caches), **EWMA/least-latency** (Envoy), **power-of-two-choices** (random pick of 2, send to less loaded — surprisingly effective).

### 72. L4 vs L7 load balancing.
**L4** (TCP/UDP, AWS NLB): fast, opaque, can't read HTTP. **L7** (HTTP, AWS ALB, Envoy, NGINX): can route by path/header, do retries, observability. Many production stacks use both: L4 at the edge, L7 between services.

### 73. CDN.
Distributed cache at the edge for static and increasingly dynamic content. Cuts latency and origin load. Cache-control headers and origin shielding matter. Modern CDNs (Cloudflare, Fastly) also run compute at the edge (Workers, Compute@Edge).

### 74. Anycast & geo-routing.
**Anycast**: same IP announced from many locations; BGP routes user to nearest. Used by big DNS/CDN providers. **Geo-DNS**: returns different IPs based on resolver region. Combined with health checks for failover.

---

## 11. Observability & SRE

### 75. Three pillars of observability.
**Logs** (events with context), **metrics** (numerical time series), **traces** (per-request causal chains across services). Modern OTel-based stacks combine them. Together they let you answer "what is happening" + "why" without code changes.

### 76. SLI, SLO, SLA.
**SLI** = measurement (request success rate, p99 latency). **SLO** = target (99.9% successful over 30 days). **SLA** = contract with consequences. Drive on-call priorities and design trade-offs via **error budgets** (1 - SLO = budget for failure / risky changes).

### 77. Distributed tracing.
Each request carries a `trace_id` and span ids; instrumentation records spans (operation, time, attributes) and ships them to a backend (Tempo, Jaeger, Honeycomb). Propagated via headers (`traceparent`). Essential to debug latency in microservices.

### 78. Logging best practices.
Structured (JSON), include `trace_id` / `request_id`, leveled, avoid PII, sampled if high-volume. Centralize (Loki, Elastic, CloudWatch). Don't log on every line — log decisions ("processed 1000 events", not "got event 1, got event 2, …").

### 79. RED & USE methods.
**RED** for services: Rate, Errors, Duration. **USE** for resources: Utilization, Saturation, Errors. Use both to dashboard everything: services with RED, hosts/disks/queues with USE.

### 80. Postmortems.
Blameless write-ups after incidents: timeline, impact, root cause, contributing factors, action items, what went well. Stored centrally; reviewed; action items tracked to completion. The point is learning, not punishment.

---

## 12. Real-World Patterns

### 81. Sharding by tenant.
Multi-tenant SaaS: assign each tenant to a shard; route requests by tenant id. Pros: simple, isolated. Cons: skew (big tenants), cross-tenant queries hard. Mitigate with re-sharding tools and "shadow" big tenants to dedicated shards.

### 82. Read replicas for scaling reads.
Add async followers, route read traffic via a proxy or app-level routing. Beware read-your-writes for the user who just wrote — route their reads to the leader for a short window.

### 83. Caching hot keys.
Identify hot keys via percentile of access frequency; replicate them to multiple cache nodes; consider **probabilistic caching** to avoid all clients seeing the same eviction at once. Re-evaluate continuously — hotness shifts.

### 84. Multi-region active-active.
Read locally; writes either route to a primary region (active-passive at write tier) or do conflict resolution (true active-active with CRDTs or LWW). Trade consistency vs latency. Spanner / CockroachDB give you SQL active-active with consensus latency.

### 85. Disaster recovery — RTO / RPO.
**RTO** = how long to recover. **RPO** = how much data you can lose. Tier services by criticality. Strategies: backup + restore (slow), warm standby (faster), active-passive replication (minutes RPO), active-active (zero or near-zero RPO).

### 86. Capacity planning.
Forecast load (organic + features), measure current saturation (queue depths, CPU, p99), plan headroom (typically 30–50%), load-test, autoscale where elastic. Re-evaluate quarterly. The cost of being under-provisioned is paged engineers and customer outages.

### 87. Data locality.
Co-locate computation with data — Spark executors on HDFS nodes, ClickHouse joining co-sharded tables, gRPC services in the same region/zone as their DBs. Network is slower than disk for many workloads now; locality cuts both cost and latency.

### 88. Tail latency mitigation.
Hedging (issue a second request after p95 and use the first response), retries with deadlines, "tied requests" (cancel slower one on first response), out-of-order processing, smaller fan-out, caching. Critical when one slow dep dominates user-visible latency.

### 89. Idempotency keys for APIs.
Client supplies a UUID per write; server stores `(key → result)` for a TTL; duplicate keys return stored result. Stripe-style. Lets clients safely retry network failures. Pair with monotonically increasing tokens for ordering.

### 90. Anti-patterns to avoid.
Distributed monolith (services that must deploy together), synchronous deep call graphs (latency stacks), shared DB across services, idempotency by hope, "we'll add observability later", one massive table partitioned by date with hot today, GC pauses bigger than your timeouts, untested DR plans.

### 91. Required reading & references.
- *Designing Data-Intensive Applications* (Kleppmann) — the field's textbook.
- Papers: Dynamo, BigTable, Spanner, MapReduce, Chubby, Raft, F1, Kafka, Calvin, Chord.
- *Site Reliability Engineering* (Google) — production discipline.
- Jepsen reports (jepsen.io) for hard truths about real systems.

### 92. Mindset summary.
Assume failure. Make every interaction idempotent or compensable. Measure everything. Set timeouts. Limit blast radius with bulkheads. Practice failure with chaos engineering. Postmortem honestly. Trade consistency, availability, and latency consciously — never accidentally.
