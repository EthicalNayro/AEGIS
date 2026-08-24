from datetime import datetime, timezone

from aegis.models.detection import Severity
from aegis.models.incident import Incident, IncidentStatus
from aegis.storage.postgres import PostgresIncidentRepository


class FakeCursor:
    def __init__(self, result):
        self.result = result
        self.query = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchone(self):
        return self.result


class FakeConnection:
    def __init__(self, result):
        self.cursor_instance = FakeCursor(result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def cursor(self):
        return self.cursor_instance


def build_incident():
    now = datetime.now(timezone.utc)

    return Incident(
        incident_id="inc-test-123",
        title="Public SSH Exposure",
        rule_id="AEGIS-AWS-SG-001",
        severity=Severity.HIGH,
        status=IncidentStatus.OPEN,
        source="cloudtrail",
        source_event_id="event-123",
        resource_type="security_group",
        resource_id="sg-test",
        region="us-east-1",
        actor="test-user",
        actor_type="IAMUser",
        source_ip="203.0.113.10",
        event_time=now,
        detected_at=now,
        evidence={
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr": "0.0.0.0/0",
        },
    )


def test_save_returns_true_when_incident_is_inserted():
    repository = PostgresIncidentRepository(
        dsn="postgresql://test",
        connect_fn=lambda _: FakeConnection(("inc-test-123",)),
    )

    inserted = repository.save(build_incident())

    assert inserted is True


def test_save_returns_false_when_incident_already_exists():
    repository = PostgresIncidentRepository(
        dsn="postgresql://test",
        connect_fn=lambda _: FakeConnection(None),
    )

    inserted = repository.save(build_incident())

    assert inserted is False
