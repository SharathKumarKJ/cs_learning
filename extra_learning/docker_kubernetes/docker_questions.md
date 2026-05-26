# Docker for Data Engineers (Detailed)

### 1. What is Docker?
A platform to package an application and its dependencies into a portable **image** that runs as an isolated **container** on any host with a compatible OS kernel. Solves "works on my machine" by shipping the runtime, libraries, and code together.

### 2. Image vs container.
An **image** is an immutable layered filesystem + metadata (entrypoint, env, ports). A **container** is a running instance of an image with a writable top layer. One image → many containers.

### 3. Dockerfile basics.
**FROM** base image; **WORKDIR**; **COPY** source; **RUN** install steps; **ENV** env vars; **EXPOSE** documented ports; **USER** non-root; **ENTRYPOINT** the binary to run; **CMD** default args. Order layers from least-to-most-frequently-changed for cache efficiency.

### 4. Multi-stage builds.
Use multiple `FROM` stages in one Dockerfile to compile/build in a fat stage, then `COPY --from=builder` only the final artifacts into a slim runtime image. Drastically reduces image size and attack surface.

### 5. Volumes vs bind mounts.
**Volumes**: Docker-managed storage, portable across hosts (more or less), preferred for state. **Bind mounts**: map a host directory into the container, useful for local dev. **tmpfs**: in-memory only. Containers should be stateless wherever possible.

### 6. Networks.
By default each container joins the `bridge` network. Create user-defined networks for service discovery by name (e.g. compose). `host` shares the host net stack; `none` isolates completely. For production K8s replaces this concept with Services.

### 7. docker-compose.
Defines a multi-container app in YAML (services, networks, volumes). Great for local dev: spin up Postgres + Kafka + your ETL with one command. Not a production orchestrator — use Kubernetes for that.

### 8. Why Docker for ETL?
**Reproducibility** (frozen Python/Spark versions), **isolation** (no host pollution), **portability** (laptop → CI → prod), **scalability** (run as KubernetesPodOperator in Airflow, Cloud Run jobs, ECS tasks), and **dependency management** (system libs like libsnappy, libpostgres bundled in).

### 9. Image size optimization.
Use slim/distroless base images, multi-stage builds, `.dockerignore` to exclude tests/data/`.git`, combine `RUN` commands to reduce layers, pin and clean apt/pip caches (`rm -rf /var/lib/apt/lists/*`, `pip --no-cache-dir`), and review with `dive` or `docker history`.

### 10. Security best practices.
Run as non-root `USER`, pin base image by digest (not just tag), scan images (Trivy, Snyk, Grype), keep secrets out of images (use runtime injection), drop Linux capabilities, use read-only root FS where possible, and refresh base images regularly for CVE patches.

### 11. Common commands.
`docker build -t name:tag .`, `docker run -e KEY=VAL -p 8080:80 name:tag`, `docker exec -it container bash`, `docker logs -f container`, `docker ps -a`, `docker images`, `docker push/pull`, `docker compose up -d`, `docker system prune` to reclaim disk.

### 12. Healthchecks.
`HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1` in Dockerfile, or `healthcheck:` in compose. Orchestrators (K8s, ECS) use them to restart unhealthy containers; for batch jobs healthchecks are less common.

---

## Advanced Docker

### 13. How containers actually work.
Containers are Linux processes isolated via **namespaces** (pid, net, mnt, uts, ipc, user) and limited via **cgroups** (cpu, memory, io). Filesystem is layered via OverlayFS. They share the host kernel — not VMs. On macOS/Windows, Docker runs a tiny Linux VM behind the scenes.

### 14. Image layers and build cache.
Each Dockerfile instruction creates a layer; identical instruction + identical context → cache hit. Order steps so frequently-changing ones come last. Copy `go.mod`/`requirements.txt` and install deps **before** copying source so code edits don't bust the dependency layer.

### 15. BuildKit.
Modern builder (default in Docker 23+). Features: parallel stage builds, secret mounts (`--mount=type=secret`), SSH forwarding, cache mounts (`--mount=type=cache,target=/root/.cache/go-build`), better output. Enable with `DOCKER_BUILDKIT=1` or use `docker buildx`.

### 16. `docker buildx` and multi-arch.
`buildx` is the BuildKit-powered CLI. Build for multiple architectures in one command: `docker buildx build --platform linux/amd64,linux/arm64 -t img:tag --push .`. Essential for Apple Silicon dev + amd64 prod.

### 17. ENTRYPOINT vs CMD.
`ENTRYPOINT` is the binary always executed; `CMD` provides default args. `docker run img foo` replaces `CMD`, not `ENTRYPOINT`. Use exec form (JSON array) — shell form spawns `/bin/sh -c` and breaks signal forwarding (SIGTERM never reaches your app → 10s SIGKILL).

### 18. PID 1 and signal handling.
The container's main process is PID 1 — Linux ignores default signal handlers for PID 1. If your app doesn't handle SIGTERM explicitly, use a tiny init like `tini` (`--init` flag or `ENTRYPOINT ["/tini","--"]`) so signals propagate and zombies are reaped. Critical for graceful shutdown.

