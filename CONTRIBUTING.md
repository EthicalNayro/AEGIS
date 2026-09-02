# Contributing to AEGIS

AEGIS is a security-focused final project. Contributions are welcome when they keep the validated architecture, trust boundaries, and evidence trail intact.

## Before you begin

1. Read the [architecture](docs/architecture.md), [security model](docs/security.md), and [architecture decisions](docs/architecture-decisions.md).
2. Open or reference an issue that states the problem, proposed scope, and security impact.
3. Keep changes focused. Do not combine application, infrastructure, and documentation refactors unless the work genuinely requires them.

## Non-negotiable invariants

Changes must not:

- give GitHub Actions direct EKS deployment permissions;
- replace immutable image digests with mutable production tags;
- commit credentials, Terraform state, plan files, kubeconfig, generated secrets, or analyst data;
- weaken authentication, CSRF protection, staff-only analyst access, or Grafana authorization;
- enable anonymous Grafana access or expose Grafana through a separate public ingress;
- allow AI output to trigger autonomous remediation;
- acknowledge an SQS message before a finding is safely persisted;
- bypass DynamoDB conditional writes for first review or idempotent finding creation;
- broaden Kubernetes/IAM permissions without a documented reason;
- claim a capability as validated without reproducible evidence.

## Development workflow

1. Create a focused branch from the current target branch.
2. Make the smallest change that completely solves the problem.
3. Add or update tests for changed behavior.
4. Run the relevant validation locally.
5. Update architecture, security, deployment, and evidence documentation when a claim or boundary changes.
6. Open a pull request using the repository template.

## Validation expectations

Choose the checks that match the change:

```bash
# Python security-processing core
cd aegis
python -m pytest -v

# AEGIS plugin contract checks
python -m compileall status-page/statuspage/aegis_review

# Terraform
terraform fmt -check -recursive terraform
terraform -chdir=terraform/environments/eks-dev init -backend=false
terraform -chdir=terraform/environments/eks-dev validate

# GitOps render
kubectl kustomize gitops/eks-dev
```

Container, Trivy, SBOM, OIDC, ECR, and GitOps synchronization checks are enforced by GitHub Actions for the delivery path.

## Pull-request checklist

- [ ] The change is scoped and explained.
- [ ] Security and failure modes were considered.
- [ ] Tests cover new or changed behavior.
- [ ] No credentials, runtime data, or generated state were added.
- [ ] Documentation reflects the resulting architecture.
- [ ] New claims are backed by evidence.
- [ ] GitOps remains the production source of truth.

## Documentation style

- Prefer exact, verifiable language over marketing claims.
- Separate validated behavior from planned work.
- Record intentional limitations rather than hiding them.
- Never include credentials, internal tokens, private keys, full sensitive logs, or customer/analyst data in screenshots.

## Reporting security issues

Do not open a public issue containing exploit details, credentials, or sensitive infrastructure data. Follow [SECURITY.md](SECURITY.md) instead.
