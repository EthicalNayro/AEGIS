# Phase 2 — Security Event Pipeline

## Status

**In progress — core detection pipeline implemented and validated.**

Phase 2 turns the Phase 1 AWS foundation into a working cloud-security event processor. The current implementation continuously polls AWS CloudTrail, normalizes supported events, enforces an explicit monitoring scope, detects public SSH and RDP exposure on EC2 Security Groups, builds deterministic incidents, and persists them to a dedicated PostgreSQL database.

AI investigation, Bedrock/AgentCore orchestration, automated remediation, and approval workflows are intentionally outside the current implementation.

---

## Current Processing Architecture

```text
AWS API activity
      |
      v
CloudTrail Event History
      |
      | LookupEvents + pagination
      v
CloudTrailCollector
      |
      v
CloudTrailNormalizer
      |
      v
Resource Scope Policy
      |
      | AEGISMonitoring=enabled
      v
Detection Engine
      |
      | AEGIS-AWS-SG-001 / AEGIS-AWS-SG-002
      v
Incident Builder
      |
      | deterministic incident ID
      v
PostgresIncidentRepository
      |
      v
AEGIS PostgreSQL database
```

The continuous runtime adds a resilient worker lifecycle around this pipeline:

```text
SecurityWorker
   |
   +--> persistent checkpoint
   +--> overlapping lookback window
   +--> retry after failed cycles
   +--> health heartbeat
   |
   v
SecurityEventPipeline
```

---

## Implemented Capabilities

### CloudTrail ingestion

`CloudTrailCollector` retrieves recent CloudTrail events using `LookupEvents`.

The collector:

- supports an explicit lookback window;
- filters by event name when requested;
- follows CloudTrail `NextToken` pagination;
- respects a total `max_results` bound;
- filters collector-generated `LookupEvents` noise.

Pagination is important because an event may exist inside the requested time window without appearing in the first CloudTrail response page.

### Normalization

CloudTrail payloads are converted into internal `NormalizedEvent` objects so the detection layer does not depend directly on raw AWS payload shape.

For Security Group ingress changes, normalization extracts:

- CloudTrail event ID and timestamp;
- service and API action;
- actor identity and source IP when available;
- AWS region;
- Security Group resource ID;
- IPv4 and IPv6 ingress rules;
- protocol and port ranges.

### Resource scope enforcement

AEGIS uses an explicit opt-in monitoring boundary before detection.

For the current EC2 Security Group implementation, the required tag is:

```text
AEGISMonitoring=enabled
```

Resources without the tag are ignored. Unsupported resource types, missing resource identifiers, resources that cannot be resolved, and AWS scope-validation failures are denied rather than implicitly trusted.

This makes the current scope policy **fail closed**.

### Detection

The current production-style Security Group rules are:

| Rule ID | Finding | Severity |
|---|---|---|
| `AEGIS-AWS-SG-001` | Public SSH Exposure | HIGH |
| `AEGIS-AWS-SG-002` | Public RDP Exposure | HIGH |

Both rules detect public exposure introduced through Security Group ingress changes and support relevant IPv4, IPv6, port-range, and all-protocol cases.

Detection is intentionally one-to-many: a single normalized CloudTrail event may produce multiple findings.

Each finding becomes a distinct incident because the rule ID and detection context are included in the deterministic incident fingerprint.

`AEGIS-AWS-SG-002` was validated end-to-end using a detached temporary Security Group. The resulting `AuthorizeSecurityGroupIngress` event was collected from CloudTrail, passed explicit resource scope, detected as Public RDP Exposure, persisted once in PostgreSQL, and safely recognized as a duplicate during overlapping replay cycles.

### Incident construction and deduplication

Detections are converted into `Incident` objects.

Incident identifiers are deterministic rather than random. The fingerprint includes the source event and detection context, allowing the same CloudTrail event to be processed repeatedly without producing a new logical incident each time.

PostgreSQL provides a second idempotency boundary through the incident primary key and:

```sql
ON CONFLICT (incident_id) DO NOTHING
```

The resulting processing model is intentionally **at least once**, not exact once.

