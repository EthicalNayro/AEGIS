# Evidence Index

This index maps major AEGIS claims to the validation evidence collected during implementation. The repository already contains historical Phase 1/Phase 2 screenshots under `docs/screenshots/`; later EKS/GitOps milestones used the numbered evidence convention below during final validation.

---

## Platform / GitOps Milestones

| Evidence | What it proves |
|---|---|
| `83-aegis-argocd-gitops-synced-healthy.png` | Argo CD Application reached `Synced` and `Healthy` |
| `84` drift/self-heal evidence | Argo CD reconciles runtime drift back to Git desired state |
| `85-aegis-secure-ci-oidc-ecr-gitops.png` | secure CI path, GitHub OIDC, ECR delivery, GitOps digest update, and digest-match proof |
| `86-aegis-argocd-presync-database-migration.png` | database migration Job completed successfully as an Argo CD `PreSync` hook |
| `87-aegis-sbom-idempotent-ci-rerun.png` | CycloneDX SBOM generation, safe rerun/idempotent ECR behavior, and GitOps synchronization |
| `88-aegis-multistage-runtime-hardening.png` | multi-stage container build rolled out to healthy application replicas |
| `89-aegis-final-gitops-runtime-verification.png` | final GitOps/runtime verification: Argo status, digest consistency, replicas, multi-AZ placement, and HTTPS health |
| `90-aegis-observability-gitops-synced.png` | Prometheus and Grafana observability application reached GitOps `Synced` / `Healthy` state |
| `91-aegis-grafana-kubernetes-observability.png` | live Kubernetes dashboards for the `aegis-system` namespace |
| `92-aegis-platform-health-dashboard.png` | custom AEGIS Platform Health dashboard and corrected health semantics |
| `93-aegis-external-dns-dynu-dry-run.png` | namespace-scoped ExternalDNS discovered only the intended AEGIS record in dry-run mode |
| `94-aegis-security-command-center.png` | deployed analyst command center with KPIs, filters, confidence, severity, status, and case navigation |

Where a screenshot has not yet been copied into `docs/screenshots/`, the filename above records the evidence naming convention used during project validation. Do not treat the index itself as a substitute for the original captured evidence.

---

## Final Runtime Proof

The final runtime acceptance check verified all of the following in one sequence:

```text
Git remote desired state
        |
        v
Argo CD Synced + Healthy
        |
        v
EKS Deployment image
        |
        | exact sha256 digest match
        v
Multiple Ready Pods
        |
        v
Separate Availability Zones
        |
        v
Public HTTPS /healthz -> 200 ok
```

Final deployed Status-Page digest at validation time:

```text
sha256:f372d341d45df682342eead5ccc19fd3534273ef9f88bba6197d210f2e334076
```

This digest is useful as historical evidence for the final validation run; future documentation-only commits do not imply a new application image.

Later UI and secured-observability releases intentionally produced newer immutable images. The historical digest above remains evidence for its named acceptance run rather than a claim that it is the current runtime digest.

---

## Secure CI Proof

Final successful Status-Page workflow:

```text
Workflow: AEGIS Status-Page Secure CI
Run:      33380244538
Result:   success
Source:   b815930713e39ac5f7727ad431ad82d5e535e4f6
```

The successful run included:

- source and renderer validation;
- container build;
- Trivy report;
- Trivy CRITICAL gate;
- GitHub OIDC authentication;
- ECR publish;
- production-image scan;
- CycloneDX SBOM;
- immutable digest resolution;
- safe GitOps branch synchronization;
- desired-state update/commit.

The resulting GitOps bot commit was:

```text
cff74a1 chore(gitops): deploy git-b815930713e3 [skip ci]
```

---

## Fail-Closed Delivery Proof

A previous UI-triggered workflow intentionally failed at the `Synchronize GitOps branch safely` step after a newer non-GitOps commit advanced the branch.

Important interpretation:

- image build succeeded;
- Trivy gates succeeded;
- SBOM succeeded;
- ECR publish succeeded;
- the workflow refused only the stale GitOps mutation.

This is evidence that the stale-run protection is not theoretical; it stopped an outdated workflow from overwriting desired state for newer source.

---

## Security Edge Proof

Validated public-path behaviors included:

| Test | Expected / observed result |
|---|---|
| HTTP request | redirected to HTTPS |
| HTTPS login | successful application response |
| `/healthz` | `HTTP 200` with `ok` body |
| controlled XSS-like query | blocked by WAF with `403` |
| WAF blocked-request threshold | CloudWatch alarm transition validated |

The WAF/CloudWatch/EventBridge/SQS path was then used as input to the security analyzer.

