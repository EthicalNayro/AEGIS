from zoneinfo import ZoneInfo

from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.detection.security_groups import detect_security_group_exposures
from aegis.incidents.builder import build_incident
from aegis.normalization.cloudtrail import CloudTrailNormalizer


def safe_actor_name(actor: str | None) -> str:
    if not actor:
        return "-"

    if "assumed-role/" in actor:
        remainder = actor.split("assumed-role/", 1)[1]
        return remainder.split("/", 1)[0]

    if "user/" in actor:
        return actor.rsplit("/", 1)[-1]

    return actor


collector = CloudTrailCollector()
normalizer = CloudTrailNormalizer()

events = collector.get_recent_events(
    minutes=30,
    max_results=10,
    event_name="AuthorizeSecurityGroupIngress",
)

incidents = []

for raw_event in events:
    event = normalizer.normalize(raw_event)

    detections = detect_security_group_exposures(event)

    for detection in detections:
        incident = build_incident(event, detection)
        incidents.append(incident)


if not incidents:
    print("No AEGIS security incidents detected.")
    raise SystemExit(0)


incident = incidents[0]

event_time = incident.event_time.astimezone(
    ZoneInfo("Asia/Jerusalem")
)

detected_time = incident.detected_at.astimezone(
    ZoneInfo("Asia/Jerusalem")
)

from_port = incident.evidence.get("from_port")
to_port = incident.evidence.get("to_port")

if from_port == to_port:
    ports = str(from_port)
else:
    ports = f"{from_port}-{to_port}"


print()
print("=" * 72)
print("AEGIS SECURITY INCIDENT")
print("=" * 72)

print(f"Incident ID : {incident.incident_id}")
print(f"Status      : {incident.status.value}")
print(f"Severity    : {incident.severity.value}")
print(f"Finding     : {incident.title}")
print(f"Rule        : {incident.rule_id}")

print()
print("Affected Resource")
print(f"  Type      : {incident.resource_type}")
print(f"  ID        : {incident.resource_id}")
print(f"  Region    : {incident.region}")

print()
print("Exposure Evidence")
print(f"  Protocol  : {incident.evidence.get('protocol')}")
print(f"  Port(s)   : {ports}")
print(f"  CIDR      : {incident.evidence.get('cidr')}")

print()
print("Source Context")
print(f"  Provider  : {incident.source.upper()}")
print(f"  Action    : {incident.evidence.get('action')}")
print(f"  Actor     : {safe_actor_name(incident.actor)}")
print(f"  Actor Type: {incident.actor_type or '-'}")

print()
print("Timeline")
print(
    f"  Event     : "
    f"{event_time.strftime('%d/%m/%Y %H:%M:%S %Z')}"
)
print(
    f"  Detected  : "
    f"{detected_time.strftime('%d/%m/%Y %H:%M:%S %Z')}"
)

print()
print("=" * 72)
