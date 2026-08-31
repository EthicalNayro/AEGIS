# Deployment

## Overview

The final AEGIS deployment model separates **CI** from **CD**.

```text
Developer
   |
GitHub
   |
GitHub Actions CI
   |
   +--> validation
   +--> container build
   +--> Trivy
   +--> SBOM
   +--> ECR
   +--> GitOps digest update
            |
            v
          Argo CD
            |
            v
            EKS
```

GitHub Actions does not run `kubectl` and does not receive EKS permissions. Argo CD continuously reconciles Kubernetes state from Git.

---

## Environment

Final showcase environment:

```text
AWS region: us-east-1
Terraform environment: terraform/environments/eks-dev
EKS cluster: aegis-eks-dev
Kubernetes namespace: aegis-system
GitOps path: gitops/eks-dev
Deployment branch: phase-1-1/platform-modernization
```

The original `terraform/environments/dev` and Ansible-based EC2 deployment remain in the repository as historical project phases, not as the final Status-Page runtime.

---

## Infrastructure Provisioning

Terraform owns the AWS infrastructure for `eks-dev`, including the VPC, EKS foundation, managed data services, ECR, WAF/observability resources, event queues, DynamoDB findings storage, and workload IAM roles.

From the environment directory:

```bash
cd terraform/environments/eks-dev
terraform fmt -check -recursive
terraform validate
```

Infrastructure changes are intentionally separate from the Status-Page application delivery workflow.

---

## Status-Page Container Build

The Status-Page image uses a multi-stage Docker build.

The builder stage contains compilation/build tooling and produces the Python virtual environment. The runtime stage starts again from the pinned Python base-image digest and installs only runtime OS dependencies before copying the virtual environment and application.

This keeps compiler and development packages out of the final runtime image.

The application source is based on a pinned upstream Status-Page revision and includes the native AEGIS review plugin plus limited intentional UI/template overrides.

---

## GitHub Actions CI

The secure Status-Page workflow performs two major jobs.

### Validate & Build

- checks out the exact repository revision;
- verifies required build inputs;
- validates AEGIS plugin Python;
- validates the runtime configuration renderer;
- builds the container;
- runs a Trivy vulnerability report;
- enforces a fail-closed CRITICAL vulnerability gate.

### Publish Immutable Image

- authenticates to AWS using GitHub OIDC;
- verifies AWS identity;
- logs in to ECR;
- derives an immutable image tag from the Git commit;
- reuses an existing exact image on safe reruns, otherwise builds it;
- runs the production-image Trivy gate;
- generates a CycloneDX SBOM;
- uploads SBOM evidence;
- pushes the image to ECR when required;
- resolves the immutable ECR digest;
- safely synchronizes the GitOps branch;
- updates the GitOps image digest;
- commits the desired-state change back to Git.

Third-party Actions are pinned by commit SHA.

---

## GitHub OIDC

CI uses short-lived AWS credentials from GitHub's OIDC token rather than repository access keys.

```text
GitHub Actions
   |
   | OIDC token
   v
AWS STS
   |
   v
AEGIS GitHub CI IAM role
```

The trust policy is scoped to the exact repository and deployment branch. The role can deliver to ECR but cannot deploy directly to EKS and cannot pass arbitrary IAM roles.

---

## Immutable Delivery

The deployment uses ECR image digests rather than mutable runtime tags.

Conceptually:

```text
git-<commit>
    |
    v
ECR immutable image
    |
    v
sha256:<digest>
    |
    v
gitops/eks-dev/kustomization.yaml
```

Argo CD therefore deploys the exact artifact that passed the CI security gates.

The final runtime verification explicitly compared the GitOps digest with the image digest in the EKS Deployment.

---

## Safe GitOps Synchronization

A workflow can become stale while it is building. AEGIS protects against that race before mutating desired state.

Before updating `gitops/eks-dev/kustomization.yaml`, CI fetches the current remote branch and inspects commits newer than the workflow's source revision.

- If the only newer change is the previous GitOps digest update, the rerun can safely continue.
- If newer non-GitOps source exists, the workflow fails closed.

This protection was exercised by a real workflow run: a stale UI delivery was rejected after a newer security-tooling commit advanced the branch. A manually triggered run at the new HEAD then completed successfully.

---

## Argo CD Continuous Delivery

Argo CD watches the deployment branch and `gitops/eks-dev` path.

The Application enables:

- automated sync;
- pruning;
- self-heal;
- `CreateNamespace=false`;
- `PruneLast`;
- `ApplyOutOfSyncOnly`;
- server-side apply.

The AppProject restricts source, destination, and allowed resource kinds.

`gitops/eks-dev/` is the authoritative production desired state for the Status-Page application. Duplicate legacy production manifests were removed from competing source-of-truth locations.

---

## Database Migration

Django migrations execute through a dedicated Kubernetes Job annotated as an Argo CD `PreSync` hook.

```text
Git desired state
   |
Argo sync
   |
PreSync migration Job
   |
Django migrate --noinput
   |
Hook succeeds
   |
Application rollout
```

The Job uses the same immutable application image, service account, runtime configuration renderer, security context, and secret boundaries as the application workload.

This prevents every web replica from racing to perform schema migration during startup.

---

## Runtime Workloads

The GitOps composition includes:

- Status-Page web Deployment;
- ClusterIP Service on `8080`;
- Pod Disruption Budget;
- Status-Page service account;
- RQ worker Deployment and PDB;
- singleton RQ scheduler;
- Ingress for the public ALB;
- unprivileged Nginx configuration;
- runtime configuration renderer;
- migration Job.

The runtime ConfigMap and the sensitive Kubernetes Secret are intentionally not stored in the public repository.

---

## Public Traffic

The production request path is:

```text
HTTP :80 -> redirect to HTTPS
HTTPS :443
  -> ACM
  -> ALB
  -> WAF
  -> Ingress
  -> Service :8080
  -> Nginx
  -> Gunicorn
  -> Django
```

Health endpoint:

```text
https://app.aegis-project.ddnsfree.com/healthz
```

Expected response:

```text
HTTP 200
ok
```

---

## Rollback Model

Because the deployed artifact is identified by digest in Git, rollback is an auditable Git operation: restore the previously validated digest in desired state and allow Argo CD to reconcile.

Application deployment is therefore reproducible independently of a developer workstation.

---

## Original Ansible Deployment

Ansible remains part of the project and demonstrates host configuration for the earlier EC2 foundation. It is still syntax-validated and its secret-bearing database tasks use `no_log: true`.

It is no longer the final application delivery mechanism for the `eks-dev` showcase environment.
