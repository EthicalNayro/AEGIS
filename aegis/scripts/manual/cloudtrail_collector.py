from aegis.collectors.cloudtrail import CloudTrailCollector


collector = CloudTrailCollector()

events = collector.get_recent_events(
    minutes=30,
    max_results=5,
)

print(f"Collected {len(events)} CloudTrail events\n")

for event in events:
    print(
        event.get("EventTime"),
        event.get("EventSource"),
        event.get("EventName"),
    )