---

## Analyzer / AI Proof

The analyzer validation demonstrated:

```text
SQS receive
 -> event parse
 -> WAF enrichment
 -> Bedrock Nova Pro analysis
 -> structured JSON validation
 -> DynamoDB conditional persistence
 -> SQS ACK after persistence
```

The production workload uses a dedicated Pod Identity scoped to the analyzer service account.

---

## Human Review Proof

A controlled XSS-related finding was reviewed and marked `CORRECT` through the human-review flow.

The review implementation demonstrates:

- staff-protected analyst access;
- DynamoDB finding retrieval;
- conditional state update from `PENDING_REVIEW`;
- analyst verdict;
- optional correction/note fields.

The production UI was subsequently hardened so the verdict buttons submit an explicit form action, preserve CSRF protection, keep `POST`-only mutation, and return a clear result instead of relying on browser submitter behavior. The fix is recorded in:

```text
11dbe4c fix(ui): make human verdict submission reliable
```

---

## AI Quality Proof

Human-reviewed findings were used by the AI-quality tooling to calculate and publish CloudWatch metrics under:

```text
AEGIS/AIQuality
```

The tooling distinguishes preliminary sample sizes with `EARLY_SAMPLE` instead of overstating model performance.

---

## Analyst Experience Proof

The final AEGIS interface includes:

- a responsive security command center;
- KPI cards for ingested, pending, critical, and high-priority findings;
- search, severity filtering, and review-state filtering;
- severity/status badges and confidence bars;
- incident-level AI assessment and WAF evidence;
- a prominent Human Analyst Review panel;
- explicit empty, loading, error, focus, and responsive states;
- a left-side security operations navigation model.

The primary UI and verdict hardening commits are:

```text
673dafb feat(ui): unify AEGIS security operations experience
11dbe4c fix(ui): make human verdict submission reliable
```

---

## Observability Proof

The observability validation demonstrated:

- Prometheus and Grafana reconciled by the dedicated `aegis-observability` Argo CD application;
- live Kubernetes namespace/workload/Pod/node dashboards;
- the custom AEGIS Platform Health dashboard;
- corrected availability and Pod-density health semantics;
- secured same-origin embedding inside the staff-only AEGIS interface;
- anonymous Grafana disabled, `ClusterIP`-only exposure, and viewer-only proxy identities.

The implementation is represented by:

```text
902ddd8 feat(observability): add Prometheus and Grafana GitOps stack
37a378f feat(observability): manage AEGIS Grafana dashboard with Argo CD
55dbaf1 fix(observability): correct AEGIS dashboard health semantics
85d53a9 feat(observability): embed secured Grafana dashboards
```

---

## ExternalDNS Dry-Run Proof

ExternalDNS v0.21 and the Dynu webhook were validated with:

- namespace-scoped ingress read permissions;
- no Kubernetes Secret read permission;
- exact ingress label and hostname filters;
- CNAME-only, `upsert-only` behavior;
- an allowed `.elb.amazonaws.com` target suffix;
- a Kubernetes Secret for the Dynu API credential;
- `--dry-run` enabled.

This evidence proves the planned record and safety boundaries. It does **not** claim that automated DNS writes are active.

---

## High Availability / Scaling Proof

Validation covered:

- two healthy Status-Page web replicas;
- Pods scheduled across separate Availability Zones;
- Pod Disruption Budget;
- revision-aware topology spread;
- readiness/liveness behavior;
- RDS Multi-AZ;
- Redis Multi-AZ/failover;
- Karpenter node scaling;
- HPA scaling on a dedicated demo workload.

Status-Page web HPA is not claimed as active production configuration.

---

## Repository / Source-of-Truth Proof

The final repository audit verified:

- Terraform source committed;
- Kubernetes/GitOps source committed;
- analyzer source committed;
- human review / AI-quality scripts committed;
- Status-Page UI source committed;
- duplicate legacy production manifests retired;
- no local-only untracked project source;
- no tracked local Terraform plans/state/editor artifacts;
- final branch synchronized with remote before documentation work.

Repository hygiene hardening was committed as:

```text
1520fb4 chore(repo): harden source control and secret handling
```

---

## Historical Evidence

The earlier screenshots in `docs/screenshots/` remain useful evidence of the original project foundation, including:

- local toolchain setup;
- Terraform network plan/apply;
- NAT/private subnet validation;
- Ansible connectivity;
- PostgreSQL and Redis configuration;
- Status-Page host deployment;
- Nginx/Gunicorn chain;
- original Git/state hygiene checks.

They should be presented as **project evolution evidence**, not as the final EKS runtime architecture.
