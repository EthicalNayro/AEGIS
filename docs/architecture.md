# Architecture

## Scope

AEGIS contains two architectural generations:

1. the original EC2/Ansible foundation and CloudTrail security-processing core;
2. the `eks-dev` modernization, which is the final showcase architecture.

The modern platform keeps persistent data outside Kubernetes, uses GitOps for workload delivery, and adds WAF-driven security telemetry, AI-assisted analysis, human review, Prometheus/Grafana observability, and a safety-bounded ExternalDNS/Dynu integration.

---

## Final Platform Topology

```text
                         Internet
                            |
                 app.aegis-project.ddnsfree.com
                            |
                         Dynu DNS
                            |
                         HTTPS
                            |
                      ACM certificate
                            |
                            v
                    Application Load Balancer
                            |
                         AWS WAF
                            |
                            v
                       EKS Ingress
                            |
                    Status-Page Service
                            |
             +--------------+--------------+
             |                             |
       Web replica A                  Web replica B
       AZ-A / private                 AZ-B / private
             |                             |
             +---------------+-------------+
                             |
                +------------+------------+
                |                         |
          RDS PostgreSQL            ElastiCache Redis
          Multi-AZ/private          Multi-AZ/private
```

The EKS workers are private. Public exposure is concentrated at the ALB/WAF boundary. Dynu provides the current public hostname; Route 53 is not part of the implemented architecture.

### VPC layout

The modern environment uses VPC `10.10.0.0/16` across `us-east-1a` and `us-east-1b` with:

- public subnets for Internet-facing load balancer/NAT infrastructure;
- dedicated EKS control-plane subnets;
- private EKS node/Pod subnets;
- private data subnets for managed database/cache services;
- NAT egress per Availability Zone.

---

## EKS Runtime

Cluster: `aegis-eks-dev`.

The runtime includes:

- Managed Node Group baseline;
- validated Karpenter scaling using Spot and On-Demand capacity;
- AWS VPC CNI;
- EKS Pod Identity Agent;
- Metrics Server;
- control-plane logging;
- Pod Security Admission in `restricted` mode for `aegis-system`.

Status-Page workloads use non-root execution, dropped Linux capabilities, `RuntimeDefault` seccomp, read-only root filesystems where practical, no privilege escalation, explicit requests/limits, probes, Pod Disruption Budgets, and multi-AZ topology spread.

The topology rule is revision-aware through `pod-template-hash`, preventing a rolling release from satisfying spread constraints with replicas from an older revision.

---

## Application Runtime

```text
ALB/WAF
  |
Ingress
  |
Service :8080
  |
Nginx (unprivileged)
  |
Gunicorn
  |
Django / Status-Page
  |             |
PostgreSQL     Redis/RQ
```

The application runs with two web replicas. Background work uses RQ workers, while the scheduler is a singleton with `Recreate` strategy to avoid concurrent schedulers during rollout.

Database schema migration is not coupled to web-container startup. Argo CD runs a dedicated Kubernetes Job as a `PreSync` hook before applying the application revision.

AEGIS security functionality is implemented as a native Status-Page plugin. A limited set of upstream presentation templates is intentionally adapted for the AEGIS operations experience; security/application logic remains isolated from upstream core logic.

---

## Runtime Configuration and Secrets

Sensitive configuration is not committed to Git.

At Pod startup, a renderer combines non-secret runtime configuration, a mounted Django `SECRET_KEY`, and RDS credentials fetched from AWS Secrets Manager through workload identity. It writes `configuration.py` into a memory-backed runtime volume with restrictive permissions.

Redis is configured with TLS. RDS credentials are not emitted as Terraform plaintext outputs.

---

## Security Event Architecture

```text
WAF telemetry
    |
CloudWatch BlockedRequests
    |
CloudWatch Alarm
    |
EventBridge
    |
SQS security-events
    | \
    |  `--> DLQ after repeated failure
    v
AEGIS Analyzer Pod
    |
WAF enrichment
    |
Bedrock Nova Pro
    |
JSON parse + schema/semantic validation
    |
Conditional DynamoDB write
    |
