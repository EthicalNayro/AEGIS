# Phase 1.1 — Platform Modernization

## Status

**Complete — deployed and validated end to end.**

Phase 1.1 modernized the original AEGIS server-oriented foundation into a container-native AWS platform while preserving the core Status-Page application requirements and the project's earlier security-processing work.

The final showcase environment runs on Amazon EKS with managed PostgreSQL/Redis, secure HTTPS ingress, GitOps delivery, AI-assisted security analysis, human review, and production-style resilience controls.

---

## Why the Modernization Exists

The original Phase 1 foundation proved:

- Terraform-managed AWS networking;
- private PostgreSQL and Redis;
- Ansible-managed application configuration;
- Django, Gunicorn, RQ, PostgreSQL, Redis, and Nginx integration;
- explicit network boundaries;
- repeatable host configuration.

The modernization keeps those application responsibilities but replaces the final runtime model with Kubernetes and managed AWS services.

After the migration was accepted, the superseded EC2/Ansible implementation was removed from the active source tree. Its evolution remains auditable in Git history and the labeled historical evidence set.

---

## Implemented Architecture

```text
                         GitHub
                            |
                    GitHub Actions CI
                            |
                  AWS OIDC authentication
                            |
            +---------------+----------------+
            |                                |
            v                                v
      Amazon ECR                     GitOps desired state
                                              |
                                              v
                                           Argo CD
                                              |
                                              v
Internet -> ACM -> ALB -> WAF -> Amazon EKS (private workers)
                                  |       |       |
                                  |       |       +--> RQ scheduler
                                  |       +----------> RQ workers
                                  +------------------> Status-Page web
                                  |
                                  +--> RDS PostgreSQL Multi-AZ
                                  +--> ElastiCache Redis Multi-AZ/TLS

WAF -> CloudWatch -> EventBridge -> SQS -> Analyzer -> Bedrock -> DynamoDB
                                                         |
                                                         v
                                                  Human Review
                                                         |
                                                         v
                                                AI Quality Metrics
```

---

## Network Design

The modern environment uses VPC `10.10.0.0/16` across two Availability Zones.

Each Availability Zone contains:

- a public subnet;
- a dedicated EKS control-plane subnet;
- a private EKS node/Pod subnet;
- a private data subnet.

The design uses NAT egress per Availability Zone and keeps worker nodes/data services private.

The larger EKS node/Pod subnet ranges provide address space for AWS VPC CNI Pod IP allocation. Dedicated control-plane subnets reduce address contention with application workloads.

---

## EKS Platform

Implemented capabilities include:

- Amazon EKS;
- EKS Managed Node Group baseline;
- private worker nodes;
- nodes across two Availability Zones;
- AWS VPC CNI;
- EKS Pod Identity Agent;
- Metrics Server;
- control-plane logging;
- Pod Security Admission in `restricted` mode;
- workload-specific service accounts and IAM roles;
- readiness/liveness probes;
- resource requests/limits;
- Pod Disruption Budgets;
- topology-spread constraints;
- validated Karpenter scaling with Spot and On-Demand capacity.

Karpenter was originally considered future work but was later implemented and validated after the baseline EKS platform became stable.

---

## Managed Data Services

The final runtime keeps persistent data outside Kubernetes.

### RDS PostgreSQL

- PostgreSQL 16;
- Multi-AZ;
- encrypted storage;
- backups;
- deletion protection;
- private subnets;
- AWS-managed master secret;
- database logs enabled.

### ElastiCache Redis

- Redis 7.1;
- two nodes;
- Multi-AZ;
- automatic failover;
- encryption at rest;
- TLS in transit;
- snapshot retention.

This preserves the original application requirement for PostgreSQL and Redis while improving operational resilience.

---

## Status-Page on Kubernetes

The application deployment includes:

- multiple web replicas;
- Gunicorn;
- unprivileged Nginx sidecar;
- ClusterIP Service;
- RQ worker deployment;
- singleton RQ scheduler;
- Pod Disruption Budgets;
- revision-aware topology spread;
- secure container contexts;
- runtime config rendering;
- managed secrets;
- dedicated migration Job.

The public path is:

```text
Internet
 -> HTTPS / ACM
 -> ALB
 -> AWS WAF
 -> Ingress
 -> Status-Page Service
 -> Nginx
 -> Gunicorn
 -> Django
```

---

## GitHub Actions and GitOps

The final delivery model is not direct CI/CD to Kubernetes.

GitHub Actions performs CI and artifact delivery:

- source validation;
- multi-stage image build;
- Trivy scan and CRITICAL gate;
- CycloneDX SBOM;
- OIDC authentication;
- immutable ECR publish/reuse;
- GitOps digest update.

Argo CD performs continuous delivery to EKS.

This means the CI role requires no EKS permissions.

The Argo CD Application uses automated sync, pruning, self-heal, and project boundaries. Database migrations run as a `PreSync` hook before rollout.

---

## Safe Delivery Enhancements

The final workflow includes safeguards added during implementation:

- immutable image tags and digest deployment;
- idempotent ECR reuse on rerun;
- exact pinned GitHub Action SHAs;
- pinned base image digest;
- SBOM evidence;
- safe synchronization with the latest GitOps branch;
- fail-closed rejection when a stale workflow detects newer non-GitOps source changes.

The stale-run protection was exercised by an actual workflow failure and then validated by a successful workflow at the updated HEAD.

---

## Security Event Modernization

The project also added a real-time WAF-driven analysis path:

```text
WAF BlockedRequests
 -> CloudWatch Alarm
 -> EventBridge
 -> SQS
 -> AEGIS Analyzer on EKS
 -> Bedrock Nova Pro
 -> validated structured result
 -> DynamoDB
 -> Human Review
 -> AI Quality Metrics
```

Reliability controls include SQS buffering, DLQ redrive, per-message visibility extension, ACK-after-persistence, and idempotent DynamoDB writes.

---

## AI Governance

Amazon Bedrock is used for security analysis, but the design does not grant autonomous control.

Telemetry is treated as untrusted input, model output is parsed and validated, and findings enter a human-review workflow.

Human verdicts are used to calculate AI-quality metrics. This is a measured feedback loop, not reinforcement learning or automatic retraining.

---

## Implementation Milestones — Final State

| Milestone | Result |
|---|---|
| Architecture and permissions | ✅ Complete |
| Multi-AZ VPC | ✅ Complete |
| EKS platform | ✅ Complete |
| ECR/container packaging | ✅ Complete |
| Managed PostgreSQL/Redis | ✅ Complete |
| Kubernetes workloads | ✅ Complete |
| HTTPS/ALB/WAF | ✅ Complete |
| Security event pipeline | ✅ Complete |
| Bedrock analyzer | ✅ Complete |
| Human review / AI quality | ✅ Complete |
| GitHub OIDC secure CI | ✅ Complete |
| Argo CD GitOps | ✅ Complete |
| PreSync migrations | ✅ Complete |
| Karpenter scaling | ✅ Complete |
| End-to-end validation | ✅ Complete |

---

## Explicit Non-Goals / Boundaries

The final modernization does not claim:

- autonomous incident remediation;
- multi-region Kubernetes;
- HA Argo CD;
- active production NetworkPolicy enforcement;
- service mesh;
- cryptographic image signing/attestation;
- production Status-Page HPA.

These are possible future extensions, not missing hidden dependencies.

---

## Outcome

Phase 1.1 successfully transformed the original deployment into a production-style AWS platform with reproducible infrastructure, private Kubernetes compute, managed stateful services, secure software delivery, GitOps reconciliation, observability, AI-assisted security analysis, and explicit human governance.
