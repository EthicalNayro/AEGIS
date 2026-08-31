# AEGIS — AI-Assisted Cloud Security & DevSecOps Platform

AEGIS is a production-style AWS DevSecOps and cloud-security engineering project that combines **Amazon EKS, GitOps, secure software delivery, managed data services, WAF telemetry, AI-assisted security analysis, and human-reviewed findings**.

The project started from a traditional Status-Page deployment requirement and evolved into a resilient, security-focused cloud platform without changing the core application goal. The final architecture demonstrates infrastructure engineering, Kubernetes operations, cloud security, CI/CD, observability, AI governance, and failure-aware design in one end-to-end system.

> AEGIS does **not** perform autonomous remediation. AI findings remain subject to human review, and automated response is intentionally kept out of scope for the validated final architecture.

---

## Project Status

| Capability | Status |
|---|---|
| AWS platform foundation | ✅ Complete |
| EKS modernization | ✅ Complete |
| Multi-AZ application runtime | ✅ Complete |
| Managed PostgreSQL / Redis | ✅ Complete |
| HTTPS / ALB / ACM / WAF | ✅ Complete |
| Security-event pipeline | ✅ Complete |
| AI-assisted analysis with Amazon Bedrock | ✅ Complete |
| Human review workflow | ✅ Complete |
| AI quality metrics | ✅ Complete |
| Secure CI with GitHub OIDC | ✅ Complete |
| Immutable ECR delivery | ✅ Complete |
| GitOps delivery with Argo CD | ✅ Complete |
| End-to-end runtime validation | ✅ Complete |

The currently validated showcase environment is `eks-dev` in `us-east-1`.

Public application endpoint:

```text
https://app.aegis-project.ddnsfree.com
```

---

## Final Architecture

### User traffic

```text
Internet
   |
 HTTPS
   v
ACM Certificate
   |
Application Load Balancer
   |
AWS WAF
   |
Kubernetes Ingress
   |
Status-Page Service
   |
+-------------------------------+
| EKS — private worker nodes    |
|                               |
|  Status-Page web replicas     |
|  Gunicorn + unprivileged Nginx|
|  RQ workers                   |
|  RQ scheduler                 |
+-------------------------------+
       |                  |
       v                  v
RDS PostgreSQL      ElastiCache Redis
Multi-AZ            Multi-AZ / TLS
```

### Security-analysis path

```text
AWS WAF
   |
CloudWatch metric / alarm
   |
EventBridge
   |
SQS security-events queue
   | \
   |  `----> Dead-letter queue
   v
AEGIS Analyzer on EKS
   |
WAF event enrichment
   |
Amazon Bedrock — Nova Pro
   |
Structured-output validation
   |
DynamoDB security findings
   |
Human analyst review
   |
AI quality metrics
   v
CloudWatch observability
```

### Secure software delivery

```text
Developer
   |
GitHub
   |
GitHub Actions
   |  temporary AWS credentials via OIDC
   v
Build + Trivy + CycloneDX SBOM
   |
Immutable ECR image
   |
Update GitOps image digest
   |
Git
   |
Argo CD
   |
