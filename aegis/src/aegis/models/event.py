from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NetworkRule:
    protocol: Optional[str]
    from_port: Optional[int]
    to_port: Optional[int]
    cidr: str
    ip_version: int


@dataclass
class NormalizedEvent:
    event_id: str
    timestamp: datetime

    source: str
    service: str
    action: str
    region: Optional[str]

    actor: Optional[str]
    actor_type: Optional[str]
    source_ip: Optional[str]

    resource_type: Optional[str]
    resource_id: Optional[str]

    network_rules: list[NetworkRule] = field(default_factory=list)
