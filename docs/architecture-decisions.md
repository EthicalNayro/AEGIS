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

Overlapping polling and checkpoint reads caused repetitive `INFO` logs for routine scope evaluations, checkpoint housekeeping, and empty polling cycles. Although technically correct, the output obscured meaningful operator signals and made a healthy worker appear noisy.

Suppressing all normal-cycle output, however, made the long-running worker appear stalled.

### Decision

AEGIS uses log levels based on operational significance:

- routine scope evaluation, checkpoint reads, and empty cycles use `DEBUG`;
- meaningful restart recovery uses `INFO`;
- incident-processing summaries use `INFO`;
- a periodic health heartbeat uses `INFO` to prove liveness without logging every cycle;
- scope-validation failures use `WARNING`;
- polling-cycle failures use `ERROR`.

### Consequences

Normal operation is quiet but visibly alive. Incidents, recovery, and failures remain easy to identify in operator output.

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
