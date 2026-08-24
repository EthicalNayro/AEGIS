from datetime import datetime, timezone

from aegis.storage.checkpoints import PostgresCheckpointRepository


class FakeCursor:
    def __init__(self, result=None):
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
    def __init__(self, result=None):
        self.cursor_instance = FakeCursor(result)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def cursor(self):
        return self.cursor_instance


def test_get_returns_checkpoint_when_worker_state_exists():
    checkpoint = datetime(
        2026,
        8,
        23,
        10,
        0,
        tzinfo=timezone.utc,
    )
    connection = FakeConnection((checkpoint,))

    repository = PostgresCheckpointRepository(
        dsn="postgresql://test",
        connect_fn=lambda _: connection,
    )

    result = repository.get("aws-security-worker")

    assert result == checkpoint
    assert connection.cursor_instance.params == (
        "aws-security-worker",
    )


def test_get_returns_none_when_worker_state_does_not_exist():
    repository = PostgresCheckpointRepository(
        dsn="postgresql://test",
        connect_fn=lambda _: FakeConnection(None),
    )

    assert repository.get("missing-worker") is None


def test_save_upserts_worker_checkpoint():
    checkpoint = datetime(
        2026,
        8,
        23,
        10,
        30,
        tzinfo=timezone.utc,
    )
    connection = FakeConnection()

    repository = PostgresCheckpointRepository(
        dsn="postgresql://test",
        connect_fn=lambda _: connection,
    )

    repository.save(
        "aws-security-worker",
        checkpoint,
    )

    assert connection.cursor_instance.params == (
        "aws-security-worker",
        checkpoint,
    )
    assert "ON CONFLICT (worker_name)" in (
        connection.cursor_instance.query
    )
