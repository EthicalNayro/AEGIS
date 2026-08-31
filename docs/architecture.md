# Architecture

## Scope

AEGIS now has two architectural generations in the same repository:

1. the original EC2/Ansible foundation and CloudTrail security-processing core;
2. the validated `eks-dev` modernization, which is the final showcase architecture.

The modern platform keeps persistent data outside Kubernetes, uses GitOps for workload delivery, and adds WAF-driven security telemetry, AI-assisted analysis, human review, and quality measurement.

---

## Final Platform Topology

```text
                         Internet
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

The EKS workers are private. Public exposure is concentrated at the ALB/WAF boundary.

### VPC layout

The modern environment uses VPC `10.10.0.0/16` across `us-east-1a` and `us-east-1b` with:

- public subnets for Internet-facing load balancer/NAT infrastructure;
- dedicated small EKS control-plane subnets;
- private EKS node/Pod subnets;
- private data subnets for managed database/cache services;
- NAT egress per Availability Zone.

The larger node/Pod ranges leave room for VPC CNI Pod IP allocation.

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

The topology rule is revision-aware through `pod-template-hash`, which prevents a rolling release from satisfying spread constraints with old replicas from the previous revision.

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

AEGIS security functionality is implemented as a native Status-Page plugin. A limited set of upstream presentation templates is intentionally overridden or modified to provide a unified AEGIS UI; security/application logic remains isolated from upstream core logic.

---

## Runtime Configuration and Secrets

Sensitive configuration is not committed to Git.

At Pod startup, a renderer combines:

- non-secret runtime configuration;
- a mounted Django `SECRET_KEY`;
- the RDS managed credential secret fetched from AWS Secrets Manager through workload identity.

It writes `configuration.py` into a memory-backed runtime volume with restrictive permissions.

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

The queue decouples detection transport from analysis. A message receives a longer per-message visibility timeout during analysis. It is acknowledged only after successful persistence.

DynamoDB uses `incident_id` as the key, conditional writes for idempotency, server-side encryption, and point-in-time recovery.

### AI trust boundary

Telemetry and model output are treated as untrusted inputs.

The analyzer:

1. separates instructions from telemetry;
2. sends telemetry to Amazon Bedrock Nova Pro;
3. requires structured JSON output;
4. validates the returned structure before persistence;
5. stores a reviewable finding rather than taking autonomous action.

This keeps AI in an advisory role.

---

## Human Review and AI Quality

The Status-Page AEGIS plugin exposes staff-only analyst views for findings stored in DynamoDB.

A reviewer can mark a finding `CORRECT` or `INCORRECT`, optionally supply a corrected classification, and add a note. Updates are conditional on the finding still being in `PENDING_REVIEW` state.

A separate metrics script calculates human-verified quality statistics and publishes them to `AEGIS/AIQuality` in CloudWatch. Samples below the configured minimum are labeled `EARLY_SAMPLE` rather than presented as mature model-quality evidence.

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
   +--> ECR immutable image
   |
   +--> update GitOps digest in Git
            |
            v
          Argo CD
            |
        reconcile EKS
```

GitHub authenticates to AWS through OIDC. The CI role has ECR delivery permissions but no EKS permissions.

Argo CD is the CD control plane. The `AppProject` constrains permitted sources, destinations, and resource kinds. The Application uses automated sync, pruning, self-heal, `PruneLast`, `ApplyOutOfSyncOnly`, and server-side apply.

The CI workflow refreshes the remote branch before modifying desired state. If a stale workflow detects newer non-GitOps changes, it fails closed rather than overwriting the newer source revision.

---

## Observability

CloudWatch dashboards combine application-edge and security signals:

- WAF allowed/blocked traffic;
- WAF rate limiting;
- ALB request count, 4XX/5XX, average and p95 response time;
- AI quality metrics from human-reviewed findings.

A CloudWatch alarm on blocked requests drives the event pipeline through EventBridge and SQS.

---

## Original Architecture Retained for History

The repository still contains the original EC2-based `dev` environment and Ansible roles. They document the system's evolution and remain useful for demonstrating configuration management and earlier validation.

The authoritative final application desired state is under `gitops/eks-dev/`; duplicate legacy production manifests were retired.

---

## Architecture Boundaries

The final project does not claim:

- autonomous remediation;
- multi-region EKS;
- Kubernetes NetworkPolicy enforcement;
- HA Argo CD deployment;
- web-tier HPA as an active production feature;
- enterprise-grade DNS.

These are conscious boundaries of the validated environment.
