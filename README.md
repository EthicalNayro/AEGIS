# AEGIS — Autonomous Cloud Security Platform

AEGIS is an AWS-focused **DevSecOps and cloud-security engineering project** built in phases: first a secure platform foundation, then a resilient security-event pipeline, and later investigation and governed response layers.

The repository intentionally separates **implemented current state** from future architecture.

---

## Project Status

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | AWS Platform Foundation | ✅ Complete |
| Phase 2 | Security Event Pipeline | ✅ Complete |
| Phase 3 | Investigation / AI layer | ⏳ Future |
| Phase 4 | Governed response / remediation | ⏳ Future |

Phase 2 is complete and includes working CloudTrail ingestion, normalization, Security Group detection, explicit resource-scope enforcement, deterministic incident creation, PostgreSQL persistence, continuous polling, persistent checkpoint recovery, and signal-oriented worker observability.

---

## Current Architecture

### Platform foundation

![AEGIS Foundation Network Architecture](docs/diagrams/01-aws-network-architecture.png)

```text
AWS VPC
├── Public Application Subnet
│   ├── Application EC2
│   └── NAT Gateway
│
├── Private Database Subnet
│   └── PostgreSQL EC2
│
└── Private Redis Subnet
    └── Redis EC2
```

The application host is the only Internet-facing compute instance. PostgreSQL and Redis remain private.

### Security event pipeline

```text
AWS API Activity
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
      v
Incident Builder
      |
      | deterministic ID
      v
PostgreSQL
```

The continuous runtime wraps the pipeline with persistent recovery state:

```text
SecurityWorker
   |
   +--> polling cadence
   +--> persistent checkpoint
   +--> safety overlap
   +--> retry after failed cycles
   +--> health heartbeat
   |
   v
SecurityEventPipeline
```

See [Architecture](docs/architecture.md) for the full implemented design.

---

# Phase 1 — Platform Foundation ✅

Phase 1 provides the infrastructure and application baseline used by AEGIS.

### AWS and networking

- VPC with public application and private backend subnets
- Internet Gateway for the public tier
- NAT Gateway for private outbound access
- Security Groups with tier-specific ingress rules
- Ubuntu 22.04 EC2 hosts
- encrypted EC2 root volumes
- IMDSv2 required

### Private data services

- PostgreSQL on a private EC2 instance
- Redis on a private EC2 instance
- no public IP addresses on backend hosts
- application-only network access to PostgreSQL/Redis
- SSH ProxyJump for administration of private hosts

### Application runtime

```text
Internet
   |
 HTTPS :443
   v
 Nginx
   |
127.0.0.1:8001
   v
Gunicorn
   |
 Django
  /    \
Postgres Redis
```

The Django development port is not exposed publicly. Testing uses an SSH local forward.

### Infrastructure automation

- Terraform for AWS infrastructure
- Ansible for host/application configuration
- Ansible Vault for encrypted secrets
- systemd-managed application services
- GitHub Actions Terraform validation

---

# Phase 2 — Security Event Pipeline ✅

Phase 2 introduces the first real AEGIS security-processing layer.

## Reliable CloudTrail ingestion

The collector uses CloudTrail `LookupEvents` with:

- configurable lookback windows;
- event-name filtering;
- `NextToken` pagination;
- bounded total results;
- collector-noise filtering.

AEGIS does not assume that the first CloudTrail response page represents the complete event window.

## Normalized security events

Raw CloudTrail payloads are converted into internal event models before detection. This keeps the detection engine independent from AWS response formatting.

The current Security Group normalization extracts actor, source IP, resource ID, region, protocol, ports, and IPv4/IPv6 CIDRs.

## Explicit resource scope

AEGIS uses a fail-closed monitoring boundary before detection.

The current EC2 Security Group scope policy requires:

```text
AEGISMonitoring=enabled
```

A missing tag, unsupported resource, unresolved resource, or failed scope validation results in denial.

## Current detection rules

| Rule ID | Finding | Severity |
|---|---|---|
| `AEGIS-AWS-SG-001` | Public SSH Exposure | HIGH |
| `AEGIS-AWS-SG-002` | Public RDP Exposure | HIGH |

The Security Group detector evaluates normalized ingress rules and can emit multiple findings from the same CloudTrail event when a rule exposes more than one monitored service.

`AEGIS-AWS-SG-002` was validated end-to-end using a detached temporary Security Group:

```text
AWS API activity
    -> CloudTrail
    -> normalization
    -> resource scope
    -> detection
    -> deterministic incident construction
    -> PostgreSQL persistence
```

## Incident persistence and deduplication

Detections become structured incidents with deterministic IDs.

The processing model is deliberately **at least once**. Overlapping polling/recovery windows may replay events, while deterministic incident IDs and PostgreSQL uniqueness make persistence idempotent.

