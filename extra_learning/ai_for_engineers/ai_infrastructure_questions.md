# AI Infrastructure Interview Questions — Basic to Advanced (Detailed)

For data, platform, ML, and software engineers building or operating the infrastructure that trains, serves, and governs ML/LLM workloads.

---

## 1. Foundations

### 1. What is "AI infrastructure"?
The systems that move data, train models, deploy them, and monitor them in production. Spans: data platforms (lakes, warehouses, feature stores), compute (GPU/TPU clusters, Kubernetes), training frameworks (PyTorch, JAX, DeepSpeed), serving (Triton, vLLM, KServe, SageMaker), MLOps (orchestration, CI/CD, registries, observability), and governance (lineage, policy, safety).

### 2. ML system anatomy.
**Data layer** → **feature engineering** → **training pipeline** → **model registry** → **serving** (online/batch) → **monitoring** → **retraining trigger**. Each step has its own infra concerns: scheduling, resource isolation, reproducibility, security, cost.

### 3. Why ML infra is hard.
ML workloads are stateful, GPU-bound, long-running, and quality-sensitive. Models are non-deterministic (data + hyperparams + initialization). Production cares about correctness *and* freshness *and* latency *and* drift — a much wider quality surface than typical services.

### 4. Difference between ML platform and AI platform.
Often used interchangeably. ML platform = classical supervised/unsupervised, recommenders, fraud, etc. AI platform now usually implies LLMs, RAG, agents, multi-modal — bigger models, different infra (vector DBs, prompt management, GPU inference at scale, safety layers).

### 5. CPU vs GPU vs TPU vs custom accelerators.
**CPU**: general-purpose, low parallelism. **GPU** (NVIDIA H100/A100, AMD MI300): massive parallel FMA, 80–192 GB HBM, the workhorse. **TPU** (Google): systolic-array matmul, very fast for large dense models, less flexible. **Custom**: Trainium/Inferentia (AWS), Gaudi (Intel), Cerebras WSE, Groq LPU. Choice driven by cost/perf and ecosystem support.

---

## 2. Compute & Hardware

### 6. Key GPU specs that matter.
HBM capacity (fits the model + activations), HBM bandwidth (feeds the compute), tensor-core throughput (mixed-precision matmul), NVLink/NVSwitch bandwidth (between GPUs in a node), PCIe Gen + InfiniBand/RoCE (between nodes), power/thermal envelope, FP8/INT8 support.

### 7. NVLink, NVSwitch, InfiniBand.
**NVLink**: high-bandwidth GPU-to-GPU inside a node (~900 GB/s H100). **NVSwitch**: NVLink fabric in DGX/HGX nodes — all GPUs see all GPUs. **InfiniBand / RoCEv2**: between nodes for distributed training (200/400 Gbps NDR/XDR). All three matter once you scale past 8 GPUs.

### 8. CUDA, cuDNN, NCCL.
**CUDA**: NVIDIA's parallel computing platform/language. **cuDNN**: optimized DL primitives (convs, attention, RNNs). **NCCL**: GPU-to-GPU collectives (all-reduce, all-gather, broadcast) over NVLink/IB. PyTorch/TF/JAX sit on top.

### 9. MIG (Multi-Instance GPU).
A100/H100 can be partitioned into up to 7 isolated instances with dedicated compute + memory slices. Useful for serving many small models or sharing GPUs across teams. Cost effective for inference; usually wasted on training.

### 10. Hardware topology and placement.
On a multi-node training job, layout matters: assign GPUs that share an NVSwitch, then nodes that share a rack switch, then within the same fabric. Topology-aware schedulers (Slurm topology plugin, Kubernetes scheduler with GPU topology) materially affect throughput.

### 11. Storage tiers for ML.
- **Hot training data**: NVMe local SSDs (or fast network FS like FSx Lustre, WekaIO, DAOS) — feeds the GPU.
- **Warm**: object storage with caching (S3 + s3fs/cache, GCS + Anywhere Cache).
- **Cold archive**: Glacier / Coldline.
GPU starvation is the #1 wasted-cost in training — feed them properly.

### 12. Data loading bottlenecks.
GPU sits idle while the next batch loads — common in CV/audio. Mitigations: parallel data loaders (`num_workers > 0`), prefetch, pinned memory, sharded WebDataset / TFRecord / parquet, on-the-fly augmentation on GPU, NVIDIA DALI, caching decoded tensors. Profile with `nsys`, PyTorch profiler.

---