### PostgreSQL persistence

Phase 2 uses a dedicated AEGIS database and user, separate from the Phase 1 Status Page database.

The database stores:

- incident metadata;
- severity and status;
- rule and source event identifiers;
- resource and actor information;
- event/detection timestamps;
- structured JSON evidence;
- persistent worker checkpoints.

PostgreSQL remains on the private database host. Local development reaches it through an SSH local forward rather than exposing the database publicly.

### Continuous worker

`SecurityWorker` executes the reusable `SecurityEventPipeline` continuously.

The worker is responsible for lifecycle concerns only:

- polling cadence;
- retrying the next cycle after an exception;
- persistent checkpoint recovery;
- safety overlap;
- liveness heartbeat;
- signal-oriented operational logging.

Collection, normalization, scope enforcement, detection, incident creation, and persistence remain inside independent components.

### Persistent checkpoint recovery

After every successful pipeline cycle, the worker stores `last_successful_poll_at` in PostgreSQL.

After a restart, the worker calculates the elapsed gap and expands the next CloudTrail lookback window by:

```text
time since last successful checkpoint
+
configured safety overlap
```

The checkpoint advances only after a successful pipeline execution. If the database or pipeline fails, the worker does not silently move the high-water mark forward.

Repeated events caused by the recovery window are safe because incident persistence is idempotent.

### Signal-oriented observability

The worker uses pipeline execution telemetry rather than relying only on incident output.

Every pipeline run records:

```text
collected events
→ normalized events
→ in-scope events
→ detections
→ inserted incidents / duplicates
```

This provides visibility into where events move through — or stop inside — the processing path.

For example:

```text
events=20 normalized=20 in_scope=0 detections=0 inserted=0 duplicates=0
```

shows that CloudTrail ingestion and normalization are functioning, but none of the collected resources passed the monitoring scope.

A result such as:

```text
events=20 normalized=20 in_scope=2 detections=1 inserted=0 duplicates=1
```

shows that detection occurred but the incident had already been persisted during an earlier at-least-once processing cycle.

Current operational logging policy:

| Signal | Level |
|---|---|
| Worker start / stop | INFO |
| Meaningful restart recovery | INFO |
| Newly inserted security incident | INFO |
| Periodic health heartbeat with pipeline telemetry | INFO |
| Routine checkpoint loading | DEBUG |
| Empty polling cycle | DEBUG |
| Duplicate-only polling cycle | DEBUG |
| Routine scope allow / deny evaluation | DEBUG |
| Historical resource no longer exists (`InvalidGroup.NotFound`) | DEBUG |
| Unexpected AWS validation / permission failure | WARNING |
| Polling-cycle failure | ERROR |

Duplicate-only detections are not treated as new security signals because replay is expected under the at-least-once processing model.

Historical resources referenced by CloudTrail may no longer exist when a recovery window is replayed. These resources still fail scope validation closed, but an expected `InvalidGroup.NotFound` condition is logged at `DEBUG` rather than generating warning noise.

This keeps normal operation quiet while preserving:

- visible worker liveness;
- meaningful security signals;
- real AWS/API failures;
- visibility into every major processing stage.

The telemetry model also creates a clean foundation for future Prometheus, CloudWatch, or other metrics integrations without moving observability logic into the detectors.

---

## Package Layout

```text
aegis/
├── pyproject.toml
├── scripts/manual/
├── src/aegis/
│   ├── collectors/
│   ├── detection/
│   ├── incidents/
│   ├── models/
│   ├── normalization/
│   ├── pipeline/
│   ├── runtime/
│   ├── scope/
│   ├── storage/
│   └── workers/
└── tests/
```

The manual scripts are development and validation entry points. Reusable processing logic belongs under `src/aegis/`.

---

## Development Runtime

The current continuous worker runs from the developer environment rather than from an EC2 runtime.

```text
Developer WSL
   |
   +--> AWS profile --> CloudTrail / EC2 APIs
   |
   +--> localhost DB port
           |
           v
       SSH tunnel
           |
           v
   private PostgreSQL EC2
```

