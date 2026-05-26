# Go (Golang) Interview Questions — Basic to Advanced (Application Development)

A comprehensive question bank covering Go fundamentals, concurrency, web/API development, performance, testing, and production patterns. Each answer is concise but detailed enough for interview prep and real-world work.

---

## 1. Basics & Language Fundamentals

### 1. What is Go and why was it created?
Go is a statically typed, compiled language created at Google (2007, released 2009 by Robert Griesemer, Rob Pike, Ken Thompson). The motivation: at Google, C++ binaries took 45 minutes to build; Python was too slow for server loads; Java's ecosystem complexity was a maintenance burden. Go's design goals: **fast compilation** (seconds, not minutes), **safe concurrency** (goroutines + channels), **simple language spec** (25 keywords), **single static binary** deployment, and strong tooling out of the box.

```go
// Hello World — the full program
package main

import "fmt"

func main() {
    fmt.Println("Hello, Go!") // no semicolons, braces on same line (enforced)
}
```

Where Go dominates: network services, CLIs, infrastructure tooling (Docker, Kubernetes, Terraform are all written in Go), data pipelines, cloud-native backends.

### 2. Key features.

```go
// 1. Type inference with :=
x := 42              // int inferred
pi := 3.14           // float64 inferred
name := "gopher"     // string inferred

// 2. Multiple return values (idiomatic error handling)
func divide(a, b float64) (float64, error) {
    if b == 0 { return 0, errors.New("division by zero") }
    return a / b, nil
}
result, err := divide(10, 2) // result=5.0, err=nil

// 3. Structural interfaces — no 'implements' keyword
type Animal interface{ Sound() string }
type Dog struct{}
func (d Dog) Sound() string { return "woof" } // Dog satisfies Animal automatically

// 4. First-class functions
add := func(a, b int) int { return a + b }
fmt.Println(add(2, 3)) // 5

// 5. Goroutines — cheap concurrency
go func() { fmt.Println("concurrent!") }()

// 6. Defer — guaranteed cleanup
f, _ := os.Open("file.txt")
defer f.Close() // runs when surrounding function returns
```

Other features: garbage collection, fast compilation (~seconds for large projects), `gofmt` enforces one canonical style, cross-compilation (`GOOS=linux go build`), single static binary (no runtime dependencies).

### 3. `var`, `:=`, `const`.

```go
// var — explicit, works at package or function level
var x int = 5
var y int      // zero value: 0
var z = "auto" // type inferred from right side

// var block
var (
    host = "localhost"
    port = 8080
    debug bool // zero value false
)

// := — short declaration, ONLY inside functions, infers type
func main() {
    name := "gopher"   // string
    count := 0         // int
    result, err := doSomething() // multiple assignment
    _ = err // blank identifier to discard

    // := can redeclare if at least one variable on left is new
    val, err := anotherCall() // err is redeclared, val is new — valid
    _ = val
}

// const — compile-time constant, cannot be a variable or function result
const Pi = 3.14159        // untyped numeric constant — flexible
const MaxRetries = 3      // untyped int
const Version string = "1.0.0" // typed constant

// iota in const blocks
const (
    A = iota // 0
    B        // 1
    C        // 2
)

const (
    KB = 1 << (10 * (iota + 1)) // 1024
    MB                           // 1048576
    GB                           // 1073741824
)
```

Rule of thumb: use `:=` for local variables, `var` for zero-value init or package-level, `const` for values known at compile time.

### 4. Zero values.
Every variable is guaranteed to be initialized — there is no "undefined" in Go.

```go
var i int       // 0
var f float64   // 0.0
var b bool      // false
var s string    // ""
var p *int      // nil
var sl []int    // nil (but safe to append to!)
var m map[string]int // nil (reading is safe, writing panics!)
var ch chan int  // nil
var fn func()   // nil
var err error   // nil (interface with nil type+value)

fmt.Println(i, f, b, s, p, sl, m, ch, fn, err)
// 0 0 false  <nil> [] map[] <nil> <nil> <nil>

// Practical benefit: struct fields have safe zero values
type Server struct {
    Port    int    // 0
    Debug   bool   // false
    Timeout time.Duration // 0 (= no timeout, or handle explicitly)
}
s := Server{} // fully usable without explicit init

// Common gotcha: nil map panics on write
var bad map[string]int
bad["x"] = 1 // PANIC: assignment to entry in nil map

// Fix: initialize it
good := make(map[string]int)
good["x"] = 1 // safe
```

### 5. Slices vs arrays.

#### Arrays — fixed-size value types
`[5]int` has fixed, compile-time length baked into the type. Assignment **copies the entire array**; functions receive a copy unless you pass a pointer.

```go
a := [3]int{1, 2, 3}
b := a        // full copy — b is independent
b[0] = 99
fmt.Println(a[0]) // 1 — unchanged
fmt.Println(b[0]) // 99

// Useful when exact size is part of the contract (e.g. [16]byte for a UUID).
```

#### Slices — dynamic, reference-based
A slice is a three-field header living on the stack: `{ptr *T, len int, cap int}`. Multiple slices can share the same backing array. **Assignment copies the header, not the data**.

```go
s := []int{1, 2, 3, 4, 5}
t := s[1:3]        // t = [2 3], shares backing array with s
t[0] = 99
fmt.Println(s)     // [1 99 3 4 5] — s is mutated through t!
```

#### len vs cap
```go
s := make([]int, 3, 6) // len=3, cap=6
fmt.Println(len(s), cap(s)) // 3 6

s = s[:5]  // extend len within cap — valid
s = s[:7]  // panic: beyond cap
```

#### append and reallocation
When `len == cap`, `append` allocates a **new, larger backing array** (roughly 2× growth), copies all elements, and returns a new slice header. The original slice no longer shares the array — a subtle but common source of bugs.

```go
a := make([]int, 3, 3)
b := a                 // b shares same backing array as a
a = append(a, 4)       // cap exceeded → new backing array for a
a[0] = 99
fmt.Println(b[0])      // 0 — b still points to the OLD array!

// Rule: after append, treat the returned slice as the authoritative one.
```

#### Preallocate when length is known
```go
// Bad — N reallocations for N elements
var out []int
for i := 0; i < 1_000_000; i++ {
    out = append(out, i)
}

// Good — single allocation
out := make([]int, 0, 1_000_000)
for i := 0; i < 1_000_000; i++ {
    out = append(out, i)
}

// Also good when final length is known
out2 := make([]int, 1_000_000)
for i := range out2 { out2[i] = i }
```

#### Slice tricks
```go
// Copy — always use copy; never rely on sharing for safety
src := []int{1, 2, 3}
dst := make([]int, len(src))
copy(dst, src)

// Delete element i (order-preserving)
i := 2
s = append(s[:i], s[i+1:]...)

// Delete element i (swap with last — O(1), changes order)
s[i] = s[len(s)-1]
s = s[:len(s)-1]

// Filter in-place (no alloc)
n := 0
for _, v := range s {
    if v%2 == 0 { s[n] = v; n++ }
}
s = s[:n]
```

#### nil slice vs empty slice
```go
var nilSlice []int        // len=0, cap=0, ptr=nil
empty := []int{}          // len=0, cap=0, ptr≠nil

fmt.Println(nilSlice == nil)  // true
fmt.Println(empty == nil)     // false

// Both: safe to range over, len()=0, append() works
// JSON: nilSlice marshals to null; empty marshals to []
```

#### 2-D slices
```go
// Slice of slices — rows may be different lengths
matrix := make([][]int, 3)
for i := range matrix {
    matrix[i] = make([]int, 4)
}
matrix[1][2] = 7

// Flat storage for cache-friendly access
rows, cols := 3, 4
flat := make([]int, rows*cols)
at := func(r, c int) int { return flat[r*cols+c] }
flat[1*cols+2] = 7
fmt.Println(at(1, 2)) // 7
```

#### Passing slices to functions
A function gets a copy of the header, not the array. Mutations to elements are visible to the caller; but `append` inside the function does NOT grow the caller's slice (it gets a new header).

```go
func fill(s []int) {
    for i := range s { s[i] = i * i } // visible to caller
}
func grow(s []int) []int {
    return append(s, 99) // caller must capture the return
}

s := make([]int, 3)
fill(s)
fmt.Println(s) // [0 1 4]
s = grow(s)
fmt.Println(s) // [0 1 4 99]
```

#### Key rules
- Use slices; use arrays only when size is semantically part of the type.
- Preallocate with `make([]T, 0, n)` when n is known.
- After `append`, always use the **returned** slice.
- Use `copy` when you need an independent copy.
- Be cautious with sub-slices sharing the backing array — it keeps the entire backing array alive (memory leak risk on large slices).

### 6. Maps.

```go
// Create
m1 := make(map[string]int)           // empty, ready to use
m2 := map[string]int{"a": 1, "b": 2} // literal

// Write
m1["score"] = 100

// Read — missing key returns zero value, NOT error
val := m1["missing"] // 0 — no panic

// Comma-ok to distinguish zero value from missing key
val, ok := m1["score"] // val=100, ok=true
val, ok = m1["missing"] // val=0, ok=false
if !ok {
    fmt.Println("key not found")
}

// Delete
delete(m1, "score")

// Iterate — order is intentionally randomized every run
for k, v := range m2 {
    fmt.Printf("%s → %d\n", k, v)
}

// Nested maps
graph := map[string]map[string]int{}
graph["a"] = map[string]int{"b": 5}

// Nil map — reads are safe, writes panic
var nilMap map[string]int
fmt.Println(nilMap["x"]) // 0, no panic
nilMap["x"] = 1          // PANIC

// Concurrent use — sync.RWMutex
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}
func (s *SafeMap) Get(k string) int {
    s.mu.RLock(); defer s.mu.RUnlock()
    return s.m[k]
}
func (s *SafeMap) Set(k string, v int) {
    s.mu.Lock(); defer s.mu.Unlock()
    s.m[k] = v
}

// Or use sync.Map for high-contention key sets
var sm sync.Map
sm.Store("key", 42)
if v, ok := sm.Load("key"); ok {
    fmt.Println(v.(int)) // 42
}
```

Key performance notes: maps are O(1) average for get/set; worst case O(n) on hash collision. Pre-size with `make(map[K]V, n)` to avoid repeated rehashing.

### 7. Strings and runes.

```go
s := "Hello, 世界" // UTF-8 encoded, immutable byte sequence

fmt.Println(len(s))           // 13 bytes ("世" = 3 bytes each)
fmt.Println(len([]rune(s)))   // 9 characters (runes)

// Range iterates by Unicode code point (rune), not byte
for i, r := range s {
    fmt.Printf("byte[%d] = %c (U+%04X)\n", i, r, r)
}
// byte[0] = H, byte[7] = 世 (U+4E16), ...

// Byte indexing
fmt.Println(s[0])       // 72 (byte value of 'H')
fmt.Println(string(s[7])) // not '世' — it's a partial byte!

// Safe character access: convert to []rune
runes := []rune(s)
fmt.Println(string(runes[7])) // 世

// strings package — common operations
import "strings"
fmt.Println(strings.ToUpper("hello"))        // HELLO
fmt.Println(strings.Contains("gopher", "go")) // true
fmt.Println(strings.Split("a,b,c", ","))      // [a b c]
fmt.Println(strings.TrimSpace("  hi  "))      // "hi"
fmt.Println(strings.HasPrefix("gopher", "go")) // true
fmt.Println(strings.Replace("aaa", "a", "b", 2)) // "bba"
fmt.Println(strings.Join([]string{"a","b"}, "-")) // a-b
fmt.Println(strings.Count("cheese", "e"))     // 3

// String building — use strings.Builder (no allocs per concat)
var b strings.Builder
for i := 0; i < 5; i++ {
    fmt.Fprintf(&b, "item%d,", i)
}
result := b.String() // "item0,item1,item2,item3,item4,"

// Conversions
bytes := []byte(s)        // string → []byte (copies)
back := string(bytes)     // []byte → string (copies)
code := rune('A')         // rune = int32 = Unicode code point
fmt.Println(string(code)) // A

// Immutability — strings cannot be mutated in place
// bytes := []byte(s); bytes[0]='h'; s = string(bytes) // must copy
```

### 8. Pointers.

```go
// Basic pointer operations
x := 42
p := &x          // p is *int, holds address of x
fmt.Println(*p)  // 42  — dereference
*p = 100         // mutate x through p
fmt.Println(x)   // 100

// new() allocates zeroed memory, returns pointer
p2 := new(int)   // *int pointing to 0
*p2 = 7

// Pointer enables mutation in functions
func increment(n *int) { *n++ }
count := 5
increment(&count)
fmt.Println(count) // 6

// Without pointer — receives a copy
func noOp(n int) { n++ } // caller's value unchanged

// Nil pointer
var ptr *int
fmt.Println(ptr)  // <nil>
// fmt.Println(*ptr) // PANIC: nil pointer dereference
if ptr != nil {
    fmt.Println(*ptr) // safe
}

// Large struct — pass by pointer to avoid copying
type Config struct {
    DB       string
    Cache    string
    Timeout  time.Duration
    MaxConns int
    // ... imagine 50 fields
}
func startServer(cfg *Config) { // avoids copying the whole struct
    fmt.Println(cfg.DB)
}

// Pointer receivers for mutation
type Counter struct{ n int }
func (c *Counter) Inc() { c.n++ }  // mutates the actual Counter
func (c Counter) Value() int { return c.n } // read-only, value receiver ok

c := &Counter{}
c.Inc(); c.Inc()
fmt.Println(c.Value()) // 2

// Go does NOT have pointer arithmetic (unlike C)
// p++ // does not exist in Go — safe by design

// Compiler chooses stack vs heap (escape analysis)
// &localVar is fine — compiler moves it to heap if it escapes
func newInt(v int) *int {
    x := v  // compiler detects x escapes, allocates on heap
    return &x
}
```

### 9. Structs.

```go
// Definition
type User struct {
    ID        int
    Name      string
    Email     string
    CreatedAt time.Time
}

// Initialization — named fields (preferred)
u1 := User{ID: 1, Name: "Alice", Email: "a@b.com"}

// Positional (avoid — breaks if fields are reordered)
u2 := User{1, "Bob", "b@c.com", time.Now()}

// Pointer to struct
u3 := &User{ID: 3, Name: "Carol"}
u3.Email = "c@d.com" // auto-dereferenced, same as (*u3).Email

// Zero value — all fields at zero, perfectly valid
var u4 User
fmt.Println(u4.Name) // ""

// Structs are VALUE types — assignment copies ALL fields
a := User{ID: 1}
b := a        // full copy
b.ID = 99
fmt.Println(a.ID) // 1 — unchanged

// Embedding — composition over inheritance
type Address struct {
    Street string
    City   string
}
type Employee struct {
    User          // embedded — promotes User's fields and methods
    Address       // embedded
    Department string
}

e := Employee{
    User:       User{ID: 10, Name: "Dan"},
    Address:    Address{Street: "123 Main", City: "NYC"},
    Department: "Engineering",
}
fmt.Println(e.Name)   // promoted from User
fmt.Println(e.City)   // promoted from Address
fmt.Println(e.User.ID) // explicit access also works

// Struct tags (used by encoding/json, validate, db, etc.)
type Product struct {
    ID    int    `json:"id" db:"product_id"`
    Price float64 `json:"price,omitempty"`
    internal string // unexported — not serialized
}

// Anonymous structs — useful for one-off shapes (tests, API responses)
response := struct {
    Code    int    `json:"code"`
    Message string `json:"message"`
}{Code: 200, Message: "ok"}

// Comparing structs — comparable if all fields are comparable
p1 := struct{ x, y int }{1, 2}
p2 := struct{ x, y int }{1, 2}
fmt.Println(p1 == p2) // true
```

### 10. Methods.

```go
type Rectangle struct {
    Width, Height float64
}

// Value receiver — receives a COPY, doesn't mutate
func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}
func (r Rectangle) Perimeter() float64 {
    return 2 * (r.Width + r.Height)
}

// Pointer receiver — mutates the actual struct
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor
    r.Height *= factor
}

rect := Rectangle{Width: 3, Height: 4}
fmt.Println(rect.Area())      // 12
rect.Scale(2)                  // modifies rect directly
fmt.Println(rect.Width)       // 6

// Go auto-takes address: rect.Scale(2) is (&rect).Scale(2)
// Go auto-dereferences: (*ptr).Area() can be written as ptr.Area()

// Methods on non-struct types
type Celsius float64
type Fahrenheit float64

func (c Celsius) ToF() Fahrenheit {
    return Fahrenheit(c*9/5 + 32)
}

boil := Celsius(100)
fmt.Println(boil.ToF()) // 212

// When to use pointer vs value receiver:
// - Use POINTER if: method mutates the receiver, or struct is large
// - Use VALUE if: method doesn't mutate and struct is small (like time.Time)
// - Be CONSISTENT per type: if any method is pointer, make all pointer

// Methods satisfy interfaces
type Shape interface {
    Area() float64
}
func printArea(s Shape) {
    fmt.Printf("Area: %.2f\n", s.Area())
}
var r Shape = rect // rect's type has Area() — satisfies Shape
printArea(r)
```

### 11. Interfaces.

```go
// Define interface
type Stringer interface {
    String() string
}

// Any type with a String() method satisfies it — no declaration needed
type Color int
const (Red Color = iota; Green; Blue)
func (c Color) String() string {
    return [...]string{"Red", "Green", "Blue"}[c]
}

var s Stringer = Red
fmt.Println(s.String()) // Red

// Compose interfaces
type ReadWriter interface {
    io.Reader
    io.Writer
}

// Empty interface — holds any value
var anything interface{} = 42
anything = "hello"
anything = []int{1, 2, 3}

// Go 1.18+ alias
var v any = true

// Type assertion — extract the concrete value
func describe(i interface{}) {
    switch v := i.(type) {
    case int:    fmt.Printf("int: %d\n", v)
    case string: fmt.Printf("string: %q\n", v)
    case bool:   fmt.Printf("bool: %t\n", v)
    default:     fmt.Printf("unknown: %T\n", v)
    }
}

// Single type assertion (panics if wrong type; use comma-ok)
n, ok := anything.(int)
if !ok {
    fmt.Println("not an int")
}

// Interface with multiple methods
type Animal interface {
    Sound() string
    Name() string
}
type Dog struct{ name string }
func (d Dog) Sound() string { return "woof" }
func (d Dog) Name() string  { return d.name }

var a Animal = Dog{name: "Rex"}
fmt.Println(a.Name(), "says", a.Sound())

// Polymorphism
func makeNoise(animals []Animal) {
    for _, a := range animals {
        fmt.Println(a.Name(), ":", a.Sound())
    }
}

// Design rule: define interfaces in the CONSUMER package, keep them SMALL
// io.Reader (1 method) > any large interface
```

### 12. Interface satisfaction & nil interface gotcha.

An interface value is an internal pair `(type, value)`. It is `nil` only when **both** the type and value are nil.

```go
// Classic bug
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

func riskyOp(fail bool) error {
    var err *MyError // typed nil pointer
    if fail {
        err = &MyError{"something broke"}
    }
    return err // BUG: returns interface{type=*MyError, value=nil} — NOT nil interface!
}

err := riskyOp(false)
if err != nil {
    fmt.Println("unexpected error:", err) // THIS PRINTS! err is not nil!
}

// Why: the returned interface has type=*MyError, even though value is nil
// interface == nil only when type=nil AND value=nil

// Fix: return nil explicitly when no error
func fixedOp(fail bool) error {
    if fail {
        return &MyError{"broke"}
    }
    return nil // untyped nil — interface(type=nil, value=nil)
}

// Inspecting interface internals
var i interface{} = (*int)(nil) // type=*int, value=nil
fmt.Println(i == nil) // false!

var j interface{} = nil // type=nil, value=nil
fmt.Println(j == nil) // true

// Interface satisfaction check at compile time
type Writer interface{ Write([]byte) (int, error) }
var _ Writer = (*os.File)(nil) // compile error if *os.File doesn't satisfy Writer

// Using reflect to inspect
import "reflect"
fmt.Println(reflect.TypeOf(i))  // *int
fmt.Println(reflect.ValueOf(i)) // <nil>
```