EKS
```

**GitHub Actions never deploys directly to EKS.** CI publishes an immutable artifact and updates Git desired state; Argo CD owns cluster reconciliation.

---

## What AEGIS Demonstrates

### Cloud & Kubernetes platform engineering

- VPC `10.10.0.0/16` across two Availability Zones
- separate public, private EKS node/Pod, control-plane, and private data subnets
- private EKS workers with no public IPs
- EKS Managed Node Group baseline plus validated Karpenter scaling
- multi-AZ workload placement with topology-spread constraints
- readiness/liveness probes, resource requests/limits, and Pod Disruption Budgets
- restricted Kubernetes Pod Security Admission for the AEGIS namespace
- managed PostgreSQL and Redis outside Kubernetes

### Application runtime

- Status-Page / Django application
- Gunicorn application server
- unprivileged Nginx sidecar on port `8080`
- RQ workers and scheduler
- dedicated database migration Job executed as an Argo CD `PreSync` hook
- runtime configuration rendered from managed configuration and secrets into an in-memory volume

AEGIS security functionality is isolated in a native Status-Page plugin. A limited set of upstream presentation templates is intentionally overridden or modified to provide a unified AEGIS operations UI; application/security logic remains separated from upstream core logic.

### Cloud security

- AWS WAF managed rule groups and per-IP rate limiting
- WAF block logging and CloudWatch metrics
- controlled XSS request validated as blocked
- EventBridge-driven security event forwarding
- SQS buffering and DLQ protection
- least-privilege workload IAM through EKS Pod Identity
- no application AWS access keys stored in Git or images
- DynamoDB encryption, idempotent writes, and point-in-time recovery

### AI-assisted security operations

- Amazon Bedrock with `amazon.nova-pro-v1:0`
- untrusted telemetry treated as data, not instructions
- structured model output parsed and validated before persistence
- human review with `CORRECT` / `INCORRECT` verdicts
- optional analyst correction and notes
- conditional review updates to prevent accidental double review
- human-verified AI quality metrics published to CloudWatch
- small reviewed samples explicitly labeled as preliminary

### Software supply-chain security

- GitHub OIDC instead of long-lived AWS keys
- branch-scoped AWS trust policy
- CI role limited to ECR delivery; no EKS access
- immutable ECR tags and digest-based Kubernetes deployment
- pinned base container image digest
- multi-stage container build separating compiler/build dependencies from runtime
- GitHub Actions pinned by commit SHA
- Trivy vulnerability and secret scanning
- fail-closed fixable-CRITICAL security gate
- CycloneDX SBOM generated for the exact release image
- safe GitOps synchronization that rejects stale workflows when newer application changes exist

---

## Reliability & High Availability

AEGIS is designed to tolerate routine failures rather than assume perfect execution.

- application web tier runs multiple replicas across Availability Zones
- Kubernetes probes remove unhealthy instances from service
- Pod Disruption Budgets protect minimum availability during voluntary disruption
- RDS PostgreSQL uses Multi-AZ deployment, encryption, backups, and deletion protection
- ElastiCache Redis uses replication, automatic failover, Multi-AZ, encryption at rest, and TLS in transit
- SQS decouples security event producers from the analyzer
- DLQ isolates repeatedly failing events
- analyzer acknowledges messages only after successful persistence
- DynamoDB conditional writes make finding persistence idempotent
- Argo CD self-heal restores declared Git state after drift
- CI refuses stale desired-state updates instead of overwriting newer code

See [Architecture Safety Enhancements](docs/architecture-safety-enhancements.md) for the failure modes and mitigations in detail.

---

## Repository Structure

```text
.
├── .github/workflows/             # CI and secure delivery
├── aegis/                         # earlier CloudTrail security-processing core
├── ansible/                       # original host configuration automation
├── gitops/eks-dev/                # authoritative production Status-Page desired state
├── kubernetes/                    # platform/security/validation Kubernetes resources
├── scripts/                       # human review and AI-quality tooling
├── status-page/                   # Status-Page application + AEGIS plugin/UI
├── terraform/
│   ├── environments/dev/          # original EC2 foundation
│   ├── environments/eks-dev/      # modern EKS environment
│   └── modules/                   # reusable infrastructure modules
└── docs/                          # architecture, security, validation, evidence
```

`gitops/eks-dev/` is the single authoritative production desired state for the Status-Page workload. Legacy duplicate production manifests were retired to reduce configuration drift.

---

## Key Design Decisions

AEGIS deliberately favors safety over convenience:

- **GitOps instead of direct CI deployment** — CI cannot mutate the cluster.
- **Digest-based deployment instead of mutable tags** — the runtime artifact is exact and auditable.
- **Human-reviewed AI instead of autonomous response** — model output is advisory until reviewed.
- **Managed secrets instead of repository secrets** — runtime credentials are fetched or mounted at runtime.
- **At-least-once processing plus idempotency** — replay is safer than silent event loss.
- **Private workers and data services** — Internet exposure is concentrated at the ALB/WAF boundary.
- **Dedicated migration Jobs** — schema changes are separated from application startup.
- **Fail-closed CI safety checks** — unexpected ECR or Git synchronization states stop delivery.

More rationale is documented in [Architecture Decisions](docs/architecture-decisions.md).

---

## Validation Highlights

The final validation covered:

- Terraform formatting and validation
- Ansible syntax validation
- Python compilation
- Kustomize rendering and Kubernetes dry-run
- repository secret/artifact hygiene
- secure GitHub Actions build and publish
- Trivy production-image gate
- CycloneDX SBOM generation
- GitHub OIDC authentication
- immutable ECR digest resolution
- safe GitOps branch synchronization
- Argo CD `Synced` and `Healthy`
- successful `PreSync` database migration
- GitOps digest == EKS runtime digest
- multiple healthy Status-Page replicas
- multi-AZ Pod placement
- public HTTPS `/healthz` returning `200 ok`
- WAF controlled-block behavior
- human review and AI-quality metrics

See [Validation](docs/validation.md) and [Evidence Index](docs/evidence.md).

---

## Implemented Earlier Phase

The repository also retains the earlier AEGIS CloudTrail security-processing core. That phase demonstrated:

- paginated CloudTrail collection
- normalization
- explicit resource-scope enforcement
- public SSH/RDP Security Group detection
- deterministic incident IDs
- idempotent PostgreSQL persistence
- restart-safe polling checkpoints

It remains useful evidence of the project's evolution, while the final EKS showcase adds WAF-driven event ingestion, Bedrock analysis, managed AWS services, Kubernetes workload identity, and GitOps delivery.

See [Phase 2 — Security Event Pipeline](docs/phase-2-security-event-pipeline.md).

---

## Current Boundaries / Known Limitations

The final project intentionally does not claim capabilities that were not validated:

- no autonomous remediation or automatic security-group changes
- no multi-region Kubernetes or cross-region disaster recovery
- Argo CD uses the standard non-HA installation; the dev cluster baseline has two nodes
- Kubernetes NetworkPolicy enforcement is not claimed as active
- Status-Page web autoscaling is not claimed; HPA behavior was validated separately on a demo workload
- the reviewer/runtime Status-Page IAM role can be further separated into distinct operational identities
- model quality metrics are meaningful only after enough findings receive human review
- public Dynu DNS is appropriate for the project environment, not an enterprise DNS architecture

These are documented as engineering boundaries, not hidden gaps.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Deployment / GitOps](docs/deployment.md)
- [Validation](docs/validation.md)
- [Architecture Safety Enhancements](docs/architecture-safety-enhancements.md)
- [Phase 1.1 Platform Modernization](docs/phase-1-1-platform-modernization.md)
- [Phase 2 Security Event Pipeline](docs/phase-2-security-event-pipeline.md)
- [Architecture Decisions](docs/architecture-decisions.md)
- [Disaster Recovery Posture](docs/disaster-recovery.md)
- [Evidence Index](docs/evidence.md)
- [Submission Checklist](docs/submission-checklist.md)

---

## Final Project Summary

AEGIS demonstrates the transition from a traditional server-oriented deployment into a modern, security-focused AWS platform where **infrastructure, application delivery, security telemetry, AI analysis, human governance, and operational resilience are treated as one system**.