```text
same CloudTrail event
        |
        v
same deterministic incident ID
        |
        v
PostgreSQL PRIMARY KEY
        |
ON CONFLICT DO NOTHING
        |
        v
one persisted incident
```

## Continuous security worker

AEGIS includes a long-running worker rather than requiring an operator to manually run the processing script after every event.

The worker provides:

- periodic polling;
- persistent PostgreSQL checkpoints;
- restart recovery;
- safety overlap for delayed events;
- retry behavior after failed cycles;
- graceful shutdown;
- periodic health heartbeat.

A checkpoint advances only after successful pipeline execution.

## Signal-oriented observability

Routine housekeeping stays at `DEBUG` while important operator signals remain visible:

| Signal | Level |
|---|---|
| Worker lifecycle | INFO |
| Meaningful recovery | INFO |
| Incident summary | INFO |
| Health heartbeat | INFO |
| Routine polling / scope evaluation | DEBUG |
| Scope validation failure | WARNING |
| Polling failure | ERROR |

This prevents normal polling from burying meaningful security events while still proving worker liveness.

For the full Phase 2 implementation and current limitations, see [Phase 2 — Security Event Pipeline](docs/phase-2-security-event-pipeline.md).

---

## Security Design Principles

AEGIS currently follows these principles:

- private data services remain private;
- security monitoring scope is explicit rather than implicit;
- scope validation fails closed;
- event replay is safer than silently missing events;
- persistence is idempotent;
- worker state survives process restarts;
- failed cycles do not advance the processing checkpoint;
- reusable processing logic is separated from runtime lifecycle code;
- AWS credentials are not copied from the developer environment to EC2 for the current Phase 2 runtime;
- logs prioritize operator signal over repetitive internal activity.

The reasoning behind these choices is recorded in [Architecture Decisions](docs/architecture-decisions.md).

---

## Repository Structure

```text
.
├── aegis/
│   ├── pyproject.toml
│   ├── scripts/manual/
│   ├── src/aegis/
│   │   ├── collectors/
│   │   ├── detection/
│   │   ├── incidents/
│   │   ├── models/
│   │   ├── normalization/
│   │   ├── pipeline/
│   │   ├── runtime/
│   │   ├── scope/
│   │   ├── storage/
│   │   └── workers/
│   └── tests/
│
├── terraform/
│   ├── environments/dev/
│   └── modules/
│
├── ansible/
│   ├── inventories/dev/
│   ├── playbooks/
│   └── roles/
│
├── docs/
│   ├── diagrams/
│   └── screenshots/
│
└── .github/workflows/
```

Manual scripts are development/validation entry points. Reusable AEGIS logic lives under `aegis/src/aegis/`.

---

## CI and Validation

AEGIS Python changes are validated through GitHub Actions using Python 3.12 and the project unit-test suite.

The repository also contains incremental validation evidence under `docs/screenshots/`, including:

- normalized CloudTrail events;
- public SSH detection;
- unit-test and CI success;
- end-to-end incident generation;
- PostgreSQL persistence and deduplication;
- CloudTrail pagination;
- continuous-worker operation;
- persistent checkpoint recovery;
- resource-scope enforcement;
- signal-oriented observability sanity validation.

Phase 1 infrastructure validation remains documented separately.

---

## Development Runtime Boundary

The current Phase 2 worker runs from the developer environment.

```text
Developer WSL
   |
   +--> AWS profile --> AWS APIs
   |
   +--> SSH local forward --> private PostgreSQL
```

This is a development-stage architecture. A future AWS-hosted worker requires an explicit workload identity and deployment design; local AWS credentials will not be copied to the application host as a shortcut.

---

## Current Limitations

The repository does **not** claim that AEGIS is already a complete autonomous incident-response platform.

Current Phase 2 limitations include:

- CloudTrail polling is the active event transport;
- detection currently focuses on Security Group ingress with public SSH and RDP exposure rules;
- tag-based scope enforcement currently targets EC2 Security Groups;
- the continuous worker currently runs from the development environment;
- AI investigation and agent orchestration are not implemented;
- automated remediation and human approval workflows are not implemented.

These are explicit phase boundaries.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Phase 2 Security Event Pipeline](docs/phase-2-security-event-pipeline.md)
- [Architecture Decisions](docs/architecture-decisions.md)
- [Networking](docs/networking.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [Validation](docs/validation.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Disaster Recovery Posture](docs/disaster-recovery.md)

---

## Next Direction

The next engineering work should build on the persisted incident layer rather than bypass it: broader detection coverage, composable resource-scope policies, production runtime identity/hosting, stronger telemetry, and eventually investigation and governed response layers.

Future AI or automated-response components will be documented only when implemented.
