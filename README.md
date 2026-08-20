# AEGIS — Status Page Platform

Production-oriented DevOps platform for deploying and operating a Django-based Status Page application on AWS.

The project combines:

- AWS infrastructure provisioned with Terraform
- Server configuration and application deployment with Ansible
- Private PostgreSQL and Redis backend services
- Nginx + Gunicorn production runtime
- HTTPS ingress
- Secure SSH-based development/testing access
- Ansible Vault for secret management

---

## Architecture

```text
                         Internet
                            |
                            | HTTPS :443
                            v
                    +----------------+
                    |     Nginx      |
                    +----------------+
                            |
                            | 127.0.0.1:8001
                            v
                    +----------------+
                    |    Gunicorn    |
                    +----------------+
                            |
                            v
                    +----------------+
                    | Django /       |
                    | Status Page    |
                    +----------------+
                       /          \
                      /            \
                     v              v
              PostgreSQL           Redis
                 :5432             :6379
                                      |
                               +------+------+
                               |             |
                               v             v
                           RQ Worker     Scheduler
```

The application server is publicly accessible only through HTTPS.

PostgreSQL and Redis run on separate EC2 instances inside private subnets and do not have public IP addresses.

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

Private instances use the NAT Gateway for outbound package installation and updates while remaining inaccessible directly from the Internet.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Cloud | AWS |
| Infrastructure as Code | Terraform |
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

---

## Security Highlights

The platform is designed around minimizing unnecessary network exposure.

- PostgreSQL is accessible only from the application server on TCP `5432`.
- Redis is accessible only from the application server on TCP `6379`.
- PostgreSQL and Redis have no public IP addresses.
- Gunicorn listens only on `127.0.0.1:8001`.
- Django development port `8000` is not exposed publicly.
- Production traffic enters through Nginx over HTTPS on TCP `443`.
- SSH access to private instances is performed through the application server using `ProxyJump`.
- Application secrets are encrypted using Ansible Vault.
- EC2 root volumes are encrypted.
- EC2 instances require IMDSv2.

> The current development environment uses a self-signed TLS certificate. A trusted certificate and domain are planned as a future hardening step.

---

## Production vs Development

### Production

```text
Internet
   |
   | HTTPS :443
   v
Nginx
   |
   | localhost :8001
   v
Gunicorn
   |
   v
Django
```

### Development / Testing

The Django development server can still be used without exposing port `8000` to the Internet.

```text
Developer Machine
       |
       | SSH Tunnel
       v
Application EC2
       |
       | 127.0.0.1:8000
       v
Django Development Server
```

Start the Django development server on the application host:

```bash
sudo -u status-page bash -c '
cd /opt/status-page &&
/opt/status-page/venv/bin/python \
statuspage/manage.py \
runserver 127.0.0.1:8000 --insecure --noreload
'
```

Create the SSH tunnel from the developer machine:

```bash
ssh -L 8000:127.0.0.1:8000 aegis-app
```

The application can then be accessed locally through:

```text
http://localhost:8000
```

This keeps the testing interface private:

```text
Public :8000        -> blocked
localhost :8000     -> development/testing
Public :443         -> production traffic
localhost :8001     -> Gunicorn
```

---

## Infrastructure as Code

Terraform manages the AWS infrastructure.

```text
terraform/
├── environments/
│   └── dev/
│       ├── main.tf
│       ├── outputs.tf
│       ├── variables.tf
│       ├── versions.tf
│       └── terraform.tfvars.example
│
└── modules/
    ├── vpc/
    ├── security_groups/
    ├── ec2/
    ├── iam/
    └── vpc_endpoints/
```

The currently deployed environment includes:

- VPC
- Internet Gateway
- Public and private subnets
- Public and private route tables
- NAT Gateway
- Elastic IP
- Security Groups
- Application EC2 instance
- PostgreSQL EC2 instance
- Redis EC2 instance

The `iam` and `vpc_endpoints` modules are retained for future platform hardening and are not currently active in the deployed environment.

---

## Configuration Management

Ansible configures the operating systems and application stack.

