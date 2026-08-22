import psycopg
from psycopg.types.json import Jsonb

from aegis.models.incident import Incident


INSERT_INCIDENT_SQL = """
INSERT INTO incidents (
    incident_id,
    status,
    severity,
    rule_id,
    title,
    source,
    source_event_id,
    resource_type,
    resource_id,
    region,
    actor,
    actor_type,
    source_ip,
    event_time,
    detected_at,
    evidence
)
VALUES (
    %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s, %s
)
ON CONFLICT (incident_id) DO NOTHING
RETURNING incident_id;
"""


class PostgresIncidentRepository:
    def __init__(self, dsn: str, connect_fn=None):
        self.dsn = dsn
        self._connect = connect_fn or psycopg.connect

    def save(self, incident: Incident) -> bool:
        """
        Persist an incident.

        Returns:
            True  -> incident was inserted
            False -> incident already existed
        """

        params = (
            incident.incident_id,
            incident.status.value,
            incident.severity.value,
            incident.rule_id,
            incident.title,
            incident.source,
            incident.source_event_id,
            incident.resource_type,
            incident.resource_id,
            incident.region,
            incident.actor,
            incident.actor_type,
            incident.source_ip,
            incident.event_time,
            incident.detected_at,
            Jsonb(incident.evidence),
        )

        with self._connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(INSERT_INCIDENT_SQL, params)
                inserted = cursor.fetchone()

        return inserted is not None
