from aegis.workers.security import SecurityWorker


class FakePipeline:
    def __init__(self):
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)

        return [
            ("incident-1", True),
            ("incident-2", False),
        ]


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
    pipeline = FakePipeline()

    try:
        SecurityWorker(
            pipeline=pipeline,
            poll_interval_seconds=0,
        )
    except ValueError as error:
        assert "poll_interval_seconds" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_worker_rejects_invalid_lookback():
    pipeline = FakePipeline()

    try:
        SecurityWorker(
            pipeline=pipeline,
            lookback_minutes=0,
        )
    except ValueError as error:
        assert "lookback_minutes" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