**Rule**: always return `nil` (not a typed nil) from functions returning interface types.

### 13. `error` interface and error handling.

```go
// error is just an interface
type error interface{ Error() string }

// Sentinel errors — for known conditions callers can check
var ErrNotFound = errors.New("not found")
var ErrUnauthorized = errors.New("unauthorized")

// Custom typed error — carries extra info
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed: %s — %s", e.Field, e.Message)
}

// Wrapping errors: %w preserves the chain for errors.Is / errors.As
func getUser(id int) (*User, error) {
    u, err := db.Query(id)
    if err != nil {
        return nil, fmt.Errorf("getUser(%d): %w", id, err) // wraps with context
    }
    if u == nil {
        return nil, fmt.Errorf("getUser(%d): %w", id, ErrNotFound)
    }
    return u, nil
}

// errors.Is — checks anywhere in the unwrap chain
u, err := getUser(99)
if errors.Is(err, ErrNotFound) {
    // handle not found (even if err is wrapped)
}

// errors.As — extract typed error anywhere in the chain
var valErr *ValidationError
if errors.As(err, &valErr) {
    fmt.Println("field:", valErr.Field)
}

// errors.Unwrap — one level
fmt.Println(errors.Unwrap(fmt.Errorf("wrap: %w", ErrNotFound))) // 'not found'

// Multi-error wrapping (Go 1.20+)
err1, err2 := errors.New("e1"), errors.New("e2")
combined := errors.Join(err1, err2)
fmt.Println(errors.Is(combined, err1)) // true
fmt.Println(errors.Is(combined, err2)) // true

// Standard pattern
func process() error {
    result, err := step1()
    if err != nil {
        return fmt.Errorf("process step1: %w", err)
    }
    if err := step2(result); err != nil {
        return fmt.Errorf("process step2: %w", err)
    }
    return nil
}

// DON'T: compare error strings
// if err.Error() == "not found" — fragile, breaks with wrapping
// DO: errors.Is / errors.As
```

### 14. `panic` and `recover`.

```go
// panic — aborts the current goroutine, unwinds the stack, runs deferred funcs
func divide(a, b int) int {
    if b == 0 {
        panic("division by zero") // use error return instead in real code
    }
    return a / b
}

// recover — must be in a deferred function; stops the panic and returns the value
func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered panic: %v", r)
        }
    }()
    result = divide(a, b)
    return
}

result, err := safeDiv(10, 0)
fmt.Println(result, err) // 0 recovered panic: division by zero

// Real-world use: HTTP middleware — prevent one panicking handler from crashing the whole server
func Recovery(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("panic: %v\n%s", err, debug.Stack())
                http.Error(w, "internal server error", 500)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// When to panic:
// 1. Programming bugs (nil map, out-of-bounds, invariant violation)
// 2. Initialization failure (can't load config, can't connect to required DB)
// 3. Package-internal: panic then wrap in recover at the public API boundary

// When NOT to panic:
// - Expected error conditions (file not found, invalid input, network error)
// - Anywhere the caller should be able to handle the error
// Rule: if the user of your API can cause it, return error; if it's a bug in your code, panic
```

### 15. `defer`.

```go
// Basic — runs when surrounding function exits (any return path)
func readFile(path string) (string, error) {
    f, err := os.Open(path)
    if err != nil { return "", err }
    defer f.Close() // guaranteed to run, even if we return early

    data, err := io.ReadAll(f)
    if err != nil { return "", err }
    return string(data), nil
}

// LIFO (Last In First Out) — multiple defers unwind in reverse order
func multiDefer() {
    defer fmt.Println("1") // runs 3rd
    defer fmt.Println("2") // runs 2nd
    defer fmt.Println("3") // runs 1st
    fmt.Println("body")
}
// Output: body, 3, 2, 1

// Arguments are evaluated at defer time, NOT at execution time
x := 10
defer fmt.Println("x =", x) // captures x=10 NOW
x = 99
// When defer runs: prints "x = 10" (not 99)

// To capture the final value, use a closure
defer func() { fmt.Println("x =", x) }() // captures x by reference → prints 99

// Named return values — defer can modify them
func doubleWithLog(n int) (result int) {
    defer func() {
        fmt.Printf("result was %d\n", result) // sees the actual return value
    }()
    result = n * 2
    return // returns result
}

// Mutex unlock pattern — defer right after Lock
mu.Lock()
defer mu.Unlock()
// ... safe section ...

// Transaction rollback pattern
tx, _ := db.Begin()
defer tx.Rollback() // no-op if already committed
// ... queries ...
tx.Commit() // on success, Rollback is a no-op

// Defer inside a loop — defers accumulate, run at function exit NOT loop iteration
for _, path := range paths {
    f, err := os.Open(path)
    if err != nil { continue }
    defer f.Close() // BAD: all files stay open until function returns
    // FIX: use an anonymous function
    func() {
        defer f.Close() // runs at end of this anonymous function
        process(f)
    }()
}
```

### 16. Packages and modules.

```
myapp/           ← module root (has go.mod)
  go.mod
  go.sum
  main.go        ← package main
  user/
    user.go      ← package user
    user_test.go ← package user (or user_test for black-box)
  db/
    postgres.go  ← package db
```

```go
// go.mod
module github.com/me/myapp
go 1.22

require (
    github.com/jackc/pgx/v5 v5.5.0
)

// user/user.go
package user

type User struct {    // exported — capital U
    ID   int
    Name string
    hash string      // unexported — lowercase
}

func New(name string) *User { return &User{Name: name} } // exported
func (u *User) setHash(h string) { u.hash = h }         // unexported

// main.go
package main

import (
    "fmt"
    "github.com/me/myapp/user" // full module path
)

func main() {
    u := user.New("Alice")
    fmt.Println(u.Name)
    // u.hash   // compile error: unexported
    // u.setHash // compile error: unexported
}
```

**Commands**:
```bash
go mod init github.com/me/myapp  # create go.mod
go get github.com/pkg/errors     # add dependency
go mod tidy                       # remove unused, add missing
go mod download                   # download all deps to cache
go list -m all                    # list all dependencies
```

**Package naming**: short, lowercase, no underscores. `user` not `userPackage`, `db` not `database_utils`. Import alias to resolve conflicts: `import pq "github.com/lib/pq"`.

### 17. `go.mod` and `go.sum`.

```
# go.mod — human-readable, edit via go get
module github.com/me/myapp

go 1.22

require (
    github.com/jackc/pgx/v5     v5.5.4      // direct
    github.com/redis/go-redis/v9 v9.3.0     // direct
    golang.org/x/sync            v0.6.0     // indirect (dep of a dep)
)

require github.com/some/dep v1.2.3          // specific version pinned

replace github.com/broken/dep => ../local-fork  // local replacement
exclude github.com/bad/dep v1.0.0               // exclude specific version
```

```
# go.sum — machine-generated, DO NOT edit manually
github.com/jackc/pgx/v5 v5.5.4 h1:abc123=
github.com/jackc/pgx/v5 v5.5.4/go.mod h1:def456=
```

- `go.sum` stores **hash of each zip + go.mod** — ensures nobody tampers with a dependency after publishing.
- **Commit both** `go.mod` and `go.sum` — needed for reproducible CI builds.
- `go mod tidy` — removes unused, adds missing; run before every commit.
- `GOMODCACHE` — local cache at `~/go/pkg/mod/`.
- Semantic versioning: major versions ≥2 change the import path (`v2`, `v3`) — breaking change signaling.
- `GOFLAGS=-mod=readonly` in CI to fail if `go.mod` would need updating.

### 18. Visibility.

```go
package mypackage

// EXPORTED — uppercase first letter, accessible from other packages
type Server struct {
    Addr string // exported field
    port int    // unexported field — external callers cannot access directly
}

const MaxRetries = 3  // exported constant
var DefaultTimeout = 30 * time.Second // exported variable

func NewServer(addr string, port int) *Server { // exported constructor
    return &Server{Addr: addr, port: port}
}

func (s *Server) Listen() error { return nil } // exported method
func (s *Server) dial() error { return nil }   // unexported method

// UNEXPORTED — lowercase, package-internal only
type connPool struct{ conns []net.Conn }
var globalState = make(map[string]any)
func helper() {}

// Internal packages: pkg/internal/... can only be imported by the parent module
// good for splitting a module without exposing internals as public API
```

```
// visibility is by PACKAGE, not file
// both files in same package can access each other's unexported identifiers
mypackage/
  server.go    → package mypackage  (can access pool.go's unexported stuff)
  pool.go      → package mypackage
  server_test.go → package mypackage (white-box test, can access unexported)
  server_ext_test.go → package mypackage_test (black-box, only exported API)
```

### 19. `init()` functions.

```go
package main

import (
    _ "github.com/lib/pq" // blank import: run pq's init() to register the driver
)

// init runs automatically; no way to call it or pass args
func init() {
    // Runs AFTER all var declarations in the package
    // Runs BEFORE main()
    log.Println("app initializing")
}

// Multiple init() in same file — all run in order
func init() {
    setupConfig()
}
func init() {
    connectDB()
}

// init() in imported packages runs first (dependency order)
// package A imports package B: B's init() runs before A's

// Typical uses:
// 1. Register codec/driver (database drivers, image formats, encoding)
// 2. Set up global config that can't be done with a simple var
// 3. Validate required environment variables at startup
func init() {
    required := []string{"DB_URL", "API_KEY"}
    for _, key := range required {
        if os.Getenv(key) == "" {
            log.Fatalf("required env var %s not set", key)
        }
    }
}

// Prefer explicit initialization over init() when possible
// init() makes code harder to test and reason about
// If you need complex startup, prefer: cfg, err := config.Load() in main()
```

### 20. `iota`.

```go
// Basic enum
type Direction int
const (
    North Direction = iota // 0
    East                   // 1
    South                  // 2
    West                   // 3
)
fmt.Println(North, East, South, West) // 0 1 2 3

// String method for readable output
func (d Direction) String() string {
    return [...]string{"North", "East", "South", "West"}[d]
}
fmt.Println(North) // North (uses String())

// Skip values with blank identifier
const (
    _ = iota // skip 0
    One      // 1
    Two      // 2
    Three    // 3
)

// Bit flags — perfect for combining permissions
type Permission uint
const (
    Read    Permission = 1 << iota // 1 (001)
    Write                          // 2 (010)
    Execute                        // 4 (100)
)

perms := Read | Write
fmt.Println(perms & Read != 0)    // true — has Read
fmt.Println(perms & Execute != 0) // false — no Execute

func (p Permission) String() string {
    var parts []string
    if p&Read != 0    { parts = append(parts, "read") }
    if p&Write != 0   { parts = append(parts, "write") }
    if p&Execute != 0 { parts = append(parts, "execute") }
    return strings.Join(parts, "|")
}
fmt.Println(perms) // read|write

// Expressions with iota
const (
    KB = 1024 * (1 << (10 * iota)) // 1024
    MB                               // 1048576
    GB                               // 1073741824
    TB
)

// iota resets to 0 in each const block
const X = iota // 0 — new block, resets
const (
    Y = iota // 0 — also resets in this new block
    Z        // 1
)
```

---

## 2. Concurrency

### 21. Goroutines.

Goroutines are **user-space threads** managed by the Go runtime, not the OS. They start with ~2 KB of stack that grows/shrinks as needed (up to 1 GB by default). The runtime uses an **M:N scheduler**: M goroutines multiplexed onto N OS threads.

```go
// Start a goroutine with the 'go' keyword
func sayHello(name string) {
    fmt.Println("Hello,", name)
}

go sayHello("Alice") // runs concurrently, main doesn't wait

// Anonymous goroutine — common pattern
go func() {
    fmt.Println("background task")
}()

// The classic closure-in-loop bug
for i := 0; i < 3; i++ {
    go func() { fmt.Println(i) }() // BUG: all goroutines may see i=3
}
// FIX: capture the value
for i := 0; i < 3; i++ {
    i := i // shadow with a new variable per iteration
    go func() { fmt.Println(i) }() // 0, 1, 2 in some order
}

// Must synchronize to wait for goroutines
var wg sync.WaitGroup
for i := 0; i < 5; i++ {
    wg.Add(1)
    go func(n int) {
        defer wg.Done()
        fmt.Println("worker", n)
    }(i)
}
wg.Wait() // blocks until all 5 are done

// Goroutines are cheap — spawning 100,000 is realistic
for i := 0; i < 100_000; i++ {
    go func() { /* 2KB stack each */ }()
}
// OS threads: 1-100; goroutines: millions — this is Go's superpower

// GOMAXPROCS: number of OS threads that can run goroutines simultaneously
// Default = number of logical CPUs; tune with runtime.GOMAXPROCS(n)
fmt.Println(runtime.NumCPU(), runtime.GOMAXPROCS(0))
```

### 22. Channels.

```go
// --- Unbuffered channel ---
ch := make(chan int) // zero capacity

go func() {
    ch <- 42 // BLOCKS until someone reads
}()
val := <-ch // BLOCKS until someone writes
fmt.Println(val) // 42

// Unbuffered = rendezvous point = synchronization guarantee
// The send and receive happen at the same instant

// --- Buffered channel ---
buf := make(chan int, 3) // capacity 3
buf <- 1 // doesn't block — space available
buf <- 2
buf <- 3
// buf <- 4 // would BLOCK — full
fmt.Println(<-buf) // 1

// --- Direction-typed channels ---
func producer(out chan<- int) { // send-only
    out <- 99
    close(out)
}
func consumer(in <-chan int) { // receive-only
    for v := range in {
        fmt.Println(v)
    }
}

// Use direction typing to express intent and catch misuse at compile time

// --- Ranging over a channel ---
ch2 := make(chan string, 2)
ch2 <- "a"
ch2 <- "b"
close(ch2)
for msg := range ch2 { // loop ends when channel is closed and drained
    fmt.Println(msg) // a, b
}

// --- Comma-ok to detect closed channel ---
v, ok := <-ch2
fmt.Println(v, ok) // "" false — closed and empty

// --- Nil channel blocks forever ---
var nilCh chan int
// <-nilCh // blocks forever; select case on nil channel is never chosen

// --- Common patterns ---
// Signal channel (done)
done := make(chan struct{}) // zero-size struct, no data
go func() {
    doWork()
    close(done) // signal completion to all listeners
}()
<-done // wait for signal

// Pipeline step
func double(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for v := range in { out <- v * 2 }
    }()
    return out
}
```

### 23. Select statement.

`select` blocks until one of its channel cases is ready, then executes it. If multiple are ready, one is chosen **randomly** (fairness).

```go
// Basic fan-in: merge two channels
func merge(a, b <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for {
            select {
            case v, ok := <-a:
                if !ok { a = nil; continue } // nil channel never selected
                out <- v
            case v, ok := <-b:
                if !ok { b = nil; continue }
                out <- v
            }
            if a == nil && b == nil { return }
        }
    }()
    return out
}

// Timeout pattern
func fetchWithTimeout(url string) ([]byte, error) {
    result := make(chan []byte, 1)
    go func() {
        body, _ := http.Get(url)
        result <- body
    }()
    select {
    case b := <-result:
        return b, nil
    case <-time.After(2 * time.Second):
        return nil, errors.New("timeout")
    }
}

// Cancellation with context
func worker(ctx context.Context, jobs <-chan Job) {
    for {
        select {
        case <-ctx.Done():
            return // stop cleanly
        case j, ok := <-jobs:
            if !ok { return }
            process(j)
        }
    }
}

// Non-blocking send/receive with default
func tryReceive(ch <-chan int) (int, bool) {
    select {
    case v := <-ch:
        return v, true
    default:
        return 0, false // channel empty, don't block
    }
}

func trySend(ch chan<- int, v int) bool {
    select {
    case ch <- v:
        return true
    default:
        return false // channel full, don't block
    }
}

// select with nil disables a case
var ch1, ch2 chan int
// neither case will ever fire — nil channels block forever in select
select {
case <-ch1: // never chosen
case <-ch2: // never chosen
}
```

### 24. `sync.WaitGroup`.

```go
var wg sync.WaitGroup

// Pattern: Add before go, Done deferred inside goroutine
for i := 0; i < 5; i++ {
    wg.Add(1)         // increment BEFORE starting goroutine
    go func(n int) {
        defer wg.Done() // decrement when goroutine exits
        fmt.Println("worker", n)
    }(i)
}
wg.Wait() // blocks until counter reaches 0

// WRONG: Add inside goroutine — race condition
for i := 0; i < 5; i++ {
    go func(n int) {
        wg.Add(1)        // BUG: Wait() might run before Add()
        defer wg.Done()
    }(i)
}
wg.Wait() // may return before all goroutines run

// Collecting results with WaitGroup + mutex
var (
    mu      sync.Mutex
    results []string
)
for _, url := range urls {
    wg.Add(1)
    go func(u string) {
        defer wg.Done()
        body, err := fetch(u)
        if err != nil { return }
        mu.Lock()
        results = append(results, body) // protect shared slice
        mu.Unlock()
    }(url)
}
wg.Wait()
// Better alternative: use errgroup (see Q33) for error propagation

// Don't copy a WaitGroup — always pass by pointer
func doWork(wg *sync.WaitGroup) {
    defer wg.Done()
    // ...
}
```

### 25. `sync.Mutex` / `RWMutex`.

```go
// Mutex — exclusive lock (one goroutine at a time)
type SafeCounter struct {
    mu    sync.Mutex
    count int
}
func (c *SafeCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock() // always defer — released even on panic
    c.count++
}
func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

// RWMutex — many readers OR one writer
type Cache struct {
    mu    sync.RWMutex
    store map[string]string
}
func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()         // multiple readers can hold RLock simultaneously
    defer c.mu.RUnlock()
    v, ok := c.store[key]
    return v, ok
}
func (c *Cache) Set(key, val string) {
    c.mu.Lock()          // exclusive write lock — blocks all readers + writers
    defer c.mu.Unlock()
    c.store[key] = val
}

// IMPORTANT: never copy a Mutex (or any sync type) — the lock state is in the value
var m sync.Mutex
m2 := m   // BUG: m2 has copied state — vet will warn you
// FIX: pass *sync.Mutex or embed in a struct and pass *struct

// Try-lock (Go 1.18+)
if m.TryLock() {
    defer m.Unlock()
    // acquired; do work
} else {
    // couldn't acquire, do something else
}

// Mutex vs Channel guideline:
// Mutex: protecting shared memory that's accessed in place (counters, maps, caches)
// Channel: passing ownership/data between goroutines, signaling events
```

### 26. `sync.Once`.

