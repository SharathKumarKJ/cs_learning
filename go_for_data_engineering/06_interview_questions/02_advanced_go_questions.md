# Go Advanced & Staff-Level Interview Questions (Detailed)

## Concurrency deep dive

### 1. How does the Go scheduler work?
Go uses an **M:N scheduler** with three core entities: **G** (goroutine), **M** (OS thread), **P** (logical processor, equal to `GOMAXPROCS` by default = number of CPUs). Each P has a local run queue of Gs; Ms execute Gs on behalf of Ps. When a goroutine blocks on I/O, the M parks and another M picks up the P's remaining Gs (work stealing across Ps balances load). This is why Go can run millions of goroutines cheaply.

### 2. When does a goroutine block vs yield?
A goroutine yields cooperatively at function calls, channel operations, syscalls, and (since 1.14) on preemptive scheduling tied to a 10 ms quantum. Tight loops without function calls used to be able to hog a P; modern Go preempts them. Always design hot loops to not starve other goroutines, especially in libraries.

### 3. How do you detect data races?
Run with the **race detector**: `go run -race main.go`, `go test -race ./...`. It instruments memory accesses and reports concurrent unsynchronized reads/writes to the same memory. Use it in CI on every PR — race conditions are silent in production but catastrophic.

### 4. When would you choose channels over mutexes (or vice versa)?
Use **channels** when goroutines pass data through the program (pipelines, work queues, fan-in/out). Use **mutexes** when goroutines share state that's read/written in place (counters, caches, registries). The mantra "share memory by communicating" is a guideline, not a law — use whichever produces simpler code. `sync.Map` and `sync/atomic` cover specific cases (read-heavy maps, lock-free counters).

### 5. How do you implement a worker pool with backpressure?
Create a buffered job channel of the desired backpressure size; sender blocks when the buffer fills, naturally throttling producers. Spawn N workers (typically `runtime.NumCPU()` or based on workload type) reading from the channel. Use a context for graceful cancellation and a `sync.WaitGroup` to wait for workers to drain on shutdown. For dynamic sizing, see worker pools with semaphores (`golang.org/x/sync/semaphore`).

### 6. How do you cancel work that has already started?
Pass a `context.Context` to every potentially blocking function. Long-running work checks `select { case <-ctx.Done(): return ctx.Err(); ... }` at safe points. Network and DB libraries accept a context and abort the underlying syscall when it's canceled. Never silently ignore context — propagate or honor it.

### 7. What is goroutine leak and how do you avoid it?
A goroutine that never exits — typically because it's blocked forever on an unbuffered channel, a select without `ctx.Done()`, or an infinite loop. Symptoms: rising goroutine count visible in `runtime.NumGoroutine()` or `/debug/pprof/goroutine`. Avoid by always providing a cancellation path (context, close channel), bounded buffers, and timeouts.

### 8. Difference between `sync.Mutex`, `sync.RWMutex`, and `sync.Map`.
**Mutex**: exclusive lock — one reader or one writer. **RWMutex**: many readers OR one writer — better for read-heavy workloads, but has overhead and can starve writers under contention. **sync.Map**: a specialized concurrent map for two specific cases (write-once-read-many, or disjoint key sets per goroutine) — slower than `map + RWMutex` for general use, so don't reach for it by default.

### 9. What is `sync.Pool` and when do you use it?
A pool of temporary objects to reduce GC pressure for short-lived allocations (buffers, request structs). Get returns an existing pooled object or calls `New`; Put returns the object to the pool. Important caveats: pool contents may be evicted at any GC, so never rely on it for correctness — only for performance.

## Memory and runtime

### 10. How does Go's garbage collector work?
A concurrent, tri-color mark-and-sweep GC with very low STW pauses (sub-millisecond on most workloads since 1.5). It runs concurrently with your program, scanning the heap for reachable objects from roots (stacks, globals). Tune with `GOGC` (default 100 = trigger when heap doubles since last GC) and `GOMEMLIMIT` (soft memory cap, Go 1.19+). Reduce GC by allocating less (pools, pre-sized slices, value types).

### 11. Stack vs heap allocation — what is escape analysis?
At compile time, the compiler decides if a variable can live on the goroutine's stack (cheap, freed on return) or must "escape" to the heap (GC-managed). Variables escape if their address leaves the function via return, channel send, closure capture, or interface conversion. Inspect with `go build -gcflags='-m'`. Heap allocations are the dominant GC cost — minimize them in hot paths.

### 12. What is the cost of interface conversion?
Interfaces are two-word structures (type pointer + data pointer). Storing a concrete value in an interface usually allocates on the heap if the value doesn't fit in a pointer. Calls through interfaces use a vtable lookup — slightly slower than direct calls and not inlinable. Avoid interfaces in tight hot loops.

### 13. How do generics affect performance?
Go's generics are implemented via a hybrid of monomorphization and "GC shape stenciling" — types with the same memory layout share generated code. There is some runtime dispatch for shape-different instantiations. For most code generics are fast; for ultra-hot paths, hand-specialized code can still be faster.

### 14. What is a closure and how does it capture variables?
A closure is a function value plus the environment of variables it references. Captured variables are by reference (the same variable, not a copy). A common bug: launching goroutines inside a `for i := range items` loop and capturing `i` — all goroutines see the final value. Fix: `for _, it := range items { it := it; go func() { use(it) }() }` (or pass as argument).

## Errors, testing, and tooling

