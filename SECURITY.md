# Security Policy

AEGIS is a security engineering project and treats responsible disclosure as part of the system design.

## Supported version

Security fixes target the current `main` branch and the supported `eks-dev` platform implementation.

## Reporting a vulnerability

Use GitHub's **Report a vulnerability** / private security advisory flow for this repository when it is available.

If private reporting is unavailable, open a minimal public issue that asks the maintainer for a private contact channel. Do not include the vulnerability details, credentials, tokens, account identifiers, infrastructure addresses, analyst data, or proof-of-concept payload in that issue.

Include the following only in the private report:

- affected component and revision;
- prerequisites and impact;
- minimal reproduction steps;
- suggested mitigation, if known;
- whether any secret or live environment may have been exposed.

## Response principles

The project will prioritize reports involving:

- authentication, authorization, CSRF, or staff-only boundary bypass;
- Grafana gateway or viewer-identity bypass;
- AWS IAM, EKS Pod Identity, GitHub OIDC, or secret exposure;
- container or software-supply-chain compromise;
- WAF/event-pipeline evasion that creates a false security claim;
- DynamoDB review-integrity or idempotency failure;
- prompt injection that crosses the advisory AI trust boundary;
- unsafe GitOps mutation or stale workflow overwrite.

## Public disclosure

Please allow reasonable time for investigation and remediation before public disclosure. Never test against infrastructure, accounts, or data that you do not own or have explicit permission to assess.

## Security design references

- [Security architecture](docs/security.md)
- [Architecture safety enhancements](docs/architecture-safety-enhancements.md)
- [Architecture decisions](docs/architecture-decisions.md)
- [Validation](docs/validation.md)
- [Evidence index](docs/evidence.md)