```go
// Classic singleton pattern
type DB struct{ conn *sql.DB }
var (
    instance *DB
    once     sync.Once
)
func GetDB() *DB {
    once.Do(func() {
        conn, _ := sql.Open("pgx", os.Getenv("DB_URL"))
        instance = &DB{conn: conn}
    })
    return instance
}
// No matter how many goroutines call GetDB() concurrently,
// the database is opened exactly once. Other goroutines wait
// for the first Do() to finish, then all receive the same instance.

// Lazy init with error capture
type Config struct {
    once sync.Once
    cfg  *AppConfig
    err  error
}
func (c *Config) Get() (*AppConfig, error) {
    c.once.Do(func() {
        c.cfg, c.err = loadFromDisk()
    })
    return c.cfg, c.err
}

// Once cannot be reset — once done, always done
// If you need a resettable singleton, use a pointer with atomic swap or mutex

// Why not double-checked locking (DCL)?
// var instance *DB
// if instance == nil {          // race! another goroutine may be writing
//     mu.Lock()
//     if instance == nil {      // needs atomic or memory barrier
//         instance = &DB{}
//     }
//     mu.Unlock()
// }
// sync.Once handles all of this correctly internally.
```

### 27. `sync.Pool`.

```go
// bufPool reduces allocations in hot paths (e.g. JSON encoding in HTTP handlers)
var bufPool = sync.Pool{
    New: func() any {
        return bytes.NewBuffer(make([]byte, 0, 1024)) // initial capacity 1KB
    },
}

func handler(w http.ResponseWriter, r *http.Request) {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()      // clear contents
        bufPool.Put(buf) // return to pool
    }()

    // use buf for temp work — no heap allocation per request
    json.NewEncoder(buf).Encode(response)
    w.Write(buf.Bytes())
}

// Key properties:
// - Get() returns a pooled object or calls New() if pool is empty
// - Put() returns an object to the pool
// - The GC MAY evict pool entries at any GC cycle (no guarantee of retention)
// - Not a fixed-size pool — size fluctuates with GC
// - NOT safe for objects needing deterministic lifecycle (like DB connections)

// fmt package uses sync.Pool internally for its buffers
// encoding/json uses it for scratch space

// Bench: with pool vs without
// BenchmarkWithPool    1000000   650 ns/op    0 allocs/op
// BenchmarkWithoutPool 1000000  3200 ns/op  128 allocs/op

// DON'T use sync.Pool for:
// - Connection pools (use database/sql or a dedicated pool library)
// - Objects with finalize/Close semantics
// - When you need a bounded pool (use a buffered channel instead)
resources := make(chan *Resource, 10) // bounded pool via channel
```

### 28. Context.

```go
// context.Context is an immutable interface:
// Deadline() — when context expires
// Done()     — channel closed when cancelled/expired
// Err()      — nil, Canceled, or DeadlineExceeded
// Value(key) — request-scoped values

// Root contexts
ctx := context.Background() // always non-nil, never cancelled — use in main/init
ctx2 := context.TODO()      // placeholder when you'll add context later

// WithCancel — manual cancellation
ctx, cancel := context.WithCancel(context.Background())
defer cancel() // ALWAYS defer cancel to avoid goroutine leaks

go func() {
    select {
    case <-ctx.Done():
        fmt.Println("cancelled:", ctx.Err())
    case result := <-doWork():
        fmt.Println(result)
    }
}()
cancel() // cancel immediately

// WithTimeout — auto-cancel after duration
ctx, cancel = context.WithTimeout(context.Background(), 2*time.Second)
defer cancel()
if err := callExternalAPI(ctx); err != nil {
    if errors.Is(err, context.DeadlineExceeded) {
        fmt.Println("API call timed out")
    }
}

// WithDeadline — cancel at absolute time
deadline := time.Now().Add(500 * time.Millisecond)
ctx, cancel = context.WithDeadline(context.Background(), deadline)
defer cancel()

// WithValue — request-scoped data (trace IDs, auth info)
type ctxKey struct{} // private type to avoid collisions
ctx = context.WithValue(ctx, ctxKey{}, "trace-id-123")

// Retrieve value
if id, ok := ctx.Value(ctxKey{}).(string); ok {
    fmt.Println("trace:", id)
}

// Propagate ctx through the call chain
func handleRequest(ctx context.Context, req Request) error {
    user, err := getUser(ctx, req.UserID)  // ctx passed down
    if err != nil { return err }
    return sendEmail(ctx, user.Email)       // ctx passed down
}

func getUser(ctx context.Context, id int) (*User, error) {
    // DB call respects the timeout set by the caller
    return db.QueryRowContext(ctx, "SELECT ...", id).Scan(...)
}

// Rules:
// 1. Always pass ctx as the FIRST parameter
// 2. Never store ctx in a struct field (pass it through the call chain)
// 3. Always call cancel() (use defer)
// 4. Use context.Value only for request-scoped metadata, not function args
// 5. A cancelled ctx propagates to ALL child contexts created from it
```

### 29. Common concurrency patterns.

```go
// --- WORKER POOL ---
func workerPool(ctx context.Context, n int, jobs <-chan Job) error {
    g, gctx := errgroup.WithContext(ctx)
    for i := 0; i < n; i++ {
        g.Go(func() error {
            for {
                select {
                case <-gctx.Done(): return gctx.Err()
                case j, ok := <-jobs:
                    if !ok { return nil }
                    if err := process(gctx, j); err != nil { return err }
                }
            }
        })
    }
    return g.Wait()
}

// --- FAN-OUT / FAN-IN ---
func fanOutFanIn(urls []string) []Result {
    results := make(chan Result, len(urls))
    var wg sync.WaitGroup
    for _, u := range urls {
        wg.Add(1)
        go func(url string) {
            defer wg.Done()
            results <- fetch(url) // fan-out: N goroutines
        }(u)
    }
    go func() { wg.Wait(); close(results) }()

    var out []Result
    for r := range results { out = append(out, r) } // fan-in: single collector
    return out
}

// --- PIPELINE ---
func pipeline(ctx context.Context, src []int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, v := range src {
            select {
            case out <- v * v:
            case <-ctx.Done(): return
            }
        }
    }()
    return out
}

// --- SEMAPHORE (limit concurrency) ---
sem := make(chan struct{}, 8) // max 8 concurrent
for _, task := range tasks {
    sem <- struct{}{}          // acquire
    go func(t Task) {
        defer func() { <-sem }() // release
        run(t)
    }(task)
}

// --- DONE CHANNEL ---
done := make(chan struct{})
go func() {
    for {
        select {
        case <-done: return
        default:
            doWork()
        }
    }
}()
time.Sleep(time.Second)
close(done) // stop the goroutine
```

### 30. Race conditions and the race detector.

```go
// Race condition example — concurrent reads and writes without protection
var counter int
for i := 0; i < 1000; i++ {
    go func() { counter++ }() // DATA RACE: read-modify-write is not atomic
}
// Result: counter value is unpredictable

// go run -race / go test -race instruments ALL memory accesses
// Reports the exact goroutines, file, line number of the conflicting accesses
/*
==================
WARNING: DATA RACE
Write at 0x... by goroutine 7:  main.main.func1()
                                    main.go:8
Previous write at 0x... by goroutine 6: main.main.func1()
                                    main.go:8
==================
*/

// Fix 1: sync.Mutex
var mu sync.Mutex
var safe int
for i := 0; i < 1000; i++ {
    go func() { mu.Lock(); safe++; mu.Unlock() }()
}

// Fix 2: sync/atomic
var atomicCount atomic.Int64
for i := 0; i < 1000; i++ {
    go func() { atomicCount.Add(1) }()
}

// Fix 3: channel
var chanCount int
incCh := make(chan struct{}, 1000)
for i := 0; i < 1000; i++ {
    go func() { incCh <- struct{}{} }()
}
for i := 0; i < 1000; i++ {
    <-incCh
    chanCount++
}

// Enable race detector in CI:
// go test -race ./...
// go build -race -o myapp-race ./...
// Overhead: ~5-10x slowdown, 5-10x memory — acceptable for tests, not prod
// The race detector uses shadow memory to track every access
```

### 31. Goroutine leaks.

```go
// --- LEAK: goroutine blocked forever ---
func leak() {
    ch := make(chan int)
    go func() {
        val := <-ch // blocked forever — no sender
        fmt.Println(val)
    }()
    // goroutine leaks when leak() returns
}

// --- LEAK: HTTP handler that never closes its goroutine ---
func badHandler(w http.ResponseWriter, r *http.Request) {
    result := make(chan string)
    go func() {
        time.Sleep(10 * time.Second)
        result <- "done" // client may have disconnected by now
    }()
    // If client disconnects, nobody reads result — goroutine leaks
    fmt.Fprint(w, <-result)
}

// --- FIX: use context cancellation ---
func goodHandler(w http.ResponseWriter, r *http.Request) {
    result := make(chan string, 1) // buffered so goroutine doesn't block
    go func() {
        // simulate slow work
        select {
        case <-r.Context().Done(): return // client disconnected
        case <-time.After(10 * time.Second):
            result <- "done"
        }
    }()
    select {
    case <-r.Context().Done():
        return // client gone
    case res := <-result:
        fmt.Fprint(w, res)
    }
}

// --- FIX: always close producer channel when done ---
func producer(ctx context.Context) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch) // signal consumers to stop
        for i := 0; ; i++ {
            select {
            case <-ctx.Done(): return
            case ch <- i:
            }
        }
    }()
    return ch
}

// --- Detect leaks in tests ---
import "go.uber.org/goleak"
func TestNoLeak(t *testing.T) {
    defer goleak.VerifyNone(t) // fails if goroutines leaked
    doSomething()
}

// --- time.Tick leaks ---
// BAD: time.Tick has no way to stop — goroutine leaks
for range time.Tick(time.Second) { /* ... */ }

// GOOD: time.NewTicker can be stopped
ticker := time.NewTicker(time.Second)
defer ticker.Stop()
for {
    select {
    case <-ticker.C: doWork()
    case <-ctx.Done(): return
    }
}
```

### 32. Channels vs mutex — when to use which.

```go
// --- USE CHANNELS when: ---
// 1. Passing ownership of data between goroutines
func pipeline(in <-chan Request) <-chan Response {
    out := make(chan Response)
    go func() {
        defer close(out)
        for req := range in {
            out <- process(req) // ownership of data moves: producer → consumer
        }
    }()
    return out
}

// 2. Signaling events
done := make(chan struct{})
go func() { doWork(); close(done) }()
<-done // wait for completion

// 3. Fan-out / fan-in, pipelines, rate limiting via semaphore
sem := make(chan struct{}, 5) // max 5 concurrent

// --- USE MUTEX when: ---
// 1. Protecting shared state accessed from multiple places in-place
type SharedMap struct {
    mu sync.RWMutex
    m  map[string]int
}
func (s *SharedMap) Get(k string) int {
    s.mu.RLock(); defer s.mu.RUnlock()
    return s.m[k]
}
func (s *SharedMap) Increment(k string) {
    s.mu.Lock(); defer s.mu.Unlock()
    s.m[k]++
}

// 2. Simple counters, caches, in-memory state
// 3. When channel would require serializing access anyway

// Rule of thumb from the Go team:
// "Use whichever is more natural for the problem."
// Channels shine for communication and coordination.
// Mutexes shine for protecting data structures.

// Both patterns are idiomatic Go. The quote
// "Don't communicate by sharing memory; share memory by communicating"
// is a design principle, not an absolute rule.
```

### 33. `errgroup`.

```go
import "golang.org/x/sync/errgroup"

// Basic: parallel fetch with error propagation
func fetchAll(ctx context.Context, urls []string) ([][]byte, error) {
    g, gctx := errgroup.WithContext(ctx)
    results := make([][]byte, len(urls))

    for i, url := range urls {
        i, url := i, url // capture loop vars
        g.Go(func() error {
            body, err := fetchURL(gctx, url)
            if err != nil { return fmt.Errorf("fetch %s: %w", url, err) }
            results[i] = body // safe: different index per goroutine
            return nil
        })
    }
    // Wait blocks until all goroutines finish or one returns an error
    // If any goroutine errors, gctx is cancelled — all others should stop
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}

// With concurrency limit (errgroup.SetLimit, Go 1.21+)
func fetchCapped(ctx context.Context, urls []string) error {
    g, gctx := errgroup.WithContext(ctx)
    g.SetLimit(10) // at most 10 goroutines at a time
    for _, url := range urls {
        url := url
        g.Go(func() error {
            return fetchURL(gctx, url)
        })
    }
    return g.Wait()
}

// Comparison with WaitGroup:
// WaitGroup: doesn't collect errors, doesn't cancel siblings on failure
// errgroup:  first error cancels the context, Wait() returns the error
// Choose errgroup for any parallel work that can fail
```

### 34. Memory model & happens-before.

```go
// The Go memory model guarantees a read of variable x
// observes the value written by a write to x
// IF the write "happens before" the read.

// Without sync primitives, reads and writes may be reordered by the compiler
// or CPU — you may read stale values.

// --- RACES (no happens-before guarantee) ---
var ready bool
var msg string

go func() {
    msg = "hello"   // write
    ready = true    // write
}()
// main goroutine may see ready=true but msg="" — no ordering guarantee!
for !ready {}
fmt.Println(msg) // RACE CONDITION — undefined behavior

// --- FIX: channel establishes happens-before ---
ch := make(chan struct{})
go func() {
    msg = "hello"
    ch <- struct{}{} // send happens-before receive
}()
<-ch
fmt.Println(msg) // safe: guaranteed to see "hello"

// Happens-before guarantees:
// - Channel send happens-before the corresponding receive completes (unbuffered)
// - Close of a channel happens-before a receive of the zero value from that channel
// - sync.Mutex Lock/Unlock: nth Unlock happens-before (n+1)th Lock
// - sync.Once: Do(f) completes before any Do(f) returns
// - goroutine start: go statement happens-before the goroutine's execution starts

// --- FIX: mutex ---
var mu sync.Mutex
go func() {
    mu.Lock()
    msg = "hello"
    mu.Unlock()
}()
mu.Lock()
fmt.Println(msg) // safe
mu.Unlock()

// --- FIX: atomic for simple flags ---
var atomicReady atomic.Bool
go func() {
    msg = "hello"
    atomicReady.Store(true)
}()
for !atomicReady.Load() { runtime.Gosched() }
// Note: still a race on msg — atomicReady doesn't synchronize msg!
// For msg, you STILL need a mutex or channel.
```

### 35. `sync/atomic`.

```go
import "sync/atomic"

// --- Go 1.19+ typed atomics (preferred) ---
var counter atomic.Int64
counter.Store(0)
counter.Add(1)
counter.Add(1)
fmt.Println(counter.Load()) // 2

// Compare-and-swap: only update if current value matches expected
old := counter.Load()
counter.CompareAndSwap(old, old*2) // doubles if nobody else changed it

// atomic.Bool
var running atomic.Bool
running.Store(true)
if running.Load() { fmt.Println("still running") }

// atomic.Pointer[T] — for lock-free pointer swaps
type Config struct{ Debug bool }
var cfg atomic.Pointer[Config]
cfg.Store(&Config{Debug: false})

go func() {
    newCfg := &Config{Debug: true} // create new config atomically
    cfg.Store(newCfg)              // atomic swap — readers see full config or nothing
}()
fmt.Println(cfg.Load().Debug)

// --- Legacy package-level functions ---
var n int64
atomic.AddInt64(&n, 1)
val := atomic.LoadInt64(&n)
atomic.StoreInt64(&n, 42)
swapped := atomic.CompareAndSwapInt64(&n, 42, 100) // returns true if swapped

// When to use atomics vs mutex:
// Atomic: single value, simple ops (inc/dec/load/store/CAS) — no allocation
// Mutex:  multiple related values that must be consistent together
// Example: updating balance + last_updated needs mutex (2 fields must be consistent)
//          updating a hit counter is fine with atomic.Add

// Benchmark: atomic ~5ns/op vs mutex ~25ns/op for simple counter
// The difference matters only under extreme contention (>100k ops/sec)
```

---

## 3. Web & API Development

### 36. `net/http` basics.

```go
// Handler function — signature is fixed
func helloHandler(w http.ResponseWriter, r *http.Request) {
    // Read request
    name := r.URL.Query().Get("name") // ?name=Alice
    if name == "" { name = "World" }

    // Write response
    w.Header().Set("Content-Type", "text/plain")
    w.WriteHeader(http.StatusOK) // optional; defaults to 200
    fmt.Fprintf(w, "Hello, %s!", name)
}

// Register routes and serve
http.HandleFunc("/hello", helloHandler)
http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
    if r.URL.Path != "/" {
        http.NotFound(w, r)
        return
    }
    w.Write([]byte("root"))
})

// DEV only — no timeouts
log.Fatal(http.ListenAndServe(":8080", nil))

// Reading request
func handler(w http.ResponseWriter, r *http.Request) {
    // Method, URL, headers
    fmt.Println(r.Method, r.URL.Path)
    fmt.Println(r.Header.Get("Authorization"))

    // Body (always close)
    defer r.Body.Close()
    body, _ := io.ReadAll(r.Body)

    // Form values
    r.ParseForm()
    val := r.FormValue("field")

    // Path params (Go 1.22+)
    id := r.PathValue("id") // route: /users/{id}

    // JSON body
    var req MyRequest
    json.NewDecoder(r.Body).Decode(&req)

    // Send JSON response
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{"id": id, "val": val})
}
```

### 37. Building an HTTP server with timeouts.

```go
srv := &http.Server{
    Addr:    ":8080",
    Handler: router,

    // Time to read the full request headers
    ReadHeaderTimeout: 5 * time.Second,
    // Time to read the entire request including body
    ReadTimeout:  10 * time.Second,
    // Time to write the response (from end of request to end of response)
    WriteTimeout: 15 * time.Second,
    // How long to keep an idle keep-alive connection open
    IdleTimeout:  60 * time.Second,
    // Max size of request headers
    MaxHeaderBytes: 1 << 20, // 1 MB
}

// Graceful start
go func() {
    if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
        log.Fatalf("listen: %v", err)
    }
}()

// Graceful shutdown on signal
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
<-ctx.Done()

shutCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
if err := srv.Shutdown(shutCtx); err != nil {
    log.Printf("shutdown error: %v", err)
}

// Why timeouts matter:
// Without ReadHeaderTimeout: Slowloris attack — attacker sends headers
//   one byte at a time, keeping connections open, exhausting the server
// Without WriteTimeout: slow client keeps the connection open forever
// Without IdleTimeout: keep-alive connections accumulate
```

### 38. Routers.

```go
// --- Go 1.22+ stdlib ServeMux (recommended for new projects) ---
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    // ...
})
mux.HandleFunc("POST /users", createUser)
mux.HandleFunc("DELETE /users/{id}", deleteUser)

// --- chi (third-party, stdlib-compatible) ---
import "github.com/go-chi/chi/v5"
r := chi.NewRouter()
r.Use(chi.Middleware.Logger)
r.Use(chi.Middleware.Recoverer)
r.Route("/api/v1", func(r chi.Router) {
    r.Get("/users/{id}", getUser)
    r.Post("/users", createUser)
    r.Group(func(r chi.Router) {
        r.Use(authMiddleware)
        r.Delete("/users/{id}", deleteUser)
    })
})
id := chi.URLParam(r, "id")

// --- Gin (popular, fastest among frameworks) ---
import "github.com/gin-gonic/gin"
g := gin.Default() // includes Logger and Recovery middleware
g.GET("/users/:id", func(c *gin.Context) {
    id := c.Param("id")
    c.JSON(200, gin.H{"id": id})
})
g.POST("/users", func(c *gin.Context) {
    var u User
    if err := c.ShouldBindJSON(&u); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    c.JSON(201, u)
})
g.Run(":8080")

// Comparison:
// stdlib mux (1.22+): no deps, good for simple APIs
// chi:     stdlib-compatible, composable middleware, good for REST APIs
// gin:     fastest, rich feature set, most popular
// echo:    similar to gin, clean API
// fiber:   fastest (net) but non-standard interface, Fasthttp-based
```

