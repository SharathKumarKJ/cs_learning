# Go-Centric System Design Questions (Detailed)

### 1. Design a high-throughput Kafka consumer service in Go (100k msg/sec).
**Architecture**: per-partition goroutines (preserves order), each running a worker pool for stateless work + per-partition serial processor for stateful operations. Use `segmentio/kafka-go` or `confluent-kafka-go`. **Backpressure**: bounded channels and `golang.org/x/sync/semaphore` to cap in-flight work. **Offset management**: manual commit after successful processing for at-least-once; idempotent downstream for effective-once. **Observability**: Prometheus metrics on lag, processing latency, error rate. **Shutdown**: SIGTERM → stop reader → drain channels → commit → exit, all via context.

### 2. Design a worker pool that auto-scales based on queue depth.
Maintain a buffered channel of jobs. A controller goroutine periodically samples `len(jobs)` and adjusts the worker count (add workers when queue grows, retire idle workers via a quit signal). Use a semaphore (`golang.org/x/sync/semaphore`) to cap parallelism. Avoid spawning unbounded goroutines on every burst — that's how memory exhaustion happens. Expose worker count and queue depth metrics.

### 3. Design a rate-limiting middleware in Go.
**Per-IP / per-token**: token bucket using `golang.org/x/time/rate` with a `sync.Map` keyed by client. Evict idle entries with a TTL goroutine. **Distributed**: Redis with atomic Lua script doing `INCR` + `EXPIRE`. Wrap as `func(http.Handler) http.Handler` middleware so it composes with logging/auth. Always set `Retry-After` on 429.

### 4. Design a graceful HTTP service with hot config reload.
Run config in a `sync/atomic.Value` so readers are lock-free. A goroutine watches a config file (fsnotify) or polls a remote source and swaps the value atomically. Handlers read the current pointer each request — never cache across requests. `SIGHUP` triggers immediate reload. Test the reload path in CI; misuse of `sync.Mutex` here is a common cause of stalls.

### 5. Design a distributed scheduler in Go.
**Single-leader** model: replicas elect a leader via etcd lease; leader pulls due jobs from the DB, dispatches to workers via gRPC. Followers stand by and take over on lease loss (fencing token in DB writes prevents split-brain). **Idempotency**: every job has a unique run ID; workers ack only after success. **Backfill** support: schedule past intervals explicitly. Reference real systems: Temporal, Cadence, Kubernetes Job controller.

### 6. Design an in-memory cache with TTL and LRU eviction.
Doubly-linked list + map for O(1) get/put/evict. TTL implemented by storing expiry per entry and a background goroutine sweeping expired entries (or lazy check on access). For multi-process or HA, abandon in-memory and use Redis or memcached. Discuss thundering herd (singleflight pattern via `golang.org/x/sync/singleflight`) and stampede protection.

### 7. Design a real-time event bus inside a service.
A struct owning a channel per topic plus a subscriber registry. Publish writes to all subscriber channels (with `default` to drop on slow consumers, OR a separate slow-consumer policy that disconnects them). Use `sync.RWMutex` on the registry. For cross-process, wrap NATS/Kafka. Discuss backpressure semantics — silently dropping is rarely what you want at scale.

### 8. Design a deduplicating ingestion service.
Consume from Kafka. For each message, compute a stable dedup key (event_id, or hash of payload). Check a TTL cache (in-process for hot keys + Redis for shared state across instances). On hit, drop and commit. On miss, write key to cache then forward to downstream. For unbounded keyspaces, switch to a Bloom filter or HyperLogLog with periodic resets. Discuss exactly-once guarantees (impossible without idempotent sinks, achievable with idempotent producer + transactional sink).

### 9. Design a gRPC API with retries, deadlines, and load balancing.
Server: `grpc.NewServer` with interceptors for logging, metrics, auth, recovery. **Client**: use `grpc.WithDefaultServiceConfig` for retry policy (status codes, max attempts, backoff), context deadlines on every call, and pluggable load balancing (round-robin, weighted, custom). For service discovery: DNS, etcd, Consul, or service mesh. Always send deadlines — they're how cascading failures stop.

### 10. Design a multi-tenant SaaS service in Go.
Tenant context lives in `context.Context`; every layer (handler → service → repo) propagates it. Repository layer enforces `tenant_id` on every query — never trust the caller to pass it. Connection pooling per-tenant if isolation is required (otherwise shared pool with `SET search_path` per request in Postgres). Quotas via rate limiter keyed by tenant. Cost attribution via metric labels and structured logs. Audit every cross-tenant access.
