# AEGIS — Platform Foundation

Infrastructure foundation for an **Autonomous Cloud Security & Incident Response Platform** on AWS.

**Phase 1** establishes the secure network, compute, application runtime, private data services, Infrastructure as Code, and configuration-management baseline on which the AEGIS security automation platform will be built.

> **Current scope:** this repository currently contains the deployed platform foundation. The AEGIS detection, investigation, agent, and automated-response layers are intentionally not implemented yet.

---

## Phase 1 — Foundation

The deployed foundation includes:

- AWS infrastructure provisioned with Terraform
- Public application and private backend network tiers
- Three Ubuntu 22.04 EC2 instances
- PostgreSQL and Redis on private subnets with no public IPs
- Django Status Page served by Gunicorn and Nginx
- RQ Worker and Scheduler on the application host
- HTTPS ingress using a self-signed certificate in the current dev environment
- SSH administration through the application host using ProxyJump
- Ansible-based server and application configuration
- Ansible Vault for application secrets
- Basic GitHub Actions CI validation for Terraform

---

## Foundation Architecture

![AEGIS Foundation Network Architecture](docs/diagrams/01-aws-network-architecture.png)

The application server is the only Internet-facing compute instance. PostgreSQL and Redis remain private and accept application traffic only from the application security group.

For the full design, see [Architecture](docs/architecture.md) and [Networking](docs/networking.md).

---

## AWS Network Design

```text
VPC — 10.0.0.0/16

├── Public Application Subnet — 10.0.1.0/24
│   ├── Application EC2
│   └── NAT Gateway
│
├── Private Database Subnet — 10.0.10.0/24
│   └── PostgreSQL EC2
│
└── Private Redis Subnet — 10.0.20.0/24
    └── Redis EC2
```

The public subnet routes Internet traffic through an Internet Gateway. Both private subnets share a private route table whose default route uses the NAT Gateway for outbound package installation and updates.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Cloud | AWS |
| Infrastructure as Code | Terraform 1.15.8 |
| Configuration Management | Ansible |
| Operating System | Ubuntu 22.04 |
| Application | Django Status Page |
| Application Server | Gunicorn |
| Reverse Proxy | Nginx |
| Database | PostgreSQL |
| Cache / Queue | Redis |
| Background Jobs | RQ |
| Service Management | systemd |
| Secrets Management | Ansible Vault |
| Version Control | Git / GitHub |
| CI Validation | GitHub Actions — Terraform checks only |

---

## Security Highlights

![AEGIS Foundation Security Architecture](docs/diagrams/02-security-architecture.png)

- HTTPS `443` is the public application entry point.
- SSH `22` to the application host is restricted to the configured administrator CIDR.
- PostgreSQL `5432` accepts traffic only from the application security group.
- Redis `6379` accepts traffic only from the application security group.
- PostgreSQL and Redis have no public IP addresses.
- SSH to private hosts is allowed only from the application security group and is reached through ProxyJump.
- Gunicorn listens on `127.0.0.1:8001` only.
- Django development port `8000` is not exposed by the AWS Security Group.
- EC2 root volumes are encrypted.
- EC2 instances require IMDSv2 tokens.
- Django and database secrets are stored in an encrypted Ansible Vault file.

> The current dev environment uses a self-signed TLS certificate. Trusted TLS with a custom domain is a future hardening step.

See [Security Design](docs/security.md) for details.

---

## Production vs Testing

![AEGIS Production vs Testing Flow](docs/diagrams/03-production-vs-testing-flow.png)

Production and testing use the **same Application EC2 instance**. The difference is the access path:

- Production: `HTTPS :443 → Nginx → Gunicorn 127.0.0.1:8001 → Django`
- Testing: `localhost:8000 → SSH tunnel → Django runserver 127.0.0.1:8000`

Port `8000` is not publicly exposed.

---

## Infrastructure as Code

Terraform owns the AWS infrastructure state.

```text
terraform/
├── environments/
│   └── dev/
└── modules/
    ├── vpc/
    ├── security_groups/
    ├── ec2/
    ├── iam/
    └── vpc_endpoints/
```

The active `dev` environment currently calls only the `vpc`, `security_groups`, and `ec2` modules.

