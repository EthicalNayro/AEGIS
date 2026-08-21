from zoneinfo import ZoneInfo

from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.detection.security_groups import detect_security_group_exposures
from aegis.normalization.cloudtrail import CloudTrailNormalizer


collector = CloudTrailCollector()
normalizer = CloudTrailNormalizer()

events = collector.get_recent_events(
    minutes=120,
    max_results=10,
    event_name="AuthorizeSecurityGroupIngress",
)

detections = []

for raw_event in events:
    event = normalizer.normalize(raw_event)

    event_detections = detect_security_group_exposures(event)

    for detection in event_detections:
        detections.append((event, detection))


if not detections:
    print("No public SSH exposures detected.")
    raise SystemExit(0)


event, detection = detections[0]

israel_time = event.timestamp.astimezone(
    ZoneInfo("Asia/Jerusalem")
)

if detection.from_port == detection.to_port:
    ports = str(detection.from_port)
else:
    ports = f"{detection.from_port}-{detection.to_port}"


print()
print("=" * 68)
print("AEGIS SECURITY DETECTION")
print("=" * 68)

print(f"Rule       : {detection.rule_id}")
print(f"Finding    : {detection.title}")
print(f"Severity   : {detection.severity.value}")
print(f"Status     : DETECTED")

print()
print("Affected Resource")
print(f"  Type     : {detection.resource_type}")
print(f"  ID       : {detection.resource_id}")
print(f"  Region   : {event.region}")

print()
print("Exposure")
print(f"  Protocol : {detection.protocol}")
print(f"  Port(s)  : {ports}")
print(f"  CIDR     : {detection.cidr}")

print()
print("Event")
print(f"  Action   : {event.action}")
print(
    f"  Time     : "
    f"{israel_time.strftime('%d/%m/%Y %H:%M:%S %Z')}"
)

print()
print(f"Reason     : {detection.description}")

print()
print("=" * 68)
