# Go Basic Interview Questions (Detailed)

### 1. Why was Go designed?
Go was created at Google to address the pain points of large-scale systems programming: slow C++ build times, complex inheritance hierarchies, weak concurrency support, and verbose syntax. Its design goals were simplicity (one obvious way to do things), fast compilation, native concurrency via goroutines, and a strong standard library. It deliberately omits features like inheritance, generics (until 1.18), and exceptions to keep the language small and the code uniform across teams.

### 2. What is a goroutine?
A goroutine is a lightweight thread managed by the Go runtime, not the OS. It starts with a small stack (~2 KB) that grows on demand and is multiplexed onto a small pool of OS threads by the Go scheduler (M:N model). Spawning thousands or even millions of goroutines is normal — context switches are cheap and there is no per-goroutine kernel-level resource cost.

### 3. What is a channel?
A channel is a typed conduit through which goroutines communicate and synchronize. **Unbuffered** channels are synchronous — send blocks until a receiver is ready. **Buffered** channels (`make(chan T, n)`) decouple sender and receiver up to capacity n. Channels are first-class values, can be passed to functions, stored in structs, and closed by senders to signal "no more values."

### 4. Difference between value and pointer receivers.
A value receiver (`func (c Counter) Inc()`) operates on a copy — mutations are local and lost. A pointer receiver (`func (c *Counter) Inc()`) operates on the original — mutations persist. Use pointer receivers when the method mutates state, when the struct is large (avoid copying), or when consistency across methods is required (mixing receiver types on the same type is a smell).

### 5. What is a slice and how does it differ from an array?
An **array** has a fixed length that is part of its type (`[5]int` and `[6]int` are different types). A **slice** is a lightweight header (pointer + length + capacity) referencing an underlying array — it can grow with `append`, shrink with reslicing, and is the standard collection type. Slices share backing storage, so mutating a sub-slice can affect the original until a grow forces reallocation.

### 6. How do maps work?
Go maps are open-addressing hash tables with O(1) amortized lookup/insert/delete. Iteration order is intentionally randomized to discourage reliance on it. Maps are not safe for concurrent use — use `sync.Map` or guard with a `sync.RWMutex`. Always use the comma-ok idiom (`v, ok := m[key]`) to distinguish "missing key" from "zero value present."

### 7. What is an interface in Go?
An interface is a set of method signatures. A type satisfies an interface **implicitly** by implementing all its methods — there is no `implements` keyword. The empty interface `interface{}` (now `any`) holds any value. Interfaces are central to Go's polymorphism, dependency injection, and testing — pass interfaces, return concrete types ("accept interfaces, return structs").

### 8. How does error handling work?
Go uses explicit return values, not exceptions. Functions that can fail return `(T, error)`, and callers must check `if err != nil`. Errors wrap with `fmt.Errorf("context: %w", err)` to preserve the cause chain; inspect with `errors.Is` (sentinel match) and `errors.As` (type assertion on chain). `panic`/`recover` exists only for truly unrecoverable bugs, not normal control flow.

### 9. What is `defer`?
`defer` schedules a function to run when the surrounding function returns, regardless of how it returns (normal or panic). Common uses: closing files/connections, unlocking mutexes, restoring state. Multiple defers execute in LIFO order. Be careful: deferred arguments are evaluated **at defer time**, but the call happens at return time.

### 10. Difference between `make` and `new`.
**`new(T)`** allocates zero-valued storage for type T and returns `*T` — rarely used directly. **`make(T, ...)`** initializes the internal data structure of slices, maps, and channels and returns the value (not a pointer). You almost always want `make` for these three types; `new` is mostly historical now that struct literals are common.

### 11. How do you write a struct in Go?
`type Order struct { ID int; Amount float64; Status string }`. Fields starting with uppercase are exported (visible outside the package), lowercase are unexported. Initialize with named fields (`Order{ID: 1, Amount: 50}`) for clarity. Struct tags (backticks) add metadata used by libraries — `json:"id"`, `db:"order_id"`.

### 12. What is the difference between `:=` and `=`?
**`:=`** is short variable declaration — declares AND assigns, only valid inside functions. **`=`** is plain assignment to an already-declared variable. At least one variable on the left of `:=` must be new; using `:=` with all existing variables is a compile error.

### 13. What are Go's basic data types?
Numerics: `int`, `int8/16/32/64`, `uint*`, `float32/64`, `complex64/128`, `byte` (alias for uint8), `rune` (alias for int32 — a Unicode code point). String: `string` (immutable UTF-8 bytes). Boolean: `bool`. Each has a zero value (`0`, `""`, `false`).

### 14. How does string handling work in Go?
Strings are immutable byte sequences, typically UTF-8 encoded. Indexing returns a byte (`s[0]` is `byte`), iterating with `range` yields `(byteIndex, rune)` pairs. Use the `strings` package for manipulation, `strings.Builder` for efficient concatenation in loops, and `[]rune(s)` when you need code-point-aware length/indexing.

### 15. What is a package?
A package is the unit of code organization and visibility. Every file declares `package name`. The first letter of an identifier determines visibility (uppercase = exported). Packages are imported by full path; each module's `go.mod` declares the module path that becomes the import prefix.

### 16. What is `iota`?
A constant generator inside `const` blocks. It starts at 0 and increments by 1 with each `ConstSpec`, perfect for enums: `const ( Sunday = iota; Monday; Tuesday )`. Combine with expressions for bit flags: `const ( ReadOnly = 1 << iota; WriteOnly; Exec )`.

### 17. What are Go's built-in functions?
`len`, `cap`, `make`, `new`, `append`, `copy`, `delete` (for maps), `close` (for channels), `panic`, `recover`, `print`, `println` (the last two are debug-only). They are pre-declared in the universe block and require no import.

### 18. How do you import packages?
`import "fmt"` for single, or `import ( "fmt"; "os" )` for grouped. Use blank identifier `_` for side-effects only (`_ "github.com/lib/pq"` registers the driver). Aliases: `import f "fmt"`. The `go.mod` file declares the module and its dependencies, managed with `go get`, `go mod tidy`.

### 19. What is the zero value?
Every type has a zero value when declared without initialization: numerics → 0, strings → "", booleans → false, pointers/slices/maps/channels/interfaces → nil, structs → all fields zero. This eliminates an entire class of "uninitialized variable" bugs and removes the need for default constructors.

### 20. What is the difference between `panic` and `error`?
**`error`** is a regular value used for expected, recoverable failures — the caller decides what to do. **`panic`** unwinds the stack and crashes the goroutine, used only for unrecoverable bugs (programming mistakes, impossible states). Library code should never panic on bad input; return an error so callers can handle it.
