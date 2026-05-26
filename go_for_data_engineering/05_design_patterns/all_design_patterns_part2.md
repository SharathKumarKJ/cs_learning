# Go Design Patterns — Part 2: Concurrency, Distributed, Architectural & Idiomatic

Covers Go-specific concurrency patterns, cloud-native / distributed patterns, architectural patterns, and idiomatic Go patterns. See `all_design_patterns.md` for classical GoF patterns.

## Contents
4. [Concurrency Patterns](#4-concurrency-patterns)
5. [Distributed / Cloud-Native Patterns](#5-distributed--cloud-native-patterns)
6. [Architectural Patterns](#6-architectural-patterns)
7. [Idiomatic Go Patterns](#7-idiomatic-go-patterns)

---

## 4. Concurrency Patterns

The patterns that make Go famous. Channels + goroutines + `context` + `sync` are the building blocks.

### 4.1 Worker Pool

```go
func WorkerPool(ctx context.Context, n int, tasks <-chan func()) {
    var wg sync.WaitGroup
    for i := 0; i < n; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case <-ctx.Done(): return
                case t, ok := <-tasks:
                    if !ok { return }
                    t()
                }
            }
        }()
    }
    wg.Wait()
}
```

---

### 4.2 Fan-out / Fan-in

```go
func fanOut(in <-chan int, n int) []<-chan int {
    outs := make([]<-chan int, n)
    for i := 0; i < n; i++ {
        ch := make(chan int)
        outs[i] = ch
        go func(out chan<- int) {
            defer close(out)
            for v := range in { out <- v * v }
        }(ch)
    }
    return outs
}

func fanIn(chans ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    wg.Add(len(chans))
    for _, c := range chans {
        go func(c <-chan int) {
            defer wg.Done()
            for v := range c { out <- v }
        }(c)
    }
    go func() { wg.Wait(); close(out) }()
    return out
}
```

---

### 4.3 Pipeline

```go
func gen(nums ...int) <-chan int {
    out := make(chan int)
    go func() { defer close(out); for _, n := range nums { out <- n } }()
    return out
}
func sq(in <-chan int) <-chan int {
    out := make(chan int)
    go func() { defer close(out); for n := range in { out <- n * n } }()
    return out
}
// for v := range sq(sq(gen(1,2,3,4))) { fmt.Println(v) }
```

---

### 4.4 Future / Promise

```go
type Result struct{ V int; Err error }

func async(work func() (int, error)) <-chan Result {
    ch := make(chan Result, 1)
    go func() {
        v, err := work()
        ch <- Result{v, err}
        close(ch)
    }()
    return ch
}
```

---

### 4.5 Cancellation with context

```go
func fetch(ctx context.Context, url string) ([]byte, error) {
    req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
    resp, err := http.DefaultClient.Do(req)
    if err != nil { return nil, err }
    defer resp.Body.Close()
    return io.ReadAll(resp.Body)
}
```

Pass `ctx` as the **first** argument; never store it in struct fields; always `defer cancel()`.

---

### 4.6 Semaphore (Bounded Concurrency)

```go
sem := make(chan struct{}, 8)
for _, item := range items {
    sem <- struct{}{}
    go func(it Item) {
        defer func() { <-sem }()
        process(it)
    }(item)
}
```

---

### 4.7 Errgroup

```go
import "golang.org/x/sync/errgroup"

func parallelFetch(ctx context.Context, urls []string) ([][]byte, error) {
    g, gctx := errgroup.WithContext(ctx)
    results := make([][]byte, len(urls))
    for i, u := range urls {
        i, u := i, u
        g.Go(func() error {
            b, err := fetch(gctx, u)
            if err != nil { return err }
            results[i] = b
            return nil
        })
    }
    if err := g.Wait(); err != nil { return nil, err }
    return results, nil
}
```

The most useful concurrency helper in modern Go.

---

### 4.8 Singleflight

```go
import "golang.org/x/sync/singleflight"

var sf singleflight.Group

func getUser(id string) (User, error) {
    v, err, _ := sf.Do("user:"+id, func() (any, error) {
        return loadFromDB(id)
    })
    if err != nil { return User{}, err }
    return v.(User), nil
}
```

Prevents thundering herd on cache misses.

---

### 4.9 Rate Limiter

```go
import "golang.org/x/time/rate"

lim := rate.NewLimiter(rate.Every(time.Second), 10)
for _, req := range requests {
    if err := lim.Wait(ctx); err != nil { return err }
    handle(req)
}
```

---

### 4.10 Sync.Once Lazy Init with Error

```go
type Loader struct {
    once sync.Once
    val  Config
    err  error
}
func (l *Loader) Get() (Config, error) {
    l.once.Do(func() { l.val, l.err = load() })
    return l.val, l.err
}
```

---

### 4.11 Broadcast (close channel)

```go
type Broadcaster struct{ done chan struct{} }
func New() *Broadcaster                       { return &Broadcaster{done: make(chan struct{})} }
func (b *Broadcaster) Wait() <-chan struct{} { return b.done }
func (b *Broadcaster) Fire()                  { close(b.done) }
```

Closing a channel signals every receiver — cheaper than per-goroutine signaling.

---

## 5. Distributed / Cloud-Native Patterns

### 5.1 Circuit Breaker

```go
type State int
const (Closed State = iota; Open; HalfOpen)

type Breaker struct {
    mu        sync.Mutex
    state     State
    failures  int
    threshold int
    cooldown  time.Duration
    openedAt  time.Time
}

func (b *Breaker) Call(fn func() error) error {
    b.mu.Lock()
    if b.state == Open {
        if time.Since(b.openedAt) > b.cooldown {
            b.state = HalfOpen
        } else {
            b.mu.Unlock(); return errors.New("circuit open")
        }
    }
    b.mu.Unlock()

    err := fn()

    b.mu.Lock(); defer b.mu.Unlock()
    if err != nil {
        b.failures++
        if b.failures >= b.threshold {
            b.state = Open; b.openedAt = time.Now()
        }
        return err
    }
    b.failures = 0; b.state = Closed
    return nil
}
```

Production: `sony/gobreaker` or `failsafe-go`.

---

### 5.2 Retry with Exponential Backoff + Jitter

```go
func Retry(ctx context.Context, attempts int, base time.Duration, fn func() error) error {
    var err error
    for i := 0; i < attempts; i++ {
        if err = fn(); err == nil { return nil }
        if !isRetryable(err) { return err }
        d := time.Duration(1<<i) * base
        d += time.Duration(rand.Int63n(int64(d / 2)))
        select {
        case <-time.After(d):
        case <-ctx.Done(): return ctx.Err()
        }
    }
    return err
}
```

---

### 5.3 Bulkhead

```go
type Bulkhead struct{ sem chan struct{} }
func New(n int) *Bulkhead { return &Bulkhead{sem: make(chan struct{}, n)} }
func (b *Bulkhead) Do(ctx context.Context, fn func() error) error {
    select {
    case b.sem <- struct{}{}:
        defer func() { <-b.sem }()
        return fn()
    case <-ctx.Done(): return ctx.Err()
    }
}
```

Separate Bulkhead per downstream prevents a single slow dependency from draining all goroutines.

---

### 5.4 Hedged Request

```go
func Hedged(ctx context.Context, do func(context.Context) ([]byte, error), delay time.Duration) ([]byte, error) {
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()
    out := make(chan []byte, 2); errs := make(chan error, 2)

    fire := func() {
        b, err := do(ctx)
        if err != nil { errs <- err; return }
        out <- b
    }
    go fire()
    select {
    case b := <-out: return b, nil
    case <-time.After(delay):
    }
    go fire()
    select {
    case b := <-out: return b, nil
    case e := <-errs: return nil, e
    case <-ctx.Done(): return nil, ctx.Err()
    }
}
```

Idempotent reads only.

---

### 5.5 Outbox Pattern

```sql
-- same DB transaction
INSERT INTO orders (...);
INSERT INTO outbox (event_type, payload, created_at) VALUES ('order_created', $1, now());
```

```go
func relay(ctx context.Context, db *sql.DB, pub Publisher) error {
    rows, err := db.QueryContext(ctx, `SELECT id, payload FROM outbox WHERE sent=false LIMIT 100`)
    if err != nil { return err }
    defer rows.Close()
    for rows.Next() {
        var id int64
        var payload []byte
        if err := rows.Scan(&id, &payload); err != nil { return err }
        if err := pub.Publish(ctx, payload); err != nil { return err }
        if _, err := db.ExecContext(ctx, `UPDATE outbox SET sent=true WHERE id=$1`, id); err != nil {
            return err
        }
    }
    return nil
}
```

Solves the dual-write problem (DB commits, message bus fails).

---

### 5.6 Saga (Choreography)

```go
type Step struct {
    Do   func(ctx context.Context) error
    Undo func(ctx context.Context) error
}

func RunSaga(ctx context.Context, steps []Step) error {
    var done []Step
    for _, s := range steps {
        if err := s.Do(ctx); err != nil {
            for i := len(done) - 1; i >= 0; i-- {
                _ = done[i].Undo(ctx)
            }
            return err
        }
        done = append(done, s)
    }
    return nil
}
```

---

### 5.7 Idempotency Key

```go
type Store interface {
    GetResult(key string) (result []byte, found bool, err error)
    SaveResult(key string, result []byte) error
}

func Handle(ctx context.Context, store Store, key string, do func() ([]byte, error)) ([]byte, error) {
    if v, found, err := store.GetResult(key); err != nil {
        return nil, err
    } else if found {
        return v, nil
    }
    res, err := do()
    if err != nil { return nil, err }
    return res, store.SaveResult(key, res)
}
```

---

### 5.8 Health Check / Readiness

```go
http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte("ok"))
})
http.HandleFunc("/readyz", func(w http.ResponseWriter, r *http.Request) {
    if !ready.Load() { w.WriteHeader(503); return }
    w.WriteHeader(200)
})
```

`/healthz` = alive (liveness). `/readyz` = ready to serve (readiness). K8s probes them separately.

---

### 5.9 Graceful Shutdown

```go
func main() {
    srv := &http.Server{Addr: ":8080", Handler: mux}
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()

    sig := make(chan os.Signal, 1)
    signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
    <-sig

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    _ = srv.Shutdown(ctx)
}
```

Drain in-flight requests, stop accepting new, then close DB pools.

---

### 5.10 Leader Election (sketch)

```go
import "k8s.io/client-go/tools/leaderelection"

leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
    Lock:            lock,
    ReleaseOnCancel: true,
    LeaseDuration:   15 * time.Second,
    RenewDeadline:   10 * time.Second,
    RetryPeriod:     2 * time.Second,
    Callbacks: leaderelection.LeaderCallbacks{
        OnStartedLeading: func(ctx context.Context) { runLeaderLoop(ctx) },
        OnStoppedLeading: func()                     { log.Println("lost leadership") },
    },
})
```

Same idea via etcd / Consul lease API.

---

## 6. Architectural Patterns

### 6.1 Hexagonal / Ports & Adapters

Domain logic in the center; everything external (DB, HTTP, queue) is an adapter plugged into a port interface.

```
internal/
  domain/      // entities + business rules (pure Go)
  ports/       // interfaces required by domain (UserRepo, EventPublisher)
  adapters/
    http/      // inbound HTTP handlers
    postgres/  // outbound DB adapter
    kafka/     // outbound event publisher
cmd/
  api/main.go  // wires adapters into the domain
```

```go
// ports/user_repo.go
type UserRepo interface {
    Get(ctx context.Context, id string) (User, error)
    Save(ctx context.Context, u User) error
}

// domain/service.go
type UserService struct{ repo ports.UserRepo }
func (s UserService) Register(ctx context.Context, name string) (User, error) {
    u := User{ID: newID(), Name: name}
    return u, s.repo.Save(ctx, u)
}
```

The domain depends on interfaces, not on Postgres or HTTP.

---

### 6.2 Clean Architecture / Layered

Same idea as hexagonal with explicit layers: `entities → use cases → interface adapters → frameworks`. Inner layers never import outer ones.

---

### 6.3 CQRS

Split writes (commands) from reads (queries) — different models, possibly different stores.

```go
// commands
type CreateOrderCmd struct{ /* ... */ }
type CommandHandler interface{ Handle(ctx context.Context, c CreateOrderCmd) error }

// queries (denormalized read model)
type OrderView struct{ ID, Status, Total string }
type QueryHandler interface{ GetOrder(ctx context.Context, id string) (OrderView, error) }
```

Often paired with event sourcing.

---

### 6.4 Event Sourcing

Persist every state change as an event; current state = fold over events.

```go
type Event interface{ Apply(*Account) }

type Deposited struct{ Amount int }
func (e Deposited) Apply(a *Account) { a.Balance += e.Amount }

type Withdrawn struct{ Amount int }
func (e Withdrawn) Apply(a *Account) { a.Balance -= e.Amount }

type Account struct{ Balance int }
func Rebuild(events []Event) Account {
    var a Account
    for _, e := range events { e.Apply(&a) }
    return a
}
```

---

### 6.5 Repository

Abstract data access behind a small interface.

```go
type UserRepo interface {
    Get(ctx context.Context, id string) (User, error)
    Save(ctx context.Context, u User) error
}

type pgUserRepo struct{ db *sql.DB }
func (r pgUserRepo) Get(ctx context.Context, id string) (User, error) { /* ... */ return User{}, nil }
func (r pgUserRepo) Save(ctx context.Context, u User) error            { /* ... */ return nil }
```

Domain depends on `UserRepo`; tests inject a fake.

---

### 6.6 Unit of Work

Group multiple repository operations in one transaction.

```go
type UoW struct{ tx *sql.Tx }
func (u *UoW) Users() UserRepo  { return pgUserRepo{db: u.tx} }
func (u *UoW) Orders() OrderRepo { return pgOrderRepo{db: u.tx} }

func WithUoW(ctx context.Context, db *sql.DB, fn func(*UoW) error) error {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil { return err }
    if err := fn(&UoW{tx: tx}); err != nil {
        _ = tx.Rollback(); return err
    }
    return tx.Commit()
}
```

---

### 6.7 Sidecar / Ambassador / Adapter (Cloud-Native)

K8s container patterns implemented as separate processes:
- **Sidecar**: helper next to main container (log shipper, mTLS proxy, service mesh agent).
- **Ambassador**: proxy for outbound traffic (Envoy as smart client).
- **Adapter**: normalize the main container's outputs (metrics translator).

You write the main Go process; the sidecar is a separate image (Envoy, Fluent Bit, OTel agent).

---

## 7. Idiomatic Go Patterns

### 7.1 Functional Options

Preferred over Builder for configurable constructors.

```go
type Server struct {
    addr    string
    timeout time.Duration
    tls     bool
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }
func WithTLS()                   Option { return func(s *Server) { s.tls = true } }

func New(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, timeout: 30 * time.Second}
    for _, o := range opts { o(s) }
    return s
}

// New(":8080", WithTimeout(5*time.Second), WithTLS())
```

---

### 7.2 Errors: Wrap, Sentinel, Typed

```go
// sentinel
var ErrNotFound = errors.New("not found")

// wrapping
if err != nil { return fmt.Errorf("get user %s: %w", id, err) }

// check by sentinel
if errors.Is(err, ErrNotFound) { /* ... */ }

// typed
type ValidationError struct{ Field, Msg string }
func (e *ValidationError) Error() string { return e.Field + ": " + e.Msg }

var ve *ValidationError
if errors.As(err, &ve) { /* use ve.Field */ }
```

Never use `panic` for ordinary errors.

---

### 7.3 Accept Interfaces, Return Structs

```go
// good: function takes any io.Reader, returns a concrete struct
func Parse(r io.Reader) (Document, error) { /* ... */ return Document{}, nil }
```

Callers get flexibility on input; concrete returns are easier to evolve.

---

### 7.4 Small Interfaces

Single-method interfaces are best (`io.Reader`, `io.Writer`, `error`, `fmt.Stringer`). Add methods only when consumers actually need them.

```go
type Closer interface { Close() error }
type Reader interface { Read(p []byte) (n int, err error) }
type ReadCloser interface { Reader; Closer } // composed when needed
```

---

### 7.5 Embedding for Composition

```go
type Logger struct{ Prefix string }
func (l Logger) Log(msg string) { fmt.Println(l.Prefix, msg) }

type Server struct {
    Logger // embedded — Server has Log() method "for free"
    Addr string
}
```

Embedding ≠ inheritance — no virtual dispatch, just method promotion.

---

### 7.6 Table-Driven Tests

```go
func TestAdd(t *testing.T) {
    cases := []struct {
        name    string
        a, b, w int
    }{
        {"both zero", 0, 0, 0},
        {"positive", 2, 3, 5},
        {"negative", -1, 1, 0},
    }
    for _, c := range cases {
        t.Run(c.name, func(t *testing.T) {
            if got := Add(c.a, c.b); got != c.w {
                t.Errorf("Add(%d,%d)=%d, want %d", c.a, c.b, got, c.w)
            }
        })
    }
}
```

---

### 7.7 Defer for Cleanup

```go
func process(path string) error {
    f, err := os.Open(path)
    if err != nil { return err }
    defer f.Close()

    mu.Lock()
    defer mu.Unlock()

    // ... use f
    return nil
}
```

Always pair acquire + `defer release`. Defers run LIFO.

---

### 7.8 Type Assertions and Switches

```go
switch v := any.(type) {
case string:
    fmt.Println("string:", v)
case int:
    fmt.Println("int:", v)
case error:
    fmt.Println("error:", v.Error())
default:
    fmt.Println("unknown")
}
```

Prefer type switches for branching on concrete types; reserve `reflect` for serialization frameworks.

---

### 7.9 Context Values (sparingly)

```go
type ctxKey struct{}
var traceIDKey = ctxKey{}

func WithTraceID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, traceIDKey, id)
}
func TraceID(ctx context.Context) string {
    if v, ok := ctx.Value(traceIDKey).(string); ok { return v }
    return ""
}
```

Only for request-scoped metadata (trace IDs, auth, locale). Never for function arguments.

---

### 7.10 Generics (where useful)

```go
func Map[T, U any](in []T, f func(T) U) []U {
    out := make([]U, len(in))
    for i, v := range in { out[i] = f(v) }
    return out
}

func Filter[T any](in []T, pred func(T) bool) []T {
    var out []T
    for _, v := range in { if pred(v) { out = append(out, v) } }
    return out
}
```

Use generics for collections / algorithms that genuinely vary by type. Don't generic-ify everything.

---

### 7.11 Stringer & Marshaler

```go
type Status int
const (StatusPending Status = iota; StatusActive; StatusDone)

func (s Status) String() string {
    return [...]string{"pending", "active", "done"}[s]
}
```

Implement `String()`, `MarshalJSON`, `MarshalText` for clean serialization and logging.

---

### 7.12 Avoid Goroutine Leaks

Every goroutine you start must have a clear way to exit. Use `context`, close channels, or wait groups. Tools: `go test -race`, `go.uber.org/goleak`.

```go
func worker(ctx context.Context, in <-chan int) {
    for {
        select {
        case <-ctx.Done(): return
        case v, ok := <-in:
            if !ok { return }
            handle(v)
        }
    }
}
```

---

## Summary: When to Use What

| Need | Pattern |
|---|---|
| One instance | Singleton with `sync.Once` |
| Optional config | Functional Options |
| Many algorithms | Strategy / function-typed field |
| Middleware chain | Decorator / function composition |
| Async result | Channel as Future |
| Bounded parallelism | Semaphore / errgroup |
| Wait for many ops | errgroup |
| Dedupe concurrent loads | singleflight |
| Survive flaky deps | Retry + Circuit Breaker |
| Reliable event publish | Outbox |
| Long workflow | Saga |
| Plug-in storage | Repository + Ports & Adapters |
| State machine | State pattern |
| Tree traversal with many ops | Visitor |
| Cross-cutting metadata | context |
