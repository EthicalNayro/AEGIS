# AEGIS EKS Development Environment

This environment contains the parallel Phase 1.1 platform modernization.

It does not replace or modify `terraform/environments/dev` yet.

## Network

```text
VPC 10.10.0.0/16

AZ-A
├── Public
├── EKS control plane
├── Private EKS nodes / Pods
└── Private data

AZ-B
├── Public
├── EKS control plane
├── Private EKS nodes / Pods
└── Private data
```

Internet-facing load balancers are placed in public subnets.

EKS worker nodes and Pods are placed in private subnets.

Dedicated small subnets are reserved for EKS control-plane ENIs.

RDS and ElastiCache will use isolated private data subnets.

The development environment defaults to one NAT Gateway to reduce cost.
The VPC module supports one NAT Gateway per Availability Zone for a
higher-availability deployment.

No EKS cluster or managed data service is created at this milestone.
