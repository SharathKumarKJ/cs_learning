# Performance and Profiling Notes

## Profiling tools
- `go test -bench=. -benchmem` — built-in benchmark runner with memory stats.
- `go test -cpuprofile=cpu.out -memprofile=mem.out` — write profiles from tests.
- `go tool pprof cpu.out` — interactive analysis.
- `net/http/pprof` — serve profiles from a running HTTP service on `/debug/pprof/`.
- `runtime/trace` — execution tracer to inspect goroutine scheduling.

## Common perf wins in Go services
1. Pre-allocate slices/maps with `make([]T, 0, n)` when size is known.
2. Reuse buffers with `sync.Pool` for hot allocations.
3. Avoid reflection in hot paths; prefer code generation if needed.
4. Use `strings.Builder` for string concatenation in loops.
5. Use `bufio.Reader/Writer` for I/O.
6. Keep struct fields aligned (largest first) to reduce padding.
7. Use `chan struct{}` for signaling — zero-byte, no allocation.
8. Profile before optimizing; intuition is often wrong.

## Memory model
- Goroutines have a small stack (2 KB) that grows on demand.
- Garbage collector is concurrent, low-latency, generational-ish.
- Escape analysis decides stack vs heap allocation; `go build -gcflags='-m'` to inspect.

## Concurrency tips
- Don't communicate by sharing memory; share memory by communicating (channels).
- Always close channels from the sender, never the receiver.
- Use `context.Context` for cancellation everywhere.
- Detect data races with `go run -race main.go` or `go test -race`.
