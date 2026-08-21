# Troubleshooting

This page records important issues encountered while building the Phase 1 foundation and the design decisions used to resolve them.

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

## SSM / PrivateLink Attempt

### Symptom

Private host management through AWS Systems Manager and interface VPC endpoints could not be completed because the account did not permit creation/passing of the required IAM role.

### Resolution

The active design was simplified to SSH ProxyJump through the application EC2 instance. The experimental `iam` and `vpc_endpoints` Terraform modules were retained as inactive future-hardening code but removed from the active environment composition.

## Git Dubious Ownership

### Symptom

Ansible cloning/updating the Status Page repository could trigger Git ownership warnings because repository ownership and the account executing Git did not match.

### Resolution

The application directory is owned by the `status-page` service account and Git tasks execute as that same account.

## Ansible Temporary Directory for Service Account

### Symptom

Running Ansible tasks with `become_user: status-page` caused warnings because the system account did not have a usable home/temp directory.

### Resolution

`/home/status-page` and `/home/status-page/.ansible/tmp` are explicitly created with restricted ownership and permissions.

## Django Permission Error from `/home/ubuntu`

### Symptom

The Django development server started successfully but its auto-reloader failed with a permission error while scanning `/home/ubuntu/locale`.

### Resolution

Run the development server from `/opt/status-page` as the `status-page` user and use `--noreload` for controlled testing.

## Status Page Documentation Build Failure

### Symptom

`upgrade.sh` completed database migrations but failed during MkDocs generation with an incompatibility involving `mkdocs-autorefs`.

### Resolution

A compatible version is pinned in `/opt/status-page/local_requirements.txt`:

```text
mkdocs-autorefs==1.0.1
```

## Ansible Idempotency: Ownership Loop

### Symptom

`local_requirements.txt`, the upgrade task, and recursive ownership tasks repeatedly reported changes.

### Resolution

Application-owned files are consistently owned by `status-page`, and the upgrade task executes as the application service account.

## Ansible Idempotency: Nginx Configuration

### Symptom

The source Nginx configuration was recopied on every run, then the server name was replaced again, causing repeated changes and restarts.

### Resolution

The initial remote copy uses `force: false`, preventing the already-customized configuration from being overwritten on every playbook run.
