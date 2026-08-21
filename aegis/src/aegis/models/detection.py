from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Detection:
    rule_id: str
    title: str
    severity: Severity

    resource_type: str
    resource_id: str

    description: str

    protocol: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    cidr: str | None = None
