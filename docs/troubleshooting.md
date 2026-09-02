# Troubleshooting

This page records important issues encountered while building AEGIS and the engineering decisions used to resolve them.

---

# Phase 1 — Platform Foundation

> [!NOTE]
> This section is historical. The superseded EC2/Ansible source was retired after the EKS migration; Git history and the linked evidence images preserve these lessons.

## Terraform Owner Tag Enforcement

### Symptom

AWS denied resource creation with `UnauthorizedOperation` because account governance required an `Owner` tag at creation time.

### Resolution

The AWS provider was configured with default tags, including the required project owner value. This ensures Terraform-created resources receive the required governance metadata consistently.

## Private Subnet Package Access

### Symptom

PostgreSQL and Redis hosts in private subnets could not complete package installation reliably.

### Resolution

A NAT Gateway was added in the public subnet and the private route table received a default route through NAT. APT was also configured to prefer IPv4 because package operations were attempting unusable IPv6 paths.

The successful private-subnet egress test is preserved in the deployment evidence:

![Private subnet NAT egress](screenshots/05-private-subnet-nat-egress.png)

## SSM / PrivateLink Attempt

### Symptom

Private host management through AWS Systems Manager and interface VPC endpoints could not be completed because the account did not permit creation/passing of the required IAM role.

### Resolution

The Phase 1 design was simplified to SSH ProxyJump through the application EC2 instance. The experimental `iam` and `vpc_endpoints` modules were never part of the active composition and were later removed with the rest of the superseded host-based infrastructure.

## Git Dubious Ownership

### Symptom

Ansible cloning/updating the Status Page repository could trigger Git ownership warnings because repository ownership and the account executing Git did not match.

### Resolution

The application directory was owned by the `status-page` service account and Git tasks executed as that same account.

## Ansible Temporary Directory for Service Account

### Symptom

Running Ansible tasks with `become_user: status-page` caused warnings because the system account did not have a usable home/temp directory.

### Resolution

`/home/status-page` and `/home/status-page/.ansible/tmp` were created with restricted ownership and permissions.

## Django Permission Error from `/home/ubuntu`

### Symptom

The Django development server started successfully but its auto-reloader failed with a permission error while scanning `/home/ubuntu/locale`.

### Resolution

The development server was run from `/opt/status-page` as the `status-page` user with `--noreload` for controlled testing.

The final private testing workflow is documented in [Validation](validation.md) and uses an SSH tunnel rather than public TCP `8000`.

## Status Page Documentation Build Failure

### Symptom

`upgrade.sh` completed database migrations but failed during MkDocs generation with an incompatibility involving `mkdocs-autorefs`.

### Resolution

A compatible version was pinned in `/opt/status-page/local_requirements.txt`:

```text
mkdocs-autorefs==1.0.1
```

## Ansible Idempotency: Ownership Loop

### Symptom

`local_requirements.txt`, the upgrade task, and recursive ownership tasks repeatedly reported changes.

### Resolution

Application-owned files were consistently owned by `status-page`, and the upgrade task executed as the application service account.

The final historical Ansible run confirmed that the configuration settled into an idempotent state:

![Ansible final idempotency](screenshots/18-ansible-final-idempotency.png)

## Ansible Idempotency: Nginx Configuration

### Symptom

The source Nginx configuration was recopied on every run, then the server name was replaced again, causing repeated changes and restarts.

### Resolution

The initial remote copy used `force: false`, preventing the already-customized configuration from being overwritten on every playbook run.

---

# Phase 2 — Security Event Pipeline

## CloudTrail Collector Generated Its Own Noise

### Symptom

Polling CloudTrail with `LookupEvents` caused the collector's own API activity to appear in subsequent CloudTrail results.

### Resolution

`CloudTrailCollector` filters events whose source/action identify the collector's own `LookupEvents` calls.

This keeps ingestion focused on target AWS activity without changing the underlying audit trail.

## Relevant Event Missing from the First CloudTrail Results

### Symptom

A Security Group change existed in CloudTrail but did not appear in the first generic result set because unrelated account activity occupied the returned page.

### Resolution

Two improvements were introduced:

1. event-name filtering where a focused runtime requires it;
2. full `NextToken` pagination up to the configured total `max_results` limit.

This became the basis for the paginated-ingestion architecture decision.

