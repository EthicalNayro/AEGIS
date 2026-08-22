import os

from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.normalization.cloudtrail import CloudTrailNormalizer
from aegis.detection.security_groups import detect_security_group_exposures
from aegis.incidents.builder import build_incident
from aegis.storage.postgres import PostgresIncidentRepository


def main() -> None:
    database_url = os.environ["AEGIS_DATABASE_URL"]
    target_resource_id = os.environ.get("AEGIS_TARGET_RESOURCE_ID")
    collector = CloudTrailCollector(region="us-east-1")
    normalizer = CloudTrailNormalizer()
    repository = PostgresIncidentRepository(database_url)

    events = collector.get_recent_events(
        minutes=60,
        max_results=50,
        event_name="AuthorizeSecurityGroupIngress",
    )

    incidents_found = 0

    for raw_event in events:
        event = normalizer.normalize(raw_event)

        if target_resource_id and event.resource_id != target_resource_id:
    	    continue

        detections = detect_security_group_exposures(event)

        for detection in detections:
            incident = build_incident(event, detection)

            inserted = repository.save(incident)

            incidents_found += 1

            actor = (
                incident.actor.rsplit("/", 1)[-1]
                if incident.actor
                else "unknown"
            )

            print("=" * 60)
            print("AEGIS SECURITY INCIDENT")
            print("=" * 60)
            print(f"Incident ID : {incident.incident_id}")
            print(f"Status      : {incident.status.value}")
            print(f"Severity    : {incident.severity.value}")
            print(f"Finding     : {incident.title}")
            print(f"Rule        : {incident.rule_id}")
            print(f"Resource    : {incident.resource_type}")
            print(f"Actor       : {actor}")
            print(f"Event Time  : {incident.event_time}")
            print(
                "Persistence : "
                + ("INSERTED" if inserted else "ALREADY EXISTS")
            )
            print()

    if incidents_found == 0:
        print("No matching AEGIS security incidents found.")


if __name__ == "__main__":
    main()
