# Design Patterns Interview Questions (Detailed)

### 1. What are design patterns?
Reusable solutions to common software design problems, classified into **creational** (object construction), **structural** (composition), and **behavioral** (interaction). They are vocabulary, not copy-paste code — the value is the shared language and the proven trade-offs, not the exact implementation.

### 2. Singleton — pros and cons.
**Pros**: single shared instance (config, connection pools, logger), lazy init, cheap access. **Cons**: hidden global state, hard to test (cannot easily swap implementations), thread-safety pitfalls if not done right, often the wrong answer — dependency injection is usually cleaner. Use sparingly; for things like connection pools and stateless config, it's fine.

### 3. Factory vs Builder vs Functional Options.
**Factory**: one method returns a concrete instance based on a key — good when you have a finite set of variants. **Builder**: fluent step-by-step construction of complex objects with many optional fields. **Functional Options** (Go-idiomatic, also nice in Python via kwargs): variadic options applied to a default config — most flexible, easiest to evolve without breaking callers.

### 4. Strategy vs Template Method.
**Strategy**: encapsulate algorithms behind an interface; swap at runtime via composition. **Template Method**: a parent class defines the skeleton with hooks subclasses override — inheritance-based, more rigid. Modern Go/Python code almost always prefers Strategy over Template Method because composition is more flexible than inheritance.

### 5. Observer / Pub-Sub.
Decouple producers from consumers: producers publish events; the bus delivers them to subscribers. Implementations range from in-process (callbacks, channels) to distributed (Kafka, NATS, Pub/Sub). Trade-offs: tight coupling vs eventual consistency, backpressure handling, dropped messages on slow consumers.

### 6. Decorator pattern.
Wrap an object/function to add cross-cutting behavior (logging, caching, retries, metrics, auth) without modifying the original. In Python it's almost a language feature (`@decorator`); in Go it's a higher-order function or a wrapping struct. Compose multiple decorators in order — the order matters (e.g. retry-inside-logging vs logging-inside-retry).

### 7. Repository pattern.
Hide persistence behind an interface so business logic depends on the abstraction, not the DB. Enables: easy unit testing (in-memory fake), swappable backends (Postgres → DynamoDB), and explicit boundaries. Pitfall: leaky abstractions (paginated queries, complex joins) — sometimes raw DB access is more honest.

### 8. Circuit breaker.
Fail fast when a downstream is unhealthy to avoid cascading failures and resource exhaustion. States: **closed** (calls pass through), **open** (calls immediately fail after failure threshold), **half-open** (probe with a single call after a timeout to test recovery). Pair with retries (with jitter) and bulkheads (isolated thread/connection pools per dependency).

### 9. Saga vs distributed transactions.
**Distributed transactions** (2PC) lock multiple systems for atomicity — high latency, poor scaling, all-or-nothing. **Sagas** break the work into a sequence of local transactions with compensations on failure — eventually consistent, scales horizontally, requires idempotent steps. Sagas dominate modern microservice architectures.

### 10. Outbox pattern.
Solves the "write to DB AND publish to message broker atomically" problem without 2PC. Writes the event to an outbox table in the same DB transaction as the business row; a separate process publishes from the outbox. Requires consumers to be idempotent (at-least-once delivery). Variant: use CDC (Debezium) to tail the table directly.

### 11. Idempotency key pattern.
Clients supply a unique key with each request; the server stores the result of the first successful processing keyed by that ID. Retries are safe — the second request returns the cached response without re-running the side effects. Essential for payment APIs and any HTTP endpoint with side effects.

### 12. Bulkhead.
Isolate resources (thread pools, connection pools, CPU) per dependency so a slow or failing downstream cannot starve unrelated work. Inspired by ship compartments. Combined with circuit breakers, gives resilience: a slow third-party API can only consume its own bulkhead, not the whole service.

### 13. Leader election.
Used to coordinate work across replicas — one leader handles writes/scheduled tasks, followers stand by. Implementations: etcd/Consul lease, ZooKeeper, Kubernetes Lease object. Make sure followers can take over quickly and the leader recognizes when it has lost the lease (fencing tokens prevent split-brain).

### 14. CQRS.
Command Query Responsibility Segregation: separate the **write model** (commands that change state, often event-sourced) from the **read model** (denormalized views optimized for queries). Powerful when read and write patterns diverge heavily; adds complexity — only use when you actually need it. Pairs naturally with event sourcing.

### 15. Event sourcing.
Persist every state change as an immutable event; rebuild current state by replaying events. Benefits: full audit log, time travel, multiple projections from one source of truth. Drawbacks: schema evolution of events is hard, snapshots needed for performance, mental model shift. Often overkill — start with simpler patterns and adopt only when needs justify.

### 16. Dependency Injection.
Pass dependencies in (constructor or function args) rather than constructing them inside. Enables testing (inject fakes), swapping implementations, and clearer ownership. Go does this with interfaces and explicit wiring; Python often uses constructor injection or DI containers. Avoid framework magic — explicit wiring scales fine for most projects.

### 17. Facade.
A unified high-level interface over a complex subsystem. Hides ugly internals, simplifies the common case. E.g. an `OrderService` facade behind which sit `PricingClient`, `InventoryClient`, `PaymentClient`. Use when the underlying system is complex; avoid creating a facade just to add a layer.

### 18. Adapter.
Convert one interface into another so two systems can interoperate. Common at boundaries: translating an external API's contract to your domain model, wrapping a legacy library to fit a new abstraction. Keep adapters thin — they should translate, not add business logic.

### 19. Anti-patterns to avoid.
**God object** (one class doing everything), **Singleton overuse** (hidden globals), **deeply nested inheritance**, **anemic domain models** (data classes with no behavior), **service locator** (hidden dependencies pulled from a global registry), **leaky abstractions** (lower layer details bleeding through), **premature abstraction** (interfaces with one implementation, just in case).

### 20. How do you pick a pattern?
Start with the simplest design that works. Reach for patterns when you actually feel the pain they solve (multiple implementations needed, complex construction, scattered cross-cutting concerns). Communicate intent — "I used the Outbox pattern" is more meaningful than "I added a table and a worker." Patterns are vocabulary among engineers, not a checklist to apply.
