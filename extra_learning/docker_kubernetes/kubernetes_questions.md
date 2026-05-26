# Kubernetes for Data Engineers (Detailed)

### 1. What is Kubernetes?
An open-source container orchestrator that schedules containers (pods) onto a cluster of nodes, handles networking, storage, scaling, rollouts, and self-healing. The de facto platform for running data services (Airflow, Spark, Kafka, Flink) in cloud-native environments.

### 2. Pod.
The smallest deployable unit — one or more tightly coupled containers sharing network and storage. Most pods have a single primary container plus optional sidecars (logging, metrics, secrets).

### 3. Deployment, Service, ConfigMap, Secret.
**Deployment**: declarative way to manage a set of replica pods with rolling updates. **Service**: stable virtual IP + DNS name fronting a pod set (ClusterIP/NodePort/LoadBalancer). **ConfigMap**: non-sensitive config as env vars or mounted files. **Secret**: sensitive data (base64-encoded; encrypt at rest with KMS).

### 4. Job vs CronJob.
**Job**: runs pods until completion (e.g. a one-shot ETL). **CronJob**: schedules Jobs on a cron expression — replacement for Linux cron in a cluster. Both are essential primitives for batch data engineering.

### 5. StatefulSet.
Manages stateful workloads (Kafka, Postgres, Elastic) needing stable network identity (pod-0, pod-1) and stable persistent storage per replica. Rolling updates respect pod identity.

### 6. PV and PVC.
**PersistentVolume**: cluster-level storage resource (often dynamically provisioned by a CSI driver — EBS, Azure Disk, GCE PD). **PersistentVolumeClaim**: a pod's request for storage of a given size/class. Together they decouple pods from underlying storage.

### 7. HPA.
**Horizontal Pod Autoscaler** scales replicas based on CPU/memory/custom metrics. For long-running services like Airflow workers, set HPA on Celery queue length. Spark on K8s uses dynamic executor allocation instead.

### 8. Helm.
A package manager for Kubernetes. **Charts** are templated YAML bundles you parameterize via `values.yaml`. Used to deploy Airflow, Spark Operator, Kafka, etc. consistently across environments.

### 9. Resource requests vs limits.
**Requests**: guaranteed resources used by the scheduler for placement. **Limits**: hard ceiling; exceeding memory limit kills the pod (OOMKilled), CPU is throttled. Set both for predictable performance; without requests, pods are best-effort and may be evicted first.

### 10. Liveness vs readiness probes.
**Liveness**: "is the container alive?" — failing kills and restarts the container. **Readiness**: "should it receive traffic?" — failing removes the pod from Service endpoints. **Startup probe**: gives slow-starting apps grace before liveness kicks in.

### 11. Taints and tolerations.
**Taints** on nodes repel pods unless those pods have matching **tolerations**. Used to dedicate nodes (e.g. GPU nodes, Spark driver nodes) to specific workloads.

### 12. Affinity and anti-affinity.
Schedule pods near or away from other pods (e.g. anti-affinity to spread Kafka brokers across availability zones). Node affinity targets specific labels (e.g. `node-type=memory-optimized`).

### 13. KubernetesPodOperator (Airflow).
Each task launches its own pod in the cluster. Big advantage: per-task isolation, custom images, and resource sizing. Use it instead of installing every library in the worker image.

### 14. Spark on Kubernetes.
Spark driver and executors run as pods (`spark-submit --master k8s://...` or via the Spark Operator). Lets data teams share GKE/EKS/AKS clusters with the rest of the org, with dynamic allocation and per-job sizing.

### 15. Security: RBAC, ServiceAccount, NetworkPolicy.
**ServiceAccount**: identity for pods. **RBAC**: roles/cluster-roles + bindings governing what SAs can do. **NetworkPolicy**: allow/deny pod-to-pod and pod-to-egress traffic. Use namespaces + RBAC + network policies + image signing + secrets management for a hardened production cluster.
