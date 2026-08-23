import logging
import math
from datetime import datetime, timezone
from threading import Event
from typing import Any


logger = logging.getLogger(__name__)


class SecurityWorker:
    def __init__(
        self,
        pipeline: Any,
        poll_interval_seconds: int = 60,
        lookback_minutes: int = 10,
        max_results: int = 200,
        event_name: str | None = None,
        checkpoint_repository: Any | None = None,
        worker_name: str = "security-worker",
        now_fn=None,
    ) -> None:
        if poll_interval_seconds < 1:
            raise ValueError(
                "poll_interval_seconds must be greater than zero"
            )

        if lookback_minutes < 1:
            raise ValueError(
                "lookback_minutes must be greater than zero"
            )

        self.pipeline = pipeline
        self.poll_interval_seconds = poll_interval_seconds
        self.lookback_minutes = lookback_minutes
        self.max_results = max_results
        self.event_name = event_name

        self.checkpoint_repository = checkpoint_repository
        self.worker_name = worker_name
        self._now = now_fn or (
            lambda: datetime.now(timezone.utc)
        )

    def run_once(self) -> list[tuple[Any, bool]]:
        cycle_started_at = self._now()

        effective_lookback = self.lookback_minutes

        if self.checkpoint_repository:
            checkpoint = self.checkpoint_repository.get(
                self.worker_name
            )

            if checkpoint:
                elapsed_seconds = max(
                    0,
                    (
                        cycle_started_at - checkpoint
                    ).total_seconds(),
                )

                elapsed_minutes = math.ceil(
                    elapsed_seconds / 60
                )

                effective_lookback = (
                    elapsed_minutes
                    + self.lookback_minutes
                )

                recovery_threshold = max(
                    self.poll_interval_seconds * 2,
                    60,
                )

                if elapsed_seconds > recovery_threshold:
                    logger.info(
                        "Worker recovery detected: "
                        "checkpoint=%s gap=%ss replay_window=%sm",
                        checkpoint.isoformat(),
                        int(elapsed_seconds),
                        effective_lookback,
                    )
                else:
                    logger.debug(
                        "Checkpoint loaded: "
                        "checkpoint=%s lookback=%sm",
                        checkpoint.isoformat(),
                        effective_lookback,
                    )

            else:
                logger.info(
                    "No previous checkpoint found; "
                    "using default lookback=%sm",
                    self.lookback_minutes,
                )

        results = self.pipeline.run(
            minutes=effective_lookback,
            max_results=self.max_results,
            event_name=self.event_name,
        )

        if self.checkpoint_repository:
            self.checkpoint_repository.save(
                self.worker_name,
                cycle_started_at,
            )

        return results

    def run_forever(
        self,
        stop_event: Event | None = None,
    ) -> None:
        stop_event = stop_event or Event()

        logger.info(
            "AEGIS security worker started "
            "(poll_interval=%ss, lookback=%sm)",
            self.poll_interval_seconds,
            self.lookback_minutes,
        )

        empty_cycles = 0

        heartbeat_cycles = max(
            1,
            math.ceil(
                60 / self.poll_interval_seconds
            ),
        )

        while not stop_event.is_set():
            try:
                results = self.run_once()

                inserted = sum(
                    1
                    for _, was_inserted in results
                    if was_inserted
                )

                duplicates = (
                    len(results) - inserted
                )

                if results:
                    empty_cycles = 0

                    logger.info(
                        "AEGIS polling cycle completed: "
                        "incidents=%s inserted=%s duplicates=%s",
                        len(results),
                        inserted,
                        duplicates,
                    )

                else:
                    empty_cycles += 1

                    if (
                        empty_cycles
                        % heartbeat_cycles
                        == 0
                    ):
                        logger.info(
                            "AEGIS worker healthy: "
                            "no security incidents detected"
                        )
                    else:
                        logger.debug(
                            "AEGIS polling cycle completed: "
                            "no incidents"
                        )

            except Exception:
                logger.exception(
                    "AEGIS polling cycle failed"
                )

            stop_event.wait(
                self.poll_interval_seconds
            )
