# Architecture Safety Enhancements

This document records the failure modes AEGIS was explicitly designed to tolerate or fail safely around. These controls are important because the project is not only a collection of AWS services; it is an attempt to make the interactions between those services predictable under retries, restarts, stale workflows, malformed AI output, and infrastructure drift.

---

## Security Event Reliability

### SQS buffering

**Risk:** a burst of WAF security events arrives faster than the analyzer can process them.

**Control:** EventBridge delivers to SQS rather than invoking the analyzer synchronously. Producers and consumers are decoupled and events remain durable while the analyzer catches up.

### Dead-letter queue

**Risk:** a malformed or repeatedly failing event is retried forever and blocks useful work.

**Control:** the main security queue has a DLQ and bounded redrive count. Poison events are isolated for investigation instead of disappearing or retrying indefinitely.

### ACK after successful persistence

**Risk:** an event is deleted from the queue before its finding is durable.

**Control:** the analyzer deletes/acknowledges the SQS message only after successful finding persistence.

### Idempotent finding creation

**Risk:** retries create duplicate findings.

**Control:** DynamoDB uses a deterministic incident identity and conditional `PutItem`. A replay is safe because an already-persisted incident cannot be silently duplicated.

### DynamoDB PITR

**Risk:** accidental or faulty updates damage finding history.

**Control:** point-in-time recovery is enabled on the findings table.

---

## AI Safety

### Untrusted telemetry boundary

**Risk:** attacker-controlled WAF telemetry contains prompt-like content intended to manipulate the model.

**Control:** telemetry is treated as data, separated from analyzer instructions, and never granted authority to redefine system behavior.

### Structured output validation

**Risk:** the model returns malformed, incomplete, or unexpected output.

**Control:** Bedrock output must parse as the expected structured JSON and pass application validation before persistence.

### Human governance

**Risk:** a model classification is treated as fact and triggers unsafe automation.

**Control:** findings are reviewable and remain advisory. Analysts mark them `CORRECT` or `INCORRECT`; AEGIS does not autonomously remediate infrastructure.

### Conditional review updates

**Risk:** two reviewers or duplicate requests overwrite an already-reviewed finding.

**Control:** review writes are conditional on the item remaining in `PENDING_REVIEW` state.

### Measured feedback, not fake RL

**Risk:** presenting a handful of verdicts as a trained reinforcement-learning system overstates capability.

**Control:** AEGIS computes human-verified quality metrics and labels small samples `EARLY_SAMPLE`. No automatic retraining is claimed.

---

## Identity and Secret Safety

### Per-workload Pod Identity

**Risk:** one compromised Pod can reuse a broad node or shared AWS identity.

**Control:** AWS permissions are attached to dedicated Kubernetes service accounts through EKS Pod Identity and scoped to expected namespace/service-account identities.

### CI without long-lived AWS keys

**Risk:** static GitHub AWS credentials leak or remain valid indefinitely.

**Control:** GitHub Actions obtains temporary AWS credentials through OIDC with branch-scoped trust.

### CI has no EKS deployment rights

**Risk:** compromise of the build pipeline immediately becomes cluster compromise.

**Control:** the Status-Page CI role is limited to ECR delivery and required AWS checks. Continuous delivery is delegated to Argo CD.

### Managed runtime secrets

**Risk:** database credentials or Django secret material are committed into a public repository or baked into images.

**Control:** RDS credentials remain in Secrets Manager, the Django secret is provided outside Git, and runtime configuration is rendered into a memory-backed volume.

### Ansible log suppression

**Risk:** password variables appear in automation output.

**Control:** PostgreSQL user-creation tasks that handle passwords use `no_log: true`.

---

## Kubernetes Runtime Safety

### Restricted privileges

**Risk:** application compromise gains unnecessary Linux/container privileges.

**Control:** workloads use non-root identities, dropped capabilities, no privilege escalation, `RuntimeDefault` seccomp, and read-only root filesystems where practical. Namespace Pod Security Admission is set to `restricted`.

### Readiness and liveness semantics

**Risk:** a process exists but cannot serve real application traffic.

**Control:** readiness checks exercise the Nginx-to-Django request path, while liveness checks confirm the Nginx listener remains alive.

### Multiple replicas and PDB

**Risk:** a single Pod restart or voluntary disruption removes the application.

**Control:** the web tier runs multiple replicas and has a Pod Disruption Budget.

### Revision-aware topology spread

**Risk:** a rolling deployment appears balanced only because old revision Pods are still present in another Availability Zone.

**Control:** topology spread uses `matchLabelKeys: pod-template-hash`, so placement decisions apply to the current rollout revision.

