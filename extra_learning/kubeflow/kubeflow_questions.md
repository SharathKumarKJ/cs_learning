# Kubeflow Interview Questions — Basic to Advanced (Detailed)

Covers Kubeflow Pipelines (KFP), training, serving, components, and production ML patterns on Kubernetes.

---

## 1. Basics

### 1. What is Kubeflow?
An open-source ML platform on Kubernetes — a collection of tools to build, train, tune, deploy, and manage ML workflows. Major components: **Kubeflow Pipelines** (workflow orchestration), **KFServing / KServe** (model serving), **Katib** (hyperparameter tuning + NAS), **Training Operators** (TFJob, PyTorchJob, MPIJob, XGBoostJob), **Notebooks**, **Central Dashboard**, **Multi-tenancy** via Profiles.

### 2. Why Kubeflow vs Airflow / Argo / SageMaker?
- **Airflow**: general workflow orchestrator, weaker first-class ML concepts (artifacts, metrics, lineage).
- **Argo Workflows**: lower-level than KFP and what KFP is built on top of.
- **SageMaker / Vertex AI**: managed, opinionated, less flexible.
- **Kubeflow**: open-source, Kubernetes-native, strong ML primitives (components, artifacts, metadata, serving), portable across clouds.

### 3. What is Kubeflow Pipelines (KFP)?
A platform for building and running ML workflows as DAGs of containerized steps. Each step is a **component** that has typed inputs/outputs. Two versions: **KFP v1** (legacy, Argo-only) and **KFP v2** (current, IR-based, can run on Argo, Tekton, or Vertex AI Pipelines).

### 4. Component.
A reusable, containerized unit of work with declared interface: inputs, outputs, container image, command. Created via the Python SDK (`@dsl.component`), YAML, or built from a Docker image. Idempotent and self-contained — the building block of pipelines.

### 5. Pipeline.
A Python function decorated with `@dsl.pipeline` that connects components by passing inputs/outputs. Compiles to an IR YAML (KFP v2) that the backend executes. Versioned, parameterized, schedulable.

### 6. Artifact.
Typed first-class data passed between steps: `Dataset`, `Model`, `Metrics`, `ClassificationMetrics`, `HTML`, `Markdown`. Stored in object storage (S3/GCS/MinIO). Lineage tracked by ML Metadata (MLMD) so you can trace a model back to the exact data and code that produced it.

### 7. Run, Experiment, Recurring Run.
A **Run** is one execution of a pipeline. **Experiment** groups related runs. **Recurring Run** schedules a pipeline (cron or interval). All visible in the KFP UI with logs, artifacts, and lineage.

### 8. Where does Kubeflow run?
On any Kubernetes cluster: GKE, EKS, AKS, OpenShift, vanilla. Installed via manifests (`kustomize`), Helm, or distributions (Charmed Kubeflow, Arrikto / OSS Mlflow integrations, Deploy KF for various clouds). Managed offerings: Google Vertex AI Pipelines runs KFP IR.

### 9. Multi-tenancy and Profiles.
A **Profile** maps to a Kubernetes namespace with quotas, RBAC, and isolation. Each user/team has its own profile; pipelines, notebooks, and serving deployments live in it. Powered by Kubeflow's Profile Controller + Istio.

### 10. Central Dashboard.
A web UI tying together pipelines, notebooks, experiments, models, and Katib. Provides per-profile views. Auth via OIDC/Dex; integrates with Google, Azure AD, Okta, etc.

---

## 2. Pipelines — Building Blocks

### 11. Building a Python component.
```python
from kfp import dsl
from kfp.dsl import Dataset, Output

@dsl.component(packages_to_install=["pandas", "scikit-learn"])
def train(data: Dataset, model_out: Output[Model], lr: float = 0.01):
    import pandas as pd
    df = pd.read_csv(data.path)
    ...
    with open(model_out.path, "wb") as f: pickle.dump(model, f)
```
KFP wraps this in a container, generates the IR, mounts inputs/outputs at runtime.

