# Validation

## Goal

Validation proves that the final AEGIS architecture is not only defined in code but also deployable, observable, and consistent from source through runtime.

The final acceptance process covered infrastructure, configuration, application packaging, GitOps, Kubernetes runtime, security controls, AI review tooling, and repository hygiene.

---

## Final Validation Matrix

| Area | Result |
|---|---|
| Terraform formatting / validation | ✅ PASS |
| Ansible syntax | ✅ PASS |
| Python source compilation | ✅ PASS |
| Kustomize render | ✅ PASS |
| Kubernetes client dry-run | ✅ PASS |
| Repository synchronized | ✅ PASS |
| No untracked project source | ✅ PASS |
| No tracked local artifacts | ✅ PASS |
| Secure Status-Page CI | ✅ PASS |
| Trivy production-image gate | ✅ PASS |
| CycloneDX SBOM | ✅ PASS |
| GitHub OIDC authentication | ✅ PASS |
| Immutable ECR delivery | ✅ PASS |
| Safe GitOps synchronization | ✅ PASS |
| Argo CD Synced | ✅ PASS |
| Argo CD Healthy | ✅ PASS |
| PreSync migration hook | ✅ PASS |
| GitOps digest == EKS runtime digest | ✅ PASS |
| Multiple Status-Page replicas | ✅ PASS |
| Multi-AZ placement | ✅ PASS |
| Public HTTPS health | ✅ PASS |
| WAF block behavior | ✅ PASS |
| Human review workflow | ✅ PASS |
| AI quality metrics | ✅ PASS |

---

## Terraform

Final infrastructure validation was run from:

```text
terraform/environments/eks-dev
```

Commands:

```bash
terraform fmt -check -recursive
terraform validate
```

The configuration validated successfully.

Terraform source-of-truth files for the modern environment and modules are committed, including the provider lock file. Local state, plans, and variable files remain excluded from Git.

---

## Ansible

The legacy EC2/Ansible layer remains part of the project and was syntax-checked as part of final repository validation.

Because the repository lives under `/mnt/c` in WSL, Ansible may ignore a world-writable `ansible.cfg`. The final syntax check therefore supplied inventory and role path explicitly rather than weakening directory permissions for the validation.

The PostgreSQL role also uses `no_log: true` for both database-user creation tasks that handle password variables.

---

## Python

Final Python compilation covered:

```text
scripts/
kubernetes/aegis-analyzer/
status-page/statuspage/aegis_review/
```

`python3 -m compileall` completed successfully. Generated `__pycache__` directories were removed afterward and remain ignored by Git.

---

## GitOps Render and Kubernetes Dry-Run

The authoritative application desired state is:

```text
gitops/eks-dev/
```

Validation included:

```bash
kubectl kustomize gitops/eks-dev
kubectl apply --dry-run=client --validate=false -f <rendered-output>
```

The render completed successfully and contained the expected immutable application digest.

---

## Secure CI Evidence

The Status-Page secure workflow validated:

- source preflight;
- plugin Python;
- runtime configuration renderer;
- container build;
- Trivy vulnerability report;
- fail-closed CRITICAL gate;
- AWS authentication with GitHub OIDC;
- ECR delivery;
- production-image Trivy gate;
- CycloneDX SBOM;
- immutable digest resolution;
- safe GitOps synchronization;
- desired-state commit.

A final manually triggered workflow at the latest source revision completed successfully after an earlier stale workflow was intentionally rejected by the GitOps safety guard.

This provides evidence for both the happy path and the fail-closed race-protection path.

---

## CI Idempotency

The workflow was rerun against an already-published commit image.

Instead of blindly rebuilding/pushing, it detected the exact ECR artifact, reused it safely, reran security evidence generation, and refreshed desired state without creating an inconsistent image.

This proved that delivery retries are intentional and repeatable.

---

## SBOM

The production workflow generates a CycloneDX SBOM from the exact release image and uploads it as a GitHub Actions artifact.

The SBOM artifact digest is evidence about the archived SBOM artifact; it is distinct from the ECR container image digest.

---

## Argo CD

Final Argo validation confirmed:

```text
Sync:   Synced
Health: Healthy
```

The application revision matched the desired deployment branch state after CI created the GitOps bot commit.

A drift/self-heal test was also performed earlier to prove that Argo CD restores declared Git state rather than accepting unmanaged runtime drift as authoritative.

---

## Database Migration

The Django migration workload runs as an Argo CD `PreSync` hook.

Final evidence confirmed the migration Job reached the expected successful state before the application rollout.

This validates schema evolution as part of the GitOps release sequence rather than as an undocumented manual operation.

---

## Runtime Digest Consistency

Final validation compared:

1. the digest declared in `gitops/eks-dev/kustomization.yaml`;
2. the image configured in the EKS `aegis-status-page` Deployment.

They matched exactly.

This proves the artifact that passed CI is the artifact declared in Git and running in Kubernetes.

---

## High Availability / Placement

The Status-Page web workload was verified with multiple Ready/Running Pods placed on nodes in separate Availability Zones.

The architecture additionally uses:

- topology-spread constraints;
- Pod Disruption Budget;
- readiness/liveness probes;
- RDS Multi-AZ;
- Redis replication, Multi-AZ, and automatic failover.

Karpenter scaling and HPA behavior were validated on dedicated test/demo workloads. Production Status-Page web HPA is not claimed as active.

---

## Public HTTPS Health

Final public runtime validation used:

```text
https://app.aegis-project.ddnsfree.com/healthz
```

Expected and observed result:

```text
HTTP 200
ok
```

The login endpoint was also reachable over HTTPS. The AEGIS analyst plugin is staff-protected and may redirect unauthenticated requests rather than return an application error.

---

## WAF Enforcement

The Internet path was tested for normal and blocked behavior.

Validated results included:

- HTTP redirected to HTTPS;
- normal HTTPS request succeeded;
- `/healthz` returned `200 ok`;
- controlled XSS-style input was blocked with `403`;
- the corresponding WAF metric/log path was visible in CloudWatch.

---

## Security Event Pipeline

The WAF-to-analyzer path was tested end to end:

```text
WAF
 -> CloudWatch alarm
 -> EventBridge
 -> SQS
 -> Analyzer
 -> Bedrock
 -> DynamoDB finding
```

A separate validation identity was able to receive/read queue events without delete permission during proof testing. The production analyzer performs delete/ACK only after successful finding persistence.

DLQ redrive configuration is active with a bounded receive count.

---

## Human Review

A controlled security finding was reviewed through the human-review workflow and marked `CORRECT`.

The review system supports conditional updates so a finding cannot be silently reviewed twice from the initial `PENDING_REVIEW` state.

---

## AI Quality Metrics

Human-reviewed findings feed a metrics script that publishes quality indicators to CloudWatch namespace:

```text
AEGIS/AIQuality
```

Small samples are marked `EARLY_SAMPLE` instead of being presented as statistically mature results.

This validates a measurable human-feedback loop without claiming automatic retraining.

---

## Repository Hygiene

Final repository checks included:

- branch synchronized with remote;
- zero ahead/behind after push;
- no untracked source files;
- no tracked Terraform state/plan artifacts;
- no tracked editor swap/backup artifacts;
- no obvious plaintext AWS keys/private keys;
- password-variable references distinguished from hardcoded password literals;
- explicit ignore rules for local plans and editor temporary files.

`git diff --check` also passed before the final hygiene commit.

---

## Acceptance Result

```text
AEGIS TECHNICAL VALIDATION: COMPLETE
```

After this point, the project entered feature freeze for final documentation and presentation work.