## 3. Training Infrastructure

### 13. Distributed training paradigms.
- **Data parallel (DDP)**: full model on each GPU, gradients all-reduced. Default for medium models.
- **Tensor parallel**: layer math split across GPUs (Megatron-LM). Needed when layers don't fit.
- **Pipeline parallel**: layers split across GPUs, microbatched (GPipe, PipeDream).
- **Fully Sharded Data Parallel (FSDP / ZeRO-3)**: shards params + grads + optimizer state, gathers on demand.
- **3D parallelism**: combine all three for >100B-parameter LLMs.

### 14. ZeRO (Zero Redundancy Optimizer).
DeepSpeed's series of memory optimizations: **ZeRO-1** shards optimizer state, **ZeRO-2** + gradients, **ZeRO-3** + parameters. Trade compute/comm for memory — enables huge models on consumer GPU counts. FSDP in PyTorch is conceptually equivalent.

### 15. Mixed precision (FP16/BF16/FP8).
Train using lower precision to speed up math and shrink memory. **BF16** has wider range, preferred for stability. **FP8** (H100) is the new frontier — needs scaling / loss-aware logic (Transformer Engine). Loss-scaling protects FP16 from underflow.

### 16. Gradient accumulation & checkpointing.
**Gradient accumulation**: simulate bigger batch by summing gradients across micro-batches before step. **Gradient checkpointing**: recompute activations in backward to save memory. Both are standard knobs when GPUs are memory-bound.

### 17. Checkpointing strategy.
Save model + optimizer + RNG state to durable storage every N steps. Async write (non-blocking) is critical at scale. For 70B+ models, sharded checkpoints (one shard per data-parallel rank) parallelize I/O. Verify restorability — corrupt checkpoints are silent killers.

### 18. Training orchestrators.
**Kubeflow Training Operator** (TFJob/PyTorchJob), **Ray Train**, **Slurm** (HPC heritage, still common in research), **AWS SageMaker / Batch**, **Vertex AI Training**, **Databricks Mosaic**, **Lightning Fabric**. Pick based on cluster ownership and integration with your data tools.

### 19. Hyperparameter optimization.
Algorithms: random search (surprisingly strong baseline), Bayesian (Optuna, Ax, Vizier), Hyperband / ASHA, population-based training. Platforms: Katib, Ray Tune, Optuna, Weights & Biases Sweeps. Spend compute proportional to model importance — full HPO on small probes, light HPO on big runs.

### 20. Spot/preemptible training.
Train on spot GPUs at 60–90% discount. Requirements: aggressive checkpointing, fast cold-start, idempotent dataset iteration (seed by epoch step), restart automation. Frameworks: SkyPilot, Slurm requeue, Kubernetes job retry policies. Massive savings if your job tolerates restarts.

---

## 4. Serving Infrastructure

### 21. Online vs batch vs streaming inference.
**Online**: low-latency per request (SLA 10–500 ms). **Batch**: schedule jobs over big inputs, throughput-oriented. **Streaming**: continuous flow (Kafka in → predictions out), often via Flink/Spark + embedded model. Choice driven by use case latency and freshness requirements.

### 22. Model serving frameworks.
**Triton Inference Server** (multi-framework, dynamic batching, ensemble — gold standard). **vLLM** / **TGI** (LLM-specialized with paged attention, continuous batching). **TorchServe**, **TF Serving**. **KServe** (K8s-native, supports multiple runtimes). **BentoML**, **MLflow** for packaging.

### 23. Latency vs throughput trade-offs.
Bigger batch → higher throughput, higher per-request latency. **Dynamic batching**: queue requests for a few ms, batch them, serve. Tune `max_queue_delay` to your SLA. Continuous batching (vLLM) makes this far better for LLMs by interleaving requests in attention.

### 24. Quantization.
Compress weights/activations to lower bits: INT8 (post-training), INT4 (GPTQ, AWQ, bitsandbytes), FP8. Saves memory and speeds up math at small accuracy loss. **Calibration** with representative data is key. INT4 weights + FP16 activations is common for LLMs.

### 25. Compilation / kernel optimization.
**TensorRT** (NVIDIA), **TorchCompile** (PT 2.0), **XLA** (JAX/TF), **ONNX Runtime**, **OpenVINO**. Fuses ops, generates kernel-fused code, lowers precision. 2–5× speedups typical. Build once during deploy; cache compiled artifacts.

