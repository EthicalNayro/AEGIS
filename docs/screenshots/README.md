# Validation Evidence Index

This directory contains incremental visual evidence captured while building AEGIS.

The images are evidence of specific validation milestones; they are not intended to replace the architecture and validation documentation.

## EKS Security, Resilience, and Scaling

| # | File | What it validates |
|---|---|---|
| 44 | [`44-eks-multi-az-nodes-ready.png`](44-eks-multi-az-nodes-ready.png) | EKS nodes ready across Availability Zones |
| 45 | [`45-aegis-system-namespace-pod-security.png`](45-aegis-system-namespace-pod-security.png) | Pod Security Admission labels on `aegis-system` |
| 46 | [`46-kubernetes-rbac-least-privilege.png`](46-kubernetes-rbac-least-privilege.png) | least-privilege Kubernetes RBAC |
| 47 | [`47-pod-security-restricted-denies-insecure-pod.png`](47-pod-security-restricted-denies-insecure-pod.png) | restricted Pod Security rejects an unsafe Pod |
| 48 | [`48-secure-workload-health-probes-running.png`](48-secure-workload-health-probes-running.png) | hardened workload running with health probes |
| 49 | [`49-kubernetes-self-healing-pod-replacement.png`](49-kubernetes-self-healing-pod-replacement.png) | Kubernetes replaces a failed Pod |
| 50 | [`50-topology-spread-multi-az-pods.png`](50-topology-spread-multi-az-pods.png) | topology spread places replicas across AZs |
| 51 | [`51-pdb-node-drain-availability-protection.png`](51-pdb-node-drain-availability-protection.png) | Pod Disruption Budget protects availability during drain |
| 52 | [`52-metrics-server-resource-metrics.png`](52-metrics-server-resource-metrics.png) | Metrics Server exposes workload utilization |
| 53 | [`53-hpa-automatic-scale-up-under-load.png`](53-hpa-automatic-scale-up-under-load.png) | demo HPA scales up under load |
| 54 | [`54-hpa-automatic-scale-down-recovery.png`](54-hpa-automatic-scale-down-recovery.png) | demo HPA scales down after recovery |
| 55 | [`55-karpenter-automatic-node-scale-up.png`](55-karpenter-automatic-node-scale-up.png) | Karpenter adds node capacity automatically |
| 56a | [`56-karpenter-automatic-scale-down-consolidation1.png`](56-karpenter-automatic-scale-down-consolidation1.png) | Karpenter consolidation begins |
| 56b | [`56-karpenter-automatic-scale-down-consolidation2.png`](56-karpenter-automatic-scale-down-consolidation2.png) | unused capacity is removed after consolidation |

## Public Edge and Security Telemetry

| # | File | What it validates |
|---|---|---|
| 57 | [`57-aws-load-balancer-controller-ready.png`](57-aws-load-balancer-controller-ready.png) | AWS Load Balancer Controller readiness |
| 58 | [`58-aegis-public-alb-ingress-working.png`](58-aegis-public-alb-ingress-working.png) | public ALB ingress reaches AEGIS |
| 59 | [`59-acm-dns-validation-certificate-issued.png`](59-acm-dns-validation-certificate-issued.png) | ACM certificate issued after DNS validation |
| 60 | [`60-aegis-https-tls-working.png`](60-aegis-https-tls-working.png) | public HTTPS/TLS path works |
| 61 | [`61-aws-waf-blocks-malicious-xss-request.png`](61-aws-waf-blocks-malicious-xss-request.png) | AWS WAF blocks a controlled XSS request |
| 62 | [`62-aegis-is-healthy.png`](62-aegis-is-healthy.png) | public AEGIS health endpoint |
| 63 | [`63-rate-limiter.png`](63-rate-limiter.png) | rate-limit rule configuration used during validation |
| 64 | [`64-aws-waf-rate-limiting-blocks-excessive-requests.png`](64-aws-waf-rate-limiting-blocks-excessive-requests.png) | excessive-request blocking at the validation threshold |
| 65 | [`65-aws-waf-blocked-xss-security-event-logging.png`](65-aws-waf-blocked-xss-security-event-logging.png) | blocked XSS request appears in WAF logs |
| 66 | [`66-aegis-cloudwatch-security-observability-dashboard.png`](66-aegis-cloudwatch-security-observability-dashboard.png) | CloudWatch security observability dashboard |
| 67 | [`67-cloudwatch-waf-security-alarm-triggered.png`](67-cloudwatch-waf-security-alarm-triggered.png) | WAF security alarm transitions to alarm state |
| 68 | [`68-eventbridge-routes-security-alarm-to-sqs.png`](68-eventbridge-routes-security-alarm-to-sqs.png) | EventBridge routes the security alarm to SQS |
| 69 | [`69-eventbridge-routes-cloudwatch-alarm-to-sqs.png`](69-eventbridge-routes-cloudwatch-alarm-to-sqs.png) | CloudWatch alarm event arrives in SQS |
| 70 | [`70-sqs-security-events-dlq-redrive-policy.png`](70-sqs-security-events-dlq-redrive-policy.png) | SQS queue and DLQ redrive policy |