### 19. Distroless and scratch images.
**`scratch`**: empty — only static binaries (Go!). **Distroless** (`gcr.io/distroless/*`): minimal base with glibc/CA certs/tzdata but no shell or package manager. Tiny, secure, fewer CVEs. Trade-off: no `exec sh` for debugging — use `:debug` variants or ephemeral debug containers.

### 20. Build secrets.
Never `COPY` secrets or use `ARG` for them — they end up in image history. Use BuildKit secret mounts:
```Dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm install
```
Pass with `docker build --secret id=npmrc,src=$HOME/.npmrc`. Secret never persists in any layer.

### 21. Image scanning & SBOMs.
`docker scout`, `trivy image img:tag`, Snyk, Grype scan for CVEs. Generate SBOMs (`syft`, `docker buildx build --sbom=true`) and sign with `cosign` for supply-chain integrity (SLSA). Wire into CI to block builds with critical CVEs.

### 22. Resource limits.
`docker run --memory=512m --cpus=1.5` maps to cgroups. JVMs and Go runtimes (`GOMEMLIMIT` since 1.19) need to know the container limit — without it they tune to host memory and OOM. Always set limits in prod; never run unbounded.

### 23. Networking deep dive.
Default `bridge` uses NAT (`docker0`). User-defined bridges add DNS-based service discovery — containers resolve each other by name. `host` network skips namespace (Linux only, fastest). `macvlan` gives container a real MAC on the LAN. Overlay networks (Swarm) for multi-host.

### 24. Volume drivers and data persistence.
Named volumes (`docker volume create`) are managed by Docker, survive container removal. Plugins enable NFS, EBS, Ceph, etc. For stateful workloads in prod prefer Kubernetes PVCs over plain Docker volumes — better lifecycle, snapshots, and replication.

### 25. Logging drivers.
Default `json-file` writes to disk on the host (rotate via `max-size`/`max-file`). Alternatives: `journald`, `syslog`, `fluentd`, `awslogs`, `gcplogs`. In K8s, app should log JSON to stdout/stderr and let the platform collect — don't write log files inside containers.

### 26. Docker socket security.
`/var/run/docker.sock` mounted into a container = root on host. Avoid it. If you must (CI runners, dind), use a rootless setup, `sysbox`, or sidecars like `docker-socket-proxy` exposing only required APIs.

### 27. Rootless Docker & user namespaces.
Run dockerd as a non-root user; container UIDs map to unprivileged host UIDs via user namespaces. Reduces blast radius dramatically. Some features (host networking, low ports) restricted. Podman is rootless by default and largely Docker-CLI-compatible.

### 28. Build context discipline.
`docker build .` sends the whole directory to the daemon. Large `.git`, `node_modules`, `data/` slow builds and may bust cache. Use `.dockerignore` aggressively. Build context size is also a security concern — secrets in the directory can leak via `COPY`.

### 29. Layer reuse across services.
Share a common base image (`FROM company/python-base:3.12`) so multiple services share layers in the registry and on hosts. Periodically rebuild bases for CVE patches. Pin base by digest (`@sha256:...`) in service Dockerfiles for reproducibility.

### 30. Reproducible builds.
Pin base images by digest, pin all package versions (apt with `=`, pip with `==`, Go with `go.sum`), set `SOURCE_DATE_EPOCH` for deterministic timestamps, avoid `apt-get update && apt-get install` without pinning. Goal: byte-identical images from identical sources.

### 31. Docker vs Podman vs containerd vs Nerdctl.
**Docker**: daemon + CLI, the de-facto standard. **Podman**: daemonless, rootless-first, Docker-compatible CLI. **containerd**: low-level runtime used by Docker, K8s, etc. **nerdctl**: Docker-like CLI on top of containerd. K8s removed dockershim — clusters use containerd/CRI-O directly.

### 32. Compose for local dev.
`docker-compose.yml` defines services, networks, volumes, healthchecks, depends_on. `docker compose up --build`, `down -v`, `logs -f svc`. Use profiles to enable optional services (`--profile debug`). Overrides via `docker-compose.override.yml`. Not a production orchestrator.

### 33. Production patterns.
Immutable images (one tag = one build), 12-factor config via env vars, log to stdout, health/readiness endpoints, graceful shutdown on SIGTERM, no SSH into containers (use ephemeral debug pods in K8s), one process per container (use a sidecar or job, not supervisord).

### 34. Debugging running containers.
`docker exec -it ctr sh` for shells. `docker logs --tail=100 -f ctr` for output. `docker inspect ctr` for full config. `docker stats` for live CPU/mem. `docker top ctr` for processes. For distroless: `docker run --rm -it --pid=container:ctr nicolaka/netshoot` to share PID/net namespaces and bring debug tools.

### 35. Sample optimized Go Dockerfile.
```Dockerfile
# syntax=docker/dockerfile:1.6
FROM golang:1.22 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY . .
RUN --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/app ./cmd/app

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/app /app
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app"]
```