The `iam` and `vpc_endpoints` modules are retained as inactive/future hardening work and are **not part of the deployed current-state architecture**.

---

## Configuration Management

Ansible configures the three EC2 hosts after Terraform provisioning.

```text
ansible/
├── ansible.cfg
├── requirements.yml
├── inventories/dev/
├── playbooks/site.yml
└── roles/
    ├── common/
    ├── postgres/
    ├── redis/
    ├── status_page/
    ├── gunicorn/
    └── nginx/
```

| Role | Responsibility |
|---|---|
| `common` | Base OS configuration, hostname and package prerequisites |
| `postgres` | PostgreSQL installation, database/user creation and private network access |
| `redis` | Redis installation, private-interface binding and protected mode |
| `status_page` | Status Page application, Python environment and Django configuration |
| `gunicorn` | Gunicorn, RQ Worker and Scheduler systemd services |
| `nginx` | HTTPS ingress and reverse proxy configuration |

---

## Deployment Workflow

![AEGIS Foundation Deployment Workflow](docs/diagrams/04-deployment-automation-flow.png)

Deployment is currently **operator-driven**, not continuous deployment.

```text
Developer / WSL
      |
      +------> GitHub
      |          |
      |          +--> GitHub Actions
      |               Terraform CI validation only
      |
      v
Terraform
fmt -> validate -> plan -> apply
      |
      v
AWS Infrastructure
      |
      v
Ansible
      |
      +--> Application EC2
      +--> PostgreSQL EC2
      +--> Redis EC2
      |
      v
Runtime Validation
```

The existing GitHub Actions workflow runs Terraform formatting, initialization with `-backend=false`, and validation. It does **not** deploy infrastructure or application changes.

See [Deployment](docs/deployment.md) for the operational procedure.

---

## Validation

The foundation has been validated at multiple layers:

```bash
terraform fmt -check
terraform validate
terraform plan
```

The target final Terraform state is:

```text
No changes. Your infrastructure matches the configuration.
```

Ansible is re-run to verify configuration idempotency:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

Runtime checks include systemd services, listening ports, private PostgreSQL/Redis connectivity, the production HTTPS path, and the private SSH-tunneled testing path.

See [Validation](docs/validation.md) for the full checklist.

---

## Repository Structure

```text
.
├── terraform/          # AWS infrastructure
├── ansible/            # Host and application configuration
├── docs/               # Foundation documentation
├── aegis/              # Reserved for the future AEGIS core
├── status-page/        # Reserved project area
├── platform/           # Reserved platform extensions
├── tests/              # Project tests
└── .github/workflows/  # CI validation
```

The `aegis/` directory is intentionally still empty apart from repository scaffolding. Detection, investigation, AI agents and governed remediation belong to later phases.

---

## Foundation Status

| Component | Status |
|---|---|
| AWS VPC / subnet foundation | ✅ Deployed |
| Internet Gateway / routing | ✅ Deployed |
| NAT Gateway | ✅ Deployed |
| Security Groups | ✅ Deployed |
| Application EC2 | ✅ Deployed |
| PostgreSQL EC2 | ✅ Deployed |
| Redis EC2 | ✅ Deployed |
| Terraform IaC | ✅ Implemented |
| Ansible configuration | ✅ Implemented |
| Django Status Page | ✅ Running |
| Gunicorn | ✅ Running |
| RQ Worker / Scheduler | ✅ Running |
| Nginx | ✅ Running |
| HTTPS | ✅ Self-signed dev certificate |
| Private testing path | ✅ SSH tunnel |
| Terraform CI validation | ✅ GitHub Actions |
| AEGIS Core | ⏳ Next phase |

---

## Documentation

- [Architecture](docs/architecture.md)
- [Networking](docs/networking.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [Validation](docs/validation.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Disaster Recovery Posture](docs/disaster-recovery.md)

---

## Next Phase — AEGIS Core

Phase 1 deliberately stops at the platform foundation. The next phase will introduce the security-event pipeline and, later, the AEGIS detection, investigation, agent orchestration, policy, approval, and remediation layers.

Those components will be documented only as they are implemented so the repository continues to distinguish clearly between **deployed current state** and **planned architecture**.
