# Architecture Decisions

This document records the major architectural decisions introduced during Phase 2. The goal is to preserve the reasoning behind the implementation, not only the resulting code.

---

## ADR-001 — Paginated CloudTrail ingestion

**Status:** Accepted

### Context

A single CloudTrail `LookupEvents` response does not necessarily represent the complete requested time window. During development, relevant Security Group activity could be pushed outside the first result page by unrelated account activity.

### Decision

AEGIS follows CloudTrail `NextToken` pagination until the configured total event limit is reached or CloudTrail returns no additional page. Event-name filters are preserved across pages and collector-generated `LookupEvents` noise is removed.

### Consequences

The ingestion layer no longer assumes that one API response is complete. The configured `max_results` value remains an intentional upper bound.

---

## ADR-002 — At-least-once processing with idempotent persistence

**Status:** Accepted

### Context

The worker deliberately uses overlapping CloudTrail time windows to reduce the risk of missing delayed or previously unavailable events. The same source event may therefore be processed multiple times.

Exact-once polling semantics would add fragile state coordination and could create monitoring gaps.

### Decision

AEGIS uses at-least-once processing. Incident IDs are deterministic and PostgreSQL enforces uniqueness with the incident primary key and `ON CONFLICT DO NOTHING`.

### Consequences

Replay is expected and safe. Reliability is preferred over attempting exact-once event delivery.

---

## ADR-003 — Separate processing orchestration from runtime entry points

**Status:** Accepted

### Context

The initial manual prototype performed collection, normalization, detection, incident construction, persistence, and presentation inside one script.

### Decision

Reusable event orchestration lives in `SecurityEventPipeline`. Runtime entry points construct dependencies and manage lifecycle, while individual components retain their own responsibilities.

### Consequences

Manual scripts, continuous workers, and future runtimes can reuse the same processing path. Transport, detection, and persistence implementations can evolve independently.

---

## ADR-004 — Persistent worker checkpoints with safety overlap

**Status:** Accepted

### Context

A long-running security worker can stop because of development shutdowns, failures, or future deployments. Process-memory state would be lost after restart.

### Decision

AEGIS stores the last successful polling checkpoint in PostgreSQL. On restart, the worker calculates the elapsed gap and adds the configured lookback as a safety overlap. The checkpoint is saved only after successful pipeline execution.

### Consequences

A restart does not silently create an unmonitored time gap. Failed cycles do not advance the high-water mark. Recovery replay is safe because incident persistence is idempotent.

---

## ADR-005 — Explicit opt-in resource scope with fail-closed enforcement

**Status:** Accepted

### Context

CloudTrail can contain activity for resources and actors outside the intended AEGIS monitoring scope. Filtering by one hard-coded resource ID was useful for a lab but was not a scalable authorization boundary.

### Decision

Scope enforcement happens before detection. The current EC2 Security Group policy requires:

```text
AEGISMonitoring=enabled
```

Missing tags, unsupported resource types, missing identifiers, unresolved resources, and validation failures result in denial.

### Consequences

AEGIS processes only resources that can be explicitly verified as in scope. New resource-specific policies can be added without embedding authorization rules inside detectors.

---

## ADR-006 — Signal-oriented observability

**Status:** Accepted

### Context

Overlapping polling and checkpoint reads can generate repetitive operational output during normal processing. At-least-once replay also means previously detected events may appear again as duplicates even though no new security incident has been created.

During recovery, CloudTrail can reference resources that no longer exist. Treating expected historical conditions such as a deleted Security Group as warnings creates noise and makes genuine AWS validation failures harder to identify.

Suppressing all normal-cycle output, however, would make the long-running worker appear stalled and would provide little visibility into whether each stage of the security pipeline is functioning.

### Decision

AEGIS uses log levels based on operational significance and exposes pipeline execution telemetry.

Each pipeline execution records:

```text
collected events
→ normalized events
→ in-scope events
→ detections
→ inserted incidents / duplicates
```

Operational logging follows these rules:

- routine scope evaluation and checkpoint reads use `DEBUG`;
- routine empty or duplicate-only polling cycles use `DEBUG`;
- newly inserted security incidents produce an immediate `INFO` summary;
- periodic health heartbeats use `INFO` and include pipeline telemetry;
- meaningful worker recovery uses `INFO`;
- historical resources that no longer exist, such as `InvalidGroup.NotFound`, remain fail-closed but are logged at `DEBUG`;
- unexpected AWS validation failures, permission failures, and similar operational problems use `WARNING`;
- polling-cycle failures use `ERROR`.

Duplicate-only cycles are not treated as new security signals. They remain expected behavior under the at-least-once processing model.