### 26. KV cache.
LLMs cache attention keys/values from previous tokens to avoid recomputation. Memory grows with context length × batch. Optimizations: **PagedAttention** (vLLM, like virtual memory for KV), **chunked prefill**, **prefix caching** (reuse KV for shared prompts).

### 27. Continuous / inflight batching for LLMs.
Classic batching waits for all in batch to finish; LLMs have variable output lengths so the slowest dominates. **Continuous batching** schedules new tokens at every step; finished sequences leave, new ones join — drastically improves GPU utilization. Native in vLLM, TGI.

### 28. Speculative decoding.
A small "draft" model proposes K tokens; large model verifies in one forward pass; accept up to first mismatch. 2–3× speedup for autoregressive LLMs with no quality loss. Variants: tree speculation, lookahead decoding, Medusa heads.

### 29. Autoscaling.
HPA on QPS or queue length, KPA (Knative) on concurrency, custom on GPU utilization. **Scale-to-zero** for rarely used models — accept cold start. **Always-warm minReplicas** for latency-critical. Cold start for LLMs may be tens of seconds (load 70B weights) — pre-warm with image+weight cache.

### 30. Multi-model and model-mesh serving.
Hosting thousands of small/medium models on a shared GPU fleet without one pod each. **KServe ModelMesh**, **Seldon Core**, **BentoML Yatai**. Models loaded on demand, evicted under memory pressure. Common for per-customer / per-segment models.

### 31. Cost per request math.
$/request = (instance cost / sec) / (throughput req/sec) × (batch overhead). Optimize via batching, quantization, smaller model (distillation), GPU sharing, cheaper hardware, caching identical/similar prompts. Always measure $/1k tokens for LLMs, not just latency.

---

## 5. Data & Features

### 32. Feature store.
Centralized place to define, compute, store, and serve features. **Offline** store for training (point-in-time correct joins), **online** store for serving (low-latency lookups). Tools: Feast (OSS), Tecton, Hopsworks, Vertex AI Feature Store, Databricks Feature Engineering. Solves training-serving skew.

### 33. Point-in-time correctness.
Training labels must use only features that would have been *available at prediction time* — otherwise you leak future info. Implemented via event-time joins (`AS OF`) on offline store. Skipping this is a top cause of "great offline, bad online" models.

### 34. Data versioning.
Track which exact data trained which model. **DVC**, **Pachyderm**, **LakeFS**, **Delta Lake time travel**, **Iceberg snapshots**. Combine with model registry to make experiments reproducible. Important for compliance (GDPR, EU AI Act).

### 35. Synthetic & augmented data.
Augmentation (crops/rotations, paraphrasing) cheap, well-understood. **Synthetic data** from LLMs / simulators / GANs is increasingly common — be careful of distribution shift and degenerate loops ("model collapse"). Audit synthetic shares of your dataset.

### 36. Data quality for ML.
**Schema validation** (types, ranges), **statistical checks** (mean/std drift), **constraint checks** (PK uniqueness, FK integrity), **labelling consistency** (cross-annotator agreement). Tools: TFDV, Great Expectations, Soda, Monte Carlo, Whylogs. Block training when checks fail.

### 37. Labeling infrastructure.
Crowd platforms (Scale AI, Surge, Labelbox), in-house tooling (Argilla, Label Studio), programmatic labelling (Snorkel weak supervision), LLM-assisted labelling (with human review). Track inter-annotator agreement and ambiguous edge cases.

### 38. Vector databases (for RAG / embeddings).
Specialized stores for nearest-neighbor search over embeddings. **Pinecone, Weaviate, Qdrant, Milvus, pgvector, Vespa, OpenSearch k-NN**. Indexes: HNSW, IVF, ScaNN. Trade recall vs latency vs memory. Re-embed when models change — major operational concern.

### 39. Embedding lifecycle.
Generate (batch job), store (vector DB), index (HNSW build), refresh (incremental upserts), reindex on model change. Monitor recall@k vs ground truth. Don't mix embeddings from different models in the same index.

### 40. Data privacy & PII.
PII detection (Presidio, Cloud DLP), tokenization / hashing, differential privacy (Opacus, DP-SGD), federated learning for sensitive data. Even removing PII isn't enough — model memorization can leak training data. Audit with membership-inference tests.

---

## 6. LLM-Specific Infrastructure

### 41. Pretraining vs fine-tuning vs prompting.
**Pretraining**: from scratch on huge corpus — only big labs. **Continued pretraining**: domain-adapt with more tokens. **Fine-tuning**: supervised on task labels (SFT) or RLHF/DPO. **PEFT** (LoRA, QLoRA, prefix tuning): tiny adapters on frozen base — cheap and effective. **Prompting / RAG**: no training, change inputs.

