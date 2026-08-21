import json

from aegis.collectors.cloudtrail import CloudTrailCollector


collector = CloudTrailCollector()

events = collector.get_recent_events(
    minutes=30,
    max_results=1,
)

if not events:
    print("No CloudTrail events found.")
    raise SystemExit(0)

event = events[0]

print("=== OUTER CLOUDTRAIL EVENT ===")
print(json.dumps(event, indent=2, default=str))

print("\n=== RAW CLOUDTRAIL EVENT ===")

raw_event = json.loads(event["CloudTrailEvent"])

print(json.dumps(raw_event, indent=2, default=str))
