# Architecture Diagram Set

The diagram folder contains two generations of visual material.

## Final EKS Architecture — authoritative

The following Mermaid source files describe the accepted final showcase architecture. Each diagram intentionally answers one architectural question rather than combining every subsystem into one crowded poster.

| Diagram | Question answered |
|---|---|
| [`10-final-platform.mmd`](10-final-platform.mmd) | What are the major runtime, data, delivery, DNS, and security components? |
| [`11-ci-cd-gitops.mmd`](11-ci-cd-gitops.mmd) | How does source become an immutable artifact and then reach EKS? |
| [`12-security-event-pipeline.mmd`](12-security-event-pipeline.mmd) | How does a WAF security signal become a human-reviewed AI finding? |
| [`13-kubernetes-ha.mmd`](13-kubernetes-ha.mmd) | How are workloads distributed and kept resilient across nodes/AZs? |
| [`14-identity-trust.mmd`](14-identity-trust.mmd) | Which identities can call AWS/Kubernetes resources, and where are trust boundaries? |
| [`15-observability.mmd`](15-observability.mmd) | Which signals belong to Prometheus/Grafana vs CloudWatch? |

These `.mmd` files can be rendered with any Mermaid-compatible renderer. The source itself remains reviewable in Git.

## Historical Phase 1 PNGs — non-authoritative for final runtime

The following images are retained as **project-evolution evidence**:

- `01-aws-network-architecture.png`
- `02-security-architecture.png`
- `03-production-vs-testing-flow.png`
- `04-deployment-automation-flow.png`

They describe the earlier EC2/Ansible phase and must not be presented as the final `eks-dev` architecture.

The final environment uses:

```text
VPC 10.10.0.0/16
private EKS workers
RDS PostgreSQL Multi-AZ
ElastiCache Redis Multi-AZ
ALB + ACM + WAF
Argo CD GitOps
Prometheus / Grafana
ExternalDNS + Dynu webhook (dry-run)
```

For narrative architecture documentation, see [`../architecture.md`](../architecture.md).
