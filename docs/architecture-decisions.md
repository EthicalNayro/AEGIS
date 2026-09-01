# Architecture Decisions

This document records the architectural decisions that define the **implemented final AEGIS showcase state**. Earlier Phase 1 / Phase 2 experiments are retained in source history and project-evolution documentation, but the statuses below describe what is actually deployed and validated now.

---

## ADR-001 — Prefer at-least-once delivery with idempotent persistence

**Status:** Implemented

### Context

Security telemetry and queue delivery can be retried. Trying to guarantee exactly-once processing across distributed systems would add fragile coordination and could create monitoring gaps.

### Decision

AEGIS accepts at-least-once delivery and makes replay safe:

- deterministic incident identity;
- conditional persistence;
- SQS ACK only after successful finding persistence;
- bounded retry with DLQ isolation.

### Consequences

Duplicate transport is expected and safe. Reliability is preferred over pretending the event path is exactly-once.

---

## ADR-002 — Fail closed at authorization and trust boundaries

**Status:** Implemented

### Context

Security telemetry, AWS resource state, GitOps race conditions, and model output can all be incomplete, stale, malformed, or attacker-controlled.

### Decision

AEGIS fails closed when a trust condition cannot be verified. Examples include:

- unsupported or unresolved monitored resources are not silently treated as trusted;
- stale CI workflows cannot overwrite newer GitOps state;
- malformed Bedrock output is not persisted as a valid finding;
- ExternalDNS refuses unexpected hostnames, record types, targets, and deletes.

### Consequences

Some ambiguous operations are rejected instead of guessed. This increases operational friction slightly but makes security behavior easier to reason about.

---

## ADR-003 — Run application compute on private Amazon EKS workers

**Status:** Implemented and validated

### Context

The original platform used standalone EC2 hosts managed with Ansible and systemd. That model couples deployment, restart behavior, placement, and scaling to individual servers.

### Decision

The final showcase uses Amazon EKS with:

- a Managed Node Group baseline;
- private worker nodes across two Availability Zones;
- Karpenter for additional Spot / On-Demand capacity;
- Kubernetes probes, requests/limits, PDBs, and topology spread;
- `restricted` Pod Security Admission for `aegis-system`.

### Consequences

Runtime behavior becomes declarative and scheduler-driven. Cluster lifecycle and Kubernetes security add complexity, but HA placement, restart tolerance, capacity recovery, and GitOps reconciliation become first-class platform capabilities.

---

## ADR-004 — Keep persistent databases outside Kubernetes

**Status:** Implemented and validated

### Context

Moving application compute to Kubernetes does not require moving stateful databases into the cluster.

### Decision

AEGIS uses:

- Amazon RDS PostgreSQL 16, Multi-AZ;
- Amazon ElastiCache Redis, Multi-AZ with automatic failover;
- DynamoDB for security findings.

### Consequences

Kubernetes remains focused on application/security-processing workloads while AWS managed services own database/cache replication, backups, failover, and storage lifecycle. Persistent-data recovery is still subject to documented restore-testing gaps.

---

## ADR-005 — Separate CI from Kubernetes deployment authority

**Status:** Implemented and validated

### Context

Giving a build pipeline direct cluster mutation rights would make CI compromise equivalent to cluster compromise.

### Decision

GitHub Actions is CI and artifact delivery, not the Kubernetes CD authority.

```text
GitHub Actions
  -> validate / build / scan / SBOM
  -> ECR immutable image
  -> guarded Git desired-state update

Argo CD
  -> reconcile EKS
```

The Status-Page GitHub OIDC role has ECR delivery permissions and no EKS deployment permission.

### Consequences

Deployment requires a reviewed desired-state change. Argo owns reconciliation and self-heal. A stale CI run fails closed before it can overwrite newer GitOps state.

---

## ADR-006 — Deploy immutable application artifacts by digest

**Status:** Implemented and validated

### Context

Mutable image tags make it difficult to prove that the artifact scanned in CI is the artifact running in Kubernetes.

### Decision

AEGIS uses immutable ECR delivery and writes the resolved `sha256` digest into `gitops/eks-dev/kustomization.yaml`.

CI also generates a CycloneDX SBOM and applies a fail-closed Trivy CRITICAL vulnerability gate. Third-party GitHub Actions are pinned by commit SHA.

### Consequences

The running application can be compared directly with Git desired state. Rollback is an auditable Git change to a previously validated digest rather than a tag mutation.

---

## ADR-007 — Run database migrations as an Argo CD PreSync Job

**Status:** Implemented and validated

### Context

Running Django migrations independently in every web Pod can create schema races during rollout.

### Decision

AEGIS runs migrations in a dedicated Kubernetes Job annotated as an Argo CD `PreSync` hook.

### Consequences

Schema mutation is separated from steady-state web startup and must succeed before the application revision is reconciled.

---

## ADR-008 — Use queue buffering and a DLQ for the security-event pipeline

**Status:** Implemented and validated

### Context

WAF security signals can arrive while the analyzer is busy, restarting, or temporarily unable to call Bedrock/DynamoDB.

### Decision

The active event path is:

