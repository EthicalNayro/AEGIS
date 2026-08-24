from datetime import datetime

import psycopg


class PostgresCheckpointRepository:
    def __init__(
        self,
        dsn: str,
        connect_fn=None,
    ) -> None:
        self.dsn = dsn
        self._connect = connect_fn or psycopg.connect

    def get(
        self,
        worker_name: str,
    ) -> datetime | None:
        query = """
        SELECT last_successful_poll_at
        FROM worker_checkpoints
        WHERE worker_name = %s;
        """

        with self._connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (worker_name,),
                )

                row = cursor.fetchone()

        if row is None:
            return None

        return row[0]

    def save(
        self,
        worker_name: str,
        checkpoint: datetime,
    ) -> None:
        query = """
        INSERT INTO worker_checkpoints (
            worker_name,
            last_successful_poll_at,
            updated_at
        )
        VALUES (%s, %s, NOW())
        ON CONFLICT (worker_name)
        DO UPDATE SET
            last_successful_poll_at =
                EXCLUDED.last_successful_poll_at,
            updated_at = NOW();
        """

        with self._connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        worker_name,
                        checkpoint,
                    ),
                )
