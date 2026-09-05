# Troubleshooting

This guide covers the supported `eks-dev` platform and follows the same ownership boundaries used in production: Git declares application state, Argo CD reconciles it, Kubernetes reports runtime health, and AWS services expose edge and security-pipeline signals.

## Start With the Final Acceptance Gate

Run the repository gate before changing infrastructure or credentials:

```bash
bash scripts/final-acceptance.sh
```

The first failing check identifies the control plane to investigate: repository state, Terraform validation, GitOps rendering, Argo health, workload rollout, DNS safety, RBAC, image digest, multi-AZ placement, or public HTTPS.

## Public Endpoint Returns `403 Forbidden`

### Expected cases

- AWS WAF intentionally blocks a request that matches a managed or custom rule.
- `/plugins/aegis/` requires an authenticated staff session.
- A stale browser session no longer carries valid Django authentication.

### Checks

1. Verify `/healthz` separately from the protected analyst route.
2. Confirm the browser is signed in with an active staff account.
3. Check the WAF sampled request and terminating rule before changing application authorization.
4. Preserve CSRF, authentication, and staff-only enforcement; do not bypass them to make the request succeed.

## Human Verdict Does Not Submit

### Checks

1. Confirm the analyst page contains a valid CSRF token and the session is still authenticated.
2. Verify the finding remains `PENDING_REVIEW`; verdicts are one-time conditional updates.
3. Confirm the Status-Page reviewer role can call `dynamodb:GetItem` and conditional `dynamodb:UpdateItem` on the findings table.
4. Inspect the application log for `ConditionalCheckFailedException`, which normally means another review already won the race.

Never replace the conditional write with an unconditional update: duplicate-review prevention is a data-integrity control.

## Analyzer Is Not Producing Findings

### Checks

1. Confirm the `security-events` queue has messages and the DLQ is not growing.
2. Verify the `aegis-security-analyzer` Deployment is Ready in `aegis-system`.
3. Confirm EKS Pod Identity is associated with the analyzer service account.
4. Check CloudWatch alarm and EventBridge delivery before debugging Bedrock.
5. Inspect analyzer logs for schema or semantic validation failure; invalid model output must not be persisted.

Messages are acknowledged only after successful validation and persistence. Repeated failures follow normal SQS retry and DLQ behavior.

## Argo CD Is `OutOfSync` or `Degraded`

### Checks

1. Compare the protected Git desired state with the rendered `gitops/eks-dev` manifests.
2. Inspect the Argo CD Application condition and failed resource, including the `PreSync` migration Job.
3. Verify that the deployed image digest matches the accepted promotion pull request.
4. Resolve the declarative source and let Argo CD reconcile; do not patch the live workload as the primary fix.

## Workload Rollout Is Stuck

### Checks

1. Inspect Pod scheduling events, readiness/liveness probes, image pulls, and Secret references.
2. Verify topology spread and Pod Disruption Budget constraints can be satisfied across both Availability Zones.
3. Check node Pod-density and Karpenter capacity signals before weakening availability controls.
4. Confirm the migration Job completed before application rollout.

## Grafana or Platform Health Is Unavailable

### Checks

1. Confirm the `aegis-observability` Argo CD Application is `Synced / Healthy`.
2. Verify Prometheus, Grafana, kube-state-metrics, and node-exporter are Ready in `monitoring`.
3. Confirm the user is authenticated as staff before opening the same-origin Grafana gateway.
4. Check node-exporter scheduling and Pod-density; it uses `system-cluster-critical` priority to protect node telemetry.

Grafana remains `ClusterIP`-only and anonymous access remains disabled.

## DNS or HTTPS Is Unhealthy

### Checks

1. Resolve `app.aegis-project.ddnsfree.com` and compare the target with the public ALB.
2. Verify the ACM certificate is issued and attached to the HTTPS listener.
3. Confirm the Ingress, ALB target health, and `/healthz` response.
4. Keep ExternalDNS in `--dry-run` unless an explicitly reviewed operational change authorizes live Dynu mutation.

## Terraform Validation Fails

The supported environment is only:

```text
terraform/environments/eks-dev
```

Run formatting, initialize without backend state, and validate. CI intentionally validates configuration without applying infrastructure; planning and apply remain explicit operational actions.

## Troubleshooting Principle

Identify the first failing boundary before changing architecture or credentials:

```text
edge request
  -> WAF / ALB
  -> Kubernetes Ingress / Service
  -> Status-Page or analyzer workload
  -> managed data / queue / AI service
  -> GitOps and observability evidence
```

Prefer evidence from the owning plane and preserve fail-closed controls while diagnosing.
