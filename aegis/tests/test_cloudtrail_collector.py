from aegis.collectors.cloudtrail import CloudTrailCollector


class FakeCloudTrailClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def lookup_events(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.responses)


def event(event_id, source="ec2.amazonaws.com", name="TestEvent"):
    return {
        "EventId": event_id,
        "EventSource": source,
        "EventName": name,
    }


def test_collector_follows_cloudtrail_pagination():
    client = FakeCloudTrailClient(
        [
            {
                "Events": [event("event-1")],
                "NextToken": "token-1",
            },
            {
                "Events": [event("event-2")],
            },
        ]
    )

    collector = CloudTrailCollector(client=client)

    events = collector.get_recent_events(max_results=10)

    assert [item["EventId"] for item in events] == [
        "event-1",
        "event-2",
    ]

    assert len(client.calls) == 2
    assert client.calls[1]["NextToken"] == "token-1"


def test_collector_filters_its_own_lookup_events_noise():
    client = FakeCloudTrailClient(
        [
            {
                "Events": [
                    event(
                        "noise",
                        source="cloudtrail.amazonaws.com",
                        name="LookupEvents",
                    ),
                    event("real-event"),
                ]
            }
        ]
    )

    collector = CloudTrailCollector(client=client)

    events = collector.get_recent_events(max_results=10)

    assert len(events) == 1
    assert events[0]["EventId"] == "real-event"


def test_collector_respects_total_max_results():
    client = FakeCloudTrailClient(
        [
            {
                "Events": [
                    event("event-1"),
                    event("event-2"),
                ],
                "NextToken": "token-1",
            }
        ]
    )

    collector = CloudTrailCollector(client=client)

    events = collector.get_recent_events(max_results=2)

    assert len(events) == 2
    assert len(client.calls) == 1


def test_event_name_filter_is_preserved_across_pages():
    client = FakeCloudTrailClient(
        [
            {
                "Events": [event("event-1")],
                "NextToken": "token-1",
            },
            {
                "Events": [event("event-2")],
            },
        ]
    )

    collector = CloudTrailCollector(client=client)

    collector.get_recent_events(
        max_results=10,
        event_name="AuthorizeSecurityGroupIngress",
    )

    expected_filter = [
        {
            "AttributeKey": "EventName",
            "AttributeValue": "AuthorizeSecurityGroupIngress",
        }
    ]

    assert client.calls[0]["LookupAttributes"] == expected_filter
    assert client.calls[1]["LookupAttributes"] == expected_filter