### 12. Container component.
For prebuilt images: `dsl.ContainerSpec(image="my/img:v1", command=["python","train.py"], args=[...])`. Use when you have custom CUDA stacks or non-Python code. Same artifact and lineage benefits as Python components.

### 13. Pipeline parameters.
Top-level pipeline arguments propagate to components: `@dsl.pipeline(...) def pipe(lr: float = 0.01): step = train(lr=lr)`. Strongly typed. Override at submit time from UI, CLI (`kfp run create`), or SDK.

### 14. Conditional, parallel, and loop control flow.
```python
with dsl.If(eval.outputs["acc"] > 0.9):
    deploy(model=train_op.outputs["model_out"])
with dsl.ParallelFor(items=[0.01, 0.001, 0.0001], parallelism=3) as lr:
    train(lr=lr)
```
KFP v2 also has `dsl.Else`, `dsl.OneOf`, `dsl.ExitHandler` for cleanup tasks.

### 15. ExitHandler.
A pipeline-wide cleanup block — guaranteed to run even if upstream steps fail. Used for notifying Slack, freeing GPUs, deleting temp data:
```python
with dsl.ExitHandler(exit_task=notify_op(status="done")):
    train_op = train(...)
    eval_op  = evaluate(train_op.outputs["model_out"])
```

### 16. Passing data — small vs large.
Small values (numbers, short strings, dicts under ~10 MB) flow as **parameters**. Large data flow as **artifacts** stored in object storage; KFP handles upload/download and mounts the path inside the container. Never paste DataFrames into parameters.

### 17. Caching.
KFP v2 caches step results keyed on inputs + image digest + command. Identical inputs → skip execution, reuse outputs. Disable per-step with `task.set_caching_options(enable_caching=False)` (e.g., for time-sensitive data fetches).

### 18. Resource & accelerator requests.
```python
train_task.set_cpu_limit("8").set_memory_limit("32Gi").set_accelerator_type("nvidia-tesla-t4").set_accelerator_limit(1)
```
Translated to pod `resources.requests/limits` and node selectors. Match your cluster's node pools and GPU device plugin.

### 19. Secrets & service accounts.
Attach Kubernetes secrets to components for credentials: `kubernetes.use_secret_as_env_variable(task, secret_name='aws', secret_key_to_env={'KEY':'AWS_ACCESS_KEY_ID'})`. Better: use **Workload Identity** (GCP) / **IRSA** (AWS) so each component pod has a least-privilege cloud identity — no static keys.

### 20. Compiling & submitting.
```python
from kfp import compiler, Client
compiler.Compiler().compile(pipe, "pipeline.yaml")
client = Client(host="http://kfp.example.com")
client.create_run_from_pipeline_package("pipeline.yaml", arguments={"lr": 0.01})
```
The compiled YAML (IR) is portable across KFP backends.

### 21. Scheduling recurring runs.
KFP UI or SDK creates a recurring run with cron / interval. Backed by an Argo `CronWorkflow` or equivalent on other backends. Watch out for overlapping runs — use `max_concurrency`.

### 22. Pipeline versioning.
Upload pipeline versions to the KFP backend (`client.upload_pipeline_version_from_pipeline_func`). Each Experiment/Run records the exact version + parameters + artifact URIs. Pair with git tags or container image digests for reproducibility.

---

## 3. Training Operators

### 23. TFJob, PyTorchJob, MPIJob, XGBoostJob.
Kubernetes CRDs that orchestrate distributed training. **TFJob** for TensorFlow (parameter server, worker, chief, evaluator roles). **PyTorchJob** for PyTorch DDP / RPC (master + workers). **MPIJob** runs OpenMPI-based jobs (Horovod). **XGBoostJob** for XGBoost. Created by the **Training Operator**.

