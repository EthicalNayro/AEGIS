# Validation Evidence Index

This directory contains incremental visual evidence captured while building AEGIS.

The images are evidence of specific validation milestones; they are not intended to replace the architecture and validation documentation.

## Phase 1 — Platform Foundation

| # | Evidence |
|---|---|
| 01 | Local tooling prerequisites |
| 02 | Terraform initialization |
| 03 | Terraform network plan |
| 04 | Terraform network apply |
| 05 | Private subnet NAT egress |
| 06 | Ansible connectivity across hosts |
| 07 | PostgreSQL network configuration |
| 08 | PostgreSQL database/user verification |
| 09 | Redis Ansible deployment |
| 10 | Redis listener verification |
| 11 | Status Page Ansible installation |
| 12 | Application systemd services |
| 13 | Nginx HTTPS deployment |
| 14 | Nginx → Gunicorn HTTPS chain |
| 15 | Public Django port removal plan |
| 16 | Private Django testing through SSH tunnel |
| 17 | Final Terraform no-change state |
| 18 | Final Ansible idempotency |
| 19 | Production runtime verification |
| 20 | Private backend connectivity |
| 21 | Git secrets/state ignore verification |
| 22 | Clean Git working tree |

## Phase 2 — Security Event Pipeline

| # | File | What it validates |
|---|---|---|
| 23 | `23-aegis-normalized-security-event.png` | Raw CloudTrail data normalized into the AEGIS event model |
| 24 | `24-aegis-public-ssh-detection.png` | Public SSH exposure detection |
| 25 | `25-aegis-detection-unit-tests.png` | Detection-rule unit tests |
| 26 | `26-aegis-security-pipeline-unit-tests.png` | Security-pipeline tests |
| 27 | `27-aegis-python-ci-success.png` | Initial Python CI success |
| 28 | `28-aegis-end-to-end-security-incident.png` | Detection converted into a structured incident |
| 29 | `29-aegis-postgresql-database-isolation.png` | Dedicated AEGIS database ownership/isolation |
| 30 | `30-aegis-incident-persistence-deduplication.png` | First insert followed by idempotent duplicate handling |
| 31 | `31-aegis-postgresql-persisted-incident.png` | Incident stored in PostgreSQL |
| 32 | `32-aegis-persistence-ci-success.png` | Persistence milestone CI |
| 33 | `33-aegis-cloudtrail-pagination-ci-success.png` | Paginated CloudTrail ingestion CI |
| 35 | `35-aegis-continuous-security-worker.png` | Continuous worker processes events without manual invocation |
| 36 | `36-aegis-worker-checkpoint-recovery.png` | Persistent checkpoint recovery after restart |
| 37 | `37-tags-applying.png` | Explicit monitoring-tag setup used by the scope integration test |
| 38 | `38-aegis-resource-scope-enforcement.png` | DENY/ALLOW resource-scope behavior |
| 39 | `39-aegis-signal-oriented-observability-sanity.png` | Quiet normal polling plus visible worker health/liveness |
| 39* | `39-aegis-resilient-security-worker-ci-success.mp4` | Recorded CI evidence for the resilient-worker milestone |
| 40 | `40-aegis-phase2-final-ci-and-sync.png` | Phase 2 branch synchronization and green CI validation |
| 41 | `41-aegis-pipeline-execution-telemetry.png` | Runtime telemetry across collection, normalization, scope, detection, and persistence |
| 42 | `42-aegis-public-rdp-runtime-detection.png` | End-to-end runtime detection of Public RDP Exposure |
| 43 | `43-aegis-public-rdp-persisted-incident.png` | SG-002 incident persisted once in PostgreSQL despite replay |

`39*` is a legacy duplicate sequence number retained to avoid rewriting historical binary evidence. New evidence should continue with the next unused number rather than renaming old files.

## Evidence Guidelines

- Do not capture credentials, Vault plaintext, database passwords, private keys, or account secrets.
- Prefer screenshots that prove one clear milestone.
- Keep architecture claims in Markdown documentation; use screenshots only as supporting evidence.
- New Phase 2 evidence should use descriptive file names and continue the existing sequence.
