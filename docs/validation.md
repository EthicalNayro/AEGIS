# Validation

## Goal

Validation proves that AEGIS is not only defined in code but is deployable, observable, secure, and consistent from source through runtime.

The final accepted state is reproducible from the repository root with:

```bash
bash scripts/final-acceptance.sh
```

The accepted run completed with:

```text
AEGIS TECHNICAL VALIDATION: COMPLETE (12 checks passed)
```

---

## Final 12-Check Acceptance Gate

The successful final run proved:

```text
PASS  repository working tree is clean
PASS  Terraform eks-dev formatting and validation
PASS  GitOps render and Kubernetes client dry-run
PASS  Argo CD aegis-status-page is Synced Healthy
PASS  Argo CD aegis-observability is Synced Healthy
PASS  Status-Page deployment rollout is complete
PASS  ExternalDNS deployment rollout is complete
PASS  ExternalDNS remains in dry-run safety mode
PASS  ExternalDNS namespace RBAC is least privilege
PASS  GitOps digest matches all EKS Status-Page application images
PASS  Status-Page has multiple Ready replicas across Availability Zones
PASS  public HTTPS health endpoint returns 200 ok
```

See [`final-acceptance.md`](final-acceptance.md) for the exact scope and interpretation.

---

## Validation Matrix

| Area | Status |
|---|---|
| Terraform `eks-dev` formatting / validation | ✅ validated |
| Terraform CI for the authoritative `eks-dev` environment | ✅ configured with pinned Actions |
| Python source compilation / tests | ✅ validated |
| Kustomize render | ✅ validated |
| Kubernetes client dry-run | ✅ validated |
| Repository hygiene | ✅ validated |
| Secure Status-Page CI | ✅ validated |
| Third-party Actions pinned by commit SHA | ✅ configured |
| Trivy production-image gate | ✅ validated |
| CycloneDX SBOM | ✅ validated |
| GitHub OIDC authentication | ✅ validated |
| Immutable ECR delivery | ✅ validated |
| Safe stale-workflow rejection | ✅ validated fail-closed |
| Argo CD application health | ✅ final gate passed |
| Argo CD observability health | ✅ final gate passed |
| PreSync migration hook | ✅ validated |
| GitOps digest == EKS application-image digests | ✅ final gate passed |
| Multiple Status-Page replicas | ✅ final gate passed |
| Multi-AZ placement | ✅ final gate passed |
| Public HTTPS health | ✅ final gate passed |
| WAF block behavior | ✅ validated |
| Security-event analyzer pipeline | ✅ validated |
| Human review workflow | ✅ validated |
| AI quality metrics | ✅ validated |
| Prometheus / Grafana | ✅ final gate passed |
| AEGIS Platform Health dashboard | ✅ validated |
| Karpenter capacity recovery | ✅ validated |
| node-exporter scheduling priority under Pod pressure | ✅ hardened and reconciled |
| ExternalDNS + Dynu controller integration | ✅ final gate passed in dry-run |
| ExternalDNS live Dynu mutation | ⛔ intentionally disabled |

---

## Terraform and Repository Validation

The modern infrastructure source is:

```text
terraform/environments/eks-dev
```

The final gate verifies:

```bash
terraform -chdir=terraform/environments/eks-dev fmt -check -recursive
terraform -chdir=terraform/environments/eks-dev validate
```

Terraform CI additionally validates both the historical `dev` environment and the final `eks-dev` environment. Third-party CI Actions are pinned to exact commit SHAs.

Terraform state, plan artifacts, variable files, credentials, editor artifacts, generated Python caches, and explicitly identified local static-generation scratch files remain excluded from source control.

---

## Secure CI and Supply Chain

The Status-Page secure workflow validates source, builds the application, scans with Trivy, fails closed on configured fixable CRITICAL vulnerabilities, authenticates to AWS through GitHub OIDC, publishes an immutable ECR artifact, generates a CycloneDX SBOM, resolves the image digest, and safely updates GitOps desired state.

A stale delivery run was previously prevented from overwriting newer source. Safe reruns also reuse an already-existing immutable commit image rather than attempting to mutate it.

GitHub Actions has no EKS deployment permission. Argo CD owns cluster reconciliation.

---

## GitOps and Runtime Consistency