### 24. PyTorchJob example.
```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
spec:
  pytorchReplicaSpecs:
    Master: { replicas: 1, template: { spec: { containers: [{image: my/train, command: ["torchrun","train.py"]}] } } }
    Worker: { replicas: 3, template: { ... } }
```
Operator sets up rendezvous env vars (`MASTER_ADDR`, `WORLD_SIZE`, `RANK`) automatically.

### 25. Distributed training strategies.
**Data parallel**: each worker has full model, processes shard of data, gradients all-reduced (DDP, Horovod). **Model parallel**: model split across workers (tensor parallel, pipeline parallel). **ZeRO** (DeepSpeed): partitions optimizer state, gradients, params across workers — enables huge models on commodity GPUs.

### 26. Choosing replicas / sizing.
Bottleneck is usually GPU memory or all-reduce bandwidth. Start with `world_size = 2-8` GPUs, profile, scale up. Use **GPUDirect RDMA** / NVLink topology-aware scheduling for large jobs. Watch step time vs single-GPU; if scaling efficiency drops below ~60%, fix it before scaling further.

### 27. Spot / preemptible training.
Use checkpointing every N steps to object storage; the operator can be configured to restart pods on preemption and resume. Combine with `runPolicy.cleanPodPolicy: None` and explicit retry logic. Big cost savings for non-urgent training.

### 28. GPU sharing and time-slicing.
NVIDIA device plugin supports time-sliced GPUs and **MIG** (Multi-Instance GPU) on A100/H100. For dev notebooks and small inference, share one GPU across pods. Production training typically wants whole GPUs.

---

## 4. Hyperparameter Tuning — Katib

### 29. What is Katib?
Kubeflow's hyperparameter tuning + neural architecture search. You define a search space, an objective metric, an algorithm (random, grid, bayesian, hyperband, CMA-ES, PBT), and a trial template (a Job/TFJob/PyTorchJob/KFP pipeline). Katib runs many trials and reports the best config.

### 30. Experiment CR.
```yaml
kind: Experiment
spec:
  objective: { type: maximize, objectiveMetricName: val_accuracy }
  algorithm: { algorithmName: bayesianoptimization }
  parameters:
    - {name: lr, parameterType: double, feasibleSpace: {min: "1e-5", max: "1e-1"}}
  trialTemplate: { ... }
```
Metrics collected via stdout patterns, TF events, or sidecar.

### 31. Early stopping.
**Median stopping rule** kills trials performing worse than the median at a checkpoint. Combined with hyperband, drastically reduces compute for large search spaces. Configured in `earlyStopping` spec.

### 32. Trial templates.
Trial = a Kubernetes Job (or TFJob/PyTorchJob/etc.) that runs one configuration. Template parameters (`${trialParameters.lr}`) are substituted at trial creation. Lets Katib drive any kind of training workload.

### 33. Neural Architecture Search.
Katib supports NAS via algorithms like ENAS and DARTS. Defines a search space over architectures, not just hyperparameters. Compute-heavy; usually combined with weight sharing or early stopping.

---

## 5. Serving — KServe (formerly KFServing)

### 34. What is KServe?
A Kubernetes-native model serving framework: declarative `InferenceService` CRD that provisions REST/gRPC endpoints, autoscaling (KPA/HPA), canary rollouts, traffic splitting, batching, and explainability. Supports many frameworks (TF, PyTorch, sklearn, XGBoost, ONNX, HuggingFace, custom).

### 35. InferenceService example.
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: sklearn-iris }
spec:
  predictor:
    sklearn:
      storageUri: gs://bucket/iris/model.joblib
      resources: { requests: { cpu: 100m, memory: 256Mi } }
