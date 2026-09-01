# Evidence Index

This index maps AEGIS claims to captured or reproducible proof. It deliberately distinguishes **implemented code**, **historically validated behavior**, and **final evidence still pending capture**.

A filename in this document is not itself proof. Screenshot evidence is considered complete only when the corresponding file exists under `docs/screenshots/`.

---

## Final Acceptance

The current post-ExternalDNS acceptance test is:

```bash
bash scripts/final-acceptance.sh
```

It must finish with:

```text
AEGIS TECHNICAL VALIDATION: COMPLETE
```

before the current repository revision is presented as fully runtime-validated.

---

## Platform / GitOps Milestones

| Evidence | Status | What it proves |
|---|---|---|
| [`83-aegis-argocd-gitops-synced-healthy.png`](screenshots/83-aegis-argocd-gitops-synced-healthy.png) | ✅ captured | Argo CD reached `Synced / Healthy` during the validated application milestone |
| `84` drift/self-heal evidence | ✅ historical | Argo CD reconciled runtime drift back to Git desired state |
| [`85-aegis-secure-ci-oidc-ecr-gitops.png`](screenshots/85-aegis-secure-ci-oidc-ecr-gitops.png) | ✅ captured | OIDC, ECR delivery, security gates, and GitOps digest update |
| [`86-aegis-argocd-presync-database-migration.png`](screenshots/86-aegis-argocd-presync-database-migration.png) | ✅ captured | database migration succeeded as an Argo CD `PreSync` hook |
| [`87-aegis-sbom-idempotent-ci-rerun.png`](screenshots/87-aegis-sbom-idempotent-ci-rerun.png) | ✅ captured | CycloneDX SBOM and safe/idempotent CI behavior |
| [`88-aegis-multistage-runtime-hardening.png`](screenshots/88-aegis-multistage-runtime-hardening.png) | ✅ captured | multi-stage runtime image and healthy rollout |
| [`89-aegis-final-gitops-runtime-verification.png`](screenshots/89-aegis-final-gitops-runtime-verification.png) | ✅ captured | historical final GitOps/runtime acceptance before later observability/DNS additions |
| [`90-aegis-prometheus-grafana-gitops-synced.png`](screenshots/90-aegis-prometheus-grafana-gitops-synced.png) | ✅ captured | Prometheus/Grafana GitOps application reached `Synced / Healthy` |
| [`91-aegis-grafana-kubernetes-observability.png`](screenshots/91-aegis-grafana-kubernetes-observability.png) | ✅ captured | live Kubernetes telemetry for `aegis-system` |
| `92-aegis-grafana-platform-health-dashboard.png` | ⏳ copy pending | final corrected AEGIS Platform Health dashboard |
| `93-aegis-externaldns-dynu-dry-run.png` | ⏳ runtime proof pending | healthy ExternalDNS/Dynu discovery in dry-run mode |
| [`94-aegis-security-command-center.png`](screenshots/94-aegis-security-command-center.png) | ✅ captured | deployed analyst command center and case navigation |

---

## Secure CI / Supply Chain

Validated CI behavior includes:

```text
source validation
 -> container build
 -> Trivy report + fail-closed CRITICAL gate
 -> GitHub OIDC authentication
 -> immutable ECR delivery
 -> production-image validation
 -> CycloneDX SBOM
 -> immutable digest resolution
 -> guarded GitOps update
 -> Argo reconciliation
```

A stale workflow was intentionally prevented from overwriting newer desired state. This proves the GitOps race protection fails closed.

The later UI release also completed successfully through the secure Status-Page workflow, confirming the hardened delivery path continued to operate after the original final-validation run.

GitHub Actions has no EKS deployment permission; Argo CD owns cluster mutation.

---

## Runtime / Availability Proof

Historically validated runtime behavior includes:

- multiple Ready Status-Page replicas;
- placement across separate Availability Zones;
- revision-aware topology spread;
- readiness/liveness probes;
- Pod Disruption Budget;
- exact Git desired digest == running EKS digest;
- public HTTPS `/healthz -> 200 ok`;
- RDS Multi-AZ;
- Redis Multi-AZ/failover.

Karpenter was also observed recovering the cluster from Pod-density pressure after the observability stack increased workload count. Additional capacity was provisioned and AEGIS workloads recovered without manual Pod deletion.

Status-Page web HPA is **not** claimed as active. HPA proof belongs to the dedicated demo workload.

---

## Security Edge Proof

Validated edge behaviors include:

