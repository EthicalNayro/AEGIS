from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineRunResult:
    collected_events: int = 0
    normalized_events: int = 0
    in_scope_events: int = 0
    detections: int = 0
    incidents: list[tuple[Any, bool]] = field(
        default_factory=list
    )

    @property
    def inserted(self) -> int:
        return sum(
            1
            for _, was_inserted in self.incidents
            if was_inserted
        )

    @property
    def duplicates(self) -> int:
        return len(self.incidents) - self.inserted