### 42. LoRA & QLoRA.
**LoRA** adds low-rank update matrices to weights; trains 0.1–1% of params. **QLoRA** combines with 4-bit quantization of the base model — fine-tunes 65B on a single 48GB GPU. Standard for adapting open-source LLMs to a domain.

### 43. RAG (Retrieval Augmented Generation).
Pipeline: user query → retrieve relevant docs from vector DB (and/or BM25) → stuff into prompt → LLM answers. Mitigates hallucinations and stale knowledge. Quality depends on chunking strategy, embedding quality, reranker, prompt design, and citation handling.

### 44. RAG infrastructure stack.
**Ingest**: doc loaders, chunkers (token/semantic), metadata enrichment. **Embed**: model + GPU pool, batched. **Store**: vector DB + metadata DB. **Retrieve**: ANN + filters + (optional) **reranker** (cross-encoder for top-N). **Generate**: LLM with prompt template. **Eval**: relevance, groundedness, latency.

### 45. Agent infrastructure.
Agents = LLM that chooses tools (functions, APIs) iteratively. Infra needs: tool registry, sandboxed execution, observability (which tool was called and why), guardrails on cost & infinite loops, memory store (short + long term), evaluation harness. Frameworks: LangGraph, LlamaIndex, AutoGen, CrewAI.

### 46. Prompt management.
Treat prompts like code: versioned, reviewed, tested. Tools: LangSmith, Helicone, PromptLayer, Arize Phoenix, custom git-based with templated rendering. Track which prompt version + model produced which output.

### 47. LLM evaluation.
- **Static benchmarks** (MMLU, HumanEval, GSM8K) — saturated for top models.
- **Custom golden sets** with task-specific grading.
- **LLM-as-judge** — fast but biased; calibrate against human.
- **Pairwise** preferences for ranking.
- **A/B in prod** on real users — ultimate signal.
Track win-rate, hallucination rate, refusal rate, latency, cost.

### 48. Hallucinations — mitigation strategies.
Better retrieval (more relevant context), require citations (`answer must quote sources`), constrained generation (function calling, JSON mode), smaller temperature, post-hoc fact-checking with retrievers, fine-tuning for groundedness. No silver bullet — combine.

### 49. Safety & guardrails.
Input filters (prompt injection, PII), output filters (toxic, PII, format checking), policy-driven refusals, rate limits per user, audit logs. Tools: Llama Guard, NeMo Guardrails, Rebuff, Lakera. Layer with classical security — LLMs are *new attack surfaces*, not just new features.

### 50. Cost control for LLMs.
Use the smallest model that meets quality. Cache identical prompts. Use prompt caching (Anthropic/OpenAI now offer). Truncate context aggressively. Batch where possible. Offline-eval cheaper variants. Set per-user/team budgets and hard caps. Track $/successful task, not raw tokens.

### 51. Self-hosting open-source LLMs.
Stack: weights (HF/llama.cpp), runtime (vLLM/TGI/SGLang), GPU pool, gateway (rate limit + auth), eval harness. Pros: privacy, predictable cost at high volume, customization. Cons: ops burden, you maintain quality vs frontier models.

### 52. Hybrid cloud + on-prem GPU.
Common large-org pattern: sensitive data + steady-state inference on on-prem GPUs; burst training and external APIs in public cloud. Bridged by VPN/peering. Plan capex amortization vs cloud opex carefully — GPUs depreciate fast.

---

## 7. MLOps & Lifecycle

### 53. Experiment tracking.
**MLflow Tracking**, **Weights & Biases**, **Neptune**, **Comet**. Logs hyperparams, metrics, artifacts, code version, dataset hash. Enables side-by-side comparison and reproducibility. Make it a habit from day one — retrofitting is painful.

### 54. Model registry.
Centralized catalog: model name, versions, lineage, metrics, stage (staging/prod). **MLflow Registry**, **Vertex Model Registry**, **SageMaker Registry**, **Unity Catalog Models**. Promotion to prod gated by approvals + automated checks.

### 55. CI/CD for ML.
- **Code CI**: lint, unit tests, integration tests on synthetic data.
- **Data CI**: schema checks, drift checks on inputs.
- **Model CI**: train on a small sample, evaluate against baseline, block on regression.
- **CD**: register model → canary deploy → automatic rollback on metric drop.
Tools: GitHub Actions / GitLab CI + Argo CD / Flux + MLflow / Kubeflow.