### 39. Middleware pattern.

```go
// Middleware signature: func(http.Handler) http.Handler

// Logging middleware
func Logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        // Wrap ResponseWriter to capture status code
        rw := &responseWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(rw, r)
        log.Printf("%s %s %d %v", r.Method, r.URL.Path, rw.status, time.Since(start))
    })
}

type responseWriter struct {
    http.ResponseWriter
    status int
}
func (rw *responseWriter) WriteHeader(code int) {
    rw.status = code
    rw.ResponseWriter.WriteHeader(code)
}

// Auth middleware
func Auth(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if !strings.HasPrefix(token, "Bearer ") {
            http.Error(w, "unauthorized", http.StatusUnauthorized)
            return
        }
        user, err := validateToken(strings.TrimPrefix(token, "Bearer "))
        if err != nil {
            http.Error(w, "invalid token", http.StatusUnauthorized)
            return
        }
        // Inject user into context
        ctx := context.WithValue(r.Context(), userKey{}, user)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Recovery middleware
func Recovery(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("panic: %v\n%s", err, debug.Stack())
                http.Error(w, "internal server error", 500)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// Compose: outer runs first
handler := Logging(Auth(Recovery(mux)))
// Request: Logging → Auth → Recovery → handler → Recovery → Auth → Logging
```

### 40. JSON encoding/decoding.

```go
type User struct {
    ID       int       `json:"id"`
    Name     string    `json:"name"`
    Email    string    `json:"email,omitempty"`   // omit if empty string
    Password string    `json:"-"`                 // never marshal
    Created  time.Time `json:"created_at"`
    Tags     []string  `json:"tags,omitempty"`
}

// Marshal (struct → JSON bytes)
u := User{ID: 1, Name: "Alice"}
data, err := json.Marshal(u)
fmt.Println(string(data)) // {"id":1,"name":"Alice","created_at":"0001-..."}

// MarshalIndent — pretty-print
data, _ = json.MarshalIndent(u, "", "  ")

// Unmarshal (JSON bytes → struct)
var u2 User
if err := json.Unmarshal(data, &u2); err != nil {
    log.Fatal(err)
}

// Streaming decoder — preferred for HTTP bodies (no full buffer in memory)
func decodeBody(r *http.Request) (User, error) {
    var u User
    dec := json.NewDecoder(r.Body)
    dec.DisallowUnknownFields() // reject unknown JSON keys
    if err := dec.Decode(&u); err != nil {
        return User{}, fmt.Errorf("decode: %w", err)
    }
    return u, nil
}

// Streaming encoder — preferred for HTTP responses
func writeJSON(w http.ResponseWriter, v any) {
    w.Header().Set("Content-Type", "application/json")
    if err := json.NewEncoder(w).Encode(v); err != nil {
        log.Printf("encode: %v", err)
    }
}

// RawMessage — defer parsing / forward arbitrary JSON
type Envelope struct {
    Type    string          `json:"type"`
    Payload json.RawMessage `json:"payload"` // stays as-is
}

// json.Number — avoid float64 precision loss for big numbers
dec := json.NewDecoder(strings.NewReader(`{"id":9999999999999999}`))
dec.UseNumber()
var m map[string]any
dec.Decode(&m)
fmt.Println(m["id"].(json.Number).String()) // 9999999999999999

// Custom MarshalJSON / UnmarshalJSON
func (u User) MarshalJSON() ([]byte, error) {
    type Alias User
    return json.Marshal(struct {
        Alias
        CreatedUnix int64 `json:"created_unix"`
    }{Alias: Alias(u), CreatedUnix: u.Created.Unix()})
}
```

### 41. Validation.

```go
// go-playground/validator
import "github.com/go-playground/validator/v10"

type CreateUserReq struct {
    Name     string `json:"name"     validate:"required,min=2,max=100"`
    Email    string `json:"email"    validate:"required,email"`
    Age      int    `json:"age"      validate:"gte=0,lte=150"`
    Role     string `json:"role"     validate:"oneof=admin user viewer"`
    Password string `json:"password" validate:"required,min=8"`
}

var validate = validator.New()

func handler(w http.ResponseWriter, r *http.Request) {
    var req CreateUserReq
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid JSON", 400); return
    }
    if err := validate.Struct(req); err != nil {
        // Extract field-level errors
        var ve validator.ValidationErrors
        errors.As(err, &ve)
        errs := map[string]string{}
        for _, fe := range ve {
            errs[fe.Field()] = fe.Tag() // e.g. "Email": "email"
        }
        w.WriteHeader(422)
        json.NewEncoder(w).Encode(errs)
        return
    }
    // proceed with valid req
}

// Custom validator
validate.RegisterValidation("nonempty", func(fl validator.FieldLevel) bool {
    return strings.TrimSpace(fl.Field().String()) != ""
})

// Manual validation (for tighter messages and more control)
type Errors map[string]string
func validateReq(req CreateUserReq) Errors {
    errs := Errors{}
    if req.Name == "" { errs["name"] = "required" }
    if !isValidEmail(req.Email) { errs["email"] = "invalid" }
    if len(errs) > 0 { return errs }
    return nil
}
```

### 42. Request lifecycle / graceful shutdown.

```go
func main() {
    // 1. Build server
    mux := buildRoutes()
    srv := &http.Server{Addr: ":8080", Handler: mux,
        ReadHeaderTimeout: 5 * time.Second,
        WriteTimeout:      30 * time.Second,
        IdleTimeout:       60 * time.Second,
    }

    // 2. Start accepting connections
    go func() {
        log.Println("listening on :8080")
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()

    // 3. Wait for OS signal (SIGINT/SIGTERM from Ctrl-C or Kubernetes)
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()
    <-ctx.Done() // blocks until signal received
    log.Println("shutdown signal received")

    // 4. Graceful shutdown — stop accepting, drain in-flight requests
    shutCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    if err := srv.Shutdown(shutCtx); err != nil {
        log.Printf("forced shutdown: %v", err)
    }

    // 5. Close other resources (DB, message consumers, etc.)
    db.Close()
    log.Println("shutdown complete")
}

// Request lifecycle:
// Accept → ReadHeaderTimeout starts
// → Parse request → ReadTimeout covers body
// → Route match → Handler executes → WriteTimeout starts on first Write
// → Response sent → Connection idle or closed (IdleTimeout)
```

### 43. REST vs gRPC in Go.

```go
// REST: text-based, any HTTP client, easy to debug with curl
// Great for: public APIs, browser clients, simple CRUD
GET  /users/123
Content-Type: application/json
{"id": 123, "name": "Alice"}

// gRPC: binary (protobuf), code-generated clients, streaming, low latency
// Great for: internal microservices, streaming, strongly-typed contracts

// 1. Define the API in .proto
// user.proto
service UserService {
    rpc GetUser(GetUserRequest) returns (User);
    rpc ListUsers(ListUsersRequest) returns (stream User); // server streaming
}
message GetUserRequest { int64 id = 1; }
message User { int64 id = 1; string name = 2; }

// 2. Generate Go code: protoc --go_out=. --go-grpc_out=. user.proto

// 3. Implement server
type server struct{ pb.UnimplementedUserServiceServer }
func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    return &pb.User{Id: req.Id, Name: "Alice"}, nil
}

// 4. Serve
lis, _ := net.Listen("tcp", ":50051")
grpcServer := grpc.NewServer(
    grpc.UnaryInterceptor(loggingInterceptor), // like middleware
)
pb.RegisterUserServiceServer(grpcServer, &server{})
grpcServer.Serve(lis)

// 5. Client
conn, _ := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
client := pb.NewUserServiceClient(conn)
user, err := client.GetUser(ctx, &pb.GetUserRequest{Id: 123})

// REST vs gRPC at a glance:
// REST:  human-readable, no code gen, any language, cache-friendly, stateless
// gRPC:  3-10x smaller payloads, 2-7x faster, bidirectional streaming,
//        strong types, code gen, HTTP/2, harder to debug
```

### 44. gRPC essentials.

```go
// Four RPC types:
// 1. Unary:            client sends one, server replies one
// 2. Server Streaming: client sends one, server replies stream
// 3. Client Streaming: client sends stream, server replies one
// 4. Bidirectional:    both stream

// Server-streaming example
func (s *server) ListUsers(req *pb.ListReq, stream pb.UserService_ListUsersServer) error {
    for _, u := range s.users {
        if err := stream.Send(u); err != nil { return err }
    }
    return nil
}
// Client side:
stream, _ := client.ListUsers(ctx, &pb.ListReq{})
for {
    u, err := stream.Recv()
    if err == io.EOF { break }
    if err != nil { return err }
    fmt.Println(u.Name)
}

// Interceptors (like middleware)
func loggingInterceptor(ctx context.Context, req any, info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler) (any, error) {
    start := time.Now()
    resp, err := handler(ctx, req)
    log.Printf("%s %v %v", info.FullMethod, err, time.Since(start))
    return resp, err
}

// Metadata (like HTTP headers)
md := metadata.Pairs("authorization", "Bearer token123")
ctx := metadata.NewOutgoingContext(ctx, md)

// Status codes
import "google.golang.org/grpc/status"
import "google.golang.org/grpc/codes"
return nil, status.Errorf(codes.NotFound, "user %d not found", id)
return nil, status.Errorf(codes.InvalidArgument, "name is required")

// Check on client:
if st, ok := status.FromError(err); ok {
    switch st.Code() {
    case codes.NotFound: // 404 equivalent
    case codes.Unauthenticated: // 401 equivalent
    }
}
```

### 45. HTTP client best practices.

```go
// Create ONE client and reuse it — it contains the connection pool
var httpClient = &http.Client{
    Timeout: 10 * time.Second, // total timeout for entire request
    Transport: &http.Transport{
        MaxIdleConns:        100,             // total idle connections
        MaxIdleConnsPerHost: 10,              // idle conns per host
        IdleConnTimeout:     90 * time.Second,
        TLSHandshakeTimeout: 5 * time.Second,
        DisableKeepAlives:   false,           // keep-alive is good!
        ForceAttemptHTTP2:   true,
    },
}

// ALWAYS pass context for cancellation
func fetchUser(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil { return nil, err }
    req.Header.Set("Accept", "application/json")
    req.Header.Set("Authorization", "Bearer "+token)

    resp, err := httpClient.Do(req)
    if err != nil { return nil, fmt.Errorf("do: %w", err) }
    defer resp.Body.Close() // ALWAYS close — even on error status codes

    // Read body — limit size to avoid memory exhaustion
    body, err := io.ReadAll(io.LimitReader(resp.Body, 10<<20)) // 10MB max
    if err != nil { return nil, fmt.Errorf("read: %w", err) }

    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("http %d: %s", resp.StatusCode, body)
    }
    return body, nil
}

// POST with JSON body
func postJSON(ctx context.Context, url string, payload any) error {
    data, _ := json.Marshal(payload)
    req, _ := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(data))
    req.Header.Set("Content-Type", "application/json")
    resp, err := httpClient.Do(req)
    if err != nil { return err }
    defer resp.Body.Close()
    io.Copy(io.Discard, resp.Body) // drain body to reuse connection
    return nil
}

// Common mistakes:
// 1. new(http.Client) per request — no connection reuse
// 2. Forgetting resp.Body.Close() — connection leak
// 3. No timeout — hangs forever
// 4. Ignoring error status codes (200 is not guaranteed)
```

### 46. Authentication patterns.

```go
// --- JWT ---
import "github.com/golang-jwt/jwt/v5"

type Claims struct {
    UserID int    `json:"user_id"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

// Issue token
func issueJWT(userID int, role string) (string, error) {
    claims := Claims{
        UserID: userID, Role: role,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            Issuer:    "myapp",
        },
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(os.Getenv("JWT_SECRET")))
}

// Validate token in middleware
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        h := r.Header.Get("Authorization")
        if !strings.HasPrefix(h, "Bearer ") {
            http.Error(w, "missing token", 401); return
        }
        tokenStr := strings.TrimPrefix(h, "Bearer ")
        var claims Claims
        token, err := jwt.ParseWithClaims(tokenStr, &claims, func(t *jwt.Token) (any, error) {
            if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
                return nil, fmt.Errorf("unexpected signing method")
            }
            return []byte(os.Getenv("JWT_SECRET")), nil
        })
        if err != nil || !token.Valid {
            http.Error(w, "invalid token", 401); return
        }
        ctx := context.WithValue(r.Context(), userClaimsKey{}, &claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// --- API Key ---
func APIKeyMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        key := r.Header.Get("X-API-Key")
        hash := sha256.Sum256([]byte(key))
        expected := os.Getenv("API_KEY_HASH") // store hash, not raw key
        if hex.EncodeToString(hash[:]) != expected {
            http.Error(w, "forbidden", 403); return
        }
        next.ServeHTTP(w, r)
    })
}
```

### 47. Configuration management.

```go
// --- Simple: os.Getenv + struct ---
type Config struct {
    DBUrl   string
    Port    int
    Debug   bool
    Timeout time.Duration
}

func LoadConfig() (Config, error) {
    port, err := strconv.Atoi(getEnvOr("PORT", "8080"))
    if err != nil { return Config{}, fmt.Errorf("PORT: %w", err) }
    timeout, _ := time.ParseDuration(getEnvOr("TIMEOUT", "30s"))
    return Config{
        DBUrl:   mustEnv("DATABASE_URL"),
        Port:    port,
        Debug:   os.Getenv("DEBUG") == "true",
        Timeout: timeout,
    }, nil
}
func mustEnv(key string) string {
    v := os.Getenv(key)
    if v == "" { log.Fatalf("required env var %s not set", key) }
    return v
}
func getEnvOr(key, def string) string {
    if v := os.Getenv(key); v != "" { return v }
    return def
}

// --- kelseyhightower/envconfig (popular) ---
import "github.com/kelseyhightower/envconfig"
type Spec struct {
    DBUrl   string        `envconfig:"DATABASE_URL" required:"true"`
    Port    int           `envconfig:"PORT" default:"8080"`
    Timeout time.Duration `envconfig:"TIMEOUT" default:"30s"`
}
var cfg Spec
envconfig.MustProcess("", &cfg)

// --- viper (hierarchical config) ---
import "github.com/spf13/viper"
viper.SetConfigFile("config.yaml")
viper.AutomaticEnv()     // env overrides file
viper.ReadInConfig()
port := viper.GetInt("server.port")

// --- flag for CLI tools ---
var (
    port    = flag.Int("port", 8080, "listening port")
    verbose = flag.Bool("verbose", false, "verbose logging")
)
flag.Parse()
fmt.Println(*port, *verbose)
```

### 48. Logging.

```go
// --- log/slog (Go 1.21+, now the standard) ---
import "log/slog"

// Text handler (dev)
logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
    Level: slog.LevelDebug,
}))

// JSON handler (prod)
logger = slog.New(slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))
slog.SetDefault(logger)

// Structured logging
slog.Info("user created", "user_id", 42, "email", "a@b.com")
slog.Error("db error", "err", err, "query", sql)
slog.Debug("cache miss", "key", key)
slog.Warn("high latency", "duration_ms", 3200)

// With context (trace ID propagation)
logger.With("trace_id", traceID, "service", "user-svc").Info("request started")

// --- uber-go/zap (fastest, more ergonomic) ---
import "go.uber.org/zap"
logger2, _ := zap.NewProduction()
defer logger2.Sync()
logger2.Info("user created", zap.Int("user_id", 42), zap.String("email", "a@b.com"))

// Sugar (less allocation-efficient but nicer)
sugar := logger2.Sugar()
sugar.Infow("user created", "user_id", 42, "email", "a@b.com")

// Rules:
// 1. Always use structured logging (key-value pairs), not fmt.Sprintf in messages
// 2. Include trace_id in every log line (from context)
// 3. Never log passwords, tokens, PII, credit card numbers
// 4. Use Debug for dev noise, Info for business events, Warn for degraded, Error for failures
// 5. Log errors once — where they're handled, not at every level of the call stack
```

### 49. Database access — `database/sql`.

```go
import (
    "database/sql"
    _ "github.com/jackc/pgx/v5/stdlib" // pgx driver registered as "pgx"
)

// Open connection pool (not a single connection)
db, err := sql.Open("pgx", os.Getenv("DATABASE_URL"))
if err != nil { log.Fatal(err) }

// Tune pool
db.SetMaxOpenConns(25)                    // max active connections
db.SetMaxIdleConns(5)                     // keep alive for reuse
db.SetConnMaxLifetime(5 * time.Minute)    // rotate connections
db.SetConnMaxIdleTime(2 * time.Minute)    // evict stale idle conns

// ALWAYS ping on startup to verify connectivity
if err := db.PingContext(ctx); err != nil { log.Fatal(err) }

// Query single row
var u User
err = db.QueryRowContext(ctx,
    "SELECT id, name, email FROM users WHERE id = $1", userID,
).Scan(&u.ID, &u.Name, &u.Email)
if errors.Is(err, sql.ErrNoRows) {
    return nil, ErrNotFound
}

// Query multiple rows
rows, err := db.QueryContext(ctx,
    "SELECT id, name FROM users WHERE active = $1 LIMIT $2", true, 100)
if err != nil { return nil, err }
defer rows.Close()
for rows.Next() {
    var u User
    if err := rows.Scan(&u.ID, &u.Name); err != nil { return nil, err }
    users = append(users, u)
}
if err := rows.Err(); err != nil { return nil, err } // check for iteration errors

// Execute (INSERT/UPDATE/DELETE)
result, err := db.ExecContext(ctx,
    "INSERT INTO users (name, email) VALUES ($1, $2)", name, email)
if err != nil { return err }
id, _ := result.LastInsertId() // not supported by all drivers; use RETURNING for Postgres

// Transaction
tx, err := db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
if err != nil { return err }
defer tx.Rollback() // no-op if committed
// ... queries using tx instead of db ...
return tx.Commit()

// Prepared statement (reuse for repeated calls)
stmt, err := db.PrepareContext(ctx, "SELECT id FROM users WHERE email = $1")
defer stmt.Close()
var id int
stmt.QueryRowContext(ctx, email).Scan(&id)
```

### 50. ORMs & query builders.

```go
// --- sqlc (recommended — type-safe SQL code gen) ---
// 1. Write SQL queries in .sql files:
// -- name: GetUser :one
// SELECT id, name, email FROM users WHERE id = $1;

// 2. Run sqlc generate — produces:
type User struct{ ID int64; Name string; Email string }
type Queries struct{ db DBTX }
func (q *Queries) GetUser(ctx context.Context, id int64) (User, error) { ... }

// 3. Use:
q := db.New(conn)
u, err := q.GetUser(ctx, 42)

// --- pgx native (best for Postgres) ---
import "github.com/jackc/pgx/v5"
conn, _ := pgx.Connect(ctx, os.Getenv("DATABASE_URL"))
rows, _ := conn.Query(ctx, "SELECT id, name FROM users")
users, _ := pgx.CollectRows(rows, pgx.RowToStructByName[User])

// Batch queries (N queries in 1 round-trip)
batch := &pgx.Batch{}
batch.Queue("UPDATE users SET score=$1 WHERE id=$2", 10, 1)
batch.Queue("UPDATE users SET score=$1 WHERE id=$2", 20, 2)
results := conn.SendBatch(ctx, batch)
results.Close()

// --- GORM (convenient but magic-heavy) ---
import "gorm.io/gorm"
db.Where("email = ?", email).First(&user)
db.Create(&user)
db.Model(&user).Updates(User{Name: "Bob"})
db.Delete(&user)
// Preload to avoid N+1:
db.Preload("Orders").Find(&users)

