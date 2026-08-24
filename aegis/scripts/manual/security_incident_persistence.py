import boto3
import os

from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.detection.security_groups import detect_security_group_exposures
from aegis.normalization.cloudtrail import CloudTrailNormalizer
from aegis.pipeline.security import SecurityEventPipeline
from aegis.scope.resources import Ec2SecurityGroupTagScope
from aegis.storage.postgres import PostgresIncidentRepository


def _get_positive_int(name: str, default: int) -> int:
    value = int(os.environ.get(name, str(default)))

    if value < 1:
        raise ValueError(
            f"{name} must be greater than zero"
        )

    return value


def main() -> None:
    database_url = os.environ["AEGIS_DATABASE_URL"]

    region = os.environ.get(
        "AEGIS_AWS_REGION",
        "us-east-1",
    )

    lookback_minutes = _get_positive_int(
        "AEGIS_LOOKBACK_MINUTES",
        60,
    )

    max_results = _get_positive_int(
        "AEGIS_MAX_RESULTS",
        200,
    )

    scope_tag_key = os.environ.get(
        "AEGIS_SCOPE_TAG_KEY",
        "AEGISMonitoring",
    )

    scope_tag_value = os.environ.get(
        "AEGIS_SCOPE_TAG_VALUE",
        "enabled",
    )

    collector = CloudTrailCollector(
        region=region,
    )

    normalizer = CloudTrailNormalizer()

    ec2_client = boto3.client(
        "ec2",
        region_name=region,
    )

    scope_policy = Ec2SecurityGroupTagScope(
        ec2_client=ec2_client,
        tag_key=scope_tag_key,
        tag_value=scope_tag_value,
    )

    repository = PostgresIncidentRepository(
        database_url
    )

    pipeline = SecurityEventPipeline(
        collector=collector,
        normalizer=normalizer,
        detector=detect_security_group_exposures,
        repository=repository,
        scope_policy=scope_policy,
    )

    result = pipeline.run(
        minutes=lookback_minutes,
        max_results=max_results,
        event_name="AuthorizeSecurityGroupIngress",
    )

    if not result.incidents:
        print(
            "No matching in-scope AEGIS "
            "security incidents found."
        )
        print(
            "Pipeline telemetry: "
            f"events={result.collected_events} "
            f"normalized={result.normalized_events} "
            f"in_scope={result.in_scope_events} "
            f"detections={result.detections}"
        )
        return

    print(
        "Pipeline telemetry: "
        f"events={result.collected_events} "
        f"normalized={result.normalized_events} "
        f"in_scope={result.in_scope_events} "
        f"detections={result.detections} "
        f"inserted={result.inserted} "
        f"duplicates={result.duplicates}"
    )
    print()

    for incident, inserted in result.incidents:
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
            + (
                "INSERTED"
                if inserted
                else "ALREADY EXISTS"
            )
        )
        print()


if __name__ == "__main__":
    main()
