from datetime import datetime, timezone

from aegis.incidents.builder import build_incident
from aegis.models.detection import Detection, Severity
from aegis.models.event import NormalizedEvent
from aegis.models.incident import IncidentStatus


def make_event() -> NormalizedEvent:
    return NormalizedEvent(
        event_id="cloudtrail-event-123",
        timestamp=datetime(
            2026,
            8,
            21,
            13,
            30,
            tzinfo=timezone.utc,
        ),
        source="aws",
        service="ec2",
        action="AuthorizeSecurityGroupIngress",
        region="us-east-1",
        actor="arn:aws:sts::123456789012:assumed-role/test-role/session",
        actor_type="AssumedRole",
        source_ip="192.0.2.10",
        resource_type="security_group",
        resource_id="sg-test123",
        network_rules=[],
    )


def make_detection() -> Detection:
    return Detection(
        rule_id="AEGIS-AWS-SG-001",
        title="Public SSH Exposure",
        severity=Severity.HIGH,
        resource_type="security_group",
        resource_id="sg-test123",
        description=(
            "A security group ingress rule exposes "
            "SSH port 22 to the public Internet."
        ),
        protocol="tcp",
        from_port=22,
        to_port=22,
        cidr="0.0.0.0/0",
    )


def test_builds_open_incident():
    incident = build_incident(
        make_event(),
        make_detection(),
    )

    assert incident.incident_id.startswith("inc-")
    assert incident.status == IncidentStatus.OPEN

    assert incident.title == "Public SSH Exposure"
    assert incident.rule_id == "AEGIS-AWS-SG-001"
    assert incident.severity == Severity.HIGH


def test_preserves_source_event_context():
    incident = build_incident(
        make_event(),
        make_detection(),
    )

    assert incident.source == "aws"
    assert incident.source_event_id == "cloudtrail-event-123"

    assert incident.resource_type == "security_group"
    assert incident.resource_id == "sg-test123"
    assert incident.region == "us-east-1"

    assert incident.actor_type == "AssumedRole"
    assert incident.source_ip == "192.0.2.10"


def test_builds_security_evidence():
    incident = build_incident(
        make_event(),
        make_detection(),
    )

    assert incident.evidence == {
        "action": "AuthorizeSecurityGroupIngress",
        "protocol": "tcp",
        "from_port": 22,
        "to_port": 22,
        "cidr": "0.0.0.0/0",
    }


def test_same_event_generates_same_incident_id():
    event = make_event()
    detection = make_detection()

    first = build_incident(event, detection)
    second = build_incident(event, detection)

    assert first.incident_id == second.incident_id


def test_different_events_generate_different_incident_ids():
    first_event = make_event()
    second_event = make_event()

    second_event.event_id = "cloudtrail-event-456"

    detection = make_detection()

    first = build_incident(first_event, detection)
    second = build_incident(second_event, detection)

    assert first.incident_id != second.incident_id


def test_detected_at_is_utc():
    incident = build_incident(
        make_event(),
        make_detection(),
    )

    assert incident.detected_at.tzinfo == timezone.utc

def test_different_detection_rules_generate_different_incident_ids():
    event = make_event()

    ssh_detection = make_detection()

    rdp_detection = Detection(
        rule_id="AEGIS-AWS-SG-002",
        title="Public RDP Exposure",
        severity=Severity.HIGH,
        resource_type="security_group",
        resource_id="sg-test123",
        description=(
            "A security group ingress rule exposes "
            "RDP port 3389 to the public Internet."
        ),
        protocol="tcp",
        from_port=3389,
        to_port=3389,
        cidr="0.0.0.0/0",
    )

    ssh_incident = build_incident(
        event,
        ssh_detection,
    )

    rdp_incident = build_incident(
        event,
        rdp_detection,
    )

    assert (
        ssh_incident.incident_id
        != rdp_incident.incident_id
    )

    assert (
        ssh_incident.rule_id
        == "AEGIS-AWS-SG-001"
    )

    assert (
        rdp_incident.rule_id
        == "AEGIS-AWS-SG-002"
    )
