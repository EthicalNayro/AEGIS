# Architecture Safety Enhancements

This document records the failure modes AEGIS is explicitly designed to tolerate or fail safely around. The project is not only a collection of AWS/Kubernetes services; the important engineering work is in making their interactions predictable under retries, restarts, scheduling pressure, stale workflows, malformed AI output, drift, and unsafe automation boundaries.

---

## 1. Security Event Reliability

### SQS buffering

**Risk:** WAF security signals arrive faster than the analyzer can process them or the analyzer is temporarily unavailable.

**Control:** EventBridge delivers to SQS rather than coupling detection directly to analysis. Producers and consumers can fail or scale independently.

### Dead-letter queue

**Risk:** one malformed or repeatedly failing event retries forever.

**Control:** the main queue has a bounded redrive policy and a DLQ. Poison events are isolated for investigation instead of blocking normal processing.

### Per-message visibility extension

**Risk:** a Bedrock/DynamoDB analysis takes longer than the queue's default visibility timeout and the same message is processed concurrently.

**Control:** the analyzer uses a longer per-message visibility window while processing.

### ACK only after durable persistence

**Risk:** a message is deleted before its finding is safely stored.

**Control:** SQS delete/ACK happens only after the DynamoDB finding write succeeds.

### Idempotent persistence

**Risk:** retries create duplicate findings.

**Control:** deterministic incident identity plus conditional `PutItem` makes replay safe.

### DynamoDB point-in-time recovery

**Risk:** accidental/faulty updates damage security finding history.

**Control:** PITR is enabled for the findings table.

---

## 2. AI Safety and Human Governance

### Untrusted telemetry boundary

**Risk:** attacker-controlled WAF telemetry contains prompt-like instructions.

**Control:** telemetry is treated as data, separated from analyzer instructions, and never allowed to redefine the task.

### Structured output validation

**Risk:** Bedrock returns malformed, incomplete, or semantically unexpected output.

**Control:** output must parse as the expected JSON structure and pass application validation before persistence.

### Advisory AI only

**Risk:** a model classification is treated as authoritative and automatically mutates infrastructure.

**Control:** AEGIS stores a reviewable finding. The model has no remediation authority.

### Conditional human review

**Risk:** two reviewers or duplicate requests silently overwrite a completed review.

**Control:** verdict updates are conditional on the item still being `PENDING_REVIEW`.

### Measured feedback, not fake reinforcement learning

**Risk:** a small number of analyst verdicts is presented as model retraining or RL.

**Control:** reviewed findings feed quality metrics; small samples are labeled `EARLY_SAMPLE`. Automatic retraining is not claimed.

---

## 3. Identity and Secret Safety

### Per-workload EKS Pod Identity

**Risk:** a compromised Pod inherits broad node/shared AWS permissions.

**Control:** AWS access is attached to dedicated Kubernetes service accounts through EKS Pod Identity.

### Analyzer least privilege

**Risk:** the analyzer identity can access unrelated AWS resources.

**Control:** its role is scoped to the security queue, Bedrock analysis, finding persistence, and required telemetry/enrichment permissions.

### Status-Page least privilege

**Risk:** the web application can consume SQS events or call Bedrock directly.

**Control:** the runtime/reviewer role is limited to the exact managed RDS secret and required DynamoDB review operations; SQS/Bedrock access is denied.

### CI without long-lived AWS keys

**Risk:** static AWS credentials leak from GitHub.

**Control:** GitHub Actions obtains short-lived AWS credentials through OIDC and branch-scoped trust.

### CI has no EKS deployment rights

**Risk:** CI compromise immediately becomes cluster compromise.

**Control:** Status-Page CI can deliver to ECR but cannot deploy to EKS. Argo CD owns Kubernetes mutation.

### Runtime secrets outside Git

**Risk:** database credentials, Django secrets, or Dynu credentials enter the public repository or image.

**Control:** RDS credentials remain in Secrets Manager; Django and Dynu credentials are provided through Kubernetes Secrets outside Git; final runtime configuration is rendered into a memory-backed volume.

### Secret-safe automation output

**Risk:** Ansible password variables appear in logs.

**Control:** password-handling database tasks use `no_log: true`.

---

## 4. Kubernetes Runtime Safety

### Restricted privileges

**Risk:** application compromise gains unnecessary Linux/container privileges.

