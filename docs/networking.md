# Networking

> [!NOTE]
> This document describes the **final `eks-dev` showcase network**. The original EC2/Ansible network is retained only as project-evolution evidence under `terraform/environments/dev` and the historical PNG diagrams.

## Current VPC

AEGIS runs the modern platform in:

```text
VPC: 10.10.0.0/16
Region: us-east-1
Availability Zones: us-east-1a, us-east-1b
```

The VPC is split into four functional subnet tiers in each Availability Zone:

| Tier | Exposure | Purpose |
|---|---|---|
| Public | Internet-routable | Internet-facing ALB and NAT Gateway infrastructure |
| EKS control plane | dedicated | EKS control-plane network interfaces |
| EKS node / Pod | private | worker nodes and VPC-CNI Pod addresses |
| Data | private | RDS PostgreSQL and ElastiCache Redis |

The design uses NAT egress per Availability Zone. Worker nodes and managed data services do not require public IP addresses.

## Public Request Path

The public application path is:

```text
Internet
   |
Dynu DNS
   | app.aegis-project.ddnsfree.com
   v
Internet-facing ALB :443
   |-- ACM certificate attached
   `-- AWS WAF Web ACL associated
   |
Kubernetes Ingress
   |
ClusterIP Service :8080
   |
Nginx (unprivileged) :8080
   |
Gunicorn / Django :8000
```

HTTP port `80` is used only to redirect clients to HTTPS. AWS WAF is associated with the ALB; it is a protection/control plane on that edge resource, not a separate network hop after the load balancer.

## DNS Boundary

The implemented hostname is:

```text
app.aegis-project.ddnsfree.com
```

Dynu is the DNS provider. Route 53 is **not** part of the implemented architecture.

The repository includes ExternalDNS plus an AEGIS Dynu webhook provider, but final acceptance intentionally keeps ExternalDNS in:

```text
--dry-run
```

Therefore the accepted state proves controller health, target discovery, and safety boundaries without claiming active automated Dynu mutation.

## Application and Data Flows

The important service paths are:

```text
ALB / Ingress  -> Status-Page Service :8080
Status-Page    -> RDS PostgreSQL :5432
Status-Page    -> ElastiCache Redis :6379 over TLS
Analyzer       -> AWS APIs through private-node egress
Prometheus     -> Kubernetes workload / node metrics
```

RDS and Redis are reachable only through their private network/security-group relationships. They are not public application endpoints.

## Security Boundaries

The final design follows these principles:

- EKS worker nodes are private and have no public IPs;
- Pods receive VPC addresses through the AWS VPC CNI;
- public exposure is concentrated at the ALB/WAF boundary;
- PostgreSQL `5432` and Redis `6379` are private service paths;
- the Status-Page Kubernetes Service is `ClusterIP` rather than directly Internet-facing;
- Grafana is also `ClusterIP`-only and is reached through the staff-authorized same-origin application path;
- workload AWS access uses Pod Identity rather than embedding AWS credentials in networked hosts or images.

## EKS API Access

The cluster API supports both private access from inside the VPC and restricted public administrative access. The worker plane does not depend on public worker-node addressing.

## Availability Characteristics

Network resilience is designed around two Availability Zones:

- public and private tiers exist in both AZs;
- NAT egress is provided per AZ;
- Status-Page replicas use topology spread across AZs;
- RDS is Multi-AZ;
- Redis uses Multi-AZ replication and automatic failover.

This is a **multi-AZ, single-region** architecture. AEGIS does not claim multi-region active/active networking or cross-region disaster recovery.

## Historical Phase 1 Network

The original project phase used a separate `10.0.0.0/16` EC2-oriented network with an application EC2 instance, PostgreSQL EC2, Redis EC2, and a single NAT Gateway. Those files and diagrams remain in the repository to demonstrate project evolution, but they are not the final runtime architecture.

See:

- [`architecture.md`](architecture.md) for the complete final topology;
- [`diagrams/README.md`](diagrams/README.md) for final versus historical diagram labeling;
- [`phase-1-1-platform-modernization.md`](phase-1-1-platform-modernization.md) for the migration story.
