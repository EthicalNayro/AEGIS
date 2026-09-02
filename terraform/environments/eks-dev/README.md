# AEGIS EKS Environment

`eks-dev` is the authoritative Terraform environment for AEGIS. It defines the AWS infrastructure used by the validated showcase platform; there is no second legacy environment in the active source tree.

## Managed infrastructure

- multi-AZ VPC with public, EKS control-plane, private worker/Pod, and private data subnets;
- Amazon EKS, managed baseline nodes, Pod Identity integration, and Karpenter prerequisites;
- RDS PostgreSQL and ElastiCache Redis with encryption and multi-AZ controls;
- ECR, ALB/WAF integration, WAF logging, CloudWatch alarms, and dashboards;
- EventBridge, SQS/DLQ, DynamoDB findings storage, and workload IAM roles;
- GitHub Actions OIDC trust constrained to the delivery branch.

Kubernetes workload desired state is deliberately separate under `gitops/eks-dev/`; Argo CD, not Terraform or CI, reconciles application workloads.

## Network

```text
VPC 10.10.0.0/16
├── AZ A: public | EKS control plane | private workers/Pods | private data
└── AZ B: public | EKS control plane | private workers/Pods | private data
```

The environment defaults to one NAT Gateway for cost-controlled development. Set `single_nat_gateway = false` for one NAT Gateway per Availability Zone.

## Validation

```bash
terraform fmt -check -recursive ../..
terraform init -backend=false
terraform validate
```

Infrastructure apply is an explicit operator action. GitHub Actions validates this environment but has no EKS deployment permission and does not run `terraform apply`.
