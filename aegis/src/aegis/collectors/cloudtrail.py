from datetime import datetime, timedelta, timezone
from typing import Any

import boto3


class CloudTrailCollector:
    def __init__(
        self,
        region: str = "us-east-1",
        client: Any | None = None,
    ) -> None:
        self.client = client or boto3.client(
            "cloudtrail",
            region_name=region,
        )

    def get_recent_events(
        self,
        minutes: int = 15,
        max_results: int = 50,
        event_name: str | None = None,
    ) -> list[dict[str, Any]]:
        if max_results < 1:
            return []

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes)

        collected_events: list[dict[str, Any]] = []
        next_token: str | None = None

        while len(collected_events) < max_results:
            remaining = max_results - len(collected_events)

            request: dict[str, Any] = {
                "StartTime": start_time,
                "EndTime": end_time,
                "MaxResults": min(50, remaining),
            }

            if event_name:
                request["LookupAttributes"] = [
                    {
                        "AttributeKey": "EventName",
                        "AttributeValue": event_name,
                    }
                ]

            if next_token:
                request["NextToken"] = next_token

            response = self.client.lookup_events(**request)

            for event in response.get("Events", []):
                if self._is_collector_noise(event):
                    continue

                collected_events.append(event)

                if len(collected_events) >= max_results:
                    break

            next_token = response.get("NextToken")

            if not next_token:
                break

        return collected_events

    @staticmethod
    def _is_collector_noise(event: dict[str, Any]) -> bool:
        return (
            event.get("EventSource") == "cloudtrail.amazonaws.com"
            and event.get("EventName") == "LookupEvents"
        )
