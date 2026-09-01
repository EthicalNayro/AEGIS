#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PASS_COUNT=0
TMP_RENDER="$(mktemp)"
trap 'rm -f "$TMP_RENDER"' EXIT

pass() {
  printf 'PASS  %s\n' "$1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  printf 'FAIL  %s\n' "$1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

for cmd in git kubectl curl terraform awk grep sort wc; do
  require_cmd "$cmd"
done

printf 'AEGIS final acceptance\n'
printf 'Repository: %s\n\n' "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  git status --short
  fail "repository working tree is not clean"
fi
pass "repository working tree is clean"

terraform -chdir=terraform/environments/eks-dev fmt -check -recursive >/dev/null
terraform -chdir=terraform/environments/eks-dev validate >/dev/null
pass "Terraform eks-dev formatting and validation"

kubectl kustomize gitops/eks-dev >"$TMP_RENDER"
[[ -s "$TMP_RENDER" ]] || fail "GitOps render is empty"
kubectl apply --dry-run=client --validate=false -f "$TMP_RENDER" >/dev/null
pass "GitOps render and Kubernetes client dry-run"

argo_state() {
  local app="$1"
  kubectl -n argocd get application "$app" \
    -o jsonpath='{.status.sync.status}{" "}{.status.health.status}'
}

[[ "$(argo_state aegis-status-page)" == "Synced Healthy" ]] \
  || fail "aegis-status-page is not Synced Healthy"
pass "Argo CD aegis-status-page is Synced Healthy"

[[ "$(argo_state aegis-observability)" == "Synced Healthy" ]] \
  || fail "aegis-observability is not Synced Healthy"
pass "Argo CD aegis-observability is Synced Healthy"

kubectl -n aegis-system rollout status deployment/aegis-status-page --timeout=120s >/dev/null
pass "Status-Page deployment rollout is complete"

kubectl -n aegis-system rollout status deployment/aegis-external-dns --timeout=120s >/dev/null
pass "ExternalDNS deployment rollout is complete"

EXTERNAL_DNS_ARGS="$(kubectl -n aegis-system get deployment aegis-external-dns \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="external-dns")].args}')"
grep -q -- '--dry-run' <<<"$EXTERNAL_DNS_ARGS" \
  || fail "ExternalDNS is not in the expected dry-run safety mode"
pass "ExternalDNS remains in dry-run safety mode"

[[ "$(kubectl auth can-i list ingresses.networking.k8s.io \
  --as=system:serviceaccount:aegis-system:aegis-external-dns \
  -n aegis-system)" == "yes" ]] \
  || fail "ExternalDNS cannot list intended ingresses"

[[ "$(kubectl auth can-i list secrets \
  --as=system:serviceaccount:aegis-system:aegis-external-dns \
  -n aegis-system)" == "no" ]] \
  || fail "ExternalDNS unexpectedly has Secret list permission"

[[ "$(kubectl auth can-i delete ingresses.networking.k8s.io \
  --as=system:serviceaccount:aegis-system:aegis-external-dns \
  -n aegis-system)" == "no" ]] \
  || fail "ExternalDNS unexpectedly has ingress delete permission"
pass "ExternalDNS namespace RBAC is least privilege"

DESIRED_DIGEST="$(awk '/^[[:space:]]*digest:[[:space:]]*sha256:/{print $2; exit}' gitops/eks-dev/kustomization.yaml)"
RUNTIME_IMAGE="$(kubectl -n aegis-system get deployment aegis-status-page \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="status-page")].image}')"
RUNTIME_DIGEST="${RUNTIME_IMAGE##*@}"

[[ -n "$DESIRED_DIGEST" ]] || fail "could not read desired Status-Page digest"
[[ "$DESIRED_DIGEST" == "$RUNTIME_DIGEST" ]] \
  || fail "GitOps digest does not match the EKS runtime digest"
pass "GitOps digest matches EKS runtime digest"

READY_REPLICAS="$(kubectl -n aegis-system get deployment aegis-status-page \
  -o jsonpath='{.status.readyReplicas}')"
[[ "${READY_REPLICAS:-0}" -ge 2 ]] || fail "fewer than two Status-Page replicas are Ready"

mapfile -t WEB_NODES < <(
  kubectl -n aegis-system get pods \
    -l app.kubernetes.io/name=aegis-status-page \
    --field-selector=status.phase=Running \
    -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' \
    | sed '/^$/d' \
    | sort -u
)

[[ "${#WEB_NODES[@]}" -ge 2 ]] || fail "Status-Page replicas are not on at least two nodes"

AZS="$({
  for node in "${WEB_NODES[@]}"; do
    kubectl get node "$node" -o jsonpath='{.metadata.labels.topology\.kubernetes\.io/zone}{"\n"}'
  done
} | sed '/^$/d' | sort -u)"

AZ_COUNT="$(wc -l <<<"$AZS" | tr -d ' ')"
[[ "$AZ_COUNT" -ge 2 ]] || fail "Status-Page replicas do not span two Availability Zones"
pass "Status-Page has multiple Ready replicas across Availability Zones"

HEALTH_BODY="$(mktemp)"
trap 'rm -f "$TMP_RENDER" "$HEALTH_BODY"' EXIT
HTTP_CODE="$(curl -sS -o "$HEALTH_BODY" -w '%{http_code}' \
  https://app.aegis-project.ddnsfree.com/healthz)"
[[ "$HTTP_CODE" == "200" ]] || fail "public health endpoint returned HTTP $HTTP_CODE"
grep -qx 'ok' "$HEALTH_BODY" || fail "public health endpoint body is not exactly 'ok'"
pass "public HTTPS health endpoint returns 200 ok"

printf '\nAEGIS TECHNICAL VALIDATION: COMPLETE (%d checks passed)\n' "$PASS_COUNT"
