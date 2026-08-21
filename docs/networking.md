# Networking

## VPC

The AEGIS foundation uses a single VPC:

```text
10.0.0.0/16
```

![AEGIS Foundation Network Architecture](diagrams/01-aws-network-architecture.png)

Subnets:

| Tier | CIDR | Exposure | Primary Workload |
|---|---|---|---|
| Public application | `10.0.1.0/24` | Public | Application EC2 + NAT Gateway |
| Private database | `10.0.10.0/24` | Private | PostgreSQL EC2 |
| Private Redis | `10.0.20.0/24` | Private | Redis EC2 |

## Routing

The public subnet is associated with a public route table whose default route points to the Internet Gateway.

```text
0.0.0.0/0 -> Internet Gateway
```

The database and Redis subnets share a private route table whose default route points to the NAT Gateway in the public subnet.

```text
0.0.0.0/0 -> NAT Gateway
```

This provides outbound package access to the private hosts without assigning them public IP addresses.

## Security Group Flows

### Application Security Group

Inbound:

- TCP `443` from `0.0.0.0/0`
- TCP `22` from the configured administrator CIDR only

Outbound:

- Current implementation allows outbound traffic from the application host.

### PostgreSQL Security Group

Inbound:

- TCP `5432` from the Application Security Group only
- TCP `22` from the Application Security Group only

Outbound:

- TCP `80` for package updates
- TCP `443` for package updates

### Redis Security Group

Inbound:

- TCP `6379` from the Application Security Group only
- TCP `22` from the Application Security Group only

Outbound:

- TCP `80` for package updates
- TCP `443` for package updates

## Allowed Paths

```text
Internet --------443--------> Application EC2
Admin CIDR ------22---------> Application EC2
Application ----5432--------> PostgreSQL EC2
Application ----6379--------> Redis EC2
Application -----22---------> PostgreSQL / Redis for ProxyJump administration
```

The following are not part of the public exposure model:

```text
Internet -> PostgreSQL :5432  BLOCKED
Internet -> Redis :6379       BLOCKED
Internet -> Django :8000      BLOCKED
Internet -> Gunicorn :8001    BLOCKED
```

## NAT Design

A single NAT Gateway is used for the current development foundation to keep cost and complexity reasonable. This is not a multi-AZ highly available NAT design.

That trade-off is intentional for Phase 1 and should be revisited if the platform moves to a production high-availability model.
