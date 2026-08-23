from datetime import datetime, timezone
from types import SimpleNamespace

from aegis.pipeline.security import SecurityEventPipeline


class FakeCollector:
    def get_recent_events(
        self,
        minutes=15,
        max_results=50,
        event_name=None,
    ):
        return [
            {
                "EventId": "event-123",
            }
        ]


class FakeNormalizer:
    def normalize(self, raw_event):
        return SimpleNamespace(
            event_id="event-123",
            resource_id="sg-test",
            source="aws",
            resource_type="security_group",
            region="us-east-1",
            actor="test-user",
            actor_type="IAMUser",
            source_ip="203.0.113.10",
            timestamp=datetime.now(timezone.utc),
            action="AuthorizeSecurityGroupIngress",
        )


class FakeRepository:
    def __init__(self):
        self.saved = []

    def save(self, incident):
        self.saved.append(incident)
        return True


class AllowScope:
    def allows(self, event):
        return True


class DenyScope:
    def allows(self, event):
        return False


def test_pipeline_processes_and_persists_detection():
    detection = SimpleNamespace(
        rule_id="AEGIS-AWS-SG-001",
        title="Public SSH Exposure",
        severity=SimpleNamespace(value="HIGH"),
        resource_type="security_group",
        resource_id="sg-test",
        protocol="tcp",
        from_port=22,
        to_port=22,
        cidr="0.0.0.0/0",
    )

    repository = FakeRepository()

    pipeline = SecurityEventPipeline(
        collector=FakeCollector(),
        normalizer=FakeNormalizer(),
        detector=lambda event: [detection],
        repository=repository,
        scope_policy=AllowScope(),
    )

    result = pipeline.run(
        event_name="AuthorizeSecurityGroupIngress",
    )

    assert result.collected_events == 1
    assert result.normalized_events == 1
    assert result.in_scope_events == 1
    assert result.detections == 1

    assert result.inserted == 1
    assert result.duplicates == 0

    assert len(result.incidents) == 1
    assert len(repository.saved) == 1

    incident, inserted = result.incidents[0]

    assert inserted is True
    assert incident.rule_id == "AEGIS-AWS-SG-001"
    assert incident.resource_id == "sg-test"


def test_pipeline_records_out_of_scope_event_telemetry():
    repository = FakeRepository()

    def detector_should_not_run(event):
        raise AssertionError(
            "Detector must not run for out-of-scope resources"
        )

    pipeline = SecurityEventPipeline(
        collector=FakeCollector(),
        normalizer=FakeNormalizer(),
        detector=detector_should_not_run,
        repository=repository,
        scope_policy=DenyScope(),
    )

    result = pipeline.run()

    assert result.collected_events == 1
    assert result.normalized_events == 1
    assert result.in_scope_events == 0
    assert result.detections == 0

    assert result.inserted == 0
    assert result.duplicates == 0
    assert result.incidents == []

    assert repository.saved == []
