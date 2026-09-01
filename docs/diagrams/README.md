# Architecture Diagram Set

This folder contains the **authoritative final EKS architecture views**, their editable Mermaid sources, and a small set of historical Phase 1 diagrams retained only as project-evolution evidence.

## Portfolio architecture views — authoritative

These rendered SVG diagrams are the primary visual architecture set used by the repository README:

| Diagram | Architectural question |
|---|---|
| [`20-aegis-final-platform.svg`](20-aegis-final-platform.svg) | How do the public edge, private EKS runtime, managed data services, security/AI services, GitOps delivery, and DNS boundary fit together? |
| [`21-aegis-security-human-decision.svg`](21-aegis-security-human-decision.svg) | How does a WAF security signal become a validated, human-reviewed AI finding? |
| [`22-aegis-secure-cicd-gitops.svg`](22-aegis-secure-cicd-gitops.svg) | How does source become an immutable artifact and reach EKS without granting CI direct cluster deployment authority? |
| [`23-aegis-resilience-observability.svg`](23-aegis-resilience-observability.svg) | How are workloads distributed and recovered across AZs, and how is the platform observed? |

The portfolio SVGs use the same clean AEGIS infographic language as the project's original architecture boards: a white presentation surface, navy/blue hierarchy, color-coded trust and service domains, rounded component cards, and explicit directional flows. They remain text-based SVGs so they stay sharp in GitHub and easy to review. The focused Mermaid sources below remain the engineering source of truth for detailed topology questions.

## Editable final sources

The focused Mermaid sources remain the reviewable engineering source of truth for detailed topology questions:

| Source | Focus |
|---|---|
| [`10-final-platform.mmd`](10-final-platform.mmd) | final runtime, data, delivery, DNS, and security components |
| [`11-ci-cd-gitops.mmd`](11-ci-cd-gitops.mmd) | immutable CI/CD and Argo CD GitOps flow |
| [`12-security-event-pipeline.mmd`](12-security-event-pipeline.mmd) | WAF event processing, Bedrock analysis, persistence, and human review |
| [`13-kubernetes-ha.mmd`](13-kubernetes-ha.mmd) | multi-AZ placement, PDBs, workers, scheduler, Karpenter, and managed data services |
| [`14-identity-trust.mmd`](14-identity-trust.mmd) | GitHub OIDC, EKS Pod Identity, namespace RBAC, and trust boundaries |
| [`15-observability.mmd`](15-observability.mmd) | Prometheus/Grafana, CloudWatch, and Argo CD health signals |

## Historical Phase 1 PNGs — non-authoritative

The following images document the earlier EC2/Ansible phase and are kept only to show the project's evolution:

- `01-aws-network-architecture.png`
- `02-security-architecture.png`
- `03-production-vs-testing-flow.png`
- `04-deployment-automation-flow.png`

They **must not** be presented as the current `eks-dev` architecture.

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