// --- squirrel (query builder) ---
import sq "github.com/Masterminds/squirrel"
sql, args, _ := sq.Select("id", "name").From("users").
    Where(sq.Eq{"active": true}).
    OrderBy("name").Limit(10).
    PlaceholderFormat(sq.Dollar).ToSql()
// Use sql/args with database/sql

// N+1 anti-pattern:
// WRONG: fetching orders for each user in a loop
for _, u := range users {
    db.Where("user_id = ?", u.ID).Find(&u.Orders) // 1 query per user!
}
// RIGHT: one query with JOIN or IN
db.Where("user_id IN ?", userIDs).Find(&orders)
```

### 51. Migrations.

```go
// --- golang-migrate ---
import "github.com/golang-migrate/migrate/v4"
import _ "github.com/golang-migrate/migrate/v4/database/postgres"
import _ "github.com/golang-migrate/migrate/v4/source/file"

m, err := migrate.New("file://migrations", os.Getenv("DATABASE_URL"))
if err != nil { log.Fatal(err) }
if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
    log.Fatal(err)
}

// File naming:
// migrations/
//   000001_create_users.up.sql
//   000001_create_users.down.sql
//   000002_add_email_index.up.sql
//   000002_add_email_index.down.sql

// 000001_create_users.up.sql:
CREATE TABLE users (
    id      BIGSERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    email   TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

// 000001_create_users.down.sql:
DROP TABLE users;

// --- goose (alternative) ---
import "github.com/pressly/goose/v3"
goose.SetDialect("postgres")
goose.Up(db, "./migrations")

// Safe deployment patterns:
// 1. Run migrations BEFORE deploying new app code (additive migrations)
// 2. Use advisory locks to prevent concurrent migration runs:
//    SELECT pg_try_advisory_lock(12345);
// 3. Make migrations backward-compatible (Blue/Green deploy safety)
// 4. Test rollback: always ensure down.sql works
// 5. In Kubernetes: run as init container or a separate Job before Deployment
```

### 52. Caching.

```go
// --- In-process LRU (ristretto) ---
import "github.com/dgraph-io/ristretto"
cache, _ := ristretto.NewCache(&ristretto.Config{
    NumCounters: 1e7, MaxCost: 1 << 30, BufferItems: 64,
})
cache.Set("user:42", user, 1)
value, found := cache.Get("user:42")

// --- Redis (go-redis) ---
import "github.com/redis/go-redis/v9"
rdb := redis.NewClient(&redis.Options{
    Addr: "localhost:6379", Password: "", DB: 0,
})

// Set with TTL
err := rdb.Set(ctx, "user:42", jsonData, 5*time.Minute).Err()

// Get with miss handling
val, err := rdb.Get(ctx, "user:42").Bytes()
if errors.Is(err, redis.Nil) {
    // cache miss — load from DB
    u, err := db.GetUser(ctx, 42)
    data, _ := json.Marshal(u)
    rdb.Set(ctx, "user:42", data, 5*time.Minute)
}

// Jitter to prevent thundering herd (all keys expiring at once)
ttl := 5*time.Minute + time.Duration(rand.Intn(60))*time.Second

// --- Singleflight: deduplicate concurrent cache misses ---
var sf singleflight.Group

func getUser(ctx context.Context, id int) (*User, error) {
    v, err, _ := sf.Do(fmt.Sprintf("user:%d", id), func() (any, error) {
        // Only ONE goroutine runs this; others wait and share the result
        val, err := rdb.Get(ctx, fmt.Sprintf("user:%d", id)).Bytes()
        if err == nil {
            var u User; json.Unmarshal(val, &u); return &u, nil
        }
        u, err := db.GetUser(ctx, id)
        if err != nil { return nil, err }
        data, _ := json.Marshal(u)
        rdb.Set(ctx, fmt.Sprintf("user:%d", id), data, 5*time.Minute)
        return u, nil
    })
    if err != nil { return nil, err }
    return v.(*User), nil
}

// Cache invalidation strategies:
// TTL (simplest): stale-while-revalidate pattern
// Write-through: update cache on every write to DB
// Write-behind: write to cache, flush to DB async
// Cache-aside (above): load on miss, explicit invalidation
```

### 53. Background workers / job queues.

```go
// --- In-process (simple, no persistence) ---
jobs := make(chan Job, 1000) // buffered queue

// Worker pool
for i := 0; i < runtime.NumCPU(); i++ {
    go func() {
        for job := range jobs { process(job) }
    }()
}
jobs <- Job{...} // enqueue

// --- asynq (Redis-backed, persistent, retry) ---
import "github.com/hibiken/asynq"

// Enqueue
client := asynq.NewClient(asynq.RedisClientOpt{Addr: ":6379"})
task := asynq.NewTask("email:send", payload, asynq.MaxRetry(3), asynq.Timeout(30*time.Second))
client.Enqueue(task)

// Worker server
srv := asynq.NewServer(asynq.RedisClientOpt{Addr: ":6379"}, asynq.Config{
    Concurrency: 10,
    RetryDelayFunc: asynq.DefaultRetryDelayFunc,
})
mux := asynq.NewServeMux()
mux.HandleFunc("email:send", handleEmailSend)
srv.Run(mux)

func handleEmailSend(ctx context.Context, t *asynq.Task) error {
    var p EmailPayload
    json.Unmarshal(t.Payload(), &p)
    return sendEmail(ctx, p.To, p.Subject, p.Body) // must be idempotent!
}

// --- river (Postgres-backed, no extra infra) ---
import "github.com/riverqueue/river"

// Idempotency patterns:
// 1. Store job_id in DB, skip if already processed
// 2. Unique constraint on outcome table (INSERT ... ON CONFLICT DO NOTHING)
// 3. Check-and-act: verify precondition before acting
func processPayment(ctx context.Context, jobID string, amount int) error {
    var exists bool
    db.QueryRowContext(ctx, "SELECT EXISTS(SELECT 1 FROM payments WHERE job_id=$1)", jobID).Scan(&exists)
    if exists { return nil } // already processed
    // ... process ...
    db.ExecContext(ctx, "INSERT INTO payments (job_id, amount) VALUES ($1,$2)", jobID, amount)
    return nil
}
```

### 54. WebSockets.

```go
import "github.com/gorilla/websocket"

var upgrader = websocket.Upgrader{
    ReadBufferSize:  1024,
    WriteBufferSize: 1024,
    CheckOrigin: func(r *http.Request) bool {
        return true // restrict in production
    },
}

func wsHandler(w http.ResponseWriter, r *http.Request) {
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil { return }
    defer conn.Close()

    // Set limits to protect against malicious clients
    conn.SetReadLimit(512 * 1024) // 512KB max message

    // Ping/pong heartbeat to detect dead connections
    conn.SetPongHandler(func(string) error {
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        return nil
    })
    go func() {
        ticker := time.NewTicker(30 * time.Second)
        defer ticker.Stop()
        for range ticker.C {
            if err := conn.WriteControl(websocket.PingMessage, nil, time.Now().Add(5*time.Second)); err != nil {
                return
            }
        }
    }()

    // Separate goroutines for read and write — ws is NOT concurrent-safe
    send := make(chan []byte, 256)
    go func() { // writer goroutine
        for msg := range send {
            conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
            if err := conn.WriteMessage(websocket.TextMessage, msg); err != nil { return }
        }
    }()

    // Reader loop (main goroutine)
    for {
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        _, msg, err := conn.ReadMessage()
        if err != nil { break } // connection closed or timed out
        // Echo back
        send <- msg
    }
    close(send)
}

// Hub pattern for broadcasting to multiple clients
type Hub struct {
    clients   map[*websocket.Conn]struct{}
    broadcast chan []byte
    mu        sync.RWMutex
}
func (h *Hub) Broadcast(msg []byte) { h.broadcast <- msg }
func (h *Hub) run() {
    for msg := range h.broadcast {
        h.mu.RLock()
        for c := range h.clients {
            c.WriteMessage(websocket.TextMessage, msg)
        }
        h.mu.RUnlock()
    }
}
```

---

## 4. Testing

### 55. `testing` package.

```go
// Files must end in _test.go, test functions start with Test
// go test ./...         — run all tests
// go test -v ./...      — verbose (print test names)
// go test -run TestUser  — run tests matching regex
// go test -count=1      — disable caching

func TestAdd(t *testing.T) {
    got := Add(2, 3)
    if got != 5 {
        t.Errorf("Add(2,3) = %d, want 5", got) // continues test
    }
}

func TestDivide(t *testing.T) {
    _, err := Divide(10, 0)
    if err == nil {
        t.Fatal("expected error, got nil") // stops test immediately
    }
}

// Subtests — t.Run groups related cases
func TestUser(t *testing.T) {
    t.Run("create", func(t *testing.T) {
        u, err := CreateUser("Alice")
        if err != nil { t.Fatal(err) }
        if u.Name != "Alice" { t.Errorf("got %q", u.Name) }
    })
    t.Run("create empty name", func(t *testing.T) {
        _, err := CreateUser("")
        if !errors.Is(err, ErrInvalidName) { t.Errorf("want ErrInvalidName, got %v", err) }
    })
}

// Setup and teardown
func TestMain(m *testing.M) {
    // Setup (e.g., start test DB)
    db := setupTestDB()

    code := m.Run() // run all tests in the package

    // Teardown
    db.Close()
    os.Exit(code)
}

// t.Cleanup — runs at end of test (cleaner than defer for subtests)
func TestWithCleanup(t *testing.T) {
    db := openDB(t)
    t.Cleanup(func() { db.Close() })
    // ... test code ...
}

// t.Parallel — run this test concurrently with other parallel tests
func TestConcurrent(t *testing.T) {
    t.Parallel()
    // ... test code ...
}

// t.Helper — mark as helper so errors show caller's line number
func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil { t.Fatalf("unexpected error: %v", err) }
}
```

### 56. Table-driven tests.

```go
func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a, b    float64
        want    float64
        wantErr bool
    }{
        {"normal", 10, 2, 5, false},
        {"zero dividend", 0, 5, 0, false},
        {"divide by zero", 10, 0, 0, true},
        {"negative", -6, 2, -3, false},
    }

    for _, tt := range tests {
        tt := tt // capture (important pre-1.22 for parallel subtests)
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // each case runs concurrently
            got, err := Divide(tt.a, tt.b)
            if (err != nil) != tt.wantErr {
                t.Errorf("Divide(%v,%v) error = %v, wantErr %v", tt.a, tt.b, err, tt.wantErr)
                return
            }
            if !tt.wantErr && got != tt.want {
                t.Errorf("Divide(%v,%v) = %v, want %v", tt.a, tt.b, got, tt.want)
            }
        })
    }
}

// testify/assert — cleaner assertions
import "github.com/stretchr/testify/assert"
func TestUser(t *testing.T) {
    u, err := CreateUser("Alice")
    assert.NoError(t, err)
    assert.Equal(t, "Alice", u.Name)
    assert.NotZero(t, u.ID)
}

// testify/require — stops test on failure (like t.Fatal)
import "github.com/stretchr/testify/require"
func TestDB(t *testing.T) {
    conn, err := db.Connect()
    require.NoError(t, err)  // stops here if err != nil
    defer conn.Close()
    require.NotNil(t, conn)
}
```

### 57. Mocking.

```go
// --- Interface + hand-written fake (simplest, most readable) ---
type UserStore interface {
    GetUser(ctx context.Context, id int) (*User, error)
    CreateUser(ctx context.Context, u User) error
}

// Production implementation
type PostgresStore struct{ db *sql.DB }
func (s *PostgresStore) GetUser(ctx context.Context, id int) (*User, error) { /* ... */ }

// Fake for testing
type fakeStore struct {
    users map[int]*User
    err   error // inject error for error path tests
}
func (f *fakeStore) GetUser(_ context.Context, id int) (*User, error) {
    if f.err != nil { return nil, f.err }
    u, ok := f.users[id]
    if !ok { return nil, ErrNotFound }
    return u, nil
}
func (f *fakeStore) CreateUser(_ context.Context, u User) error { return f.err }

// Test with fake
func TestGetUser(t *testing.T) {
    svc := NewUserService(&fakeStore{
        users: map[int]*User{1: {ID: 1, Name: "Alice"}},
    })
    u, err := svc.GetUser(context.Background(), 1)
    assert.NoError(t, err)
    assert.Equal(t, "Alice", u.Name)

    // Error path
    svc2 := NewUserService(&fakeStore{err: ErrNotFound})
    _, err = svc2.GetUser(context.Background(), 99)
    assert.ErrorIs(t, err, ErrNotFound)
}

// --- mockery (code generation) ---
// go generate ./...
//go:generate mockery --name=UserStore --output=mocks
import "github.com/stretchr/testify/mock"

mock := new(mocks.UserStore)
mock.On("GetUser", ctx, 1).Return(&User{Name: "Alice"}, nil)
mock.On("GetUser", ctx, 99).Return(nil, ErrNotFound)
mock.AssertExpectations(t)

// --- httptest for HTTP mocking ---
func TestHTTPClient(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        assert.Equal(t, "/users/1", r.URL.Path)
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(User{ID: 1, Name: "Alice"})
    }))
    defer server.Close()

    client := NewUserClient(server.URL)
    u, err := client.GetUser(ctx, 1)
    assert.NoError(t, err)
    assert.Equal(t, "Alice", u.Name)
}
```

### 58. Integration tests.

```go
//go:build integration
// Run: go test -tags=integration ./...

import "github.com/testcontainers/testcontainers-go"
import "github.com/testcontainers/testcontainers-go/modules/postgres"

func TestIntegration(t *testing.T) {
    ctx := context.Background()

    // Start a real Postgres container
    pg, err := postgres.RunContainer(ctx,
        testcontainers.WithImage("postgres:16"),
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready").WithOccurrence(2),
        ),
    )
    require.NoError(t, err)
    defer pg.Terminate(ctx)

    connStr, _ := pg.ConnectionString(ctx, "sslmode=disable")

    // Migrate
    db, _ := sql.Open("pgx", connStr)
    runMigrations(db)

    // Test against real DB
    store := NewPostgresStore(db)
    u, err := store.CreateUser(ctx, User{Name: "Alice"})
    require.NoError(t, err)
    assert.NotZero(t, u.ID)

    got, err := store.GetUser(ctx, u.ID)
    require.NoError(t, err)
    assert.Equal(t, "Alice", got.Name)
}

// Alternatively: docker-compose test environment
// docker-compose -f docker-compose.test.yml up -d
// go test ./... (reads DB_URL from env)
// docker-compose -f docker-compose.test.yml down
```

### 59. Benchmarks.

```go
// Benchmark function: must loop b.N times
func BenchmarkHash(b *testing.B) {
    data := []byte("hello world")
    b.ReportAllocs()   // show allocations per op
    b.SetBytes(int64(len(data))) // for throughput (MB/s)
    b.ResetTimer()     // don't count setup time

    for i := 0; i < b.N; i++ {
        sha256.Sum256(data)
    }
}

// Run:
// go test -bench=. -benchmem ./...
// go test -bench=BenchmarkHash -benchtime=3s -count=5

// Output:
// BenchmarkHash-8   5000000   234 ns/op   0 B/op   0 allocs/op

// Sub-benchmarks
func BenchmarkSort(b *testing.B) {
    sizes := []int{100, 1000, 10000}
    for _, n := range sizes {
        n := n
        b.Run(fmt.Sprintf("size=%d", n), func(b *testing.B) {
            data := makeData(n)
            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                s := make([]int, len(data))
                copy(s, data)
                sort.Ints(s)
            }
        })
    }}
}

// Compare benchmarks with benchstat
// go test -bench=. -count=5 -benchmem > before.txt
// # make changes
// go test -bench=. -count=5 -benchmem > after.txt
// benchstat before.txt after.txt

// Profile a benchmark
// go test -bench=BenchmarkHash -cpuprofile=cpu.out
// go tool pprof cpu.out
// go test -bench=BenchmarkHash -memprofile=mem.out
// go tool pprof mem.out
```

### 60. Fuzz testing.

```go
// Fuzz function: find inputs that cause panics or incorrect behavior
func FuzzParseURL(f *testing.F) {
    // Seed corpus: valid inputs to start from
    f.Add("https://example.com/path?q=1")
    f.Add("http://localhost:8080")
    f.Add("")

    f.Fuzz(func(t *testing.T, input string) {
        // Must not panic on any input
        url, err := url.Parse(input)
        if err != nil { return } // errors are fine, panics are not
        // Optionally assert invariants:
        if url != nil && url.String() != "" {
            // Re-parsing should give same result
            url2, _ := url.Parse(url.String())
            if url.Host != url2.Host {
                t.Errorf("round-trip failed: %q != %q", url.Host, url2.Host)
            }
        }
    })
}

// Run the fuzzer:
// go test -fuzz=FuzzParseURL -fuzztime=30s
// Found inputs are saved to testdata/fuzz/FuzzParseURL/

// Run seed corpus only (no fuzzing, runs on every go test):
// go test ./...

// Great for: JSON/XML parsers, HTTP handlers, decoders, protocol implementations
// The fuzzer will find edge cases (null bytes, max ints, huge strings)
// that manual tests miss
```

### 61. Coverage.

```bash
# Basic coverage
go test -cover ./...
# PASS
# coverage: 78.3% of statements

# Save coverage profile
go test -coverprofile=coverage.out ./...

# HTML report (opens in browser)
go tool cover -html=coverage.out

# Coverage by function
go tool cover -func=coverage.out
# mypackage/user.go:15:    CreateUser    95.5%
# mypackage/user.go:42:    DeleteUser    60.0%

# Exclude generated files from coverage
go test -coverprofile=coverage.out -coverpkg=./... ./...

# Threshold check in CI (fail if < 80%)
COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | tr -d '%')
if (( $(echo "$COVERAGE < 80" | bc -l) )); then
  echo "Coverage $COVERAGE% below threshold"; exit 1
fi
```

**Focus on covering**:
- Error paths and edge cases (not just the happy path)
- Core business logic (service layer)
- Complex conditional branches

**Don't obsess over 100%**: boilerplate getters, generated code, and `main()` rarely need coverage. A 70-80% meaningful coverage beats 100% coverage of trivial code.

---

## 5. Performance & Tooling

### 62. Profiling with pprof.

```go
// Add pprof endpoints to your HTTP server
import _ "net/http/pprof" // side-effect registers /debug/pprof/ routes

// Start a separate debug server (don't expose on public port!)
go func() {
    log.Println(http.ListenAndServe("localhost:6060", nil))
}()

// Available endpoints:
// /debug/pprof/               index
// /debug/pprof/goroutine      all goroutines
// /debug/pprof/heap           heap allocations
// /debug/pprof/allocs         all allocations (not just live)
// /debug/pprof/block          goroutines blocked on sync (needs runtime.SetBlockProfileRate)
// /debug/pprof/mutex          contended mutexes (needs runtime.SetMutexProfileFraction)
// /debug/pprof/profile        30-second CPU profile
// /debug/pprof/trace          runtime trace

// Enable block/mutex profiling at startup
runtime.SetBlockProfileRate(1)
runtime.SetMutexProfileFraction(1)

// CPU profile — what's consuming CPU?
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
// Then in interactive mode:
// (pprof) top 10      — top 10 functions by CPU
// (pprof) list fnName — source-annotated view
// (pprof) web         — open flame graph in browser

