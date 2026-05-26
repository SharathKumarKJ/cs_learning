# Go for Senior / Staff Data & Backend Engineers

A complete Go learning track for engineers moving into Go-based services, streaming workers, and platform code.

## Folders
- `01_basics/` — syntax, types, structs, slices/maps, methods, interfaces, errors.
- `02_concurrency/` — goroutines, channels, sync primitives, worker pool, fan-in/out, pipeline, context.
- `03_advanced/` — generics, reflection, performance, profiling, testing, benchmarks.
- `04_data_engineering/` — Kafka producer/consumer, HTTP server, gRPC, JSON, Postgres, S3.
- `05_design_patterns/` — singleton, factory, builder, strategy, observer, repository, circuit breaker, rate limiter.
- `06_interview_questions/` — basic-to-staff-level Go Q&A with detailed answers.
- `07_system_design/` — Go-centric system design problems.

## How to run any example
```bash
cd go_for_data_engineering/<folder>
go mod init example.com/<name>   # if needed
go run main.go
```

Most examples are self-contained `main.go` programs. For external deps (Kafka, gRPC), see comments in each file for `go get` commands.