### 15. How do you design error types for a public API?
Use sentinel errors (`var ErrNotFound = errors.New(...)`) for stable, comparable error conditions consumers may want to match. Use custom types implementing `Error() string` when callers need structured fields (HTTP status, validation field). Wrap with `%w` to preserve cause chains. Document which errors are part of the API contract — once exposed, they're hard to change.

### 16. How do you write good tests in Go?
Use the standard library `testing` package with **table-driven tests** — a slice of cases iterated with `t.Run(case.name, ...)`. Subtests give per-case isolation and selective execution. Use `t.Parallel()` for independent cases. Run with `-race`, `-cover`, and `-count=1` (to bypass cache). For HTTP, use `httptest.NewServer`; for DB, use docker-compose or a fake.

### 17. How do you benchmark Go code?
`func BenchmarkX(b *testing.B) { for i := 0; i < b.N; i++ { fn() } }` — the framework picks `b.N`. Run with `go test -bench=. -benchmem`. Use `b.ResetTimer()` after setup, `b.ReportAllocs()` for memory stats. Compare with `benchstat` to determine statistical significance. Always benchmark before optimizing.

### 18. How do you profile a running service?
Import `_ "net/http/pprof"` and serve on a separate port; then use `go tool pprof http://host:port/debug/pprof/profile` for CPU, `/heap` for memory, `/goroutine` for goroutine dumps. In production, expose pprof on a private port. For execution traces, hit `/debug/pprof/trace?seconds=5` and open with `go tool trace`.

### 19. What is `go mod` and why is it important?
The official module system (Go 1.11+). `go.mod` declares the module path and minimum Go version plus dependencies; `go.sum` contains cryptographic hashes for reproducible builds. Use `go mod tidy` to clean unused deps, `go mod vendor` for vendored deps, and semantic versioning (`v1.x.y`) for releases. Major version 2+ requires `/v2` in the path.

### 20. How do you organize a large Go project?
A common layout: `cmd/<binary>/main.go` for entry points, `internal/<pkg>` for code that should not be imported by other modules, `pkg/<pkg>` for reusable libraries (optional, sometimes considered an anti-pattern), `api/` for protobuf/openapi specs, `deploy/` for k8s/terraform. Keep packages small, named by what they provide (not "utils" or "helpers"), and prefer flat over deep hierarchies.

## Staff-level system-design Go questions

### 21. Design a high-throughput log ingestion service in Go.
HTTP/gRPC ingest → in-memory ring buffer per shard → batch flusher goroutines writing to Kafka with `acks=all` and async batching. Use `sync.Pool` for request buffers, `bytes.Buffer` reuse, and zero-copy where possible. Backpressure via bounded channels; drop or shed load when full with a `503` and Retry-After. Profile under load and tune `GOMAXPROCS`, batch size, and GC.

### 22. Design a distributed rate limiter.
Token-bucket per key stored in Redis (atomic Lua script for `INCR` + TTL) or use Redis Cell module. In Go, abstract with an interface so local in-memory limiter (golang.org/x/time/rate) and distributed Redis limiter are interchangeable. Discuss precision vs cost (sliding-window counters, leaky bucket) and per-tenant fairness.

### 23. Design a streaming deduplication service.
Consume events from Kafka by partition (preserves per-key ordering). Maintain a per-key TTL-cache (e.g. groupcache, BigCache, or Redis) of recently-seen event IDs. On hit, drop; on miss, write the ID and forward the event. For unbounded keyspaces, switch to a probabilistic Bloom/HyperLogLog filter. Discuss exactly-once vs at-least-once trade-offs.

### 24. How do you build a reliable Kafka consumer in Go?
Use a library that supports consumer groups (segmentio/kafka-go, IBM/sarama, confluent-kafka-go). Process messages **idempotently**, commit offsets **after** successful processing (manual commit, not auto). Use context for graceful shutdown (drain in-flight, commit, close). Handle retries with backoff for transient errors; route poison messages to a dead-letter topic.

### 25. How do you design for graceful shutdown?
Listen for SIGINT/SIGTERM. Stop accepting new work (close HTTP server, stop reading Kafka). Drain in-flight work with a timeout (via context). Flush buffers, commit offsets, close connections. Use `errgroup` to coordinate multiple shutdown paths. Test the shutdown path in CI — it's the most common source of data loss in production.

### 26. How do you observe a Go service in production?
**Logs**: structured (zerolog, zap) with correlation IDs propagated via context. **Metrics**: Prometheus (`prometheus/client_golang`) for RED/USE metrics. **Traces**: OpenTelemetry SDK, exporting to Jaeger/Tempo/Datadog. **Health**: liveness vs readiness endpoints. Bake all three in from day one — adding later is painful.

### 27. How do you do feature flagging in Go?
Abstract via an interface (`type Flagger interface { Enabled(name string, ctx Context) bool }`). Implement with LaunchDarkly/Unleash/in-house. Pull configs at startup, refresh periodically, cache locally so an outage of the flag service doesn't break the app. Use flags for gradual rollout, kill switches, and A/B experiments — not as long-term config.

### 28. How do you secure a Go service?
Validate every input at the boundary (use `validator` package). Run with non-root user in container. TLS on all external endpoints (`crypto/tls` minimum version 1.2). Manage secrets via environment + secrets manager, never logs. Set HTTP timeouts (`ReadTimeout`, `WriteTimeout`, `IdleTimeout`) to defeat slowloris. Use middleware for auth (JWT/mTLS), rate limiting, and CORS.
