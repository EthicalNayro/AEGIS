# Validation

## Goal

Validation proves that AEGIS is not only defined in code but is deployable, observable, secure, and consistent from source through runtime.

AEGIS has accumulated validated milestones throughout the project. Because Prometheus/Grafana and ExternalDNS were added after the earlier feature-freeze acceptance run, the repository now distinguishes **historical validated evidence** from the **current final acceptance gate**.

---

## Current Final Acceptance Gate

Run from the repository root:

```bash
bash scripts/final-acceptance.sh
```

The script fails closed unless all of the following are true:

- the repository working tree is clean;
- Terraform `eks-dev` formatting and validation pass;
- `gitops/eks-dev` renders and passes a Kubernetes client dry-run;
- `aegis-status-page` is `Synced` and `Healthy` in Argo CD;
- `aegis-observability` is `Synced` and `Healthy` in Argo CD;
- Status-Page and ExternalDNS Deployments have completed their rollouts;
- ExternalDNS is still in the intentionally non-mutating `--dry-run` mode;
- ExternalDNS can read the intended Ingress but cannot list Secrets or delete Ingresses;
- the GitOps image digest exactly matches the Status-Page image running in EKS;
- at least two Status-Page replicas are Ready across at least two Availability Zones;
- the public HTTPS `/healthz` endpoint returns `HTTP 200` with `ok`.

Only a run that reaches:

```text
AEGIS TECHNICAL VALIDATION: COMPLETE
```

should be treated as the final post-ExternalDNS acceptance result.

---

## Validation Matrix

| Area | Status |
|---|---|
| Terraform formatting / validation | ✅ validated |
| Ansible syntax | ✅ validated |
| Python source compilation | ✅ validated |
| Kustomize render | ✅ validated |
| Kubernetes client dry-run | ✅ validated |
| Repository hygiene | ✅ validated |
| Secure Status-Page CI | ✅ validated |
| Trivy production-image gate | ✅ validated |
| CycloneDX SBOM | ✅ validated |
| GitHub OIDC authentication | ✅ validated |
| Immutable ECR delivery | ✅ validated |
| Safe GitOps synchronization | ✅ validated |
| PreSync migration hook | ✅ validated |
| GitOps digest == EKS runtime digest | ✅ historically validated; rechecked by final gate |
| Multiple Status-Page replicas | ✅ historically validated; rechecked by final gate |
| Multi-AZ placement | ✅ historically validated; rechecked by final gate |
| Public HTTPS health | ✅ historically validated; rechecked by final gate |
| WAF block behavior | ✅ validated |
| Security-event analyzer pipeline | ✅ validated |
| Human review workflow | ✅ validated |
| AI quality metrics | ✅ validated |
| Prometheus / Grafana GitOps stack | ✅ validated |
| AEGIS Platform Health dashboard | ✅ validated implementation and telemetry |
| ExternalDNS + Dynu implementation | ✅ committed with safety boundaries |
| ExternalDNS live DNS mutation | ⛔ intentionally disabled (`--dry-run`) |
| Final Argo `Synced / Healthy` after ExternalDNS addition | ⏳ must pass final acceptance gate |

---

## Terraform and Configuration Validation

The modern infrastructure is validated from:

```text
terraform/environments/eks-dev
```

The final gate runs:

```bash
terraform -chdir=terraform/environments/eks-dev fmt -check -recursive
terraform -chdir=terraform/environments/eks-dev validate
```

Terraform state, plans, local variable files, editor artifacts, and generated Python cache files remain excluded from source control.

The legacy EC2/Ansible layer remains part of the project history and has also been syntax-validated. PostgreSQL password-handling tasks use `no_log: true`.

---

## Secure CI and Supply Chain

The Status-Page workflow validates source and renderer code, builds the production image, runs Trivy, enforces a fail-closed CRITICAL gate, authenticates to AWS with GitHub OIDC, publishes to immutable ECR, generates a CycloneDX SBOM, resolves the immutable digest, and updates GitOps state through the guarded synchronization path.

An intentionally stale workflow was previously prevented from overwriting newer desired state. That is evidence that the stale-run protection works rather than being only a design claim.

CI has no EKS deployment permission. Argo CD owns cluster reconciliation.

---

## GitOps and Runtime Consistency

The authoritative Status-Page desired state is:

```text
gitops/eks-dev/
```

The final acceptance gate renders this directory, performs a Kubernetes client dry-run, checks Argo application health, and compares the declared immutable image digest with the live EKS Deployment.

Database migrations execute through the dedicated Argo CD `PreSync` Job rather than application startup side effects.

---

## Availability and Resilience

Validated resilience behaviors include:

- multiple Status-Page web replicas;
- revision-aware multi-AZ topology spread;
- Pod Disruption Budgets;
- readiness and liveness probes;
- RDS Multi-AZ;
- Redis Multi-AZ / automatic failover;
- Karpenter node scaling and recovery after Pod-density pressure;
- HPA scaling on the dedicated demo workload.

Status-Page web HPA is **not** claimed as an active production configuration.

---

## Public Edge and Security Pipeline

Validated public-path behavior includes:

- HTTP to HTTPS redirect;
- HTTPS application access;
- `/healthz` returning `200 ok`;
- a controlled XSS-style request blocked by AWS WAF;
- CloudWatch security signals;
- EventBridge delivery to SQS;
- analyzer processing through Bedrock Nova Pro;
- structured-output validation;
- conditional DynamoDB persistence;
- SQS ACK only after successful persistence;
- DLQ redrive after bounded repeated failures.

AEGIS does not grant the model autonomous remediation authority.

---

## Human Review and AI Quality

A controlled security finding was reviewed through the staff-only workflow. Findings can transition conditionally from `PENDING_REVIEW` to an analyst verdict, preventing silent double review.

Reviewed findings feed the AI-quality tooling, which publishes metrics under:

```text
AEGIS/AIQuality
```

Small samples are marked `EARLY_SAMPLE`; the project does not claim reinforcement learning or automatic retraining.

---

## Observability

The `aegis-observability` Argo CD application manages Prometheus, Grafana, kube-state-metrics, node metrics, and the Git-provisioned **AEGIS Platform Health** dashboard.

Validated telemetry includes workload CPU/memory, replica availability, node readiness, restarts, deployment availability, and node Pod-density pressure. CloudWatch remains the complementary plane for WAF, ALB, event-pipeline, and AI-quality signals.

---

## ExternalDNS / Dynu Boundary

ExternalDNS v0.21 and the AEGIS Dynu webhook are committed with:

- namespace-scoped Ingress read access;
- no Kubernetes Secret list permission;
- no Ingress delete permission;
- an exact AEGIS Ingress label;
- an exact hostname filter for `app.aegis-project.ddnsfree.com`;
- CNAME-only handling;
- an allowed `.elb.amazonaws.com` target suffix;
- `upsert-only` policy;
- the Dynu API credential supplied from a Kubernetes Secret, never Git;
- `--dry-run` intentionally enabled.

The final acceptance run must prove the Deployment is healthy before ExternalDNS is presented as runtime-validated. Automated DNS writes are not claimed while `--dry-run` remains enabled.

---

## Acceptance Rule

The earlier project milestones remain valid evidence for the behaviors they captured. The final submission state, however, should only be declared after the current repository revision passes `scripts/final-acceptance.sh` and the corresponding final screenshots are copied into `docs/screenshots/`.
