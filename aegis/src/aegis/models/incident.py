from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from aegis.models.detection import Severity


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


@dataclass
class Incident:
    incident_id: str

    title: str
    rule_id: str
    severity: Severity
    status: IncidentStatus

    source: str
    source_event_id: str

    resource_type: str
    resource_id: str
    region: str | None

    actor: str | None
    actor_type: str | None
    source_ip: str | None

    event_time: datetime
    detected_at: datetime

    evidence: dict[str, Any] = field(default_factory=dict)