AWS credentials are not copied to the application EC2 host for this phase.

Example runtime configuration uses environment variables for operational settings such as:

```text
AEGIS_DATABASE_URL
AEGIS_AWS_REGION
AEGIS_POLL_INTERVAL_SECONDS
AEGIS_LOOKBACK_MINUTES
AEGIS_MAX_RESULTS
AEGIS_EVENT_NAME
AEGIS_SCOPE_TAG_KEY
AEGIS_SCOPE_TAG_VALUE
```

Credentials and database passwords must not be committed to the repository.

---

## Validation Evidence

Phase 2 has been validated incrementally with unit tests, CI, safe lab Security Groups, CloudTrail events, and PostgreSQL persistence.

Selected evidence in `docs/screenshots/`:

| Evidence | File |
|---|---|
| Normalized CloudTrail security event | `23-aegis-normalized-security-event.png` |
| Public SSH detection | `24-aegis-public-ssh-detection.png` |
| Security pipeline unit tests | `26-aegis-security-pipeline-unit-tests.png` |
| Python CI | `27-aegis-python-ci-success.png` |
| End-to-end incident construction | `28-aegis-end-to-end-security-incident.png` |
| Dedicated AEGIS PostgreSQL database | `29-aegis-postgresql-database-isolation.png` |
| Persistence and deduplication | `30-aegis-incident-persistence-deduplication.png` |
| Persisted PostgreSQL incident | `31-aegis-postgresql-persisted-incident.png` |
| Persistence CI | `32-aegis-persistence-ci-success.png` |
| CloudTrail pagination CI | `33-aegis-cloudtrail-pagination-ci-success.png` |
| Continuous security worker | `35-aegis-continuous-security-worker.png` |
| Worker checkpoint recovery | `36-aegis-worker-checkpoint-recovery.png` |
| Resource scope enforcement | `38-aegis-resource-scope-enforcement.png` |
| Signal-oriented observability sanity check | `39-aegis-signal-oriented-observability-sanity.png` |
| Phase 2 branch synchronization and CI | `40-aegis-phase2-final-ci-and-sync.png` |
| Pipeline execution telemetry | `41-aegis-pipeline-execution-telemetry.png` |
| Public RDP runtime detection | `42-aegis-public-rdp-runtime-detection.png` |
| Persisted Public RDP incident | `43-aegis-public-rdp-persisted-incident.png` |

The repository also contains CI evidence for the resilient worker milestone.

---

## Current Security Boundaries

- PostgreSQL remains private; development access uses SSH forwarding.
- The worker does not expose the database to the Internet.
- Resource monitoring is explicit opt-in through `AEGISMonitoring=enabled`.
- Scope validation fails closed.
- The current runtime keeps AWS credentials in the developer AWS profile rather than copying them to EC2.
- Deterministic IDs plus database uniqueness make replay safe.
- Worker checkpoints do not advance after a failed processing cycle.

---

## Current Limitations

Phase 2 is deliberately not presented as a finished autonomous response platform.

Current limitations include:

- CloudTrail `LookupEvents` polling is the active event transport; EventBridge/SQS ingestion is not active.
- The current detection scope is focused on EC2 Security Group ingress changes.
- The current concrete rules detect public SSH and public RDP exposure.
- The continuous worker currently runs from the development environment.
- Scope policy currently supports Security Groups through tag validation.
- Incident investigation, AI agents, approval policy, and automated remediation are not implemented yet.

These are explicit phase boundaries rather than hidden future-state claims.

---

## Next Engineering Steps

The next Phase 2 work should extend reliability and security capability without collapsing component boundaries. Candidate work includes:

1. expand normalized resource support and detection rules;
2. make resource scope policies composable across AWS resource types;
3. improve collector state/metrics and operational telemetry;
4. introduce a production AWS runtime identity before moving the worker off the developer host;
5. evaluate event-driven transport when the required AWS permissions and runtime design are available;
6. keep investigation/AI/remediation as later layers consuming persisted incidents rather than embedding them into ingestion.

See [Architecture Decisions](architecture-decisions.md) for the decisions that shaped the current design.
