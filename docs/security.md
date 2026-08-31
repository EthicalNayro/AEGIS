# Security

## Security Model

AEGIS uses defense in depth across network boundaries, workload identity, software delivery, application runtime, security telemetry, and AI governance.

The final platform intentionally minimizes direct trust relationships. Public traffic terminates at the ALB/WAF boundary, Kubernetes workers remain private, managed data services are private, CI does not receive cluster access, and AI output is never treated as authoritative without validation and human review.

---

## Internet Edge

The public path is:

```text
Internet
  -> HTTPS :443
ACM
  -> ALB
AWS WAF
  -> Kubernetes Ingress
Status-Page Service
  -> private EKS Pods
```

Controls include:

- ACM-managed TLS certificate;
- HTTP-to-HTTPS redirect;
- AWS WAF managed rule groups;
- Amazon IP reputation filtering;
- known-bad-input protections;
- per-IP rate limiting;
- WAF block logging to CloudWatch Logs.

A controlled XSS-style query was used to prove WAF enforcement and returned HTTP `403`.

---

## Private Compute and Data

EKS worker nodes and application Pods run in private subnets with no public IPs.

RDS PostgreSQL and ElastiCache Redis are private and are not exposed directly to the Internet.

RDS uses encryption, backups, Multi-AZ deployment, and deletion protection. Redis uses encryption at rest, TLS in transit, Multi-AZ replication, automatic failover, and snapshots.

---

## Kubernetes Workload Security

The `aegis-system` namespace uses Pod Security Admission in `restricted` mode.

Workloads apply controls such as:

- non-root user/group IDs;
- `allowPrivilegeEscalation: false`;
- `RuntimeDefault` seccomp;
- dropped Linux capabilities;
- read-only root filesystems where practical;
- explicit CPU/memory requests and limits;
- readiness and liveness probes;
- Pod Disruption Budgets;
- topology spread across Availability Zones;
- service-account token automount disabled where not required.

The unprivileged Nginx sidecar listens on port `8080` instead of requiring privileged port binding.

---

## AWS Workload Identity

AEGIS uses EKS Pod Identity for AWS access from Kubernetes workloads.

Examples include:

- the security analyzer role scoped to its namespace and service account;
- the Status-Page runtime/reviewer role scoped to the Status-Page service account;
- the AWS Load Balancer Controller identity.

The analyzer receives only the permissions it needs for its security pipeline. The Status-Page runtime can read the exact managed RDS secret and the DynamoDB finding data needed by the review UI; it does not receive SQS or Bedrock permissions.

No long-lived application AWS access keys are stored in the repository or container image.

---

## Secrets and Runtime Configuration

Sensitive values are not stored in Git.

The runtime configuration renderer reads managed secret material at startup and writes the final Django configuration to an in-memory volume with restrictive file permissions.

Controls include:

- RDS master credentials managed by AWS Secrets Manager;
- Django `SECRET_KEY` stored in a Kubernetes Secret created outside the public repository;
- no plaintext Terraform output for RDS credentials;
- repository ignore rules for Terraform state, local variable files, editor artifacts, keys, and environment files;
- Ansible database-user tasks marked `no_log: true` to reduce credential exposure in logs.

---

## Software Supply-Chain Security

The Status-Page delivery workflow includes:

- GitHub OIDC authentication to AWS;
- exact branch-scoped IAM trust;
- ECR-only CI permissions and no EKS access;
- pinned third-party GitHub Action commit SHAs;
- pinned Python base-image digest;
- multi-stage image build;
- immutable ECR tags;
- deployment by image digest;
- Trivy vulnerability scanning;
- fail-closed fixable-CRITICAL gate;
- CycloneDX SBOM generation and artifact retention;
- concurrency controls;
- idempotent image reuse on safe reruns;
- fail-closed GitOps synchronization when a workflow is stale.

The stale-workflow protection was validated in practice: an older UI delivery run was refused after a newer non-GitOps commit advanced the branch, preventing stale desired state from overwriting newer source.

---

## GitOps Security Boundary

GitHub Actions is CI, not the Kubernetes deployment authority.

```text
GitHub Actions
  -> ECR + Git desired-state update

Argo CD
  -> EKS reconciliation
```

The Argo CD Application is constrained by an AppProject with explicit source, destination, and resource-kind boundaries. Automated sync uses self-heal and pruning so drift is reconciled back to reviewed Git state.

Database migrations execute as a dedicated `PreSync` Job, keeping privileged schema-change behavior separate from the steady-state application process.

---

## Security Event Pipeline

The active WAF-driven security path is:

```text
WAF BlockedRequests
  -> CloudWatch Alarm
  -> EventBridge
  -> SQS
  -> AEGIS Analyzer
  -> Bedrock
  -> DynamoDB
  -> Human Review
```

SQS provides buffering between event production and analysis. A DLQ captures events that repeatedly fail processing.

The analyzer acknowledges a message only after persistence succeeds. DynamoDB conditional writes make processing idempotent when an event is replayed.

---

## AI Security and Governance

Telemetry can contain attacker-controlled strings and is treated as untrusted data.

AEGIS therefore:

- separates system instructions from telemetry;
- does not permit telemetry to redefine the analyzer's task;
- requests structured JSON from Bedrock;
- parses and validates model output before storing it;
- does not automatically execute remediation from model output;
- requires human analyst review for trust decisions;
- measures quality from reviewed findings instead of assuming model correctness.

The AI layer is advisory and governed, not autonomous.

---

## Human Review Separation

The review workflow supports `CORRECT` and `INCORRECT` verdicts, optional corrected classification, and analyst notes.

Updates are conditional on `PENDING_REVIEW`, preventing silent overwrite of a finding that has already been reviewed.

The current Status-Page IAM role acts as both runtime and reviewer identity because the application also needs the managed RDS secret. A future production refinement would split those duties into separate identities.

---

## Current Security Boundaries

The following are intentionally **not** claimed as active controls:

- autonomous remediation;
- Kubernetes NetworkPolicy enforcement;
- multi-region active/active architecture;
- HA Argo CD;
- cryptographic container signing/attestation;
- production-scale reviewer identity separation.

These remain future hardening opportunities rather than undocumented assumptions.