### Consequences

Normal operation remains quiet while still providing periodic evidence that CloudTrail collection, normalization, scope enforcement, detection, and persistence are functioning.

Operators can distinguish between:

```text
no source activity
vs
out-of-scope activity
vs
in-scope activity with no detection
vs
duplicate replay
vs
a newly persisted security incident
```

Expected recovery conditions do not hide genuine AWS or runtime failures behind excessive warning output.

The same pipeline telemetry also provides a foundation for future metrics and monitoring integrations without coupling those systems directly to detection logic.

---

## ADR-007 — Local development runtime keeps AWS credentials off EC2

**Status:** Accepted for the current phase

### Context

Phase 2 needs AWS API access and private PostgreSQL access, but the current environment does not yet have the final production runtime identity design.

### Decision

The continuous worker currently runs from the developer environment using the configured AWS profile. PostgreSQL remains private and is reached through an SSH local port forward. AWS credentials are not copied to the application EC2 instance.

### Consequences

The current implementation is suitable for development and validation while preserving the private database boundary. Moving the worker to AWS requires a dedicated runtime identity and deployment design rather than copying local credentials to a host.

---


## ADR-008 — Migrate application compute from standalone EC2 to Amazon EKS

**Status:** Accepted

### Context

The original Phase 1 platform deploys application workloads directly to an EC2 host and uses Ansible and systemd for runtime configuration.

This architecture successfully established the initial platform but couples workload deployment and scaling to individual servers.

### Decision

AEGIS will migrate application compute to Amazon EKS.

The first implementation will use EKS Managed Node Groups with worker nodes in private subnets across two Availability Zones.

Django/Gunicorn, RQ workers, the scheduler, and the AEGIS security worker will become containerized Kubernetes workloads.

The existing EC2 platform will remain available during the migration and will not be destroyed until the EKS replacement is validated.

### Consequences

Application deployment becomes container-oriented rather than server-oriented.

Kubernetes provides scheduling, workload replication, health management, resource governance, and horizontal scaling capabilities.

The platform also gains additional operational complexity including cluster lifecycle, Kubernetes networking, container image management, workload identity, and Kubernetes security controls.

---

## ADR-009 — Use managed AWS services for persistent PostgreSQL and Redis

**Status:** Accepted with deployment prerequisite

### Context

The original platform operates PostgreSQL and Redis directly on private EC2 instances.

Moving the application to Kubernetes does not imply that persistent databases should also move into the cluster.

Operating databases inside Kubernetes would require additional responsibility for storage lifecycle, backup, failover, upgrades, and data durability.

### Decision

The target Phase 1.1 architecture uses Amazon RDS for PostgreSQL and Amazon ElastiCache for Redis.

Persistent application data will remain outside the EKS cluster.

### Consequences

Database lifecycle and availability responsibilities move toward AWS managed services while the Kubernetes cluster remains focused on application and security-processing workloads.

The current project identity does not presently have sufficient RDS or ElastiCache API permissions, so deployment of this decision requires an AWS permission change or pre-provisioned managed services.

The existing EC2 database and Redis services remain in place until replacement services are available and migration is validated.

---

## ADR-010 — Deploy Terraform through approval-gated GitHub Actions

**Status:** Accepted

### Context

The original platform validates Terraform in GitHub Actions but executes Terraform plan/apply operationally from the developer environment.

This creates a difference between code validation and the actual deployment control path.

Long-lived AWS credentials stored in GitHub would also create unnecessary credential-management risk.

### Decision

The target delivery model uses GitHub Actions as the infrastructure deployment control plane.

Pull requests perform validation, testing, security checks, and Terraform planning.

Changes merged to `main` produce a deployment workflow that authenticates to AWS through GitHub OIDC.

Terraform apply is protected by a GitHub Environment approval gate and deployment concurrency controls.

Long-lived AWS access keys will not be stored as GitHub repository secrets.

### Consequences

Infrastructure deployment becomes repeatable, auditable, and tied directly to reviewed repository changes.

Terraform state must move to a remote backend.

GitHub OIDC and the AWS deployment roles become bootstrap dependencies.

Because the current AWS identity cannot list IAM OIDC providers, IAM bootstrap may require an administrator or separately authorized identity.

---

## Decision Summary

The Phase 2 architecture is intentionally built around these properties:

```text
reliable ingestion
+ explicit authorization scope
+ reusable processing pipeline
+ at-least-once delivery
+ idempotent persistence
+ restart recovery
+ fail-closed behavior
+ signal-oriented observability
```

These decisions are the baseline for future detection, investigation, and response layers.
