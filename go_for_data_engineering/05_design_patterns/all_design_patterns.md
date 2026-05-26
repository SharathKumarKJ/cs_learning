# Go Design Patterns — Comprehensive Reference (Part 1: Classical Patterns)

Covers Gang-of-Four patterns adapted to idiomatic Go. See `all_design_patterns_part2.md` for concurrency, distributed, and architectural patterns.

> **Idiomatic Go note**: Go favors composition over inheritance, small interfaces, returning errors over exceptions, and explicit concurrency. Many GoF patterns simplify dramatically in Go — use the *intent*, not the OOP machinery.

## Contents
1. [Creational](#1-creational-patterns)
2. [Structural](#2-structural-patterns)
3. [Behavioral](#3-behavioral-patterns)

---

## 1. Creational Patterns

### 1.1 Singleton

**Intent**: Exactly one instance accessible globally.
**Use when**: Shared resource (config, logger, DB pool) where multiple instances would be wrong or wasteful.
**Avoid when**: You're just hiding global state — prefer DI.

```go
package singleton

import "sync"

type Config struct{ Env string }

var (
    instance *Config
    once     sync.Once
)

func Get() *Config {
    once.Do(func() { instance = &Config{Env: "prod"} })
    return instance
}
```

`sync.Once` is the canonical Go way — safer than `init()` for lazy initialization with error handling.

---

### 1.2 Factory Method

**Intent**: Create objects without specifying the concrete type at the call site.

```go
type Storage interface{ Save(key, val string) error }

type s3Store struct{}
func (s *s3Store) Save(k, v string) error { return nil }

type gcsStore struct{}
func (s *gcsStore) Save(k, v string) error { return nil }

func NewStorage(kind string) (Storage, error) {
    switch kind {
    case "s3":  return &s3Store{}, nil
    case "gcs": return &gcsStore{}, nil
    default:    return nil, fmt.Errorf("unknown storage %q", kind)
    }
}
```

---

### 1.3 Abstract Factory

**Intent**: A factory of factories — produce families of related objects (switching whole cloud stacks).

```go
type CloudFactory interface {
    NewStorage() Storage
    NewQueue() Queue
}

type AWS struct{}
func (AWS) NewStorage() Storage { return &s3Store{} }
func (AWS) NewQueue() Queue     { return &sqsQueue{} }

type GCP struct{}
func (GCP) NewStorage() Storage { return &gcsStore{} }
func (GCP) NewQueue() Queue     { return &pubsubQueue{} }
```

---

### 1.4 Builder

**Intent**: Step-by-step construction of complex objects with many optional fields.
**Idiomatic Go**: Prefer **functional options** (see Part 2) over a heavy builder.

```go
type Request struct {
    URL     string
    Method  string
    Headers map[string]string
    Body    []byte
}

type RequestBuilder struct{ r Request }

func NewRequest(url string) *RequestBuilder {
    return &RequestBuilder{r: Request{URL: url, Method: "GET", Headers: map[string]string{}}}
}
func (b *RequestBuilder) Method(m string) *RequestBuilder { b.r.Method = m; return b }
func (b *RequestBuilder) Header(k, v string) *RequestBuilder { b.r.Headers[k] = v; return b }
func (b *RequestBuilder) Body(p []byte) *RequestBuilder { b.r.Body = p; return b }
func (b *RequestBuilder) Build() Request { return b.r }
```

---

### 1.5 Prototype

**Intent**: Clone an existing object instead of creating from scratch.

```go
type Job struct {
    Name    string
    Steps   []string
    Timeout time.Duration
}
func (j Job) Clone() Job {
    cp := j
    cp.Steps = append([]string(nil), j.Steps...) // deep copy slice
    return cp
}
```

> Always deep-copy slice/map/pointer fields — Go assignments copy the header, not the backing data.

---

### 1.6 Object Pool

**Intent**: Reuse expensive objects (buffers, parsers, DB conns) instead of allocating each time.

```go
var bufPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func handle(payload []byte) {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() { buf.Reset(); bufPool.Put(buf) }()
    buf.Write(payload)
}
```

`sync.Pool` items may be GC'd between gets — only safe for caches, not for resources requiring deterministic cleanup.

---

## 2. Structural Patterns

### 2.1 Adapter

**Intent**: Make an incompatible interface usable through a wrapper.

```go
type Logger interface{ Log(level, msg string) }

type zap struct{}
func (zap) Infow(msg string, kv ...any) {}

type ZapAdapter struct{ z zap }
func (a ZapAdapter) Log(level, msg string) { a.z.Infow(msg, "level", level) }
```

---

### 2.2 Bridge

**Intent**: Decouple an abstraction from its implementation so both can vary independently.

```go
type Sender interface{ Send(to, msg string) error }
type EmailSender struct{}; func (EmailSender) Send(to, m string) error { return nil }
type SMSSender struct{};   func (SMSSender) Send(to, m string) error { return nil }

type Notifier struct{ sender Sender }
func (n Notifier) Notify(to, msg string) error { return n.sender.Send(to, msg) }

type UrgentNotifier struct{ Notifier }
func (n UrgentNotifier) Notify(to, msg string) error { return n.sender.Send(to, "URGENT: "+msg) }
```

---

### 2.3 Composite

**Intent**: Treat a tree of objects uniformly with leaves.

```go
type Node interface{ Size() int64 }

type File struct{ Bytes int64 }
func (f File) Size() int64 { return f.Bytes }

type Dir struct{ Children []Node }
func (d Dir) Size() int64 {
    var total int64
    for _, c := range d.Children { total += c.Size() }
    return total
}
```

---

### 2.4 Decorator

**Intent**: Add behavior to an object dynamically by wrapping it. Common for HTTP middleware.

```go
type Handler func(req string) string

func WithLogging(next Handler) Handler {
    return func(req string) string {
        log.Println("req:", req)
        resp := next(req)
        log.Println("resp:", resp)
        return resp
    }
}
func WithRetry(n int, next Handler) Handler {
    return func(req string) string {
        var resp string
        for i := 0; i < n; i++ { resp = next(req); if resp != "" { break } }
        return resp
    }
}
// pipeline := WithLogging(WithRetry(3, baseHandler))
```

---

### 2.5 Facade

**Intent**: Provide a simple, unified interface over a complex subsystem.

```go
type OrderFacade struct {
    payments  PaymentService
    inventory InventoryService
    notify    NotificationService
}
func (f OrderFacade) PlaceOrder(o Order) error {
    if err := f.payments.Charge(o); err != nil { return err }
    if err := f.inventory.Reserve(o); err != nil { return err }
    f.notify.Confirm(o)
    return nil
}
```

---

### 2.6 Flyweight

**Intent**: Share intrinsic state across many instances to save memory (string interning, tokens, glyphs).

```go
type Token struct{ Lexeme string }

var (
    tokenPool = map[string]*Token{}
    mu        sync.Mutex
)

func Intern(s string) *Token {
    mu.Lock(); defer mu.Unlock()
    if t, ok := tokenPool[s]; ok { return t }
    t := &Token{Lexeme: s}
    tokenPool[s] = t
    return t
}
```

---

### 2.7 Proxy

**Intent**: Stand in for another object to add lazy load, access control, caching, or remote call behavior.

```go
type Image interface{ Render() []byte }

type realImage struct{ path string; data []byte }
func (r *realImage) load() { r.data = []byte("pixels") }
func (r *realImage) Render() []byte { if r.data == nil { r.load() }; return r.data }

type CachedImage struct {
    inner Image
    cache []byte
}
func (c *CachedImage) Render() []byte {
    if c.cache == nil { c.cache = c.inner.Render() }
    return c.cache
}
```

---

## 3. Behavioral Patterns

### 3.1 Strategy

**Intent**: Encapsulate interchangeable algorithms behind a common interface.

```go
type Pricing interface{ Price(qty int, unit float64) float64 }

type Regular struct{}
func (Regular) Price(q int, u float64) float64 { return float64(q) * u }

type BulkDiscount struct{}
func (BulkDiscount) Price(q int, u float64) float64 {
    p := float64(q) * u
    if q > 100 { p *= 0.9 }
    return p
}
```

---

### 3.2 Observer / Pub-Sub

**Intent**: When a subject changes, notify all subscribers. Idiomatic Go: channel-based bus.

```go
type EventBus struct {
    mu   sync.RWMutex
    subs map[string][]chan string
}
func New() *EventBus { return &EventBus{subs: map[string][]chan string{}} }
func (b *EventBus) Subscribe(topic string) <-chan string {
    ch := make(chan string, 16)
    b.mu.Lock(); b.subs[topic] = append(b.subs[topic], ch); b.mu.Unlock()
    return ch
}
func (b *EventBus) Publish(topic, msg string) {
    b.mu.RLock(); defer b.mu.RUnlock()
    for _, ch := range b.subs[topic] {
        select { case ch <- msg: default: /* drop slow */ }
    }
}
```

---

### 3.3 Command

**Intent**: Encapsulate a request as an object so it can be queued, logged, undone.

```go
type Command interface{ Execute() error }

type CreateUser struct{ Name string }
func (c CreateUser) Execute() error { fmt.Println("create", c.Name); return nil }

type DeleteUser struct{ ID int }
func (c DeleteUser) Execute() error { fmt.Println("delete", c.ID); return nil }

func Run(cmds []Command) error {
    for _, c := range cmds {
        if err := c.Execute(); err != nil { return err }
    }
    return nil
}
```

---

### 3.4 Chain of Responsibility

**Intent**: Pass a request along a chain until one handler processes it (middleware, validation, escalation).

```go
type Handler interface{ Handle(req string) string }

type AuthHandler struct{ next Handler }
func (h AuthHandler) Handle(req string) string {
    if !strings.HasPrefix(req, "auth:") { return "deny" }
    return h.next.Handle(req)
}
type LogHandler struct{ next Handler }
func (h LogHandler) Handle(req string) string {
    log.Println("got:", req)
    return h.next.Handle(req)
}
type FinalHandler struct{}
func (FinalHandler) Handle(req string) string { return "ok" }
```

---

### 3.5 Mediator

**Intent**: Centralize communication between objects so they don't depend on each other.

```go
type ChatRoom struct{ users map[string]*User }
func (r *ChatRoom) Send(from, to, msg string) { r.users[to].Receive(from, msg) }

type User struct {
    Name string
    room *ChatRoom
}
func (u *User) Send(to, msg string)         { u.room.Send(u.Name, to, msg) }
func (u *User) Receive(from, msg string)    { fmt.Printf("%s -> %s: %s\n", from, u.Name, msg) }
```

---

### 3.6 Iterator

**Intent**: Sequentially access elements without exposing structure.

```go
type PagedIterator struct {
    page  int
    fetch func(page int) ([]string, bool)
    buf   []string
    done  bool
}
func (it *PagedIterator) Next() (string, bool) {
    if len(it.buf) == 0 && !it.done {
        items, more := it.fetch(it.page)
        it.buf = items; it.page++; it.done = !more
    }
    if len(it.buf) == 0 { return "", false }
    v := it.buf[0]; it.buf = it.buf[1:]
    return v, true
}
```

In Go 1.23+, prefer `iter.Seq` / range-over-func for synchronous iteration.

---

### 3.7 State

**Intent**: Object behavior changes with its state (finite state machine — orders, connections).

```go
type State interface{ Next(o *Order) State; Name() string }

type Created struct{}
func (Created) Name() string  { return "created" }
func (Created) Next(o *Order) State { o.Paid = true; return Paid{} }

type Paid struct{}
func (Paid) Name() string     { return "paid" }
func (Paid) Next(o *Order) State    { o.Shipped = true; return Shipped{} }

type Shipped struct{}
func (Shipped) Name() string  { return "shipped" }
func (Shipped) Next(o *Order) State { return Shipped{} }

type Order struct{ Paid, Shipped bool; state State }
func (o *Order) Advance() { o.state = o.state.Next(o) }
```

---

### 3.8 Template Method

**Intent**: Define the skeleton of an algorithm; fill in steps. Use callback fields, not inheritance.

```go
type Importer struct {
    Fetch     func() ([]byte, error)
    Transform func([]byte) ([]byte, error)
    Load      func([]byte) error
}
func (i Importer) Run() error {
    raw, err := i.Fetch();          if err != nil { return err }
    clean, err := i.Transform(raw); if err != nil { return err }
    return i.Load(clean)
}
```

---

### 3.9 Visitor

**Intent**: Add operations to an object structure without changing its classes (AST passes).

```go
type Node interface{ Accept(v Visitor) }
type Num struct{ V int }
func (n Num) Accept(v Visitor) { v.VisitNum(n) }

type Add struct{ L, R Node }
func (n Add) Accept(v Visitor) { v.VisitAdd(n) }

type Visitor interface {
    VisitNum(Num)
    VisitAdd(Add)
}

type Eval struct{ Result int }
func (e *Eval) VisitNum(n Num) { e.Result = n.V }
func (e *Eval) VisitAdd(a Add) {
    l := &Eval{}; a.L.Accept(l)
    r := &Eval{}; a.R.Accept(r)
    e.Result = l.Result + r.Result
}
```

---

### 3.10 Memento

**Intent**: Capture and restore an object's state without exposing internals (undo/redo).

```go
type Editor struct{ text string }
type Memento struct{ snapshot string }

func (e *Editor) Save() Memento     { return Memento{snapshot: e.text} }
func (e *Editor) Restore(m Memento) { e.text = m.snapshot }
func (e *Editor) Type(s string)     { e.text += s }
```

---

### 3.11 Interpreter

**Intent**: Evaluate sentences in a small language (DSL for filters, pricing rules).

```go
type Expr interface{ Eval(ctx map[string]int) int }

type Const struct{ V int }
func (c Const) Eval(_ map[string]int) int { return c.V }

type Var struct{ Name string }
func (v Var) Eval(ctx map[string]int) int { return ctx[v.Name] }

type Plus struct{ A, B Expr }
func (p Plus) Eval(ctx map[string]int) int { return p.A.Eval(ctx) + p.B.Eval(ctx) }
// Plus{A: Var{"x"}, B: Const{1}}.Eval(map[string]int{"x":5}) == 6
```