// Heap profile — what's consuming memory?
go tool pprof http://localhost:6060/debug/pprof/heap
// (pprof) top -cum     — sort by cumulative allocation
// (pprof) inuse_space  — live allocations
// (pprof) alloc_space  — total allocated (including freed)

// Goroutine leak check
go tool pprof http://localhost:6060/debug/pprof/goroutine
// (pprof) top          — goroutines by function

// Automated profiling in tests
func BenchmarkSlow(b *testing.B) {
    for i := 0; i < b.N; i++ { slowFunc() }
}
// go test -bench=BenchmarkSlow -cpuprofile=cpu.out
// go tool pprof cpu.out

// Flame graph (most intuitive visualization)
// go get github.com/google/pprof
// pprof -http=:8090 cpu.out
```

### 63. Escape analysis.

```go
// Compiler decides: stack allocation (fast, no GC) vs heap allocation (GC work)
// go build -gcflags="-m" shows escape decisions:
// main.go:5:13: moved to heap: x
// main.go:10:12: ... does not escape

// Stack allocation (fast path)
func add(a, b int) int {
    result := a + b // stays on stack
    return result
}

// Heap allocation (variable escapes)
func newUser(name string) *User {
    u := User{Name: name} // escapes to heap because pointer is returned
    return &u
}

// Interface boxing causes heap allocation
var i interface{} = 42 // int escapes to heap (boxed into interface)

// Avoid in hot paths:
func serialize(w io.Writer, v any) {
    // 'v any' may box v, causing allocation
    // Better: use concrete type or generic
}

// Preallocated slice stays on heap but avoids repeated reallocation
buf := make([]byte, 0, 1024) // one alloc
buf = append(buf, data...)   // no realloc if fits

// Closures capture variables — captured vars escape to heap
func makeAdder(x int) func(int) int {
    return func(y int) int { return x + y } // x escapes because closure captures it
}

// View escape analysis:
// go build -gcflags='-m -m' ./...
// go build -gcflags='-m=2' main.go   — verbose
```

### 64. Reducing allocations.

```go
// --- Preallocate slices ---
// BAD: O(log N) reallocations
var out []string
for _, u := range users {
    out = append(out, u.Name)
}

// GOOD: single allocation
out := make([]string, 0, len(users))
for _, u := range users {
    out = append(out, u.Name)
}

// --- String building ---
// BAD: each += allocates a new string
var s string
for i := 0; i < 1000; i++ { s += strconv.Itoa(i) }

// GOOD: strings.Builder
var sb strings.Builder
sb.Grow(5000) // pre-size hint
for i := 0; i < 1000; i++ { sb.WriteString(strconv.Itoa(i)) }
result := sb.String()

// --- Avoid fmt.Sprintf in hot paths ---
// BAD: allocates for formatting
key := fmt.Sprintf("user:%d", id)

// GOOD: strconv
key := "user:" + strconv.Itoa(id)

// --- sync.Pool for temp buffers ---
var pool = sync.Pool{New: func() any { return make([]byte, 0, 1024) }}
func process() {
    buf := pool.Get().([]byte)
    defer func() { pool.Put(buf[:0]) }() // reset, return
    // use buf
}

// --- Zero-alloc struct comparison ---
// Pass small structs by value (4-5 words) — avoids pointer indirection
func Equal(a, b Point) bool { return a.X == b.X && a.Y == b.Y }

// Pass large structs by pointer to avoid copying
func process(cfg *BigConfig) {} // 50-field struct

// --- Benchmark allocations ---
// BenchmarkHash-8   5000000   234 ns/op   0 B/op   0 allocs/op
//                                          ^^^^^^^^^^^^^^^^^^^^
//                                          target: 0 allocs/op in hot path

// go test -bench=. -benchmem -memprofile=mem.out
// go tool pprof mem.out
```

### 65. Garbage collection.

```go
// Go uses concurrent tri-color mark-sweep GC
// - Runs concurrently with the program (minimal STW pauses, typically < 1ms)
// - Triggered when heap grows to GOGC% above the previous live heap size

// GOGC=100 (default): collect when heap is 2x the live heap
// GOGC=200: collect less often (more memory, less CPU)
// GOGC=50:  collect more often (less memory, more CPU)
// GOGC=off: disable GC (for batch jobs that allocate and exit)
GOGC=off go run main.go

// GOMEMLIMIT (Go 1.19+): soft memory limit for container environments
// Prevents OOM kills by triggering GC more aggressively near the limit
GOMEMLIMIT=512MiB go run main.go

// In code:
runtime.GOMAXPROCS(4) // set OS thread count
debug.SetGCPercent(200) // same as GOGC=200
debug.SetMemoryLimit(512 << 20) // same as GOMEMLIMIT=512MiB

// Monitor GC
var stats runtime.MemStats
runtime.ReadMemStats(&stats)
fmt.Printf("GC runs: %d, HeapAlloc: %d MB, NextGC: %d MB\n",
    stats.NumGC,
    stats.HeapAlloc/1024/1024,
    stats.NextGC/1024/1024,
)

// Force GC (only for testing/benchmarks)
runtime.GC()

// Go 1.21+: runtime/metrics package for fine-grained GC stats
import "runtime/metrics"
samples := []metrics.Sample{{Name: "/gc/cycles/total:gc-cycles"}}
metrics.Read(samples)

// Best practices:
// 1. Set GOMEMLIMIT to ~80% of container memory limit
// 2. Reduce allocations in hot paths (see Q64)
// 3. Profile heap with pprof before tuning GC
// 4. Don't set GOGC=off unless it's a short-lived batch process
```

### 66. Useful tooling.

```bash
# --- Code quality ---
go vet ./...                   # built-in static analysis (always run)
golangci-lint run              # umbrella linter (staticcheck + 50+ linters)
staticcheck ./...              # advanced static analysis

# --- Formatting ---
gofmt -w .                     # format all files
goimports -w .                 # format + fix imports

# --- Dependencies ---
go mod tidy                    # clean up go.mod/go.sum
go mod why github.com/pkg/foo  # why is this dependency included?
go mod graph                   # full dependency graph
go list -m all                 # all dependencies with versions
go mod vendor                  # create vendor/ directory

# --- Build ---
go build -v ./...              # verbose build
go build -gcflags='-m' ./...   # escape analysis output
go build -ldflags='-s -w' ...  # strip debug info (smaller binary)
GOOS=linux GOARCH=arm64 go build ./... # cross-compile

# --- Testing ---
go test -race ./...            # race detector (always in CI)
go test -count=1 ./...         # disable test caching
go test -v -run TestUser ./... # specific tests, verbose

# --- Debugging ---
dlv debug ./cmd/server         # interactive debugger
dlv test ./... --test.run=TestUser # debug specific test

# --- Tracing ---
import "runtime/trace"
trace.Start(f)
defer trace.Stop()
// then: go tool trace trace.out

# --- Other tools ---
go generate ./...              # run //go:generate directives
godoc -http=:6060              # local documentation server
go tool compile -S main.go     # show assembly output
whereis go                     # find Go binary
go env                         # show all Go env variables
```

### 67. Build tags & cross-compilation.

```go
// Build tags — control which files are compiled
//go:build linux           // only on Linux
//go:build linux && amd64  // Linux on x86_64
//go:build !windows        // everything except Windows
//go:build integration     // custom tag: go test -tags=integration

// Tag must be at very top of file, before package declaration, with a blank line after
//go:build linux

package server

// Platform-specific code
//go:build linux
// +build linux  // old syntax for Go < 1.17 compatibility

func getMemoryUsage() uint64 {
    var stat syscall.Sysinfo_t
    syscall.Sysinfo(&stat)
    return stat.Totalram
}
```

```bash
# Cross-compilation — just set GOOS and GOARCH
GOOS=linux   GOARCH=amd64  go build -o app-linux-amd64  ./cmd/server
GOOS=linux   GOARCH=arm64  go build -o app-linux-arm64  ./cmd/server
GOOS=darwin  GOARCH=amd64  go build -o app-darwin-amd64 ./cmd/server
GOOS=windows GOARCH=amd64  go build -o app.exe          ./cmd/server

# Supported GOOS: linux, darwin, windows, freebsd, openbsd, android, ios, js, wasip1
# Supported GOARCH: amd64, arm64, arm, 386, wasm, riscv64, loong64

# Minimal Docker image
# Dockerfile:
# FROM golang:1.22 AS builder
# WORKDIR /app
# COPY . .
# RUN CGO_ENABLED=0 GOOS=linux go build -ldflags='-s -w' -o server ./cmd/server
#
# FROM gcr.io/distroless/static-debian12
# COPY --from=builder /app/server /server
# ENTRYPOINT ["/server"]

# CGO_ENABLED=0: pure Go, no C dependency, truly static binary
# -ldflags='-s -w': strip debug info (30-50% smaller binary)
```

### 68. `cgo`.

```go
// cgo lets Go call C code (and vice versa)
package main

/*
#include <stdlib.h>
#include <string.h>

char* greet(const char* name) {
    char* result = malloc(256);
    snprintf(result, 256, "Hello, %s!", name);
    return result;
}
*/
import "C" // this import is special — no blank line before it
import "unsafe"

func Greet(name string) string {
    cName := C.CString(name)
    defer C.free(unsafe.Pointer(cName)) // MUST free C memory

    cResult := C.greet(cName)
    defer C.free(unsafe.Pointer(cResult))

    return C.GoString(cResult)
}

// Real use cases:
// - SQLite (mattn/go-sqlite3) — C library
// - OpenSSL/BoringSSL wrappers
// - Calling CUDA/GPU kernels
// - Wrapping legacy C/C++ libraries

// Costs of cgo:
// 1. Breaks cross-compilation (CGO_ENABLED=0 removes cgo)
// 2. Each cgo call has ~200ns overhead (context switch goroutine <> OS thread)
// 3. The C code runs outside the Go scheduler — blocks an OS thread
// 4. Can't use go test -race across the C/Go boundary safely
// 5. Static linking becomes complex
// 6. Build is much slower

// Alternatives:
// - Use pure Go libraries when possible (modernc.org/sqlite vs go-sqlite3)
// - Subprocess/IPC: run C program separately, communicate via pipe/gRPC
// - WASM for browser/sandbox scenarios
```

### 69. Generics (Go 1.18+).

```go
// Type parameter syntax: [T constraint]

// Generic function — works for any comparable type
func Contains[T comparable](slice []T, item T) bool {
    for _, v := range slice {
        if v == item { return true }
    }
    return false
}
Contains([]int{1, 2, 3}, 2)         // true
Contains([]string{"a", "b"}, "c")  // false

// Map / Filter / Reduce
func Map[T, U any](s []T, f func(T) U) []U {
    out := make([]U, len(s))
    for i, v := range s { out[i] = f(v) }
    return out
}
names := Map(users, func(u User) string { return u.Name })

func Filter[T any](s []T, pred func(T) bool) []T {
    var out []T
    for _, v := range s { if pred(v) { out = append(out, v) } }
    return out
}

// Custom constraints
type Number interface {
    ~int | ~int64 | ~float64 // ~ means "underlying type"
}
func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums { total += n }
    return total
}
Sum([]int{1, 2, 3})     // 6
Sum([]float64{1.1, 2.2}) // 3.3

// Generic type — type-safe stack
type Stack[T any] struct{ items []T }
func (s *Stack[T]) Push(v T)     { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.items) == 0 { return zero, false }
    n := len(s.items) - 1
    v := s.items[n]; s.items = s.items[:n]
    return v, true
}

var ints Stack[int]
ints.Push(1); ints.Push(2)
v, _ := ints.Pop() // 2, type-safe

// stdlib generics: slices, maps, cmp packages (Go 1.21+)
import "slices"
slices.Sort(nums)               // sort any ordered slice
slices.Contains(nums, 5)        // check membership
import "maps"
maps.Keys(m)                    // get all keys as a slice

// When to use generics:
// YES: utility functions (contains, map, filter, min/max)
// YES: type-safe collections (stack, queue, set, tree)
// NO:  when interface{} + type switch would be clearer
// NO:  prematurely — add generics when you have 3+ concrete types
```

### 70. Reflection (`reflect`).

```go
import "reflect"

// Inspect type and value at runtime
func describe(i any) {
    t := reflect.TypeOf(i)
    v := reflect.ValueOf(i)
    fmt.Printf("type=%v kind=%v value=%v\n", t, t.Kind(), v)
}
describe(42)          // type=int kind=int value=42
describe("hello")     // type=string kind=string value=hello
describe([]int{1,2})  // type=[]int kind=slice value=[1 2]

// Struct field inspection (used by json, validate, gorm, etc.)
type User struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
}
u := User{ID: 1, Name: "Alice"}
t := reflect.TypeOf(u)
for i := 0; i < t.NumField(); i++ {
    f := t.Field(i)
    fmt.Println(f.Name, f.Tag.Get("json")) // ID id, Name name
}

// Modify value via reflection (must use pointer)
v := reflect.ValueOf(&u).Elem()
v.FieldByName("Name").SetString("Bob")
fmt.Println(u.Name) // Bob

// Check if value implements an interface
var err error
errType := reflect.TypeOf(&err).Elem() // reflect.Type for 'error'
fmt.Println(reflect.TypeOf(u).Implements(errType)) // false

// Deep equality (useful in tests)
reflect.DeepEqual(a, b) // compares maps, slices, structs recursively

// Performance cost
// Direct call:      ~1ns
// reflect call:     ~100ns (100x slower)
// json.Marshal:     reflection + allocation overhead

// When to use reflection:
// - Framework code (serialization, validation, ORM, DI containers)
// - Testing utilities (deepEqual, diff)
// - Generic operations that can't be solved with generics

// Prefer code generation (go generate, sqlc, protoc) when:
// - Performance is critical
// - Type errors should be caught at compile time
// - The set of types is known at write time
```

---

## 6. Advanced Topics & Production Patterns

### 71. Clean architecture in Go.

```
myapp/
  cmd/server/main.go        ← wires everything together
  internal/
    domain/                 ← pure types, no external imports
      user.go               ← type User struct{...}
      errors.go             ← var ErrNotFound = ...
    ports/                  ← interfaces (what domain needs from outside)
      repository.go         ← type UserRepo interface{...}
      email.go              ← type EmailSender interface{...}
    service/                ← business logic, depends only on ports/domain
      user_service.go
    adapters/
      postgres/             ← implements UserRepo
        user_repo.go
      smtp/                 ← implements EmailSender
        sender.go
      http/                 ← HTTP handlers, calls service
        user_handler.go
```

```go
// domain/user.go — pure types, no framework imports
package domain

type User struct {
    ID    int
    Name  string
    Email string
}

var ErrNotFound = errors.New("user not found")
var ErrInvalidEmail = errors.New("invalid email")

// ports/repository.go — interface defined by the consumer (service layer)
package ports

type UserRepo interface {
    Get(ctx context.Context, id int) (domain.User, error)
    Save(ctx context.Context, u domain.User) error
    Delete(ctx context.Context, id int) error
}

// service/user_service.go — depends only on port interfaces, not concrete types
package service

type UserService struct {
    repo  ports.UserRepo
    email ports.EmailSender
}
func NewUserService(repo ports.UserRepo, email ports.EmailSender) *UserService {
    return &UserService{repo: repo, email: email}
}
func (s *UserService) Register(ctx context.Context, name, emailAddr string) (domain.User, error) {
    if !isValidEmail(emailAddr) { return domain.User{}, domain.ErrInvalidEmail }
    u := domain.User{Name: name, Email: emailAddr}
    if err := s.repo.Save(ctx, u); err != nil { return domain.User{}, err }
    s.email.SendWelcome(ctx, u)  // fire-and-forget, or handle error
    return u, nil
}

// adapters/postgres/user_repo.go — concrete, implements ports.UserRepo
package postgres

type UserRepo struct{ db *sql.DB }
func (r *UserRepo) Get(ctx context.Context, id int) (domain.User, error) {
    var u domain.User
    err := r.db.QueryRowContext(ctx, "SELECT id,name,email FROM users WHERE id=$1", id).Scan(&u.ID, &u.Name, &u.Email)
    if errors.Is(err, sql.ErrNoRows) { return domain.User{}, domain.ErrNotFound }
    return u, err
}

// adapters/http/user_handler.go
package http

type UserHandler struct{ svc *service.UserService }
func (h *UserHandler) Register(w http.ResponseWriter, r *http.Request) {
    var req struct{ Name, Email string }
    json.NewDecoder(r.Body).Decode(&req)
    u, err := h.svc.Register(r.Context(), req.Name, req.Email)
    if errors.Is(err, domain.ErrInvalidEmail) {
        http.Error(w, "invalid email", 422); return
    }
    if err != nil { http.Error(w, "internal", 500); return }
    json.NewEncoder(w).Encode(u)
}

// cmd/server/main.go — wiring
func main() {
    db := setupDB()
    repo := &postgres.UserRepo{db}
    emailer := &smtp.Sender{}
    svc := service.NewUserService(repo, emailer)
    handler := &httphandler.UserHandler{svc}
    // ...
}
```

**Key rules**: dependencies point inward (adapters → service → domain, never reversed). Domain has zero framework imports. Interfaces live with the consumer.

### 72. Dependency injection.

```go
// --- Constructor injection (idiomatic, no framework needed) ---
type UserService struct {
    repo   UserRepo      // interface
    cache  Cache         // interface
    logger *slog.Logger  // concrete, but swappable
}

func NewUserService(repo UserRepo, cache Cache, logger *slog.Logger) *UserService {
    return &UserService{repo: repo, cache: cache, logger: logger}
}

// In main — manual wiring (fine for small/medium apps)
func main() {
    logger := slog.Default()
    db := mustConnectDB()
    redis := mustConnectRedis()

    repo := postgres.NewUserRepo(db)
    cache := rediscache.New(redis)
    svc := service.NewUserService(repo, cache, logger)
    handler := httphandler.New(svc)

    srv := &http.Server{Handler: handler}
    srv.ListenAndServe()
}

// --- google/wire (compile-time DI, generates wiring code) ---
// wire.go (not compiled normally)
//go:build wireinject

func InitializeApp() *App {
    wire.Build(
        postgres.NewUserRepo,
        rediscache.New,
        service.NewUserService,
        httphandler.New,
        NewApp,
    )
    return nil
}
// Run: wire gen ./... → generates wire_gen.go with the manual wiring

// --- uber-go/fx (runtime DI, lifecycle management) ---
import "go.uber.org/fx"

app := fx.New(
    fx.Provide(
        postgres.NewUserRepo,
        rediscache.New,
        service.NewUserService,
        httphandler.New,
    ),
    fx.Invoke(func(srv *http.Server) { /* start */ }),
)
app.Run() // manages Start/Stop lifecycle

// When to use what:
// Small app (<5 services): manual wiring in main — simplest, most readable
// Medium app:              google/wire — compile-time safety, no runtime overhead
// Large app with lifecycle: uber-go/fx — modules, lifecycle hooks, decorators

