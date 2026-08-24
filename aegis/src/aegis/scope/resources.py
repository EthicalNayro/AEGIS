import logging
from typing import Any, Protocol

from botocore.exceptions import ClientError

from aegis.models.event import NormalizedEvent


logger = logging.getLogger(__name__)


class ResourceScopePolicy(Protocol):
    def allows(
        self,
        event: NormalizedEvent,
    ) -> bool:
        ...


class AllowAllResourceScope:
    def allows(
        self,
        event: NormalizedEvent,
    ) -> bool:
        return True


class Ec2SecurityGroupTagScope:
    def __init__(
        self,
        ec2_client: Any,
        tag_key: str = "AEGISMonitoring",
        tag_value: str = "enabled",
    ) -> None:
        self.ec2_client = ec2_client
        self.tag_key = tag_key
        self.tag_value = tag_value

    def allows(
        self,
        event: NormalizedEvent,
    ) -> bool:
        if (
            event.resource_type != "security_group"
            or not event.resource_id
        ):
            logger.debug(
                "Scope DENIED resource=%s "
                "reason=unsupported-resource",
                event.resource_id,
            )
            return False

        try:
            response = self.ec2_client.describe_security_groups(
                GroupIds=[event.resource_id]
            )

        except ClientError as error:
            error_code = (
                error.response
                .get("Error", {})
                .get("Code", "Unknown")
            )

            if error_code == "InvalidGroup.NotFound":
                logger.debug(
                    "Scope DENIED resource=%s "
                    "reason=resource-not-found",
                    event.resource_id,
                )
            else:
                logger.warning(
                    "Scope DENIED resource=%s "
                    "reason=validation-failed "
                    "error=%s",
                    event.resource_id,
                    error_code,
                )

            return False

        except Exception as error:
            logger.warning(
                "Scope DENIED resource=%s "
                "reason=validation-failed "
                "error=%s",
                event.resource_id,
                type(error).__name__,
            )
            return False

        security_groups = response.get(
            "SecurityGroups",
            [],
        )

        if len(security_groups) != 1:
            logger.debug(
                "Scope DENIED resource=%s "
                "reason=resource-not-found",
                event.resource_id,
            )
            return False

        tags = {
            tag["Key"]: tag["Value"]
            for tag in security_groups[0].get(
                "Tags",
                [],
            )
            if "Key" in tag and "Value" in tag
        }

        allowed = (
            tags.get(self.tag_key)
            == self.tag_value
        )

        if allowed:
            logger.debug(
                "Scope ALLOWED resource=%s tag=%s=%s",
                event.resource_id,
                self.tag_key,
                self.tag_value,
            )
        else:
            logger.debug(
                "Scope DENIED resource=%s "
                "reason=missing-required-tag",
                event.resource_id,
            )

        return allowed
