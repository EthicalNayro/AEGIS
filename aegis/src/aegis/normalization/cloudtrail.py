import json
from typing import Any

from aegis.models.event import NetworkRule, NormalizedEvent


class CloudTrailNormalizer:
    def normalize(self, event: dict[str, Any]) -> NormalizedEvent:
        raw = json.loads(event["CloudTrailEvent"])

        identity = raw.get("userIdentity") or {}

        actor = (
            identity.get("arn")
            or identity.get("userName")
            or identity.get("principalId")
            or identity.get("invokedBy")
        )

        event_source = raw.get("eventSource", "")
        service = (
            event_source.removesuffix(".amazonaws.com")
            if event_source
            else "unknown"
        )

        resource_type = None
        resource_id = None
        network_rules: list[NetworkRule] = []

        if (
            service == "ec2"
            and raw.get("eventName") == "AuthorizeSecurityGroupIngress"
        ):
            (
                resource_type,
                resource_id,
                network_rules,
            ) = self._normalize_security_group_ingress(raw)

        return NormalizedEvent(
            event_id=event["EventId"],
            timestamp=event["EventTime"],
            source="aws",
            service=service,
            action=raw.get("eventName", "unknown"),
            region=raw.get("awsRegion"),
            actor=actor,
            actor_type=identity.get("type"),
            source_ip=raw.get("sourceIPAddress"),
            resource_type=resource_type,
            resource_id=resource_id,
            network_rules=network_rules,
        )

    @staticmethod
    def _normalize_security_group_ingress(
        raw: dict[str, Any],
    ) -> tuple[str, str | None, list[NetworkRule]]:
        request = raw.get("requestParameters") or {}

        resource_id = request.get("groupId")

        permissions = (
            request.get("ipPermissions", {}).get("items", [])
        )

        network_rules: list[NetworkRule] = []

        for permission in permissions:
            protocol = permission.get("ipProtocol")
            from_port = permission.get("fromPort")
            to_port = permission.get("toPort")

            ipv4_ranges = (
                permission.get("ipRanges", {}).get("items", [])
            )

            for ip_range in ipv4_ranges:
                cidr = ip_range.get("cidrIp")

                if cidr:
                    network_rules.append(
                        NetworkRule(
                            protocol=protocol,
                            from_port=from_port,
                            to_port=to_port,
                            cidr=cidr,
                            ip_version=4,
                        )
                    )

            ipv6_ranges = (
                permission.get("ipv6Ranges", {}).get("items", [])
            )

            for ipv6_range in ipv6_ranges:
                cidr = ipv6_range.get("cidrIpv6")

                if cidr:
                    network_rules.append(
                        NetworkRule(
                            protocol=protocol,
                            from_port=from_port,
                            to_port=to_port,
                            cidr=cidr,
                            ip_version=6,
                        )
                    )

        return "security_group", resource_id, network_rules