## Analyzer, AI, and Human Governance

| # | File | What it validates |
|---|---|---|
| 71 | [`71-eks-pod-identity-security-analyzer-role.png`](71-eks-pod-identity-security-analyzer-role.png) | analyzer workload identity and IAM role |
| 72 | [`72-aegis-security-analyzer-processes-sqs-event.png`](72-aegis-security-analyzer-processes-sqs-event.png) | analyzer consumes an SQS security event |
| 73 | [`73-aegis-analyzer-enriches-waf-security-event.png`](73-aegis-analyzer-enriches-waf-security-event.png) | analyzer enriches the event with WAF evidence |
| 74 | [`74-aegis-bedrock-ai-security-classification.png`](74-aegis-bedrock-ai-security-classification.png) | Bedrock returns structured security classification |
| 75 | [`75-aegis-ai-finding-persisted-to-dynamodb.png`](75-aegis-ai-finding-persisted-to-dynamodb.png) | AI finding persisted to DynamoDB |
| 76 | [`76-aegis-persisted-security-finding-human-readable.png`](76-aegis-persisted-security-finding-human-readable.png) | persisted finding remains human-readable |
| 77 | [`77-aegis-human-review-feedback-recorded.png`](77-aegis-human-review-feedback-recorded.png) | human review feedback is recorded |
| 78 | [`78-aegis-ai-quality-feedback-metrics.png`](78-aegis-ai-quality-feedback-metrics.png) | AI quality metrics derived from reviewed findings |
| 79 | [`79-aegis-cloudwatch-ai-quality-feedback-dashboard.png`](79-aegis-cloudwatch-ai-quality-feedback-dashboard.png) | CloudWatch AI-quality dashboard |
| 80 | [`80-aegis-reviewer-least-privilege-validation.png`](80-aegis-reviewer-least-privilege-validation.png) | reviewer least-privilege access |
| 81 | [`81-aegis-human-review-web-ui.png`](81-aegis-human-review-web-ui.png) | staff-only Human Review web UI |
| 81b | [`81b-aegis-new-pending-review-finding.png`](81b-aegis-new-pending-review-finding.png) | new finding reaches the UI as `PENDING_REVIEW` |
| 82 | [`82-aegis-public-https-human-review-platform.png`](82-aegis-public-https-human-review-platform.png) | public HTTPS application and protected review platform |

## GitOps, Delivery, and Observability

| # | File | What it validates |
|---|---|---|
| 83 | [`83-aegis-argocd-gitops-synced-healthy.png`](83-aegis-argocd-gitops-synced-healthy.png) | Argo CD Application is `Synced` and `Healthy` |
| 85 | [`85-aegis-secure-ci-oidc-ecr-gitops.png`](85-aegis-secure-ci-oidc-ecr-gitops.png) | OIDC, ECR, GitOps update, and runtime digest evidence |
| 86 | [`86-aegis-argocd-presync-database-migration.png`](86-aegis-argocd-presync-database-migration.png) | Argo CD `PreSync` database migration |
| 87 | [`87-aegis-sbom-idempotent-ci-rerun.png`](87-aegis-sbom-idempotent-ci-rerun.png) | SBOM generation and idempotent CI rerun |
| 88 | [`88-aegis-multistage-runtime-hardening.png`](88-aegis-multistage-runtime-hardening.png) | hardened multi-stage runtime rollout |
| 89 | [`89-aegis-final-gitops-runtime-verification.png`](89-aegis-final-gitops-runtime-verification.png) | final GitOps/runtime acceptance |
| 90 | [`90-aegis-prometheus-grafana-gitops-synced.png`](90-aegis-prometheus-grafana-gitops-synced.png) | Prometheus/Grafana GitOps health |
| 91 | [`91-aegis-grafana-kubernetes-observability.png`](91-aegis-grafana-kubernetes-observability.png) | Kubernetes observability for `aegis-system` |
| 94 | [`94-aegis-security-command-center.png`](94-aegis-security-command-center.png) | final AEGIS analyst command center |

Evidence number 84 was intentionally left unused. Captures 92 and 93 are referenced by the final validation convention but were not present in the supplied screenshot archive, so they are not represented as committed files.

## Evidence Guidelines

- Do not capture credentials, secret plaintext, database passwords, private keys, or account secrets.
- Prefer screenshots that prove one clear milestone.
- Keep architecture claims in Markdown documentation; use screenshots only as supporting evidence.
- New evidence should use descriptive file names and continue with the next unused sequence number.