```
KServe builds a pod with the right runtime, downloads the model, exposes `/v1/models/iris:predict`.

### 36. Predictor / Transformer / Explainer pipeline.
Three optional components per `InferenceService`:
- **Predictor** (mandatory): runs the model.
- **Transformer**: pre/post-processing (tokenize, normalize) often in Python.
- **Explainer**: explanations (Alibi, Captum) — separate pod called on demand.

### 37. Scale-to-zero & autoscaling.
By default uses Knative Serving — pods scale to zero when idle, scale up by concurrency/RPS. Trade-off: first request has cold-start latency (load model into memory). For latency-sensitive prod, set `minReplicas: 1`.

### 38. Canary rollouts.
`spec.predictor.canaryTrafficPercent: 10` routes 10% of traffic to a new model version. Combine with metrics (latency, error rate, business KPIs) to promote/abort. Implements progressive delivery for ML.

### 39. Batching.
KServe can batch incoming requests with `enableBatching: true`, `maxBatchSize`, `maxLatency`. Crucial for GPU efficiency — single-request inference under-utilizes GPUs.

### 40. Custom predictors.
For models not covered by built-in runtimes, build a container exposing the standard API (V1 / V2 inference protocol) — KServe handles the rest of the lifecycle. ModelMesh (a KServe sub-project) hosts thousands of small models on a shared serving fleet.

### 41. Multi-model serving (ModelMesh).
Multiple models share a few pods; models loaded on demand, evicted under memory pressure. Designed for high-density (1000s of models, e.g., per-customer models) without 1 pod per model.

### 42. Streaming / async inference.
gRPC bidirectional streaming, Server-Sent Events, or async with a queue (Kafka/RabbitMQ in front, results posted back). Use for long-running inference (LLMs, video) where holding HTTP connections is unwieldy.

---

## 6. Lineage, Metadata, Notebooks

### 43. ML Metadata (MLMD).
Backend that records artifacts, executions, and contexts (pipelines, runs). Every step you run logs: which images, parameters, inputs/outputs (with object-storage URIs), metrics. Lets you answer "which dataset version trained model X?" with a SQL query.

### 44. Lineage in the UI.
KFP UI shows a DAG with artifacts as nodes and steps as edges. Clicking an artifact reveals its producer execution, its consumers, and the run it belongs to. Foundation for governance and audits.

### 45. Notebooks.
Kubeflow Notebooks launches Jupyter / VSCode / RStudio pods in your profile namespace with mounted PVCs, GPU access, and pre-baked images. Use to prototype components and pipelines that you then promote to production.

### 46. Custom notebook images.
Extend the Kubeflow Jupyter base image with your libs; publish to a registry; allow your team to launch from the UI. Standardize on a small set so you can patch CVEs centrally.

---

## 7. Architecture & Components

### 47. KFP architecture (v2).
- **API server** (FastAPI on top of Argo / Tekton / Vertex).
- **ML Pipeline Persistence** (MySQL/PostgreSQL).
- **Cache server** for step caching.
- **Argo Workflow Controller** (typical backend) runs the DAG.
- **MinIO/S3/GCS** for artifacts.
- **MLMD** for metadata (often gRPC + MySQL).
- **Frontend** + Central Dashboard.

### 48. Argo vs Tekton vs Vertex backend.
KFP v2 IR can be executed by any compatible engine. **Argo Workflows** is the de-facto OSS backend. **Tekton** is an alternative (popular in OpenShift). **Vertex AI Pipelines** runs the same IR as a managed service on GCP.

### 49. Istio and the Kubeflow mesh.
Istio provides mTLS between components, an ingress gateway, and identity. KFP UI, Notebook controller, and Profiles depend on Istio for auth flow. In some installs, Istio is replaced with simpler stack — confirm with the distribution.

### 50. Dex / OIDC.
Dex is the default identity broker — connects Kubeflow to corporate IdPs (Google, Okta, AzureAD, LDAP). Users authenticate at the dashboard; tokens propagate to subcomponents. Some distros use Keycloak instead.

---

## 8. Production Patterns

### 51. End-to-end ML pipeline.
**Ingest** (Spark/BigQuery) → **Validate** (TFDV / great_expectations) → **Feature engineering** (Beam/Spark, Feast) → **Train** (TFJob/PyTorchJob) → **Evaluate** + **Bias check** → **Register** (model registry) → **Deploy** to KServe (canary) → **Monitor** (drift, performance) → **Retrain trigger**. Whole flow is a KFP pipeline (or several composed).

### 52. Model registry.
KFP integrates with **MLflow Model Registry**, **Vertex AI Model Registry**, or a custom registry. Stages: `staging`, `production`, `archived`. Registry promotion is what triggers KServe rollouts.

### 53. Feature store integration.
**Feast** is commonly paired with Kubeflow: training pipelines pull point-in-time features from offline store (BigQuery, Snowflake, Delta), serving pulls from online store (Redis, DynamoDB). Avoid training-serving skew by computing both from the same SQL definition.

### 54. CI/CD for ML.
- Code in git → unit tests on components → integration test compiling the pipeline.
- PR-triggered run in a dev namespace with sample data.
- On merge: build images, push, register pipeline version.
- Promotion via tags / GitOps to staging/prod namespaces.
Tools: GitHub Actions / GitLab CI / Argo CD, with reusable workflows for ML.

### 55. Model monitoring.
Once deployed: monitor input drift (PSI, KL divergence over feature distributions), prediction drift, performance vs labels when available, latency, errors. **Alibi Detect**, **WhyLabs**, **Arize**, **Evidently** integrate with KServe via transformers/sidecars.

### 56. Retraining triggers.
**Time-based** (weekly), **data-volume** (every N new rows), **drift-based** (PSI > threshold), **performance** (AUC drops in shadow mode). Triggered by Airflow/KFP recurring run reading metrics from Prometheus/MLMD.

### 57. Shadow & A/B deployments.
**Shadow**: send a copy of prod traffic to new model, don't use response — compares offline. **A/B**: split real traffic by user/session. Use KServe canary + a router (Argo Rollouts / Flagger / Istio VirtualService).

### 58. Security & compliance.
RBAC via Profiles + Kubernetes. Image scanning (Trivy). Pod security policies (non-root, read-only FS). Network policies between namespaces. PII handling: encrypt artifacts at rest (KMS), redact in logs. Audit via MLMD + Kubernetes audit logs.

### 59. Cost optimization.
Right-size pods, use spot/preemptible for training, scale serving to zero where latency allows, batch inference, cache intermediate KFP steps aggressively, share GPUs for inference (MIG/time-slice/ModelMesh), prune old artifacts in object storage.

### 60. Common pitfalls.
Huge data in pipeline parameters (use artifacts); not pinning component images (`:latest` breaks reproducibility); skipping caching by always changing image tag; running training in the KFP pod instead of a TFJob/PyTorchJob (no distributed); deploying a notebook prototype directly to prod without tests; ignoring drift after launch.

### 61. Kubeflow vs MLflow vs Metaflow.
- **MLflow**: lightweight tracking + registry + projects + serving. Best as a *component* (often used alongside Kubeflow).
- **Metaflow**: pipeline + tracking, simpler API, AWS-native, less K8s-centric.
- **Kubeflow**: full platform — orchestration + training + serving + tuning + multi-tenancy on K8s.
Most teams combine: KFP for orchestration, MLflow for tracking/registry, KServe for serving.

### 62. When *not* to use Kubeflow.
Small team without Kubernetes expertise (operational overhead is large), heavy use of managed cloud ML (SageMaker/Vertex covers most needs), simple notebook+train+deploy flow that fits in MLflow + a single VM, or strict regulatory env where a smaller surface is desirable.

### 63. Migration / adoption strategy.
Start with **KFP for orchestration** alongside existing infra. Add **Katib** for tuning when needed. Move serving to **KServe** once you have multiple models. Adopt **multi-tenancy / Profiles** when team count grows. Build internal templates (golden pipelines, base images) to keep teams consistent.
