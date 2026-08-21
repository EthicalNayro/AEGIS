import json
from datetime import datetime, timezone

from aegis.normalization.cloudtrail import CloudTrailNormalizer


def make_cloudtrail_event(raw_event: dict) -> dict:
    return {
        "EventId": "test-event-001",
        "EventName": raw_event.get("eventName"),
        "EventSource": raw_event.get("eventSource"),
        "EventTime": datetime(
            2026,
            8,
            21,
            13,
            30,
            38,
            tzinfo=timezone.utc,
        ),
        "CloudTrailEvent": json.dumps(raw_event),
    }


def test_normalizes_basic_cloudtrail_fields():
    raw = {
        "eventSource": "ec2.amazonaws.com",
        "eventName": "DescribeInstances",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "192.0.2.10",
        "userIdentity": {
            "type": "AssumedRole",
            "arn": "arn:aws:sts::123456789012:assumed-role/test-role/session",
        },
    }

    event = CloudTrailNormalizer().normalize(
        make_cloudtrail_event(raw)
    )

    assert event.event_id == "test-event-001"
    assert event.source == "aws"
    assert event.service == "ec2"
    assert event.action == "DescribeInstances"
    assert event.region == "us-east-1"
    assert event.actor_type == "AssumedRole"
    assert event.actor.endswith(
        "assumed-role/test-role/session"
    )
    assert event.source_ip == "192.0.2.10"

    assert event.resource_type is None
    assert event.resource_id is None
    assert event.network_rules == []


def test_extracts_public_ipv4_security_group_rule():
    raw = {
        "eventSource": "ec2.amazonaws.com",
        "eventName": "AuthorizeSecurityGroupIngress",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "192.0.2.10",
        "userIdentity": {
            "type": "AssumedRole",
            "arn": "arn:aws:sts::123456789012:assumed-role/test-role/session",
        },
        "requestParameters": {
            "groupId": "sg-test123",
            "ipPermissions": {
                "items": [
                    {
                        "ipProtocol": "tcp",
                        "fromPort": 22,
                        "toPort": 22,
                        "groups": {},
                        "ipRanges": {
                            "items": [
                                {
                                    "cidrIp": "0.0.0.0/0",
                                }
                            ]
                        },
                        "ipv6Ranges": {},
                        "prefixListIds": {},
                    }
                ]
            },
        },
    }

    event = CloudTrailNormalizer().normalize(
        make_cloudtrail_event(raw)
    )

    assert event.resource_type == "security_group"
    assert event.resource_id == "sg-test123"

    assert len(event.network_rules) == 1

    rule = event.network_rules[0]

    assert rule.protocol == "tcp"
    assert rule.from_port == 22
    assert rule.to_port == 22
    assert rule.cidr == "0.0.0.0/0"
    assert rule.ip_version == 4


def test_extracts_public_ipv6_security_group_rule():
    raw = {
        "eventSource": "ec2.amazonaws.com",
        "eventName": "AuthorizeSecurityGroupIngress",
        "awsRegion": "us-east-1",
        "userIdentity": {
            "type": "AssumedRole",
            "arn": "arn:aws:sts::123456789012:assumed-role/test-role/session",
        },
        "requestParameters": {
            "groupId": "sg-test123",
            "ipPermissions": {
                "items": [
                    {
                        "ipProtocol": "tcp",
                        "fromPort": 22,
                        "toPort": 22,
                        "ipRanges": {},
                        "ipv6Ranges": {
                            "items": [
                                {
                                    "cidrIpv6": "::/0",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    }

    event = CloudTrailNormalizer().normalize(
        make_cloudtrail_event(raw)
    )

    assert len(event.network_rules) == 1

    rule = event.network_rules[0]

    assert rule.protocol == "tcp"
    assert rule.from_port == 22
    assert rule.to_port == 22
    assert rule.cidr == "::/0"
    assert rule.ip_version == 6


def test_extracts_multiple_network_rules():
    raw = {
        "eventSource": "ec2.amazonaws.com",
        "eventName": "AuthorizeSecurityGroupIngress",
        "awsRegion": "us-east-1",
        "userIdentity": {
            "type": "AssumedRole",
            "arn": "arn:aws:sts::123456789012:assumed-role/test-role/session",
        },
        "requestParameters": {
            "groupId": "sg-test123",
            "ipPermissions": {
                "items": [
                    {
                        "ipProtocol": "tcp",
                        "fromPort": 22,
                        "toPort": 22,
                        "ipRanges": {
                            "items": [
                                {
                                    "cidrIp": "0.0.0.0/0",
                                },
                                {
                                    "cidrIp": "10.0.0.0/16",
                                },
                            ]
                        },
                        "ipv6Ranges": {},
                    },
                    {
                        "ipProtocol": "tcp",
                        "fromPort": 443,
                        "toPort": 443,
                        "ipRanges": {
                            "items": [
                                {
                                    "cidrIp": "0.0.0.0/0",
                                }
                            ]
                        },
                        "ipv6Ranges": {},
                    },
                ]
            },
        },
    }

    event = CloudTrailNormalizer().normalize(
        make_cloudtrail_event(raw)
    )

    assert len(event.network_rules) == 3

    assert event.network_rules[0].cidr == "0.0.0.0/0"
    assert event.network_rules[0].from_port == 22

    assert event.network_rules[1].cidr == "10.0.0.0/16"
    assert event.network_rules[1].from_port == 22

    assert event.network_rules[2].cidr == "0.0.0.0/0"
    assert event.network_rules[2].from_port == 443


def test_uses_invoked_by_for_aws_service_actor():
    raw = {
        "eventSource": "ssm.amazonaws.com",
        "eventName": "ManagedInstanceConnectionLost",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "ssm.amazonaws.com",
        "userIdentity": {
            "type": "AWSService",
            "invokedBy": "ssm.amazonaws.com",
        },
    }

    event = CloudTrailNormalizer().normalize(
        make_cloudtrail_event(raw)
    )

    assert event.service == "ssm"
    assert event.actor_type == "AWSService"
    assert event.actor == "ssm.amazonaws.com"


def test_unrelated_event_has_no_network_rules():
    raw = {
        "eventSource": "sts.amazonaws.com",
        "eventName": "AssumeRole",
        "awsRegion": "us-east-1",
        "userIdentity": {
            "type": "IAMUser",
            "userName": "test-user",
        },
    }

    event = CloudTrailNormalizer().normalize(
        make_cloudtrail_event(raw)
    )

    assert event.service == "sts"
    assert event.action == "AssumeRole"
    assert event.actor == "test-user"

    assert event.resource_type is None
    assert event.resource_id is None
    assert event.network_rules == []
