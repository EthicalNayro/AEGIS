# Status Page Platform

Production-oriented DevOps platform for deploying and operating a Django-based Status-Page application on AWS.

## Architecture

```text
Internet
   |
  HTTPS :443
   |
 Nginx
   |
Gunicorn :8001
   |
Status-Page / Django
   |
   +-------------------+
   |                   |
PostgreSQL           Redis
  :5432               :6379
```

## Repository structure

```text
.
├── terraform/
│   ├── environments/
│   │   └── dev/
│   └── modules/
│       ├── vpc/
│       ├── security_groups/
│       ├── iam/
│       └── ec2/
├── ansible/
│   ├── inventories/
│   ├── group_vars/
│   ├── playbooks/
│   └── roles/
├── platform/
│   ├── monitoring/
│   ├── security/
│   ├── config/
│   └── scripts/
├── status-page/
├── tests/
├── docs/
├── aegis/
└── .github/workflows/
```

## Current phase

Phase 1 — AWS infrastructure foundation with Terraform.

The first implementation target is:

- VPC
- Public subnet for the application host
- Private subnets for PostgreSQL and Redis
- Internet Gateway
- Route tables
- Security groups using least-privilege rules
- IAM role/profile for EC2
- EC2 instances

## Local requirements

- Terraform 1.15.8
- AWS CLI
- Git
- An AWS account with credentials configured locally

## Deployment principles

1. Terraform manages infrastructure.
2. Ansible manages server configuration.
3. Secrets are never committed to Git.
4. PostgreSQL and Redis are not exposed to the public Internet.
5. Django development server is used only for testing.
6. Production traffic enters through Nginx over HTTPS and is proxied to Gunicorn.
