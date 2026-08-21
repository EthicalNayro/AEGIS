# Disaster Recovery Posture

## Current Phase 1 Position

The current AEGIS foundation is a development-oriented platform baseline, not a highly available production deployment.

There is no automated disaster-recovery mechanism yet. Recovery currently depends on Infrastructure as Code, configuration automation, and rebuilding the environment from source-controlled definitions.

## What Can Be Recreated

Terraform can recreate the AWS foundation:

- VPC
- Subnets
- Internet Gateway
- Route tables
- NAT Gateway
- Security Groups
- EC2 instances
- SSH key-pair registration

Ansible can recreate host configuration and the Status Page runtime:

- PostgreSQL packages and database configuration
- Redis configuration
- Status Page application dependencies
- Gunicorn and systemd services
- Nginx reverse proxy and TLS configuration

## Current Recovery Gaps

Phase 1 does not yet provide:

- Automated PostgreSQL backups
- Point-in-time database recovery
- Redis persistence/recovery strategy documentation
- Multi-AZ compute redundancy
- Load balancing
- Auto Scaling
- Automated restore testing
- Remote Terraform state locking/backups
- Trusted certificate automation

## Recovery Principle

The present recovery model is:

```text
Git repository
   |
   +--> Terraform -> rebuild AWS infrastructure
   |
   `--> Ansible -> rebuild host/application configuration
```

Persistent application data is the main remaining recovery risk. Backup and restore automation should be added before treating the platform as production-ready.

## Future Hardening

Planned improvements include automated PostgreSQL backups, documented restore procedures, health checks, high availability, and routine recovery testing.
