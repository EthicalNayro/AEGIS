import hashlib
from datetime import datetime, timezone

from aegis.models.detection import Detection
from aegis.models.event import NormalizedEvent
from aegis.models.incident import Incident, IncidentStatus


def build_incident(
    event: NormalizedEvent,
    detection: Detection,
) -> Incident:
    incident_id = _build_incident_id(event, detection)

    evidence = {
        "action": event.action,
        "protocol": detection.protocol,
        "from_port": detection.from_port,
        "to_port": detection.to_port,
        "cidr": detection.cidr,
    }

    return Incident(
        incident_id=incident_id,
        title=detection.title,
        rule_id=detection.rule_id,
        severity=detection.severity,
        status=IncidentStatus.OPEN,
        source=event.source,
        source_event_id=event.event_id,
        resource_type=detection.resource_type,
        resource_id=detection.resource_id,
        region=event.region,
        actor=event.actor,
        actor_type=event.actor_type,
        source_ip=event.source_ip,
        event_time=event.timestamp,
        detected_at=datetime.now(timezone.utc),
        evidence=evidence,
    )


def _build_incident_id(
    event: NormalizedEvent,
    detection: Detection,
) -> str:
    fingerprint = "|".join(
        [
            event.source,
            event.event_id,
            detection.rule_id,
            detection.resource_type,
            detection.resource_id,
            detection.protocol or "",
            str(detection.from_port or ""),
            str(detection.to_port or ""),
            detection.cidr or "",
        ]
    )

    digest = hashlib.sha256(
        fingerprint.encode("utf-8")
    ).hexdigest()[:32]

    return f"inc-{digest}"
