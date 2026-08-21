from zoneinfo import ZoneInfo

from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.normalization.cloudtrail import CloudTrailNormalizer


collector = CloudTrailCollector()
normalizer = CloudTrailNormalizer()

events = collector.get_recent_events(
    minutes=60,
    max_results=10,
    event_name="AuthorizeSecurityGroupIngress",
)

security_group_events = []

for raw_event in events:
    normalized = normalizer.normalize(raw_event)

    if normalized.network_rules:
        security_group_events.append(normalized)


if not security_group_events:
    print("No Security Group ingress events found.")
    raise SystemExit(0)


event = security_group_events[0]

israel_time = event.timestamp.astimezone(
    ZoneInfo("Asia/Jerusalem")
)

print()
print("=" * 64)
print("AEGIS NORMALIZED SECURITY EVENT")
print("=" * 64)

print(
    f"Time       : "
    f"{israel_time.strftime('%d/%m/%Y %H:%M:%S %Z')}"
)
print(f"Region     : {event.region}")
print(f"Service    : {event.service}")
print(f"Action     : {event.action}")

print()
print("Resource")
print(f"  Type     : {event.resource_type}")
print(f"  ID       : {event.resource_id}")

print()
print("Network Change")

for rule in event.network_rules:
    if rule.from_port == rule.to_port:
        ports = str(rule.from_port)
    else:
        ports = f"{rule.from_port}-{rule.to_port}"

    print(f"  Protocol : {rule.protocol}")
    print(f"  Port(s)  : {ports}")
    print(f"  CIDR     : {rule.cidr}")
    print(f"  IP Ver.  : IPv{rule.ip_version}")

print()
print("=" * 64)