// Avoid: global variables for dependencies (hard to test)
// Prefer: pass interfaces, not concrete types
```

### 73. Graceful shutdown checklist.

```go
func main() {
    // 1. Root context — cancel triggers shutdown cascade
    ctx, stop := signal.NotifyContext(context.Background(),
        os.Interrupt, syscall.SIGTERM) // Kubernetes sends SIGTERM
    defer stop()

    // 2. Start all components
    srv := startHTTPServer()
    consumer := startKafkaConsumer(ctx)
    db := connectDB()

    // 3. Block until signal
    <-ctx.Done()
    log.Println("shutdown initiated")

    // 4. Shutdown with deadline (K8s default terminationGracePeriodSeconds=30)
    shutCtx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
    defer cancel()

    var wg sync.WaitGroup

    // 5a. Stop HTTP (stop accepting new requests, drain in-flight)
    wg.Add(1)
    go func() {
        defer wg.Done()
        if err := srv.Shutdown(shutCtx); err != nil {
            log.Printf("http shutdown: %v", err)
        }
    }()

    // 5b. Stop message consumer (commit current offsets, stop polling)
    wg.Add(1)
    go func() {
        defer wg.Done()
        consumer.Stop() // signals consumer to stop after current batch
        consumer.Wait()
    }()

    wg.Wait()

    // 6. Flush metrics and logs (after no more work in flight)
    metrics.Flush()
    logger.Sync()

    // 7. Close DB connection pool last
    db.Close()
    log.Println("shutdown complete")
}

// Kubernetes PreStop hook to delay SIGTERM until load balancer drains
// In your deployment YAML:
// lifecycle:
//   preStop:
//     exec:
//       command: ["sleep", "5"]  // wait for LB to remove pod from rotation

// Checklist:
// ✓ Trap SIGTERM + SIGINT
// ✓ Stop accepting new work first
// ✓ Drain in-flight requests
// ✓ Commit message queue offsets
// ✓ Flush async metrics/logs
// ✓ Close DB connections
// ✓ Cancel root context last (goroutines watching it should have already stopped)
// ✓ Respect deadline — K8s will SIGKILL after terminationGracePeriodSeconds
```

### 74. Observability — the three pillars.

```go
// ============================================================
// PILLAR 1: LOGS — structured, leveled
// ============================================================
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))
logger.Info("request completed",
    "method", r.Method,
    "path", r.URL.Path,
    "status", status,
    "duration_ms", time.Since(start).Milliseconds(),
    "trace_id", traceID,
)

// ============================================================
// PILLAR 2: METRICS — counters, histograms, gauges
// ============================================================
import "github.com/prometheus/client_golang/prometheus"
import "github.com/prometheus/client_golang/prometheus/promauto"

var (
    requestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "http_requests_total",
        Help: "Total HTTP requests",
    }, []string{"method", "path", "status"})

    requestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request latency",
        Buckets: prometheus.DefBuckets, // .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10
    }, []string{"method", "path"})

    activeConnections = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "http_active_connections",
    })
)

// Instrument a handler
func Instrument(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        activeConnections.Inc()
        defer activeConnections.Dec()

        rw := &statusWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(rw, r)

        duration := time.Since(start).Seconds()
        status := strconv.Itoa(rw.status)
        requestsTotal.WithLabelValues(r.Method, r.URL.Path, status).Inc()
        requestDuration.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
    })
}

// Expose /metrics endpoint
http.Handle("/metrics", promhttp.Handler())

// ============================================================
// PILLAR 3: TRACES — distributed tracing with OpenTelemetry
// ============================================================
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

// Initialize tracer (once at startup)
tp := initTracerProvider("my-service", "otlp-endpoint:4317")
defer tp.Shutdown(ctx)
otel.SetTracerProvider(tp)

// Create spans in your code
tracer := otel.Tracer("user-service")
func getUser(ctx context.Context, id int) (*User, error) {
    ctx, span := tracer.Start(ctx, "getUser",
        trace.WithAttributes(attribute.Int("user.id", id)),
    )
    defer span.End()

    u, err := repo.Get(ctx, id) // ctx propagates the trace
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return nil, err
    }
    return u, nil
}

// HTTP middleware for automatic span creation
import "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
handler := otelhttp.NewHandler(mux, "server") // auto-creates spans

// Context propagation: trace ID travels with context
// Parent → Child: HTTP header W3C traceparent is set/read automatically
// Tools: Jaeger, Zipkin, Grafana Tempo, Honeycomb, Datadog, AWS X-Ray
```

### 75. Error wrapping & sentinel errors.

```go
// --- Sentinel errors: identity-based comparison ---
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrConflict     = errors.New("conflict")
)

// --- Typed errors: carry extra context ---
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

type DBError struct {
    Op  string // "insert", "query"
    Err error  // underlying error
}
func (e *DBError) Error() string { return fmt.Sprintf("db %s: %v", e.Op, e.Err) }
func (e *DBError) Unwrap() error { return e.Err } // enables errors.Is/As traversal

// --- Wrapping with context: %w ---
func getUser(ctx context.Context, id int) (*User, error) {
    u, err := db.Query(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("getUser(%d): %w", id, err) // add context, preserve chain
    }
    if u == nil {
        return nil, fmt.Errorf("getUser(%d): %w", id, ErrNotFound)
    }
    return u, nil
}

// --- Caller side ---
u, err := getUser(ctx, 99)

// errors.Is: checks entire unwrap chain (works through multiple wraps)
if errors.Is(err, ErrNotFound) {
    http.Error(w, "user not found", 404)
    return
}

// errors.As: extract typed error from chain
var valErr *ValidationError
if errors.As(err, &valErr) {
    http.Error(w, valErr.Message, 422)
    return
}

// Log with full chain
log.Printf("error: %v", err) // getUser(99): not found

// --- HTTP error mapping pattern ---
func httpStatusFor(err error) int {
    switch {
    case errors.Is(err, ErrNotFound):     return http.StatusNotFound
    case errors.Is(err, ErrUnauthorized): return http.StatusUnauthorized
    case errors.Is(err, ErrConflict):     return http.StatusConflict
    default:                               return http.StatusInternalServerError
    }
}

// --- Pitfalls ---
// DON'T: if err.Error() == "not found" // breaks when err is wrapped
// DON'T: return error from typed nil var (Q12 nil interface gotcha)
// DON'T: ignore errors (_, _ = fmt.Println(...) is fine, DB writes are not)
// DO: always add context to errors as they propagate up
```

### 76. Idempotency & retries.

```go
// --- Retry with exponential backoff + jitter ---
func retryWithBackoff(ctx context.Context, maxAttempts int, fn func() error) error {
    base := 100 * time.Millisecond
    var err error
    for attempt := 0; attempt < maxAttempts; attempt++ {
        err = fn()
        if err == nil { return nil }
        if !isRetryable(err) { return err } // don't retry permanent errors

        wait := time.Duration(1<<attempt) * base
        wait += time.Duration(rand.Int63n(int64(wait / 2))) // jitter
        if wait > 30*time.Second { wait = 30 * time.Second } // cap

        select {
        case <-time.After(wait):
        case <-ctx.Done(): return ctx.Err()
        }
    }
    return fmt.Errorf("after %d attempts: %w", maxAttempts, err)
}

func isRetryable(err error) bool {
    // Retry on: network errors, timeout, 429/503; NOT on: 400, 401, 404
    var netErr net.Error
    if errors.As(err, &netErr) && netErr.Timeout() { return true }
    if errors.Is(err, context.DeadlineExceeded) { return true }
    return false
}

// --- cenkalti/backoff library ---
import "github.com/cenkalti/backoff/v4"
err = backoff.Retry(func() error {
    return callExternalService(ctx)
}, backoff.WithContext(backoff.NewExponentialBackOff(), ctx))

// --- Idempotency key ---
// For non-idempotent writes (payment, email), pass a unique key the server
// uses to deduplicate retries.
type PaymentReq struct {
    IdempotencyKey string `json:"idempotency_key"` // UUID from client
    Amount         int    `json:"amount"`
    UserID         int    `json:"user_id"`
}

// Server-side: store key + result, return cached on retry
func (s *PaymentService) Charge(ctx context.Context, req PaymentReq) (Payment, error) {
    existing, err := s.store.GetByIdemKey(ctx, req.IdempotencyKey)
    if err == nil {
        return existing, nil // return previous result — safe replay
    }
    result, err := s.gateway.Charge(req.Amount)
    if err != nil { return Payment{}, err }
    s.store.Save(ctx, req.IdempotencyKey, result)
    return result, nil
}

// --- Idempotent consumers (Kafka / SQS at-least-once) ---
func processEvent(ctx context.Context, event Event) error {
    // Option 1: natural idempotency (setting a value is idempotent)
    return db.ExecContext(ctx, "UPDATE status SET value=$1 WHERE id=$2", event.Value, event.ID)

    // Option 2: deduplication table
    _, err := db.ExecContext(ctx,
        "INSERT INTO processed_events (id) VALUES ($1) ON CONFLICT DO NOTHING",
        event.ID)
    if err != nil { return nil } // already processed
    return doRealWork(ctx, event)
}
```

### 77. Rate limiting.

```go
// --- In-process: token bucket (golang.org/x/time/rate) ---
import "golang.org/x/time/rate"

// Global limiter: 100 req/s, burst of 20
limiter := rate.NewLimiter(rate.Limit(100), 20)

func handler(w http.ResponseWriter, r *http.Request) {
    if !limiter.Allow() {
        http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
        return
    }
    // ... handle request ...
}

// Per-user / per-IP limiter
type IPRateLimiter struct {
    mu       sync.Mutex
    limiters map[string]*rate.Limiter
    limit    rate.Limit
    burst    int
}
func (l *IPRateLimiter) Get(ip string) *rate.Limiter {
    l.mu.Lock(); defer l.mu.Unlock()
    if lim, ok := l.limiters[ip]; ok { return lim }
    lim := rate.NewLimiter(l.limit, l.burst)
    l.limiters[ip] = lim
    return lim
}

func RateLimitMiddleware(ipLim *IPRateLimiter) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ip := r.RemoteAddr
            if !ipLim.Get(ip).Allow() {
                http.Error(w, "rate limited", 429); return
            }
            next.ServeHTTP(w, r)
        })
    }
}

// --- Distributed: Redis sliding window ---
// Use INCR + EXPIRE for simple fixed windows
// Use Lua scripts or redis-cell for sliding windows
script := redis.NewScript(`
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local current = redis.call('INCR', key)
if current == 1 then redis.call('EXPIRE', key, 1) end
if current > limit then return 0 end
return 1
`)
allowed, _ := script.Run(ctx, rdb, []string{"ratelimit:" + userID}, 100).Int()
if allowed == 0 { /* rate limited */ }

// --- Headers to communicate limits ---
w.Header().Set("X-RateLimit-Limit", "100")
w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(remaining))
w.Header().Set("X-RateLimit-Reset", strconv.FormatInt(resetAt.Unix(), 10))
w.Header().Set("Retry-After", "1") // seconds until retry is safe
```

### 78. Circuit breakers & bulkheads.

```go
// --- Circuit Breaker (sony/gobreaker) ---
import "github.com/sony/gobreaker"

cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    Name:          "payment-service",
    MaxRequests:   3,               // allow 3 requests in half-open
    Interval:      10 * time.Second, // clear counts every 10s in closed
    Timeout:       30 * time.Second, // open → half-open after 30s
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures > 5 // open after 5 consecutive failures
    },
    OnStateChange: func(name string, from, to gobreaker.State) {
        log.Printf("circuit %s: %s → %s", name, from, to)
        metrics.GaugeSet("circuit_open", float64(to), "name", name)
    },
})

func callPayment(ctx context.Context, req PayReq) (PayResp, error) {
    result, err := cb.Execute(func() (interface{}, error) {
        return paymentClient.Charge(ctx, req)
    })
    if err == gobreaker.ErrOpenState {
        return PayResp{}, fmt.Errorf("payment service unavailable: %w", err)
    }
    if err != nil { return PayResp{}, err }
    return result.(PayResp), nil
}

// States:
// CLOSED:    normal, all calls pass through
// OPEN:      failing, all calls fail fast (no network calls)
// HALF-OPEN: probing, MaxRequests calls allowed, then → CLOSED or OPEN

// --- Bulkhead: limit concurrent calls per downstream ---
type Bulkhead struct {
    sem chan struct{}
    name string
}
func NewBulkhead(name string, n int) *Bulkhead {
    return &Bulkhead{sem: make(chan struct{}, n), name: name}
}
func (b *Bulkhead) Execute(ctx context.Context, fn func() error) error {
    select {
    case b.sem <- struct{}{}:
        defer func() { <-b.sem }()
        return fn()
    case <-ctx.Done():
        return ctx.Err()
    default: // non-blocking: reject immediately if full
        return fmt.Errorf("bulkhead %s full: too many concurrent calls", b.name)
    }
}

// Separate bulkheads prevent cascade: slow DB can't starve HTTP calls
dbBulkhead := NewBulkhead("postgres", 20)
redisBulkhead := NewBulkhead("redis", 50)
thirdPartyBulkhead := NewBulkhead("stripe", 5) // very limited

// Combine both for maximum resilience:
// 1. Bulkhead caps concurrency to protect YOUR goroutines
// 2. Circuit breaker stops calls when downstream is unhealthy
```

### 79. Distributed locks & leader election.

```go
// --- Redis lock (go-redis + SETNX pattern) ---
func acquireLock(ctx context.Context, rdb *redis.Client, key string, ttl time.Duration) (bool, error) {
    // SET key value NX PX milliseconds — atomic, returns true if acquired
    ok, err := rdb.SetNX(ctx, "lock:"+key, "owner-id-uuid", ttl).Result()
    return ok, err
}

func releaseLock(ctx context.Context, rdb *redis.Client, key string) error {
    // Only delete if we own it (compare-and-delete via Lua)
    script := `
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end`
    return rdb.Eval(ctx, script, []string{"lock:" + key}, "owner-id-uuid").Err()
}

// --- rueidis-go/rueidislock (production-grade Redis lock) ---
import "github.com/redis/rueidis"
import "github.com/redis/rueidis/rueidislock"
locker, _ := rueidislock.NewLocker(rueidislock.LockerOption{
    ClientOption: rueidis.ClientOption{InitAddress: []string{":6379"}},
    KeyMajority: 1,
})
ctx, cancel, err := locker.WithContext(ctx, "my-lock")
if err == rueidislock.ErrNotLocked { return errors.New("couldn't acquire lock") }
defer cancel()
// ... do work while holding lock ...

// --- Postgres advisory locks (great when you already have Postgres) ---
func withAdvisoryLock(ctx context.Context, db *sql.DB, key int64, fn func() error) error {
    tx, _ := db.BeginTx(ctx, nil)
    defer tx.Rollback()
    if _, err := tx.ExecContext(ctx, "SELECT pg_advisory_xact_lock($1)", key); err != nil {
        return err // blocks until lock is acquired or timeout
    }
    if err := fn(); err != nil { return err }
    return tx.Commit() // lock released on commit
}

// --- Kubernetes leader election (for singleton background workers) ---
import "k8s.io/client-go/tools/leaderelection"

leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
    Lock:            &resourcelock.LeaseLock{...},
    ReleaseOnCancel: true,
    LeaseDuration:   15 * time.Second,
    RenewDeadline:   10 * time.Second,
    RetryPeriod:     2 * time.Second,
    Callbacks: leaderelection.LeaderCallbacks{
        OnStartedLeading: func(ctx context.Context) {
            runCronJobLoop(ctx) // only runs on leader pod
        },
        OnStoppedLeading: func() {
            log.Fatal("lost leadership") // restart the pod
        },
    },
})
// Use case: exactly one pod runs the scheduled cleanup job in a multi-replica deployment
```

### 80. Channels patterns — pipelines and cancellation.

```go
// Generic cancellable pipeline stage
func stage[T, U any](ctx context.Context, in <-chan T, f func(T) (U, error)) <-chan U {
    out := make(chan U)
    go func() {
        defer close(out)
        for v := range in {
            result, err := f(v)
            if err != nil {
                // optionally send to error channel; here we just drop
                continue
            }
            select {
            case out <- result:
            case <-ctx.Done(): return
            }
        }
    }()
    return out
}

// Full pipeline: source → transform → sink
func runPipeline(ctx context.Context, records []Record) error {
    // Stage 1: emit records
    source := func() <-chan Record {
        ch := make(chan Record)
        go func() {
            defer close(ch)
            for _, r := range records {
                select {
                case ch <- r:
                case <-ctx.Done(): return
                }
            }
        }()
        return ch
    }()

    // Stage 2: enrich (fan-out for parallelism)
    enriched := make(chan EnrichedRecord, 32)
    var wg sync.WaitGroup
    for i := 0; i < 4; i++ { // 4 parallel enrichers
        wg.Add(1)
        go func() {
            defer wg.Done()
            for r := range source {
                enriched <- enrich(r)
            }
        }()
    }
    go func() { wg.Wait(); close(enriched) }()

    // Stage 3: write to sink
    for e := range enriched {
        select {
        case <-ctx.Done(): return ctx.Err()
        default:
            if err := db.Insert(ctx, e); err != nil { return err }
        }
    }
    return nil
}

// Cancellation propagation rule:
// EVERY stage must select on ctx.Done() on both send and receive
// Forgetting this leaves goroutines blocked forever (goroutine leak)
```

### 81. Streaming large payloads.

```go
// --- Stream-decode a large JSON array without loading it all ---
func streamJSONArray(r io.Reader, process func(Item) error) error {
    dec := json.NewDecoder(r)

    // Read opening '['
    t, err := dec.Token()
    if err != nil { return err }
    if delim, ok := t.(json.Delim); !ok || delim != '[' {
        return errors.New("expected JSON array")
    }

    for dec.More() { // iterate through array elements
        var item Item
        if err := dec.Decode(&item); err != nil { return err }
        if err := process(item); err != nil { return err }
    }
    return nil
}

// --- Stream large file upload to S3 ---
func uploadHandler(w http.ResponseWriter, r *http.Request) {
    // Limit body size to prevent abuse
    r.Body = http.MaxBytesReader(w, r.Body, 100<<20) // 100 MB

    // Multipart reader — don't use r.ParseMultipartForm (loads to memory/disk)
    reader, err := r.MultipartReader()
    if err != nil { http.Error(w, "bad request", 400); return }

    for {
        part, err := reader.NextPart()
        if err == io.EOF { break }
        if err != nil { http.Error(w, "read error", 500); return }

        if part.FormName() == "file" {
            // Stream directly to S3 — never buffers the whole file in memory
            _, err = s3.PutObject(r.Context(), &s3.PutObjectInput{
                Bucket: aws.String("my-bucket"),
                Key:    aws.String(part.FileName()),
                Body:   part, // part implements io.Reader
            })
            if err != nil { http.Error(w, "upload failed", 500); return }
        }
    }
    w.WriteHeader(http.StatusCreated)
}

// --- io.Copy for efficient streaming between readers/writers ---
func proxyHandler(w http.ResponseWriter, r *http.Request) {
    resp, err := http.Get("https://backend/large-file")
    if err != nil { http.Error(w, "upstream error", 502); return }
    defer resp.Body.Close()

    w.Header().Set("Content-Type", resp.Header.Get("Content-Type"))
    // Streams: reads from upstream, writes to client in 32KB chunks
    // Never loads the entire response body into memory
    io.Copy(w, resp.Body)
}

// --- bufio.Scanner for large line-by-line files ---
func processCSV(path string) error {
    f, _ := os.Open(path)
    defer f.Close()
    scanner := bufio.NewScanner(f)
    scanner.Buffer(make([]byte, 1<<20), 1<<20) // 1MB per line max
    for scanner.Scan() {
        line := scanner.Text()
        processLine(line)
    }
    return scanner.Err()
}
```

### 82. File I/O patterns.

```go
// --- Reading ---
// Small file: read all at once
data, err := os.ReadFile("config.json") // convenience wrapper

// Large file: stream with bufio
f, err := os.Open("big.log")
if err != nil { return err }
defer f.Close()

scanner := bufio.NewScanner(f) // default 64KB per line
for scanner.Scan() {
    fmt.Println(scanner.Text())
}
if err := scanner.Err(); err != nil { return err }