### Singleton scheduler

**Risk:** rolling updates temporarily run two RQ schedulers, causing duplicate scheduled work.

**Control:** the scheduler is a singleton and uses `Recreate` strategy.

### Dedicated migrations

**Risk:** every web replica races to mutate the database schema during startup.

**Control:** migrations run in a dedicated Argo CD `PreSync` Job before workload rollout.

---

## Data-Service Safety

### Managed PostgreSQL Multi-AZ

**Risk:** a single database host failure causes extended outage.

**Control:** RDS PostgreSQL uses Multi-AZ, backups, encrypted storage, and deletion protection.

### Redis replication and failover

**Risk:** a single Redis node failure breaks queues/cache state.

**Control:** ElastiCache Redis uses two nodes, Multi-AZ placement, automatic failover, encryption at rest, TLS in transit, and snapshots.

### Persistent data outside Kubernetes

**Risk:** application Pod/node lifecycle becomes coupled to database/cache durability.

**Control:** PostgreSQL and Redis are managed AWS services outside the cluster.

---

## Software Supply-Chain Safety

### Pinned upstream and base image

**Risk:** rebuilds silently consume changed upstream source or a newly-mutated base tag.

**Control:** Status-Page source and the Python base image are pinned to exact revisions/digests.

### Multi-stage build

**Risk:** compilers and development headers increase runtime attack surface.

**Control:** build dependencies remain in a builder stage; the final runtime stage contains only required runtime packages and the built virtual environment.

### Pinned GitHub Actions

**Risk:** a mutable Action tag changes underneath the pipeline.

**Control:** third-party Actions are pinned by commit SHA.

### Immutable ECR artifacts

**Risk:** an image tag is overwritten after validation.

**Control:** ECR tags are immutable and Kubernetes deploys by digest.

### Trivy fail-closed gate

**Risk:** a known fixable CRITICAL vulnerability reaches production because scanning is informational only.

**Control:** the workflow fails before publication when the configured CRITICAL gate is violated.

### CycloneDX SBOM

**Risk:** the exact dependency composition of a released image cannot be reconstructed later.

**Control:** CI generates and retains a CycloneDX SBOM for the release image.

---

## GitOps and Drift Safety

### Argo self-heal

**Risk:** manual cluster changes silently become the new production state.

**Control:** Argo CD reconciles drift back to declared Git state.

### AppProject boundaries

**Risk:** an application definition gains unrestricted access to arbitrary cluster resources or destinations.

**Control:** source repositories, destinations, and allowed resource kinds are constrained by an Argo CD AppProject.

### Safe stale-workflow rejection

**Risk:** a slow/retried CI job overwrites desired state for newer application code.

**Control:** before editing GitOps state, CI fetches the remote branch and inspects newer commits. Newer non-GitOps source changes cause a fail-closed stop.

This control was proven by a real failed delivery: an older UI workflow refused to update GitOps after a newer security-tooling commit advanced the branch. A new workflow at current HEAD then succeeded.

### Idempotent CI reruns

**Risk:** retrying a workflow creates conflicting images or fails because immutable artifacts already exist.

**Control:** CI checks for the exact commit-tagged image. When it exists, the workflow reuses that artifact and still regenerates security evidence and desired-state output.

### Single authoritative production desired state

**Risk:** multiple copies of production manifests drift independently.

**Control:** `gitops/eks-dev/` is authoritative for the Status-Page production workload; duplicate legacy production manifests were retired.

---

## Repository Safety

### Source-of-truth audit

Terraform, Kubernetes/GitOps, analyzer code, human-review scripts, and Status-Page UI changes were audited for local-only/untracked source and committed before feature freeze.

### Local artifact exclusion

The repository ignores Terraform state/plans, local variable files, editor swaps/backups, environment files, keys, virtual environments, Python caches, and other local artifacts.

### Final secret scan

Tracked files were scanned for obvious AWS access keys, private keys, and likely hardcoded password literals. Ansible Jinja password-variable references were intentionally distinguished from plaintext password values.

---

## Remaining Hardening Opportunities

The following are useful future improvements but are not required to support the validated final claims:

- sign/attest container images and verify signatures before deployment;
- add dedicated secret-scanning tooling such as Gitleaks to CI;
- pin the Nginx sidecar by digest;
- activate and validate Kubernetes NetworkPolicy enforcement after confirming the VPC CNI policy mode;
- split Status-Page runtime and reviewer AWS identities;
- harden Argo CD administrative access further and consider HA Argo on a larger cluster;
- perform formal backup-restore exercises;
- expand application autoscaling and load testing;
- expand human-reviewed sample size before drawing conclusions about AI quality.