ACK SQS message
```

The queue decouples detection transport from analysis. A message receives a longer per-message visibility timeout during analysis and is acknowledged only after successful persistence.

DynamoDB uses `incident_id` as the key, conditional writes for idempotency, server-side encryption, and point-in-time recovery.

### AI trust boundary

Telemetry and model output are treated as untrusted inputs. The analyzer separates instructions from telemetry, requires structured JSON output, validates that output before persistence, and stores a reviewable finding rather than taking autonomous action.

AI therefore remains advisory.

---

## Human Review and AI Quality

The native AEGIS plugin exposes staff-only analyst views for findings stored in DynamoDB.

A reviewer can mark a finding `CORRECT` or `INCORRECT`, optionally supply a corrected classification, and add a note. Updates are conditional on the finding still being in `PENDING_REVIEW` state.

A separate metrics script calculates human-verified quality statistics and publishes them to `AEGIS/AIQuality` in CloudWatch. Small samples are labeled `EARLY_SAMPLE` rather than presented as mature model-quality evidence.

This is measured feedback, not reinforcement learning and not automatic retraining.

---

## CI/CD and GitOps Architecture

```text
Git commit
   |
GitHub Actions CI
   |
   +--> source validation
   +--> container build
   +--> Trivy report + CRITICAL gate
   +--> CycloneDX SBOM
   +--> immutable ECR image
   |
   +--> guarded GitOps digest update
            |
            v
          Argo CD
            |
        reconcile EKS
```

GitHub authenticates to AWS through OIDC. The CI role has ECR delivery permissions but no EKS deployment permission.

Argo CD is the CD control plane. `AppProject` boundaries constrain sources, destinations, and resource kinds. Automated sync, pruning, self-heal, `PruneLast`, `ApplyOutOfSyncOnly`, and server-side apply enforce declared state.

The CI workflow refreshes the remote branch before modifying desired state. A stale workflow fails closed instead of overwriting newer source.

---

## Observability

AEGIS uses two complementary observability planes.

### Kubernetes and workload telemetry

The GitOps-managed `aegis-observability` application deploys `kube-prometheus-stack` into the isolated `monitoring` namespace. It includes Prometheus, Grafana, kube-state-metrics, and node metrics while keeping the observability GitOps project constrained to that namespace.

The custom **AEGIS Platform Health** dashboard is provisioned from:

```text
kubernetes/observability/manifests/aegis-platform-health-dashboard.yaml
```

It visualizes Status-Page/analyzer/RQ/scheduler availability, node readiness, restarts, CPU, memory, deployment availability, and Pod-density pressure.

Grafana remains a `ClusterIP` service with anonymous access disabled. The AEGIS plugin provides a same-origin staff-authorized gateway and viewer-only embedded access.

### AWS edge and security telemetry

CloudWatch remains authoritative for AWS-native edge and event-pipeline signals:

- WAF allowed/blocked traffic and rate limiting;
- ALB request count, 4XX/5XX, and latency;
- security-event pipeline alarms;
- human-verified AI-quality metrics.

---

## DNS Automation Boundary

The implemented public DNS provider is Dynu for:

```text
app.aegis-project.ddnsfree.com
```

The repository contains ExternalDNS v0.21 plus an AEGIS Dynu webhook provider. The design intentionally applies multiple safety boundaries:

```text
AEGIS Ingress
   |
   | exact label + exact hostname
   v
ExternalDNS
   | namespace-scoped Ingress read
   | CNAME only
   | upsert-only
   | --dry-run
   v
Dynu webhook sidecar
   | exact hostname
   | target must end .elb.amazonaws.com
   | credential from Kubernetes Secret
   v
Dynu API v2
```

The Dynu API credential is never stored in Git.

`--dry-run` remains intentionally enabled, so AEGIS does **not** claim active automated DNS mutation. The implementation is present in Git, but current runtime proof is only considered complete after `scripts/final-acceptance.sh` verifies Argo health, the ExternalDNS rollout, and the least-privilege RBAC boundary.

This is a deliberate showcase-environment DNS model, not an enterprise DNS architecture.

---

## Original Architecture Retained for History

The repository retains the original EC2-based `dev` environment and Ansible roles as project-evolution evidence. The authoritative final application desired state is under `gitops/eks-dev/`; duplicate legacy production manifests were retired.

---

## Architecture Boundaries

The final project does not claim:

- autonomous remediation;
- reinforcement learning or automatic retraining;
- multi-region EKS;
- Kubernetes NetworkPolicy enforcement;
- HA Argo CD deployment;
- Status-Page web HPA as an active production feature;
- cryptographically signed images;
- active automated Dynu writes while ExternalDNS remains in `--dry-run`;
- enterprise-grade DNS.

These are explicit boundaries rather than hidden gaps.