## Random Incident IDs Created Duplicate Incidents

### Symptom

The same CloudTrail event was seen again during overlapping polling windows, but a randomly generated incident ID caused a new database record to be treated as a new incident.

### Resolution

Incident IDs were changed to deterministic fingerprints derived from source event and detection context.

PostgreSQL additionally enforces uniqueness and uses `ON CONFLICT DO NOTHING`.

Repeated observation of the same source event is now safe and forms the basis of AEGIS at-least-once processing.

## Incident Builder Import Mismatch

### Symptom

A manual persistence script attempted to import an `IncidentBuilder` class that did not exist, resulting in an import error.

### Resolution

The script was updated to use the actual incident-builder API: the `build_incident()` function.

The reusable processing path was later moved into `SecurityEventPipeline` so manual entry points no longer own incident orchestration logic.

## Python `TabError` After Manual Edit

### Symptom

A manual code edit introduced mixed tabs and spaces and Python failed with `TabError: inconsistent use of tabs and spaces in indentation`.

### Resolution

Indentation was normalized to four spaces and syntax validation was added to the development workflow before runtime tests.

## PostgreSQL Authentication Through a Working Tunnel

### Symptom

The SSH tunnel successfully reached PostgreSQL, but the application connection failed during authentication.

### Resolution

The database connection URL was constructed safely at runtime, including correct URL encoding of the password rather than embedding an unescaped secret into the DSN.

The credential remains outside Git and is supplied through environment configuration during development.

## Ansible Vault Interactive Prompt Inconsistency

### Symptom

`ansible-vault view` could decrypt the encrypted Vault successfully, while some inventory/playbook commands using interactive `--ask-vault-pass` reported that no usable Vault secret was available.

### Resolution

A temporary restricted password file created with `mktemp` was used for the affected historical Ansible commands and deleted after the session.

This isolated the issue to the interactive prompt path without changing the encrypted Vault file or exposing the secret in the repository.

## Worker Database Connection Timeout

### Symptom

The continuous worker failed while reading its checkpoint with a PostgreSQL connection timeout.

### Resolution

The development access path was validated layer by layer:

```text
SSH / ProxyJump
    -> PostgreSQL service
    -> local SSH forward
    -> DSN host/port
    -> psycopg SELECT 1
```

The local PostgreSQL tunnel must remain active while the development worker runs.

Importantly, a database failure prevents the worker checkpoint from advancing, so the next successful cycle can retry the missed time window instead of creating a silent gap.

## Shell Variables Lost Between Terminals

### Symptom

A Security Group integration test failed with `InvalidGroupId.Malformed` because the shell variable containing the test Security Group ID was empty in a newly opened terminal.

### Resolution

Lab resource IDs are resolved or exported in the shell that executes the AWS CLI commands. The test workflow verifies the variable value before changing any Security Group rules.

## AWS CLI Table Output Failed for Nested Tags

### Symptom

An AWS CLI query combining Security Group metadata and nested tag objects with `--output table` failed with a list-index error.

### Resolution

Resource identity and tag verification are queried separately. This produces predictable output and makes the DENY/ALLOW scope state explicit before the integration test.

## Resource Scope Logs Were Too Noisy

### Symptom

Overlapping polling caused routine `Scope DENIED`, `Scope ALLOWED`, checkpoint, and empty-cycle messages to appear repeatedly at `INFO`, obscuring important security signals.

### Resolution

AEGIS adopted signal-oriented observability:

- routine scope decisions, checkpoint loads, and empty cycles use `DEBUG`;
- meaningful restart recovery and incident summaries use `INFO`;
- a periodic heartbeat confirms worker liveness without logging every poll;
- scope-validation failures use `WARNING`;
- polling failures use `ERROR`.

The resulting output remains useful during normal operation without appearing stalled or flooding the operator terminal.

---

## Troubleshooting Principle

AEGIS troubleshooting should identify the failing layer before changing architecture or credentials.

For the current Phase 2 development runtime, the preferred sequence is:

```text
AWS event exists?
    -> collector retrieved it?
    -> normalizer extracted the resource?
    -> scope policy allowed it?
    -> detector produced a finding?
    -> incident ID was built?
    -> PostgreSQL connection works?
    -> incident/checkpoint persisted?
```

This keeps failures observable and prevents unrelated fixes from masking the original problem.
