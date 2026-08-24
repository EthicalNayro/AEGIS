# Phase 1.1 — Platform Modernization

## Status

**In progress — architecture defined, implementation not yet deployed.**

Phase 1.1 modernizes the original AEGIS platform foundation without rewriting the completed Phase 2 security-processing logic.

The original foundation remains the current working environment until the modernized platform has been deployed and validated end-to-end.

---

## Why this modernization exists

The original Phase 1 architecture established:

- AWS networking with Terraform;
- private PostgreSQL and Redis hosts;
- application deployment through Ansible;
- explicit Security Group boundaries;
- encrypted EC2 storage;
- private backend administration;
- working Django, Gunicorn, RQ, PostgreSQL, and Redis services.

That foundation proved the platform behavior, but the compute and deployment model is server-oriented.

Phase 1.1 moves the platform toward a scalable container-native operating model.

---

# Target Architecture

```text
                         GitHub
                            |
                 GitHub Actions CI/CD
                            |
                    OIDC authentication
                            |
                            v
                           AWS
                            |
            +---------------+---------------+
            |                               |
            v                               v
     Terraform Platform                   Amazon ECR
            |
            v
    +-------------------+
    |       VPC         |
    |   10.10.0.0/16    |
    +-------------------+
            |
      +-----+-----+
      |           |
      v           v
     AZ-A        AZ-B
      |           |
      +-----+-----+
            |
       Amazon EKS
            |
     +------+------+----------------+
     |             |                |
     v             v                v
 Django Pods    RQ Workers     AEGIS Worker
     |
     v
   ALB
     |
  Internet

EKS workloads
     |
     +-------------> RDS PostgreSQL
     |
     +-------------> ElastiCache Redis
```

---

# Network Design

The modernization uses a new VPC rather than modifying the currently deployed Phase 1 VPC in place.

```text
VPC: 10.10.0.0/16

Availability Zone A
├── Public Subnet
│   └── 10.10.0.0/24
│
├── EKS Control-Plane Subnet
│   └── 10.10.2.0/28
│
├── Private EKS Node / Pod Subnet
│   └── 10.10.16.0/20
│
└── Private Data Subnet
    └── 10.10.64.0/24


Availability Zone B
├── Public Subnet
│   └── 10.10.1.0/24
│
├── EKS Control-Plane Subnet
│   └── 10.10.2.16/28
│
├── Private EKS Node / Pod Subnet
│   └── 10.10.32.0/20
│
└── Private Data Subnet
    └── 10.10.65.0/24
```

The larger EKS node/Pod subnet ranges intentionally leave room for Kubernetes Pod IP allocation through the AWS VPC CNI.

The two small EKS control-plane subnets are reserved for EKS-managed network interfaces. Keeping them separate reduces address competition between control-plane ENIs and application workloads.

The existing Phase 1 VPC remains unchanged until migration validation is complete.

---

# Compute Model

## Current

```text
Application EC2
PostgreSQL EC2
Redis EC2
```

## Target

```text
Amazon EKS
├── Django / Gunicorn Deployment
├── RQ Worker Deployment
├── RQ Scheduler workload
└── AEGIS Security Worker Deployment

Amazon RDS PostgreSQL

Amazon ElastiCache Redis
```

The Kubernetes workloads are stateless where possible.

Persistent data is intentionally kept outside Kubernetes and delegated to managed AWS data services.

---

# EKS Initial Design

The first implementation will use:

- Amazon EKS;
- EKS Managed Node Groups;
- private worker nodes;
- nodes distributed across two Availability Zones;
- Kubernetes Deployments for application workloads;
- Kubernetes Services for internal discovery;
- AWS Load Balancer Controller for ingress;
- Horizontal Pod Autoscaler where appropriate;
- readiness and liveness probes;
- resource requests and limits;
- Pod Disruption Budgets;
- NetworkPolicies;
- dedicated workload identities.

Karpenter may be evaluated later after the initial EKS architecture is stable.

---

# Terraform Environment Strategy

The existing environment is not modified destructively.

```text
terraform/environments/

├── dev/
│   └── existing Phase 1 EC2 architecture
│
└── eks-dev/
    └── Phase 1.1 modernized architecture
```

The modernization follows a parallel-build strategy:

```text
Build new platform
      |
      v
Validate
      |
      v
Deploy workloads
      |
      v
Validate Phase 2 runtime
      |
      v
Cut over
      |
      v
Retire old EC2 platform
```

This reduces migration risk and preserves a known-good environment during the refactor.

---

# Terraform State

The target deployment model uses remote state rather than developer-local Terraform state.

Target:

```text
Amazon S3
├── encrypted Terraform state
├── versioning
└── state locking
```

The backend infrastructure is a bootstrap dependency and must exist before the main Terraform environment can use it.

---

# CI/CD Target

## Pull Request

