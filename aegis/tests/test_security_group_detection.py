from datetime import datetime, timezone

from aegis.detection.security_groups import (
    detect_security_group_exposures,
)
from aegis.models.detection import Severity
from aegis.models.event import (
    NetworkRule,
    NormalizedEvent,
)


def make_event(
    rule: NetworkRule,
) -> NormalizedEvent:
    return NormalizedEvent(
        event_id="test-event-001",
        timestamp=datetime.now(timezone.utc),
        source="aws",
        service="ec2",
        action="AuthorizeSecurityGroupIngress",
        region="us-east-1",
        actor="test-actor",
        actor_type="AssumedRole",
        source_ip="127.0.0.1",
        resource_type="security_group",
        resource_id="sg-test123",
        network_rules=[rule],
    )


def test_detects_public_ipv4_ssh():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 1
    assert (
        detections[0].rule_id
        == "AEGIS-AWS-SG-001"
    )
    assert (
        detections[0].title
        == "Public SSH Exposure"
    )
    assert (
        detections[0].severity
        == Severity.HIGH
    )


def test_detects_public_ipv6_ssh():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr="::/0",
            ip_version=6,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 1
    assert (
        detections[0].rule_id
        == "AEGIS-AWS-SG-001"
    )


def test_detects_port_range_containing_ssh_only():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=20,
            to_port=25,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 1
    assert (
        detections[0].rule_id
        == "AEGIS-AWS-SG-001"
    )


def test_detects_public_ipv4_rdp():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=3389,
            to_port=3389,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 1
    assert (
        detections[0].rule_id
        == "AEGIS-AWS-SG-002"
    )
    assert (
        detections[0].title
        == "Public RDP Exposure"
    )
    assert (
        detections[0].severity
        == Severity.HIGH
    )


def test_detects_public_ipv6_rdp():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=3389,
            to_port=3389,
            cidr="::/0",
            ip_version=6,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 1
    assert (
        detections[0].rule_id
        == "AEGIS-AWS-SG-002"
    )


def test_all_traffic_creates_ssh_and_rdp_detections():
    event = make_event(
        NetworkRule(
            protocol="-1",
            from_port=None,
            to_port=None,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 2

    rule_ids = {
        detection.rule_id
        for detection in detections
    }

    assert rule_ids == {
        "AEGIS-AWS-SG-001",
        "AEGIS-AWS-SG-002",
    }


def test_public_range_containing_ssh_and_rdp_creates_two_detections():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=1,
            to_port=65535,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert len(detections) == 2

    rule_ids = {
        detection.rule_id
        for detection in detections
    }

    assert rule_ids == {
        "AEGIS-AWS-SG-001",
        "AEGIS-AWS-SG-002",
    }


def test_does_not_detect_public_https():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert detections == []


def test_does_not_detect_private_ssh():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr="10.0.0.0/16",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert detections == []


def test_does_not_detect_private_rdp():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=3389,
            to_port=3389,
            cidr="10.0.0.0/16",
            ip_version=4,
        )
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert detections == []


def test_ignores_unrelated_event_action():
    event = make_event(
        NetworkRule(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr="0.0.0.0/0",
            ip_version=4,
        )
    )

    event.action = (
        "RevokeSecurityGroupIngress"
    )

    detections = (
        detect_security_group_exposures(
            event
        )
    )

    assert detections == []
