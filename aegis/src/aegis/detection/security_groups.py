from aegis.models.detection import Detection, Severity
from aegis.models.event import NetworkRule, NormalizedEvent


PUBLIC_IPV4 = "0.0.0.0/0"
PUBLIC_IPV6 = "::/0"
SSH_PORT = 22


def detect_security_group_exposures(
    event: NormalizedEvent,
) -> list[Detection]:
    detections: list[Detection] = []

    if event.action != "AuthorizeSecurityGroupIngress":
        return detections

    if event.resource_type != "security_group":
        return detections

    if not event.resource_id:
        return detections

    for rule in event.network_rules:
        if _is_public_ssh(rule):
            detections.append(
                Detection(
                    rule_id="AEGIS-AWS-SG-001",
                    title="Public SSH Exposure",
                    severity=Severity.HIGH,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    description=(
                        "A security group ingress rule exposes "
                        "SSH port 22 to the public Internet."
                    ),
                    protocol=rule.protocol,
                    from_port=rule.from_port,
                    to_port=rule.to_port,
                    cidr=rule.cidr,
                )
            )

    return detections


def _is_public_ssh(rule: NetworkRule) -> bool:
    if rule.cidr not in {PUBLIC_IPV4, PUBLIC_IPV6}:
        return False

    # AWS uses "-1" to represent all protocols.
    if rule.protocol == "-1":
        return True

    if rule.protocol != "tcp":
        return False

    if rule.from_port is None or rule.to_port is None:
        return False

    return rule.from_port <= SSH_PORT <= rule.to_port