### 56. Drift detection.
**Input drift** (PSI, KL, Chi-square on feature distributions), **prediction drift** (output distribution shift), **concept drift** (relationship between X and Y changed — detected via labels lagging in). Tools: Alibi Detect, Evidently, Arize, WhyLabs, Fiddler.

### 57. Monitoring metrics.
Latency p50/p95/p99, error rate, request rate, GPU utilization, GPU memory, queue depth, batch fullness, drift scores, business metrics (conversion, AUC against delayed labels). Dashboard separately by model/version/segment.

### 58. Shadow / canary deployment for models.
**Shadow**: send copy of traffic to new model, compare offline. **Canary**: 1% → 10% → 50% → 100% with metric guardrails. **Champion-challenger**: parallel models, periodically swap if challenger wins. All require automation to be safe at scale.

### 59. Retraining triggers.
**Scheduled** (weekly), **data volume** (every N events), **drift-based** (PSI > 0.2), **performance** (online AUC drop), **manual** (after bug fix or new features). Each trigger fires the training pipeline; gated deployment ensures bad models don't ship.

### 60. Reproducibility checklist.
Pin: code (git sha), data (snapshot hash), feature definitions, environment (container digest), random seeds, hardware (GPU model — matters for FP semantics), framework versions. Store all of the above with the artifact in the registry.

---

## 8. Security, Governance, Compliance

### 61. AI governance landscape.
**EU AI Act** (risk-tiered obligations on AI providers/deployers), **NIST AI RMF** (US, voluntary framework), **GDPR / CCPA** (data protection), **ISO/IEC 42001** (AI management systems), sector rules (HIPAA, finance). Compliance is now infrastructure work — track model purpose, data sources, risk class.

### 62. Lineage & auditability.
For any prediction, you should be able to reproduce: which model version, trained on which dataset version, with which hyperparameters, on which features at prediction time. Stored centrally and queryable. Regulators and incident responses both need this.

### 63. Model cards & datasheets.
Structured documentation of a model: intended use, training data, performance metrics broken down by slice, limitations, ethical considerations. Mirrors data sheets for datasets. Standard practice for responsible release.

### 64. Bias and fairness.
Measure performance across protected/relevant slices (gender, age, geography). Tools: Fairlearn, Aequitas, IBM AIF360. Mitigations: re-weighting, adversarial debiasing, post-hoc threshold tuning. Pick fairness definition consciously — they're mathematically incompatible.

### 65. Adversarial attacks.
**Evasion** (fool model at inference), **poisoning** (corrupt training data), **model extraction** (steal weights via queries), **prompt injection** for LLMs. Defenses: input validation, rate limiting, robust training, watermarking, red-teaming. New OWASP Top 10 for LLMs codifies the landscape.

### 66. Data residency & sovereignty.
Customers may require data stay in-region. Implement via region-pinned data stores, region-aware routing, separate model deployments per region, careful audit logging. Affects training too — federated learning is one answer.

### 67. Access control.
Per-team/per-model RBAC on training data, registries, deployments. Service-to-service via mTLS / Workload Identity. Secrets via vault (not env files in repos). Most ML platforms still under-invest here — fix early.

### 68. Watermarking & provenance.
Watermarks in generated content (text, image) help detect AI output (C2PA standard). Internal provenance: signed model artifacts (`cosign`), signed datasets, end-to-end signing of inference responses. Useful for trust and incident forensics.

---

## 9. Cost & Capacity

### 69. Where the money goes.
For modern AI infra, typically: **GPU compute (training + inference)** 50–80%, **storage + data egress** 10–20%, **everything else (orchestration, observability, devs)** 10–20%. Optimize where the dollars are.

### 70. Capacity planning for GPUs.
Forecast model & request growth, account for batch-size scaling, get reservations / committed-use discounts well in advance (H100s are still constrained), keep mix of reserved + on-demand + spot. Negotiate multi-region capacity to mitigate regional shortages.

### 71. Optimizing inference cost.
Smaller model when quality allows, quantization, batching, caching, autoscaling, prompt compression for LLMs, splitting workloads across heterogeneous GPUs (cheap GPUs for cheap models). Measure $/successful task end-to-end.

### 72. Carbon and energy.
Training big models is energy-intensive. Tools to estimate: CodeCarbon, ML CO2 calculator. Mitigations: train in lower-carbon regions, schedule with grid intensity, share base models (LoRA fine-tunes vs retraining), use efficient hardware (H100 vs older). Increasingly a reporting requirement.

