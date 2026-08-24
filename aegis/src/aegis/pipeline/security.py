from typing import Any

from aegis.incidents.builder import build_incident
from aegis.models.pipeline import PipelineRunResult


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
    ) -> PipelineRunResult:
        events = self.collector.get_recent_events(
            minutes=minutes,
            max_results=max_results,
            event_name=event_name,
        )

        result = PipelineRunResult(
            collected_events=len(events),
        )

        for raw_event in events:
            event = self.normalizer.normalize(
                raw_event
            )

            result.normalized_events += 1

            if (
                self.scope_policy
                and not self.scope_policy.allows(event)
            ):
                continue

            result.in_scope_events += 1

            detections = list(
                self.detector(event)
            )

            result.detections += len(
                detections
            )

            for detection in detections:
                incident = build_incident(
                    event,
                    detection,
                )

                inserted = self.repository.save(
                    incident
                )

                result.incidents.append(
                    (incident, inserted)
                )

        return result