**Control:** non-root identities, dropped capabilities, `allowPrivilegeEscalation: false`, `RuntimeDefault` seccomp, read-only root filesystems where practical, and Pod Security Admission `restricted`.

### Health probes

**Risk:** Kubernetes keeps routing traffic to a process that exists but cannot serve real application requests.

**Control:** readiness exercises the Nginx-to-Django path while liveness verifies the serving process/listener remains alive.

### Multiple replicas and PDB

**Risk:** one Pod restart or voluntary disruption removes the application.

**Control:** multiple web replicas plus a Pod Disruption Budget.

### Revision-aware topology spread

**Risk:** a rolling deployment appears balanced only because an old revision exists in another Availability Zone.

**Control:** topology spread uses `matchLabelKeys: pod-template-hash`, so the current rollout must independently satisfy placement.

### Singleton scheduler

**Risk:** rolling updates temporarily run two RQ schedulers and duplicate scheduled work.

**Control:** one scheduler replica with `Recreate` strategy.

### Dedicated migration Job

**Risk:** every web replica races to alter the database schema at startup.

**Control:** migrations run once as an Argo CD `PreSync` Job before rollout.

### Node telemetry priority under Pod-density pressure

**Observed failure:** during final observability validation, node-exporter for one current node stayed Pending because the node had reached its Pod limit. Argo correctly remained `Progressing` while telemetry coverage was incomplete.

**Control:** node-exporter is assigned:

```yaml
prometheus-node-exporter:
  priorityClassName: system-cluster-critical
```

**Result:** node-level observability retains scheduling priority under Pod pressure instead of silently leaving a node unmonitored. After reconciliation, observability returned to `Synced / Healthy` and the final acceptance gate passed.

---

## 5. Data-Service Safety

### RDS PostgreSQL Multi-AZ

**Risk:** a single database host failure creates an extended application outage.

**Control:** Multi-AZ RDS, encrypted storage, automated backups, deletion protection, and managed credentials.

### Redis replication and failover

**Risk:** a single Redis node failure breaks queue/cache operation.

**Control:** two-node ElastiCache deployment, Multi-AZ placement, automatic failover, encryption at rest, TLS in transit, and snapshots.

### Persistent state outside Kubernetes

**Risk:** Pod/node lifecycle becomes coupled to database/cache durability.

**Control:** PostgreSQL and Redis are managed AWS services outside the cluster.

---

## 6. Software Supply-Chain Safety

### Pinned source and runtime base

**Risk:** rebuilds silently consume changed upstream source or a mutated base tag.

**Control:** Status-Page source and the Python production base image are pinned to exact revisions/digests.

### Multi-stage image

**Risk:** compilers/build headers increase the runtime attack surface.

**Control:** build tooling stays in the builder stage; the final image contains runtime dependencies only.

### Pinned GitHub Actions

**Risk:** a mutable Action tag changes underneath CI.

**Control:** all active third-party Actions are pinned by commit SHA. Terraform CI also validates both `dev` and `eks-dev`.

### Immutable ECR artifacts

**Risk:** a validated tag is overwritten later.

**Control:** immutable ECR tags plus Kubernetes deployment by digest.

### Trivy fail-closed gate

**Risk:** vulnerability scanning is informational only and a fixable CRITICAL issue reaches the release path.

**Control:** configured fixable CRITICAL findings fail delivery.

### CycloneDX SBOM

**Risk:** the released image's dependency composition cannot be reconstructed.

**Control:** CI generates and retains a CycloneDX SBOM for the release artifact.

### Safe stale-workflow rejection

**Risk:** a slow/retried CI run overwrites desired state for newer source.

**Control:** before editing GitOps state, CI fetches the remote branch and checks newer commits. Newer non-GitOps source causes a fail-closed stop.

This behavior was validated by a real stale workflow rejection.

### Idempotent CI reruns

**Risk:** retrying CI conflicts with immutable image tags or creates a second artifact for the same commit.

**Control:** CI detects/reuses the exact existing commit image and still regenerates security evidence/desired-state output.

---

## 7. GitOps and Drift Safety

### Argo self-heal

**Risk:** manual cluster changes silently become production truth.

**Control:** Argo CD reconciles live drift back to Git desired state.

### AppProject boundaries

**Risk:** an application gains unrestricted sources, destinations, or cluster resource access.

**Control:** Argo AppProjects constrain source repositories, destinations, and allowed resource kinds.

