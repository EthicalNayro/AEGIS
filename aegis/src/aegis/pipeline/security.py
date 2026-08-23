from typing import Any

from aegis.incidents.builder import build_incident


class SecurityEventPipeline:
    def __init__(
        self,
        collector: Any,
        normalizer: Any,
        detector: Any,
        repository: Any,
        scope_policy: Any | None = None,
    ) -> None:
        self.collector = collector
        self.normalizer = normalizer
        self.detector = detector
        self.repository = repository
        self.scope_policy = scope_policy

    def run(
        self,
        minutes: int = 15,
        max_results: int = 50,
        event_name: str | None = None,
    ) -> list[tuple[Any, bool]]:
        events = self.collector.get_recent_events(
            minutes=minutes,
            max_results=max_results,
            event_name=event_name,
        )

        results: list[tuple[Any, bool]] = []

        for raw_event in events:
            event = self.normalizer.normalize(
                raw_event
            )

            if (
                self.scope_policy
                and not self.scope_policy.allows(event)
            ):
                continue

            detections = self.detector(event)

            for detection in detections:
                incident = build_incident(
                    event,
                    detection,
                )

                inserted = self.repository.save(
                    incident
                )

                results.append(
                    (incident, inserted)
                )

        return results