---

## 10. Operating & Reliability

### 73. SRE practices for ML.
SLIs/SLOs for inference (latency, error, freshness), error budgets that gate model rollouts, runbooks for common incidents (GPU OOM, drift alert, latency spike), on-call rotations including an ML expert.

### 74. Incident response for ML.
Triage: is it infra (latency, errors) or quality (drift, hallucination)? Rollback to previous model version is often the fastest mitigation. Capture inputs + outputs at time of incident for offline analysis. Postmortem includes data + model considerations, not just code.

### 75. Common production failure modes.
GPU OOM (batch too big / KV cache blow-up), driver/CUDA mismatch (after node patch), data pipeline silently producing nulls, retraining pipeline using last week's broken features, prompt injection causing chain-of-tools nightmare, drift gone unmonitored for weeks, cost runaway because of unbounded agent loops.

### 76. Disaster recovery.
For inference: multi-region deployments, model artifacts in multi-region object storage. For training: checkpoints replicated, code in git, data lineage to allow recompute. RTO/RPO depends on business — ML serving is now critical-path for many products.

---

## 11. Emerging Topics

### 77. On-device & edge inference.
Phones, browsers, IoT devices running smaller models (quantized, distilled). Frameworks: ONNX Runtime, TensorFlow Lite, Core ML, MLC LLM, llama.cpp. Privacy + offline + latency benefits, but harder ops (versioning across millions of devices).

### 78. Multimodal models.
Models that ingest/produce text + images + audio + video (GPT-4o, Gemini, Claude vision). Infra implications: bigger context, more diverse data pipelines (image/audio decoders, frame extractors), larger KV caches, new evaluation suites.

### 79. Mixture of Experts (MoE).
Activate a subset of "expert" sub-networks per token. Inference is cheaper than dense models of same param count; training requires routing balancing and careful comm. Mixtral, GPT-4-class. Infra needs to handle sparse activation routing.

### 80. Agentic systems and scaling.
Agents fan out tool calls and recursive LLM calls — cost and latency grow non-linearly. Infra answers: tool call budgets, depth limits, parallel tool execution, structured caching, deterministic replay for debugging. New observability primitives ("agent traces") are emerging.

### 81. Open-source LLM ecosystem.
Llama family, Mistral/Mixtral, Qwen, DeepSeek, Phi, Gemma. Tooling: HuggingFace (models + datasets + spaces), TGI, vLLM, llama.cpp, Ollama. Closing the gap with frontier closed models on many tasks. Self-hostable, customizable, but you own the ops.

### 82. AI gateways.
A reverse proxy in front of LLM providers/own models, providing: unified API, key management, rate limiting, fallback, cost tracking, prompt caching, content filtering, logging. Examples: LiteLLM, Portkey, Helicone, Cloudflare AI Gateway. Increasingly standard component.

### 83. AI observability stack.
LLM-aware tracing: per-call prompts, responses, tokens, latency, cost, tool calls. Drift on prompt distributions, eval scores over time. Tools: Arize Phoenix, LangSmith, Helicone, Langfuse, Datadog LLM Observability. Plain APM is no longer enough for AI apps.

---

## 12. Mindset & Trade-offs

### 84. ML infra vs SWE infra — biggest differences.
- Workloads are GPU-bound and long-running.
- Correctness is statistical, not boolean.
- Data versioning matters as much as code versioning.
- Reproducibility requires pinning more (hardware, seeds, frameworks).
- Quality issues can be subtle and delayed (drift, fairness).
- Costs are 10–100× higher per unit work.

### 85. Build vs buy.
Buy: training compute (cloud GPUs), eval tools, observability, vector DB if you can. Build: feature store integration to your data, in-house evals for your domain, anything where your moat sits. Don't write your own vLLM unless you have a team of 10 dedicated to inference.

### 86. Roadmap pitfalls.
Skipping data quality and jumping to bigger models; deploying a great Jupyter notebook directly to prod; treating MLOps as one engineer's side project; no eval set so you can't tell if changes help; agent demos shipped without cost caps; "we'll add monitoring later".

### 87. What separates great AI infra teams.
Treat the platform as a product (internal users + SLOs). Standardize golden paths (template pipelines, base images, eval harnesses). Invest in reproducibility from day one. Measure cost + quality + latency in every system. Stay current — the stack moves quarterly.