### Single authoritative desired state

**Risk:** duplicate production manifests drift independently.

**Control:** `gitops/eks-dev/` is authoritative; duplicate legacy production manifests were retired.

### Immutable runtime verification

**Risk:** Git points to one image while Kubernetes runs another.

**Control:** final acceptance compares the GitOps digest against Gunicorn and both application init-container images in EKS.

---

## 8. Observability Safety

### Complementary monitoring planes

**Risk:** forcing every signal into one tool creates blind spots or misleading ownership.

**Control:** Prometheus/Grafana cover Kubernetes/workload/node telemetry; CloudWatch covers WAF, ALB, AWS alarms, event-pipeline, and AI-quality signals. Argo health remains a separate GitOps control-plane signal.

### Git-managed dashboard

**Risk:** important dashboards exist only as manual Grafana configuration.

**Control:** the AEGIS Platform Health dashboard is stored in Git and reconciled by Argo CD.

### Grafana exposure boundary

**Risk:** direct public Grafana access bypasses application authorization.

**Control:** Grafana remains `ClusterIP`-only, anonymous access is disabled, and the AEGIS application enforces staff authorization before issuing a viewer-only identity.

---

## 9. ExternalDNS / Dynu Safety

### Dry-run final boundary

**Risk:** a final-project DNS controller accidentally changes the public record during validation.

**Control:** ExternalDNS final acceptance requires `--dry-run` to remain enabled.

### Exact resource scope

**Risk:** ExternalDNS discovers/manages unrelated ingresses or domains.

**Control:** namespace-scoped controller, exact Ingress label, exact hostname filter, and CNAME-only managed record type.

### Least-privilege Kubernetes RBAC

**Risk:** DNS automation can read application Secrets or delete Ingress resources.

**Control:** final acceptance proves intended Ingress read permission while Secret listing and Ingress deletion are denied.

### Webhook fail-closed validation

**Risk:** a malformed/unexpected ExternalDNS request targets arbitrary DNS names/services.

**Control:** the Dynu webhook refuses:

- any hostname other than `app.aegis-project.ddnsfree.com`;
- non-CNAME records;
- targets outside `.elb.amazonaws.com`;
- invalid TTL boundaries;
- delete requests;
- ambiguous multiple existing managed CNAMEs.

### Credential isolation

**Risk:** the Dynu API key leaks into Git/logs or the webhook obtains unnecessary cluster identity.

**Control:** the key comes from a Kubernetes Secret, is never logged, and the webhook sidecar does not receive the Kubernetes service-account token. Only the ExternalDNS container receives a manually projected API token.

---

## 10. Repository and Acceptance Safety

### Local artifact exclusion

The repository excludes Terraform state/plans, local variable files, editor files, environment files, keys, virtual environments, Python caches, and identified local static-generation scratch artifacts.

### Historical/current architecture separation

**Risk:** Phase 1 EC2 documents/diagrams are mistaken for the final architecture.

**Control:** final documentation explicitly labels the old EC2/Ansible material as historical and provides a dedicated final EKS diagram set.

### Reproducible final acceptance gate

**Risk:** the project is declared "done" based on screenshots or memory rather than a current runtime check.

**Control:** `scripts/final-acceptance.sh` fails closed unless repository, Terraform, GitOps render, Argo health, rollouts, DNS safety, RBAC, digest consistency, multi-AZ placement, and public HTTPS health all pass.

Accepted result:

```text
AEGIS TECHNICAL VALIDATION: COMPLETE (12 checks passed)
```

---

## Remaining Hardening Opportunities

These would improve production maturity but are **not required for the validated final claims**:

- sign/attest container images and verify signatures before deployment;
- add dedicated secret scanning such as Gitleaks to CI;
- pin the Nginx sidecar by digest;
- activate and validate Kubernetes NetworkPolicy after confirming VPC CNI policy enforcement;
- split Status-Page runtime and reviewer AWS identities;
- harden Argo CD administration and consider HA Argo on a larger cluster;
- perform formal RDS/DynamoDB/Redis restore exercises and define measured RTO/RPO;
- enable/validate Status-Page web HPA under production-style load;
- expand the human-reviewed AI sample before making stronger quality claims;
- move ExternalDNS from dry-run to live writes only after an explicit DNS cutover decision and rollback plan;
- enable branch protection and require CI on `main`;
- sign final release/tag or add artifact attestation.