// --- Writing ---
// Small file: write all at once
os.WriteFile("out.txt", data, 0644)

// Large/streaming: buffered writer
f, err = os.Create("output.log")
if err != nil { return err }
bw := bufio.NewWriter(f)

for _, line := range lines {
    if _, err := fmt.Fprintln(bw, line); err != nil { return err }
}

// MUST flush before close — unflushed data in buffer will be lost
if err := bw.Flush(); err != nil { return err }

// ALWAYS check Close error on writers (Flush happens inside)
if err := f.Close(); err != nil { return err } // catches flush failures

// --- Atomic write (avoid partial writes) ---
func atomicWrite(path string, data []byte) error {
    tmpPath := path + ".tmp." + strconv.FormatInt(time.Now().UnixNano(), 36)
    if err := os.WriteFile(tmpPath, data, 0644); err != nil { return err }
    return os.Rename(tmpPath, path) // atomic on same filesystem
}

// --- fsync for durability (important for WAL, DB files) ---
f.Sync() // flushes OS page cache to disk — expensive but necessary for durability

// --- Temp files ---
tmpFile, err := os.CreateTemp("", "prefix-*.json")
defer os.Remove(tmpFile.Name())
defer tmpFile.Close()

// --- Walk directory ---
err = filepath.WalkDir("./data", func(path string, d fs.DirEntry, err error) error {
    if err != nil { return err }
    if d.IsDir() { return nil } // skip directories
    fmt.Println(path, d.Name())
    return nil
})
```

### 83. Embedding files in binaries.

```go
import "embed"

// Embed a single file
//go:embed config/default.yaml
var defaultConfig []byte

// Embed multiple files into an FS
//go:embed templates/*
var templateFS embed.FS

//go:embed migrations/*.sql
var migrationsFS embed.FS

//go:embed static
var staticFS embed.FS

// Use embedded templates
func main() {
    tmpl, err := template.ParseFS(templateFS, "templates/*.html")
    if err != nil { log.Fatal(err) }
    tmpl.ExecuteTemplate(os.Stdout, "index.html", data)
}

// Use embedded migrations
func runMigrations(db *sql.DB) error {
    m, err := migrate.New(
        "iofs://migrationsFS/migrations", // iofs source
        "postgres://...",
    )
    if err != nil { return err }
    return m.Up()
}

// Serve static files
http.Handle("/static/", http.FileServer(http.FS(staticFS)))

// Read individual file from embed.FS
data, err := migrationsFS.ReadFile("migrations/001_create_users.up.sql")

// Walk embedded files
entries, _ := templateFS.ReadDir("templates")
for _, entry := range entries {
    fmt.Println(entry.Name())
}

// Benefits:
// ✓ Single binary deployment — no external files to manage
// ✓ No "file not found" errors in containers
// ✓ Files are baked in at compile time — version-locked with code
// ✓ Works great for: HTML templates, SQL migrations, default configs,
//   static assets (for small apps), i18n files, test fixtures
//
// Limitation: embedded files increase binary size
// For large static assets, prefer a CDN or object storage
```

### 84. `context.Value` — when (not) to use.

```go
// --- CORRECT uses: request-scoped metadata ---

// 1. Trace/request ID (set by middleware, read anywhere in the call chain)
type traceKey struct{}
func WithTraceID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, traceKey{}, id)
}
func TraceID(ctx context.Context) string {
    if v, ok := ctx.Value(traceKey{}).(string); ok { return v }
    return ""
}

// 2. Authenticated user (set after JWT validation in middleware)
type userKey struct{}
func WithUser(ctx context.Context, u *User) context.Context {
    return context.WithValue(ctx, userKey{}, u)
}
func CurrentUser(ctx context.Context) *User {
    u, _ := ctx.Value(userKey{}).(*User)
    return u
}

// Middleware sets it:
ctx = WithUser(r.Context(), authenticatedUser)
ctx = WithTraceID(ctx, uuid.New().String())
// Handler reads it:
user := CurrentUser(r.Context())
log.Info("request", "trace", TraceID(r.Context()), "user", user.ID)

// --- INCORRECT uses ---

// BAD: passing function parameters through context
func getUser(ctx context.Context) (*User, error) {
    id := ctx.Value("user_id").(int) // hidden dependency, untestable
    return db.Get(ctx, id)
}
// GOOD: explicit parameter
func getUser(ctx context.Context, id int) (*User, error) {
    return db.Get(ctx, id)
}

// BAD: using string keys — collision-prone
ctx = context.WithValue(ctx, "token", token) // any package can collide on "token"
// GOOD: private struct type as key
type tokenKey struct{}
ctx = context.WithValue(ctx, tokenKey{}, token)

// BAD: using context to pass optional config
func processOrder(ctx context.Context) error {
    dryRun := ctx.Value("dry_run").(bool) // hides control flow
    // ...
}
// GOOD: explicit boolean parameter or a config struct
func processOrder(ctx context.Context, opts ProcessOpts) error {}

// Rule of thumb: if you can put it in a function parameter, do that.
// context.Value is only for cross-cutting concerns (auth, tracing, locale)
// that would pollute every function signature if passed explicitly.
```

### 85. TLS / crypto best practices.

```go
import "crypto/tls"

// --- Server TLS ---
tlsCfg := &tls.Config{
    MinVersion: tls.VersionTLS13, // or VersionTLS12 for broader compat
    // Go's defaults are good — don't set CipherSuites manually for TLS 1.3
    // For TLS 1.2 compatibility, avoid RC4, 3DES, export ciphers
    CurvePreferences: []tls.CurveID{tls.X25519, tls.CurveP256},
    ServerName: "api.myapp.com",
}

srv := &http.Server{
    Addr:      ":443",
    Handler:   mux,
    TLSConfig: tlsCfg,
}
srv.ListenAndServeTLS("cert.pem", "key.pem")

// --- Let's Encrypt (auto-renew certs) ---
import "golang.org/x/crypto/acme/autocert"
m := &autocert.Manager{
    Prompt:     autocert.AcceptTOS,
    HostPolicy: autocert.HostWhitelist("api.myapp.com"),
    Cache:      autocert.DirCache("/var/cache/certs"),
}
srv.TLSConfig = m.TLSConfig()

// --- Client TLS ---
var httpClient = &http.Client{
    Transport: &http.Transport{
        TLSClientConfig: &tls.Config{
            MinVersion: tls.VersionTLS12,
            // InsecureSkipVerify: true — NEVER in production
        },
    },
}

// --- Hashing passwords ---
import "golang.org/x/crypto/bcrypt"
hash, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
bcrypt.CompareHashAndPassword(hash, []byte(candidatePassword))

// --- Generating random tokens ---
import "crypto/rand"
token := make([]byte, 32)
if _, err := rand.Read(token); err != nil { panic(err) }
hex.EncodeToString(token) // safe URL token

// --- HMAC for signing ---
import "crypto/hmac"
import "crypto/sha256"
mac := hmac.New(sha256.New, []byte(secret))
mac.Write([]byte(message))
signature := mac.Sum(nil)
hex.EncodeToString(signature)

// Rules:
// ✓ Use crypto/rand, never math/rand for security-sensitive values
// ✓ Use bcrypt/argon2 for passwords, never MD5/SHA-1
// ✓ Never implement your own crypto algorithm
// ✓ Store hashes, never plaintext passwords
// ✓ Use TLS 1.2+ everywhere
// ✓ Rotate secrets regularly; use a secrets manager (Vault, AWS Secrets Manager)
```

### 86. Package design rules of thumb.

```
myapp/
  cmd/server/       ← entry point — minimal, just wiring
  internal/         ← can't be imported by external modules
    user/           ← package named for the DOMAIN CONCEPT, not "UserManager"
    order/
    payment/
  pkg/              ← reusable utilities (if truly generic)
    httputil/       ← HTTP helpers
    pgutil/         ← Postgres helpers
```

```go
// GOOD package names: user, order, payment, auth, notification
// BAD: models, utils, helpers, common, manager, service (too vague)

// --- Circular imports — NOT allowed in Go ---
// package a imports b, b imports a → compile error
// Fix: extract shared types to a third package (domain)

// --- Interface placement: consumer defines, not producer ---
// In service/user_service.go:
type UserRepo interface {   // defined where it's used
    Get(ctx context.Context, id int) (User, error)
}
// NOT in adapters/postgres:
type UserRepo interface { Get(...) } // producer shouldn't define what consumers need

// --- Minimal public API ---
package auth

// Export only what callers need:
func Validate(token string) (*Claims, error) { ... } // exported
func parseJWT(raw string) (*Claims, error)  { ... } // unexported — implementation detail

// --- internal/ packages ---
// internal/user/ can ONLY be imported from within the same module
// Great for shared code that shouldn't become a public API

// --- Error types: avoid leaking internals ---
// BAD: return *postgres.Error — caller depends on postgres package
// GOOD: return *AppError or sentinel — caller only sees domain errors

// --- File layout within a package ---
user/
  user.go           ← type definitions, constructors
  service.go        ← business logic
  repository.go     ← repo interface
  user_test.go      ← tests
  testhelpers_test.go ← test utilities (only available in tests)

// Rules summary:
// 1. Name for what it PROVIDES, not what it CONTAINS
// 2. No circular dependencies
// 3. Interfaces belong to the consumer
// 4. Use internal/ to prevent external coupling
// 5. Keep exported API minimal — it's easier to add than remove
// 6. Avoid utils/common dumps — put code where it belongs
```

### 87. Goroutine ownership.

```go
// Rule: every goroutine must have:
// 1. A clear OWNER (the thing that started it)
// 2. A way to STOP it
// 3. A way to know when it's DONE

// --- Pattern 1: context cancellation ---
func StartWorker(ctx context.Context, jobs <-chan Job) <-chan Result {
    results := make(chan Result)
    go func() {
        defer close(results) // signals consumers that we're done
        for {
            select {
            case <-ctx.Done(): return // stop via context cancellation
            case j, ok := <-jobs:
                if !ok { return } // stop when jobs channel closed
                results <- process(j)
            }
        }
    }()
    return results
}

// Owner:
ctx, cancel := context.WithCancel(context.Background())
results := StartWorker(ctx, jobs)
cancel() // stop the worker
// drain results to ensure goroutine has exited
for range results {}

// --- Pattern 2: explicit Stop + Wait ---
type Processor struct {
    jobs chan Job
    done chan struct{}
    wg   sync.WaitGroup
}
func (p *Processor) Start() {
    p.wg.Add(1)
    go func() {
        defer p.wg.Done()
        for {
            select {
            case <-p.done: return
            case j := <-p.jobs: process(j)
            }
        }
    }()
}
func (p *Processor) Stop() {
    close(p.done) // signal stop
    p.wg.Wait()   // wait for goroutine to exit
}

// --- Goroutine leak example (BAD) ---
func badLeaky() {
    go func() {
        for {
            // infinite loop with no way to stop
            time.Sleep(time.Second)
            doWork()
        }
    }()
    // goroutine lives forever — even after caller is done
}

// --- Goroutine documentation ---
// Document the contract in comments:
// // StartPoller starts a background goroutine that polls every d.
// // The goroutine exits when ctx is cancelled.
// // Callers should wait for Done() before program exit.
func StartPoller(ctx context.Context, d time.Duration) *Poller { ... }

// --- Detection ---
import "go.uber.org/goleak"
func TestNoLeaks(t *testing.T) {
    defer goleak.VerifyNone(t)
    p := StartPoller(ctx, time.Second)
    cancel()
    p.Wait()
}
```

### 88. Deadlocks.

```go
// --- Deadlock type 1: channel with no sender ---
ch := make(chan int)
fmt.Println(<-ch) // DEADLOCK: nobody sends

// --- Deadlock type 2: send with no receiver ---
ch := make(chan int)
ch <- 1 // DEADLOCK: nobody receives
fmt.Println("never reached")

// --- Deadlock type 3: mutex in inconsistent order ---
var mu1, mu2 sync.Mutex
go func() {
    mu1.Lock(); defer mu1.Unlock() // goroutine A: locks mu1 then mu2
    mu2.Lock(); defer mu2.Unlock()
}()
go func() {
    mu2.Lock(); defer mu2.Unlock() // goroutine B: locks mu2 then mu1
    mu1.Lock(); defer mu1.Unlock() // → circular wait → DEADLOCK
}()
// Fix: always acquire locks in the SAME ORDER across all goroutines

// --- Deadlock type 4: goroutine waiting on itself ---
var wg sync.WaitGroup
wg.Add(1)
go func() {
    wg.Wait()  // waits for counter to reach 0
    wg.Done()  // but Done() is only called AFTER Wait() returns → DEADLOCK
}()

// Fix: Done() must be called before Wait() returns
var wg2 sync.WaitGroup
wg2.Add(1)
go func() {
    defer wg2.Done()
    doWork()
}()
wg2.Wait() // correct

// --- Deadlock type 5: channel in select not drained ---
ch1 := make(chan int, 1)
ch2 := make(chan int)
ch1 <- 99
select {
case v := <-ch1: fmt.Println(v)    // this fires
case ch2 <- 1: fmt.Println("sent")  // ch2 has no receiver
}

// --- Runtime detection ---
// Go runtime detects when ALL goroutines are blocked:
// fatal error: all goroutines are asleep - deadlock!
// goroutine 1 [chan receive]:
// main.main() /tmp/main.go:7 +0x28

// --- Detection tools ---
// go run -race .                 // detects data races (not deadlocks directly)
// GOTRACEBACK=all go run .       // full stack on panic
// pprof /debug/pprof/goroutine   // see all blocked goroutines in prod

// --- Prevention patterns ---
// 1. Consistent lock ordering
// 2. Use context timeouts so blocked goroutines eventually unblock
// 3. Use select with ctx.Done() on all channel ops
// 4. Never call Lock() and Wait() from the same goroutine in a way that could cycle
```

### 89. Memory leaks in Go.

```go
// --- Leak 1: goroutine holding references (most common) ---
func leaky() {
    data := make([]byte, 100<<20) // 100MB
    go func() {
        time.Sleep(365 * 24 * time.Hour) // goroutine lives forever
        _ = data // data can't be GC'd while goroutine is alive!
    }()
}

// --- Leak 2: ever-growing map ---
var cache = map[string][]byte{}
func handle(key string, data []byte) {
    cache[key] = data // never deleted → OOM eventually
}
// Fix: use TTL cache (ristretto, groupcache) or bounded LRU

// --- Leak 3: time.Tick leaks a goroutine ---
for range time.Tick(time.Second) { // BAD: no way to stop
    doWork()
}
// Fix:
ticker := time.NewTicker(time.Second)
defer ticker.Stop() // stops the internal goroutine
for range ticker.C { doWork() }

// --- Leak 4: large backing array pinned by small subslice ---
func getFirst100(s []byte) []byte {
    return s[:100] // entire backing array (e.g., 100MB) stays alive!
}
// Fix: copy out the needed part
func getFirst100Safe(s []byte) []byte {
    result := make([]byte, 100)
    copy(result, s[:100]) // breaks reference to large slice
    return result
}

// --- Leak 5: large string pinned by substring ---
func extractPrefix(s string) string {
    return s[:10] // same issue as slices
}
// Fix:
func extractPrefix(s string) string {
    return strings.Clone(s[:10]) // Go 1.20+: breaks reference
}

// --- Leak 6: net.Conn / http.Response.Body not closed ---
resp, _ := http.Get(url)
// if we never read and close resp.Body, the connection is never returned
// to the pool, and the goroutine inside the transport leaks
defer resp.Body.Close()           // ALWAYS
io.Copy(io.Discard, resp.Body)     // drain before closing (if not fully read)

// --- Detection ---
go func() {
    log.Println(http.ListenAndServe("localhost:6060", nil))
}()
// go tool pprof http://localhost:6060/debug/pprof/heap
// Watch: inuse_space, inuse_objects over time
// Steadily growing → leak

import "runtime"
var ms runtime.MemStats
runtime.ReadMemStats(&ms)
fmt.Printf("Alloc=%dMB, HeapInuse=%dMB, NumGC=%d\n",
    ms.Alloc/1024/1024, ms.HeapInuse/1024/1024, ms.NumGC)
```

### 90. When *not* to use Go.

```
Go EXCELS at:                         Go is NOT the best for:
─────────────────────────────────     ────────────────────────────────────
✓ HTTP/gRPC services                 ✗ GUI desktop apps
✓ CLI tools (fast startup, small     ✗ Scientific computing / ML training
  binary — kubectl, helm, tf)           (Python + NumPy/PyTorch wins here)
✓ Infrastructure tooling             ✗ Embedded MCUs (no runtime for C/ARM)
  (Docker, K8s, Terraform)           ✗ One-off scripts (Python is faster
✓ Network proxies and sidecars          to write; no binary needed)
  (Envoy, Istio control plane)       ✗ Heavy DSP/signal processing
✓ Data pipelines (ETL, streaming)    ✗ Browser/frontend (WASM possible,
✓ Cloud-native microservices            but React/Vue is far more ergonomic)
✓ Platform/SRE tooling              ✗ Scripting in notebooks
✓ High-concurrency data plane       ✗ Rapid ML experimentation
```

```go
// Use Go when you need:
// 1. Predictable, low latency (GC pauses <1ms, efficient goroutines)
// 2. High concurrency (thousands of goroutines vs OS threads)
// 3. Single static binary for simple deployment
// 4. Fast startup (containers, CLIs, Lambda)
// 5. Strong typing without verbosity
// 6. Easy cross-compilation (build for Linux from Mac)

// Don't use Go when:
// 1. The domain has better libraries elsewhere
//    - ML model training → Python (PyTorch/TensorFlow ecosystem)
//    - Statistical analysis → Python (pandas, scipy)
//    - Browser UI → TypeScript/React
// 2. You need a REPL for interactive exploration
// 3. You need generics/metaprogramming that Go doesn't support well
// 4. Script-level tasks where python/bash is faster to write

// Common polyglot architecture:
// ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
// │  Go service │───▶│ Python model │    │  TypeScript  │
// │  (REST/gRPC)│    │  inference   │    │  frontend    │
// │  - auth     │    │  (FastAPI +  │    │  (Next.js)   │
// │  - routing  │    │   PyTorch)   │    │              │
// │  - data ETL │    └──────────────┘    └──────────────┘
// └─────────────┘
// Go handles the high-throughput service layer;
// Python handles ML; TypeScript handles UI.
// Use the right tool for each layer.
```

---

## 7. Common Sample Snippets

### Worker pool
```go
func process(ctx context.Context, jobs <-chan Job) error {
    g, ctx := errgroup.WithContext(ctx)
    for i := 0; i < runtime.NumCPU(); i++ {
        g.Go(func() error {
            for {
                select {
                case <-ctx.Done():
                    return ctx.Err()
                case j, ok := <-jobs:
                    if !ok { return nil }
                    if err := handle(ctx, j); err != nil { return err }
                }
            }
        })
    }
    return g.Wait()
}
```

### HTTP handler with timeout & JSON
```go
func GetUser(svc UserService) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
        defer cancel()
        u, err := svc.Get(ctx, r.PathValue("id"))
        if errors.Is(err, ErrNotFound) {
            http.Error(w, "not found", http.StatusNotFound); return
        }
        if err != nil {
            http.Error(w, "internal", http.StatusInternalServerError); return
        }
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(u)
    }
}
```

### Graceful shutdown
```go
func main() {
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()
    srv := &http.Server{Addr: ":8080", Handler: router()}
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()
    <-ctx.Done()
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    _ = srv.Shutdown(shutdownCtx)
}
```
