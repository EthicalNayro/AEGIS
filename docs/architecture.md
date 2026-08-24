# Architecture

## Scope

AEGIS currently contains two implemented layers:

- **Phase 1 — Platform Foundation:** AWS networking, compute, private PostgreSQL/Redis, Django runtime, Terraform, and Ansible.
- **Phase 2 — Security Event Pipeline:** CloudTrail ingestion, normalization, resource-scope enforcement, detection, incident persistence, and a resilient continuous worker.

AI investigation, agent orchestration, approval policy, and automated remediation are future layers and are not described as current state.

---

## Phase 1 — Platform Foundation

![AEGIS Foundation Network Architecture](diagrams/01-aws-network-architecture.png)

The foundation uses three Ubuntu 22.04 EC2 instances inside one VPC:

- **Application EC2** in a public subnet
- **PostgreSQL EC2** in a private database subnet
- **Redis EC2** in a private Redis subnet

The application host is the only Internet-facing compute instance. PostgreSQL and Redis do not receive public IP addresses.

### Network layout

```text
VPC 10.0.0.0/16

├── Public Application Subnet 10.0.1.0/24
│   ├── Application EC2
│   └── NAT Gateway
│
├── Private Database Subnet 10.0.10.0/24
│   └── PostgreSQL EC2
│
└── Private Redis Subnet 10.0.20.0/24
    └── Redis EC2
```

The public subnet uses an Internet Gateway. Both private subnets use the shared private route table and NAT Gateway for outbound package installation and updates.

### Application runtime

```text
Client
  -> HTTPS :443
Nginx
  -> 127.0.0.1:8001
Gunicorn
  -> Django
Django
  -> PostgreSQL :5432
  -> Redis :6379
```

Background processing runs on the application EC2 instance through Redis, RQ Worker, and RQ Scheduler.

### Administration path

SSH access to the public application host is restricted to the configured administrator CIDR. Private hosts are reached using SSH ProxyJump through the application host.

```text
Administrator
   |
   | SSH :22
   v
Application EC2
   |
   | ProxyJump
   +------> PostgreSQL EC2
   `------> Redis EC2
```

Terraform owns AWS infrastructure state. Ansible owns host and application configuration.

The active Terraform environment calls the `vpc`, `security_groups`, and `ec2` modules. The `iam` and `vpc_endpoints` modules remain inactive/future hardening work and are not part of the deployed current-state architecture.

---

## Phase 2 — Security Event Pipeline

The current Phase 2 implementation is a reusable cloud-security event-processing core.

```text
AWS API Activity
      |
      v
CloudTrail Event History
      |
      | LookupEvents
      | pagination
      v
CloudTrailCollector
      |
      v
CloudTrailNormalizer
      |
      v
Resource Scope Policy
      |
      | explicit opt-in
      v
Detection Engine
      |
      v
Incident Builder
      |
      | deterministic ID
      v
PostgresIncidentRepository
      |
      v
AEGIS PostgreSQL database
```

### Continuous runtime

A long-running `SecurityWorker` executes the same reusable `SecurityEventPipeline` used by development entry points.

```text
SecurityWorker
   |
   +--> polling cadence
   +--> persistent checkpoint
   +--> recovery lookback
   +--> safety overlap
   +--> health heartbeat
   |
   v
SecurityEventPipeline
```

The worker does not contain CloudTrail normalization or detection logic. Its responsibility is lifecycle and scheduling.

### Event reliability model

CloudTrail ingestion follows pagination and the worker intentionally uses overlapping time windows.

The same source event may therefore be processed more than once.

AEGIS handles this through:

```text
At-least-once processing
        +
Deterministic incident IDs
        +
PostgreSQL primary-key uniqueness
        +
ON CONFLICT DO NOTHING
        =
Safe replay
```

### Checkpoint recovery

Worker progress is persisted in PostgreSQL. After restart, AEGIS expands its lookback from the last successful checkpoint plus a configured safety overlap.

The checkpoint advances only after a successful pipeline cycle. A failed database or processing cycle therefore causes retry rather than silently skipping a time window.

### Resource authorization boundary

Scope enforcement occurs before detection.

The current EC2 Security Group scope policy requires:

```text
AEGISMonitoring=enabled
```

Resources that are not explicitly opted in are ignored. Unsupported resources and validation failures are denied by default.

### Current detection capability

The current Security Group detector contains two implemented rules:

```text
AEGIS-AWS-SG-001
Public SSH Exposure
Severity: HIGH

AEGIS-AWS-SG-002
Public RDP Exposure
Severity: HIGH
```

Both rules operate on normalized events rather than raw CloudTrail payloads.

The detector supports one-to-many detection. A single normalized event can produce multiple findings when one ingress rule exposes multiple monitored services.

Each finding receives its own deterministic incident identity because the detection rule ID and detection context are part of the incident fingerprint.

### Persistence boundary

AEGIS incidents use a dedicated PostgreSQL database/user rather than the Status Page database.

PostgreSQL remains private. During the current development phase, the worker reaches it through an SSH local forward.

### Runtime location

The continuous worker currently runs from the developer environment using the configured AWS profile. AWS credentials are not copied to the application EC2 host.

This is a deliberate development-stage boundary; a future AWS-hosted runtime requires its own workload identity and deployment design.

### Observability

Phase 2 uses signal-oriented logging:

- routine polling and scope evaluation are `DEBUG`;
- meaningful recovery and incident summaries are `INFO`;
- periodic health heartbeats provide visible liveness;
- scope-validation problems are `WARNING`;
- polling failures are `ERROR`.

---

## Current vs Future Architecture

### Implemented now

```text
CloudTrail
   -> Collector
   -> Normalizer
   -> Scope Policy
   -> Detection
   -> Incident Builder
   -> PostgreSQL

Continuous Worker
   -> Checkpoint Recovery
   -> Safety Overlap
   -> Health Heartbeat
```

### Not implemented yet

```text
EventBridge / SQS production transport
AI investigation agents
Bedrock / AgentCore investigation orchestration
Human approval workflows
Governed remediation actions
Automated response execution
Security operations UI
```

These future components should consume the existing incident layer rather than being embedded into ingestion or detection.

---

## Documentation

- [Phase 2 Security Event Pipeline](phase-2-security-event-pipeline.md)
- [Architecture Decisions](architecture-decisions.md)
- [Networking](networking.md)
- [Security](security.md)
- [Deployment](deployment.md)
- [Validation](validation.md)
- [Troubleshooting](troubleshooting.md)
