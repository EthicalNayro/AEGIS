from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.normalization.cloudtrail import CloudTrailNormalizer


collector = CloudTrailCollector()
normalizer = CloudTrailNormalizer()

events = collector.get_recent_events(
    minutes=30,
    max_results=10,
)

print(f"\nAEGIS collected {len(events)} relevant CloudTrail events.\n")

for index, raw_event in enumerate(events, start=1):
    event = normalizer.normalize(raw_event)

    print("=" * 72)
    print(f"EVENT #{index}")
    print("=" * 72)

    print(f"Time       : {event.timestamp}")
    print(f"Region     : {event.region or '-'}")
    print(f"Service    : {event.service}")
    print(f"Action     : {event.action}")
    print(f"Actor Type : {event.actor_type or '-'}")
    print(f"Actor      : {event.actor or '-'}")
    print(f"Origin     : {event.source_ip or '-'}")

    if event.resource_id:
        print(f"Resource   : {event.resource_type} / {event.resource_id}")

    print()
