import boto3
import logging
import os
import signal
from threading import Event

from aegis.collectors.cloudtrail import CloudTrailCollector
from aegis.detection.security_groups import detect_security_group_exposures
from aegis.normalization.cloudtrail import CloudTrailNormalizer
from aegis.pipeline.security import SecurityEventPipeline
from aegis.scope.resources import Ec2SecurityGroupTagScope
from aegis.storage.checkpoints import PostgresCheckpointRepository
from aegis.storage.postgres import PostgresIncidentRepository
from aegis.workers.security import SecurityWorker


def _get_positive_int(name: str, default: int) -> int:
    value = int(os.environ.get(name, str(default)))

    if value < 1:
        raise ValueError(
            f"{name} must be greater than zero"
        )

    return value


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    logger = logging.getLogger("aegis.runtime")

    database_url = os.environ["AEGIS_DATABASE_URL"]

    region = os.environ.get(
        "AEGIS_AWS_REGION",
        "us-east-1",
    )

    poll_interval = _get_positive_int(
        "AEGIS_POLL_INTERVAL_SECONDS",
        60,
    )

    lookback_minutes = _get_positive_int(
        "AEGIS_LOOKBACK_MINUTES",
        10,
    )

    max_results = _get_positive_int(
        "AEGIS_MAX_RESULTS",
        200,
    )

    event_name = os.environ.get(
        "AEGIS_EVENT_NAME",
        "AuthorizeSecurityGroupIngress",
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

    incident_repository = PostgresIncidentRepository(
        database_url
    )

    checkpoint_repository = PostgresCheckpointRepository(
        database_url
    )

    pipeline = SecurityEventPipeline(
        collector=collector,
        normalizer=normalizer,
        detector=detect_security_group_exposures,
        repository=incident_repository,
        scope_policy=scope_policy,
    )

    worker = SecurityWorker(
        pipeline=pipeline,
        checkpoint_repository=checkpoint_repository,
        worker_name="aws-security-worker",
        poll_interval_seconds=poll_interval,
        lookback_minutes=lookback_minutes,
        max_results=max_results,
        event_name=event_name,
    )

    stop_event = Event()

    def request_shutdown(signum, frame):
        logger.info(
            "Shutdown requested (signal=%s)",
            signum,
        )
        stop_event.set()

    signal.signal(
        signal.SIGINT,
        request_shutdown,
    )

    signal.signal(
        signal.SIGTERM,
        request_shutdown,
    )

    logger.info(
        "AEGIS continuous security worker starting"
    )

    worker.run_forever(
        stop_event=stop_event
    )

    logger.info(
        "AEGIS continuous security worker stopped"
    )


if __name__ == "__main__":
    main()
