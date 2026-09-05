# Authoritative Architecture Diagrams

This directory intentionally contains one curated set of four production-state AEGIS views. These are the only architecture diagrams embedded by the repository and portfolio documentation.

| Diagram | Architectural question |
|---|---|
| [`20-aegis-final-platform.png`](20-aegis-final-platform.png) | How do the public edge, private EKS runtime, managed data plane, AI services, GitOps delivery, and DNS safety boundary fit together? |
| [`21-aegis-security-human-decision.png`](21-aegis-security-human-decision.png) | How does a WAF signal become validated data, an advisory AI classification, and a one-time human verdict? |
| [`22-aegis-secure-cicd-gitops.png`](22-aegis-secure-cicd-gitops.png) | How does CI produce a validated immutable artifact and promote it through a protected GitOps pull request without direct EKS authority? |
| [`23-aegis-resilience-observability.png`](23-aegis-resilience-observability.png) | How do multi-AZ placement, PDBs, recovery capacity, managed data services, Prometheus/Grafana, and CloudWatch provide resilience and visibility? |

The set uses a consistent presentation language: clear numbered views, explicit trust boundaries, service-native icons, directional flows, concise governance callouts, and a legend on every dense topology board.

> [!IMPORTANT]
> Documentation should link only to these four files. New diagrams must describe the accepted `eks-dev` state and replace an existing view rather than introduce a competing architecture set.

## Accepted final environment

```text
VPC 10.10.0.0/16
private EKS workers across 2 AZs
RDS PostgreSQL Multi-AZ
ElastiCache Redis Multi-AZ / TLS
ALB + ACM + AWS WAF
AEGIS Analyzer + Amazon Bedrock + DynamoDB findings
human-in-the-loop review
GitHub OIDC + immutable ECR + Argo CD GitOps
Prometheus / Grafana + CloudWatch
ExternalDNS + Dynu webhook in deliberate --dry-run safety mode
```

For narrative architecture documentation and engineering boundaries, see [`../architecture.md`](../architecture.md).