| Test | Observed result |
|---|---|
| HTTP request | redirected to HTTPS |
| normal HTTPS request | application response succeeded |
| `/healthz` | `HTTP 200` with `ok` |
| controlled XSS-style query | blocked by AWS WAF |
| WAF blocked-request threshold | CloudWatch alarm transition observed |

The security processing path was validated as:

```text
WAF
 -> CloudWatch alarm
 -> EventBridge
 -> SQS
 -> Analyzer
 -> Bedrock Nova Pro
 -> structured validation
 -> conditional DynamoDB persistence
 -> SQS ACK after persistence
```

The main queue has a DLQ redrive path after repeated receive failures.

![AWS WAF blocks a controlled XSS request](screenshots/61-aws-waf-blocks-malicious-xss-request.png)

---

## Analyzer / AI Governance Proof

The analyzer uses a dedicated Pod Identity and treats telemetry and model output as untrusted inputs. Bedrock output is parsed and validated before persistence.

A controlled finding was successfully persisted and later reviewed. AI has no infrastructure mutation authority.

![Amazon Bedrock security classification](screenshots/74-aegis-bedrock-ai-security-classification.png)

---

## Human Review Proof

The review workflow demonstrates:

- staff-protected access;
- DynamoDB finding retrieval;
- conditional transition from `PENDING_REVIEW`;
- `CORRECT` / `INCORRECT` analyst verdicts;
- optional correction and analyst note;
- protection against accidental double review.

![Human review feedback recorded](screenshots/77-aegis-human-review-feedback-recorded.png)

---

## AI Quality Proof

Human-reviewed findings feed metrics published under:

```text
AEGIS/AIQuality
```

Small sample sizes are labeled `EARLY_SAMPLE`; AEGIS does not claim reinforcement learning or automatic model retraining.

![CloudWatch AI quality feedback dashboard](screenshots/79-aegis-cloudwatch-ai-quality-feedback-dashboard.png)

---

## Observability Proof

Prometheus/Grafana validation demonstrated:

- a dedicated `aegis-observability` Argo CD application;
- Prometheus, Grafana, kube-state-metrics, and node metrics;
- live namespace/workload/Pod/node telemetry;
- a Git-provisioned custom AEGIS Platform Health dashboard;
- corrected availability and Pod-density health semantics;
- Grafana kept `ClusterIP`-only with anonymous access disabled;
- staff-controlled same-origin embedding through the AEGIS interface.

Implementation commits include:

```text
902ddd8 feat(observability): add Prometheus and Grafana GitOps stack
37a378f feat(observability): manage AEGIS Grafana dashboard with Argo CD
55dbaf1 fix(observability): correct AEGIS dashboard health semantics
85d53a9 feat(observability): embed secured Grafana dashboards
```

![Grafana Kubernetes observability for AEGIS](screenshots/91-aegis-grafana-kubernetes-observability.png)

Screenshot 92 should be copied only after the corrected Platform Health dashboard is captured in its final state.

---

## ExternalDNS / Dynu Status

The repository contains an ExternalDNS v0.21 + Dynu webhook implementation with:

- namespace-scoped Ingress read permission;
- no Kubernetes Secret list permission;
- no Ingress delete permission;
- exact Ingress label and hostname filtering;
- CNAME-only handling;
- allowed `.elb.amazonaws.com` target validation;
- `upsert-only` policy;
- Dynu API credential supplied through a Kubernetes Secret;
- `--dry-run` enabled.

This proves the **implementation and intended safety boundary**. It does **not** yet count as current runtime evidence while the final post-change Argo/Deployment health gate is unresolved.

Screenshot 93 should only be captured after:

```text
aegis-status-page   Synced   Healthy
aegis-external-dns  rollout complete
external-dns pod    2/2 Running
```

and the provider logs confirm discovery of only `app.aegis-project.ddnsfree.com` without performing a DNS mutation.

Automated Dynu writes are not claimed while `--dry-run` is enabled.

---

## Repository / Source-of-Truth Proof

Repository validation has covered:

- committed Terraform source;
- committed Kubernetes/GitOps source;
- committed analyzer and review tooling;
- committed Status-Page plugin/UI source;
- committed observability and ExternalDNS source;
- duplicate legacy production manifests retired;
- no tracked local Terraform state/plan/editor artifacts;
- credentials excluded from Git;
- explicit ignore rules for local/generated artifacts.

`gitops/eks-dev/` remains the authoritative production-style Status-Page desired state.

---

## Historical Evidence

Earlier screenshots remain useful proof of project evolution, including Terraform networking, NAT/private subnet validation, Ansible, PostgreSQL/Redis setup, Nginx/Gunicorn, and the original EC2 deployment.

They should be presented as **evolution evidence**, not as the final EKS runtime architecture.