```text
ansible/
├── ansible.cfg
├── requirements.yml
│
├── inventories/
│   └── dev/
│       ├── hosts.ini
│       └── group_vars/
│           └── all/
│               ├── main.yml
│               └── vault.yml
│
├── playbooks/
│   └── site.yml
│
└── roles/
    ├── common/
    ├── postgres/
    ├── redis/
    ├── status_page/
    ├── gunicorn/
    └── nginx/
```

Role responsibilities:

| Role | Responsibility |
|---|---|
| `common` | Base OS configuration and packages |
| `postgres` | PostgreSQL installation, database and network access |
| `redis` | Redis installation and private interface configuration |
| `status_page` | Django Status Page installation and configuration |
| `gunicorn` | Gunicorn, RQ and Scheduler systemd services |
| `nginx` | HTTPS ingress and reverse proxy configuration |

---

## Deployment Flow

```text
Developer
    |
    v
Terraform
    |
    v
AWS Infrastructure
    |
    v
Ansible
    |
    +------ Application Server
    |
    +------ PostgreSQL Server
    |
    +------ Redis Server
    |
    v
Runtime Validation
```

Terraform owns infrastructure state.

Ansible owns server and application configuration.

This separation allows infrastructure and configuration changes to be managed independently while remaining reproducible.

---

## Validation

Terraform configuration is validated using:

```bash
terraform fmt -check
terraform validate
terraform plan
```

The expected final Terraform state is:

```text
No changes. Your infrastructure matches the configuration.
```

Ansible deployment is validated using:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

The roles are designed to be idempotent so repeated runs do not unnecessarily modify already-correct configuration.

Production services can be verified with:

```bash
sudo systemctl is-active nginx
sudo systemctl is-active status-page
sudo systemctl is-active status-page-rq
sudo systemctl is-active status-page-scheduler
```

Expected production listeners:

```text
TCP/443              -> Nginx
127.0.0.1:8001       -> Gunicorn
TCP/8000             -> Not publicly exposed
```

Backend connectivity can be validated from the application server:

```bash
nc -vz 10.0.10.39 5432
nc -vz 10.0.20.141 6379
```

These tests validate private application-to-PostgreSQL and application-to-Redis communication.

---

## Repository Structure

```text
.
├── terraform/
│   ├── environments/
│   └── modules/
│
├── ansible/
│   ├── inventories/
│   ├── playbooks/
│   └── roles/
│
├── platform/
│   ├── monitoring/
│   ├── security/
│   ├── config/
│   └── scripts/
│
├── status-page/
├── aegis/
├── tests/
├── docs/
└── .github/
    └── workflows/
```

---

## Current Status

| Component | Status |
|---|---|
| AWS Infrastructure | ✅ |
| Terraform | ✅ |
| Public / Private Networking | ✅ |
| NAT Gateway | ✅ |
| Security Groups | ✅ |
| Application EC2 | ✅ |
| PostgreSQL | ✅ |
| Redis | ✅ |
| Ansible Automation | ✅ |
| Django Status Page | ✅ |
| Gunicorn | ✅ |
| RQ Worker | ✅ |
| Scheduler | ✅ |
| Nginx | ✅ |
| HTTPS | ✅ Self-signed |
| Private Development Access | ✅ |

---

## Documentation

Detailed project documentation is maintained under `docs/`.

Planned documentation includes:

- `docs/architecture.md`
- `docs/deployment.md`
- `docs/security.md`
- `docs/validation.md`
- `docs/diagrams/`
- `docs/screenshots/`

---

## Future Improvements

Planned platform improvements include:

- Trusted TLS certificate and custom domain
- AWS Systems Manager private instance management
- VPC Interface Endpoints / AWS PrivateLink
- Stronger IAM automation
- Monitoring and observability
- Centralized logging
- Automated PostgreSQL backups
- CI/CD deployment pipeline
- Automated infrastructure testing
- Application health checks
- High availability and Auto Scaling
- AEGIS security automation layer

---

## Design Principles

1. Infrastructure should be reproducible.
2. Configuration should be automated and idempotent.
3. Backend services should remain private.
4. Internet-facing exposure should be minimized.
5. Secrets must not be stored in plaintext.
6. Development interfaces should not become production interfaces.
7. Infrastructure and configuration management should remain separated.
8. Security controls should be part of the architecture from the beginning.