```text
Pull Request
    |
    +--> terraform fmt
    |
    +--> terraform validate
    |
    +--> linting
    |
    +--> security scanning
    |
    +--> unit tests
    |
    +--> terraform plan
```

No infrastructure changes occur from a pull request.

---

## Main Branch Deployment

```text
Merge to main
     |
     v
GitHub Actions
     |
     v
AWS authentication through OIDC
     |
     v
Terraform Plan
     |
     v
GitHub Environment
Required Approval
     |
     v
Terraform Apply
```

The apply stage must never run automatically without the configured deployment approval gate.

Concurrent Terraform deployments must also be prevented.

---

# AWS Authentication

Long-lived AWS access keys must not be stored in GitHub.

Target authentication:

```text
GitHub Actions
      |
      | OIDC
      v
AWS STS
      |
      v
Deployment IAM Role
```

IAM bootstrap resources may need to be created outside the normal deployment pipeline when the active project role does not have permission to manage IAM identity providers or roles.

---

# Current Permission Readiness

The initial read-only permission check produced the following result:

| Capability | Current result |
|---|---|
| AWS STS session | Available |
| EKS list/read entry point | Available |
| EC2 networking reads | Available |
| IAM role read | Available |
| IAM OIDC provider listing | Blocked |
| ECR repository read | Available |
| RDS DB instance read | Blocked |
| ElastiCache cluster read | Blocked |
| S3 bucket listing | Available |
| KMS key listing | Available |

These checks confirm API visibility only.

They do **not** prove create, update, delete, or `iam:PassRole` permissions.

---

# Permission Prerequisites

Before infrastructure deployment, the AWS account must support the capabilities required for:

## EKS

- cluster lifecycle;
- managed node groups;
- EC2 networking dependencies;
- required service roles;
- role passing where required.

## GitHub OIDC

- an AWS OIDC identity provider for GitHub Actions;
- dedicated GitHub deployment roles;
- restricted trust policies.

## RDS

- DB subnet groups;
- PostgreSQL instance lifecycle;
- parameter/security configuration;
- required describe operations.

## ElastiCache

- subnet groups;
- Redis lifecycle;
- required describe operations.

## Terraform Backend

- S3 state object read/write;
- state locking;
- bucket encryption/versioning access.

---

# Migration Principles

Phase 1.1 follows these rules:

1. Do not destroy the existing Phase 1 platform before replacement validation.
2. Build the modernized platform in parallel.
3. Do not move persistent databases into Kubernetes.
4. Keep AWS credentials out of application containers.
5. Prefer workload-specific AWS identities.
6. Keep Kubernetes worker nodes private.
7. Treat GitHub Actions as the deployment control plane.
8. Require approval before Terraform apply.
9. Keep infrastructure changes reproducible through Terraform.
10. Preserve the existing Phase 2 processing boundaries during runtime migration.

---

# Implementation Milestones

## Milestone 0 — Architecture and permissions

- define target architecture;
- define migration strategy;
- document AWS permission gaps;
- define IAM/OIDC bootstrap requirements.

## Milestone 1 — Multi-AZ network

- create the new VPC;
- create two public subnets;
- create two dedicated EKS control-plane subnets;
- create two private EKS node/Pod subnets;
- create two private data subnets;
- configure routing and NAT strategy;
- add Kubernetes load-balancer subnet discovery tags.

## Milestone 2 — EKS platform

- create EKS cluster;
- create Managed Node Group;
- validate private node networking;
- configure cluster access;
- validate Kubernetes scheduling.

## Milestone 3 — Container registry and application packaging

- create ECR repositories;
- build application containers;
- build AEGIS worker container;
- push immutable image tags.

## Milestone 4 — Managed data services

- deploy RDS PostgreSQL;
- deploy ElastiCache Redis;
- configure private connectivity;
- migrate required schema/data.

This milestone is blocked until the AWS project identity receives the required RDS and ElastiCache permissions.

## Milestone 5 — Kubernetes workloads

- deploy Django/Gunicorn;
- deploy RQ Worker;
- deploy scheduler;
- deploy AEGIS Security Worker;
- configure health checks and resources;
- configure NetworkPolicies;
- validate Phase 2 incident processing from EKS.

## Milestone 6 — GitHub Actions delivery

- configure AWS OIDC bootstrap;
- configure remote Terraform state;
- implement PR validation and plan workflow;
- implement approval-gated apply workflow;
- protect concurrent deployments.

## Milestone 7 — Cutover

- validate application traffic;
- validate PostgreSQL and Redis connectivity;
- validate AEGIS event detection;
- validate incident persistence;
- update architecture documentation;
- retire the legacy EC2 workload architecture.

---

# Explicit Non-Goals During Initial Modernization

The first EKS migration does not immediately require:

- service mesh;
- multi-region Kubernetes;
- Karpenter;
- GitOps controllers;
- automated incident remediation;
- Phase 3 AI investigation.

Those capabilities can be evaluated after the platform modernization is stable.