The authoritative application desired state is:

```text
gitops/eks-dev/
```

Final validation rendered that tree, passed a Kubernetes client dry-run, confirmed Argo health, and compared the Git-declared immutable digest against all application-image uses in the live Status-Page Deployment:

- `gunicorn`;
- `render-configuration` init container;
- `collect-static` init container.

Database migration remains a dedicated Argo CD `PreSync` Job.

---

## Availability and Scheduling Resilience

Final validation confirmed at least two Ready Status-Page replicas across at least two Availability Zones.

Additional implemented controls include:

- revision-aware topology spread;
- Pod Disruption Budgets;
- readiness/liveness probes;
- RDS Multi-AZ;
- Redis Multi-AZ and automatic failover;
- Karpenter node-capacity recovery;
- HPA behavior on the dedicated demo workload.

Status-Page web HPA is **not** claimed as active production configuration.

During final observability validation, a node-exporter Pod remained Pending because its target node had reached the Kubernetes Pod-density limit. Argo correctly stayed `Progressing` while the DaemonSet was incomplete. The final GitOps values were hardened with:

```yaml
prometheus-node-exporter:
  priorityClassName: system-cluster-critical
```

After reconciliation, `aegis-observability` returned to `Synced / Healthy` and the final acceptance gate passed.

---

## Public Edge and WAF

Validated public behavior includes:

- HTTP redirects to HTTPS;
- ACM-backed TLS on the public ALB;
- AWS WAF associated with the ALB;
- `/healthz` returns `HTTP 200` and body `ok`;
- a controlled XSS-like request was blocked by WAF;
- WAF and ALB telemetry are observable through CloudWatch.

The WAF Web ACL is associated with the ALB; it should not be modeled as a separate serial network hop after the load balancer.

---

## Security Event Pipeline

The active validated path is:

```text
WAF BlockedRequests metric
 -> CloudWatch Alarm
 -> EventBridge
 -> SQS
 -> AEGIS Analyzer
 -> WAF enrichment
 -> Amazon Bedrock Nova Pro
 -> structured-output validation
 -> conditional DynamoDB persistence
 -> SQS ACK after persistence
```

The main queue has a DLQ after bounded repeated receive failures. AI output has no autonomous infrastructure mutation authority.

---

## Human Review and AI Quality

A controlled finding was reviewed through the staff-only workflow. Review updates are conditional on the item remaining in `PENDING_REVIEW`, preventing silent double review.

Reviewed findings feed quality metrics under:

```text
AEGIS/AIQuality
```

Small sample sizes are labeled `EARLY_SAMPLE`; AEGIS does not claim reinforcement learning or automatic retraining.

---

## Observability

The dedicated `aegis-observability` Argo CD application manages Prometheus, Grafana, kube-state-metrics, node-exporter, and the Git-provisioned **AEGIS Platform Health** dashboard.

Prometheus/Grafana cover Kubernetes and workload telemetry. CloudWatch remains complementary and authoritative for WAF, ALB, event-pipeline, alarm, and AI-quality signals.

---

## ExternalDNS / Dynu Boundary

ExternalDNS v0.21 and the AEGIS Dynu webhook are installed and reconciled with:

- namespace-scoped Ingress read access;
- no Kubernetes Secret list permission;
- no Ingress delete permission;
- exact label and hostname filtering;
- CNAME-only handling;
- `.elb.amazonaws.com` target validation;
- `upsert-only` policy;
- Dynu credential supplied through a Kubernetes Secret, never Git;
- `--dry-run` intentionally enabled.

The final gate proved the Deployment rollout, Argo health, least-privilege RBAC, and dry-run safety state. AEGIS does **not** claim active automated Dynu writes.

---

## Evidence Rule

A documentation entry or planned filename is not itself screenshot proof. Screenshots are considered captured only when the corresponding image exists under `docs/screenshots/`.

The runtime itself is technically accepted. Remaining screenshot-copy tasks are presentation/evidence curation, not engineering blockers.

---

## Acceptance Result

```text
AEGIS TECHNICAL VALIDATION: COMPLETE (12 checks passed)
```

This is the technical freeze point. Further changes should be limited to documentation, evidence organization, diagrams, repository metadata, and fixes for proven defects rather than new runtime features.