```text
WAF metric/alarm
 -> EventBridge
 -> SQS security-events
 -> Analyzer
 -> Bedrock
 -> DynamoDB
```

Repeated failures are isolated through a DLQ. Analyzer visibility is extended during processing and the SQS message is deleted only after persistence succeeds.

### Consequences

Producer and consumer availability are decoupled. Poison events do not disappear or retry forever in the main queue.

---

## ADR-009 — Treat AI as advisory, structured, and human-governed

**Status:** Implemented and validated

### Context

Telemetry can contain attacker-controlled content and model output can be wrong or malformed.

### Decision

AEGIS:

- treats telemetry as untrusted data;
- separates analyzer instructions from telemetry;
- requests structured Bedrock output;
- validates parsed output before persistence;
- never grants model output infrastructure mutation authority;
- requires staff analyst review;
- derives quality metrics from human-reviewed findings.

### Consequences

The AI layer improves triage without becoming an autonomous security principal. Human feedback is measured; reinforcement learning or automatic retraining is not claimed.

---

## ADR-010 — Use complementary observability planes

**Status:** Implemented and validated

### Context

AWS edge/security signals and Kubernetes workload signals have different authoritative sources.

### Decision

AEGIS keeps two complementary planes:

- **CloudWatch** for WAF, ALB, security-event pipeline, alarms, and AI-quality signals;
- **Prometheus/Grafana** for Kubernetes, workload, Pod, node, and platform-health telemetry.

The custom **AEGIS Platform Health** dashboard is provisioned from Git and reconciled through the dedicated observability Argo CD application.

### Consequences

The project does not force every signal into one backend. Each monitoring plane remains aligned with the layer it observes best.

---

## ADR-011 — Protect node-level telemetry under Pod-density pressure

**Status:** Implemented after final-validation incident

### Context

During observability rollout, one node-exporter Pod remained Pending because its target node had reached the Kubernetes Pod-density limit. Prometheus and Grafana were otherwise healthy, but Argo correctly remained `Progressing` because the DaemonSet did not cover every current node.

### Decision

Node exporter is assigned:

```yaml
priorityClassName: system-cluster-critical
```

### Consequences

Node-level telemetry can preempt lower-priority workload Pods when necessary instead of silently leaving a current node without exporter coverage. This was added as a resilience hardening based on observed scheduling pressure, not as a theoretical control.

---

## ADR-012 — Keep public DNS on Dynu and safety-bound ExternalDNS

**Status:** Implemented in dry-run; active writes intentionally disabled

### Context

The project does not own a Route 53-managed domain and cannot honestly present Route 53 as the implemented DNS architecture.

### Decision

The public hostname remains:

```text
app.aegis-project.ddnsfree.com
```

AEGIS integrates ExternalDNS with a custom Dynu webhook provider. The accepted state enforces:

- exact hostname filtering;
- namespace-scoped Ingress read access;
- CNAME-only handling;
- `upsert-only` policy;
- `.elb.amazonaws.com` target suffix validation;
- no delete behavior;
- API key supplied from a Kubernetes Secret;
- `--dry-run` enabled.

### Consequences

The project demonstrates a real controller/provider integration without overstating DNS maturity or risking an accidental live mutation during final acceptance.

---

## ADR-013 — Keep the original EC2/Ansible platform as historical evidence

**Status:** Implemented documentation boundary

### Context

The repository contains a meaningful earlier phase that demonstrates Terraform networking, private hosts, Ansible configuration, PostgreSQL/Redis setup, and Nginx/Gunicorn deployment.

### Decision

The EC2/Ansible material remains in the repository as **project-evolution evidence**, while `terraform/environments/eks-dev` and `gitops/eks-dev` represent the final showcase architecture.

### Consequences

Recruiters/reviewers can see architectural progression without confusing historical resources for the current production-style runtime. Historical documents and diagrams must be labeled accordingly.

---

## ADR-014 — Validate infrastructure code in CI; keep infrastructure apply operationally separate

**Status:** Implemented

### Context

An earlier design proposed approval-gated Terraform apply through GitHub Actions. That deployment control plane was not implemented and should not be implied by documentation.

### Decision

Terraform CI performs formatting, initialization without backend state, and validation for both:

```text
terraform/environments/dev
terraform/environments/eks-dev
```

The workflow uses pinned third-party Actions. Infrastructure apply remains an explicit operational action outside the Status-Page application CI/CD path.

### Consequences

The repository accurately separates **Terraform validation** from **application delivery**. It does not claim a remote Terraform backend, GitHub Environment approval gate, or automated Terraform apply that has not been implemented.

---

## Decision Summary

The final platform is intentionally built around:

```text
private multi-AZ compute
+ managed persistent data
+ least-privilege workload identity
+ immutable artifact delivery
+ Git as desired state
+ Argo-owned cluster reconciliation
+ queue buffering and idempotency
+ structured AI with human governance
+ complementary observability
+ explicit fail-closed boundaries
+ evidence-driven acceptance
```

These decisions define the accepted AEGIS showcase state. Future improvements such as NetworkPolicy enforcement, signed images, HA Argo CD, formal restore drills, production Status-Page HPA, and live Dynu mutation should be treated as new decisions rather than retroactively claimed as current capabilities.
