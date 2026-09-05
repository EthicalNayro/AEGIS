# Disaster Recovery Posture

## Scope

This document describes the supported EKS-based showcase state.

AEGIS has meaningful recovery building blocks and multi-AZ resilience, but it does **not** claim a fully exercised disaster-recovery program. In particular, there is no validated cross-region recovery, no automated full-environment restore workflow, and no formal restore-drill evidence.

## What Is Resilient Today

### Application compute

The Status-Page web tier runs multiple replicas across Availability Zones and is declared through GitOps. Kubernetes can recreate failed Pods, while Argo CD can reconcile workload drift back to Git.

Karpenter capacity recovery was validated during Pod-density pressure. This is node/workload resilience, not a substitute for regional disaster recovery.

### PostgreSQL

RDS PostgreSQL provides:

- Multi-AZ deployment;
- encrypted storage;
- seven-day automated backup retention;
- AWS-managed master credentials;
- deletion protection;
- private networking.

These controls reduce recovery risk for database host failure and provide a managed backup window. AEGIS does not claim that a complete application restore from RDS backup has been formally exercised end to end.

### Redis

ElastiCache Redis provides:

- two-node replication;
- Multi-AZ placement;
- automatic failover;
- encryption at rest;
- TLS in transit;
- snapshot retention.

Redis is treated as a managed cache/queue dependency, not as the authoritative findings database.

### Security findings

DynamoDB findings use server-side encryption and point-in-time recovery. Idempotent incident IDs and conditional writes also make replay safer after interrupted event processing.

### Security-event transport

SQS decouples security-event production from analysis, and a dead-letter queue isolates repeatedly failing messages. Analyzer ACK occurs only after finding persistence succeeds.

## Rebuild Sources of Truth

The recoverable control-plane sources are:

```text
Git repository
   |
   +--> Terraform -> AWS infrastructure definition
   |
   +--> GitOps manifests -> Kubernetes desired state
   |
   +--> immutable ECR image digests -> application artifacts
   |
   `--> Argo CD -> workload reconciliation
```

The final application desired state is under:

```text
gitops/eks-dev/
```

The Status-Page image is deployed by immutable ECR digest, so a rollback or rebuild can reference an exact previously validated artifact rather than a mutable tag.

## Secret Recovery Boundary

Secrets are deliberately not reconstructed from Git:

- RDS master credentials are managed by AWS Secrets Manager;
- the Django `SECRET_KEY` is supplied as a Kubernetes Secret outside the public repository;
- the Dynu API key is supplied through a Kubernetes Secret and is not committed.

A full environment rebuild therefore requires restoring or recreating these external secret inputs through an authorized operator process.

## Failure Scenarios

| Failure | Current recovery posture |
|---|---|
| Individual Pod failure | Kubernetes recreates the Pod; probes prevent unhealthy traffic |
| Voluntary node disruption | multiple replicas, topology spread, and PDB reduce service interruption |
| Node capacity pressure | Karpenter recovery validated; critical node telemetry receives scheduling priority |
| Single-AZ database infrastructure failure | RDS Multi-AZ provides managed failover behavior |
| Redis primary/node failure | managed replication and automatic failover |
| Analyzer interruption | SQS buffering preserves pending events; DLQ isolates poison messages |
| Accidental finding-table update | DynamoDB PITR provides a recovery mechanism |
| Bad application release | restore a previously validated immutable digest in Git and let Argo reconcile |
| Entire EKS cluster loss | infrastructure/workloads are declarative, but full cluster rebuild has not been formally timed or restore-tested |
| Region loss | not implemented; AEGIS is single-region |

## Explicitly Unvalidated

AEGIS does **not** claim:

- multi-region active/active or warm-standby recovery;
- a measured RTO or RPO;
- a completed RDS restore drill;
- a completed DynamoDB PITR restore drill;
- a completed Redis snapshot restore drill;
- AWS Backup service integration;
- automated Terraform state disaster recovery;
- HA Argo CD across a regional failure;
- automated secret recreation after total environment loss.

These are documented gaps rather than implied production guarantees.

## Recommended Restore Exercise

A future formal DR exercise should prove, in order:

1. restore or provision the AWS infrastructure from the reviewed Terraform revision;
2. recover required external secrets through the authorized secret-management path;
3. restore the database to a controlled recovery point;
4. reconcile `gitops/eks-dev/` through Argo CD;
5. verify immutable application digest consistency;
6. validate RDS/Redis connectivity and migrations;
7. run `scripts/final-acceptance.sh`;
8. record elapsed recovery time and data-loss window.

Until that exercise exists, the accurate claim is **multi-AZ resilience plus declarative rebuild capability**, not fully validated disaster recovery.
