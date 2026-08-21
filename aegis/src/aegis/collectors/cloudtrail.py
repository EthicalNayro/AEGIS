from datetime import datetime, timedelta, timezone
from typing import Any

import boto3


class CloudTrailCollector:
    def __init__(self, region: str = "us-east-1") -> None:
        self.client = boto3.client(
            "cloudtrail",
            region_name=region,
        )

    def get_recent_events(
        self,
        minutes: int = 15,
        max_results: int = 50,
        event_name: str | None = None,
    ) -> list[dict[str, Any]]:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes)

        request: dict[str, Any] = {
            "StartTime": start_time,
            "EndTime": end_time,
            "MaxResults": max_results,
        }

        if event_name:
            request["LookupAttributes"] = [
                {
                    "AttributeKey": "EventName",
                    "AttributeValue": event_name,
                }
            ]

        response = self.client.lookup_events(**request)

        events = response.get("Events", [])

        return [
            event
            for event in events
            if not self._is_collector_noise(event)
        ]

    @staticmethod
    def _is_collector_noise(event: dict[str, Any]) -> bool:
        return (
            event.get("EventSource") == "cloudtrail.amazonaws.com"
            and event.get("EventName") == "LookupEvents"
        )
