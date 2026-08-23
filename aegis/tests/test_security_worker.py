from datetime import datetime, timezone

import pytest

from aegis.workers.security import SecurityWorker


class FakePipeline:
    def __init__(self, results=None):
        self.calls = []
        self.results = results or [
            ("incident-1", True),
            ("incident-2", False),
        ]

    def run(self, **kwargs):
        self.calls.append(kwargs)
        return self.results


class FakeCheckpointRepository:
    def __init__(self, checkpoint=None):
        self.checkpoint = checkpoint
        self.saved = []

    def get(self, worker_name):
        return self.checkpoint

    def save(self, worker_name, checkpoint):
        self.saved.append((worker_name, checkpoint))


def test_worker_run_once_calls_pipeline_with_configuration():
    pipeline = FakePipeline()

    worker = SecurityWorker(
        pipeline=pipeline,
        poll_interval_seconds=60,
        lookback_minutes=10,
        max_results=200,
        event_name="AuthorizeSecurityGroupIngress",
    )

    results = worker.run_once()

    assert len(results) == 2
    assert pipeline.calls == [
        {
            "minutes": 10,
            "max_results": 200,
            "event_name": "AuthorizeSecurityGroupIngress",
        }
    ]


def test_worker_rejects_invalid_poll_interval():
    with pytest.raises(
        ValueError,
        match="poll_interval_seconds",
    ):
        SecurityWorker(
            pipeline=FakePipeline(),
            poll_interval_seconds=0,
        )


def test_worker_rejects_invalid_lookback():
    with pytest.raises(
        ValueError,
        match="lookback_minutes",
    ):
        SecurityWorker(
            pipeline=FakePipeline(),
            lookback_minutes=0,
        )


def test_worker_recovers_from_checkpoint_with_safety_overlap():
    checkpoint = datetime(
        2026,
        8,
        23,
        10,
        0,
        tzinfo=timezone.utc,
    )
    now = datetime(
        2026,
        8,
        23,
        10,
        30,
        tzinfo=timezone.utc,
    )

    pipeline = FakePipeline(results=[])
    checkpoints = FakeCheckpointRepository(
        checkpoint=checkpoint
    )

    worker = SecurityWorker(
        pipeline=pipeline,
        lookback_minutes=10,
        checkpoint_repository=checkpoints,
        worker_name="test-worker",
        now_fn=lambda: now,
    )

    worker.run_once()

    assert pipeline.calls[0]["minutes"] == 40
    assert checkpoints.saved == [
        ("test-worker", now)
    ]


def test_worker_uses_default_lookback_without_checkpoint():
    now = datetime(
        2026,
        8,
        23,
        10,
        30,
        tzinfo=timezone.utc,
    )

    pipeline = FakePipeline(results=[])
    checkpoints = FakeCheckpointRepository()

    worker = SecurityWorker(
        pipeline=pipeline,
        lookback_minutes=10,
        checkpoint_repository=checkpoints,
        worker_name="test-worker",
        now_fn=lambda: now,
    )

    worker.run_once()

    assert pipeline.calls[0]["minutes"] == 10
    assert checkpoints.saved == [
        ("test-worker", now)
    ]


def test_worker_does_not_advance_checkpoint_on_pipeline_failure():
    class FailingPipeline:
        def run(self, **kwargs):
            raise RuntimeError("simulated pipeline failure")

    now = datetime(
        2026,
        8,
        23,
        10,
        30,
        tzinfo=timezone.utc,
    )
    checkpoints = FakeCheckpointRepository()

    worker = SecurityWorker(
        pipeline=FailingPipeline(),
        checkpoint_repository=checkpoints,
        worker_name="test-worker",
        now_fn=lambda: now,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated pipeline failure",
    ):
        worker.run_once()

    assert checkpoints.saved == []
