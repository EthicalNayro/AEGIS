from types import SimpleNamespace

from aegis.scope.resources import Ec2SecurityGroupTagScope


class FakeEc2Client:
    def __init__(self, security_groups=None, error=None):
        self.security_groups = security_groups or []
        self.error = error
        self.calls = []

    def describe_security_groups(self, **kwargs):
        self.calls.append(kwargs)

        if self.error:
            raise self.error

        return {
            "SecurityGroups": self.security_groups,
        }


def security_group_event(resource_id="sg-test"):
    return SimpleNamespace(
        resource_type="security_group",
        resource_id=resource_id,
    )


def test_scope_allows_explicitly_enabled_security_group():
    client = FakeEc2Client(
        security_groups=[
            {
                "GroupId": "sg-test",
                "Tags": [
                    {
                        "Key": "AEGISMonitoring",
                        "Value": "enabled",
                    }
                ],
            }
        ]
    )

    policy = Ec2SecurityGroupTagScope(client)

    assert policy.allows(security_group_event()) is True
    assert client.calls == [{"GroupIds": ["sg-test"]}]


def test_scope_denies_security_group_without_opt_in_tag():
    client = FakeEc2Client(
        security_groups=[
            {
                "GroupId": "sg-test",
                "Tags": [],
            }
        ]
    )

    policy = Ec2SecurityGroupTagScope(client)

    assert policy.allows(security_group_event()) is False


def test_scope_denies_wrong_tag_value():
    client = FakeEc2Client(
        security_groups=[
            {
                "GroupId": "sg-test",
                "Tags": [
                    {
                        "Key": "AEGISMonitoring",
                        "Value": "disabled",
                    }
                ],
            }
        ]
    )

    policy = Ec2SecurityGroupTagScope(client)

    assert policy.allows(security_group_event()) is False


def test_scope_denies_unsupported_resource_without_aws_lookup():
    client = FakeEc2Client()
    policy = Ec2SecurityGroupTagScope(client)

    event = SimpleNamespace(
        resource_type="instance",
        resource_id="i-test",
    )

    assert policy.allows(event) is False
    assert client.calls == []


def test_scope_fails_closed_when_resource_lookup_fails():
    client = FakeEc2Client(
        error=RuntimeError("simulated AWS failure")
    )
    policy = Ec2SecurityGroupTagScope(client)

    assert policy.allows(security_group_event()) is False


def test_scope_fails_closed_when_security_group_is_not_returned():
    client = FakeEc2Client(security_groups=[])
    policy = Ec2SecurityGroupTagScope(client)

    assert policy.allows(security_group_event()) is False
