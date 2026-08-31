import logging
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlencode

import boto3

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST


PLUGIN_NAME = "aegis_review"

logger = logging.getLogger(__name__)

VALID_CLASSIFICATIONS = {
    "TRUE_POSITIVE",
    "FALSE_POSITIVE",
    "UNCERTAIN",
}

MAX_ANALYST_NOTE_LENGTH = 2000


def analyst_required(view_func):
    """
    AEGIS review actions are restricted to authenticated staff users.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse("login")
            query_string = urlencode({
                "next": request.get_full_path()
            })

            return redirect(f"{login_url}?{query_string}")

        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied(
                "AEGIS Security Review requires analyst privileges."
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


def get_plugin_config():
    config = settings.PLUGINS_CONFIG.get(
        PLUGIN_NAME,
        {}
    )

    return {
        "aws_region": config.get(
            "aws_region",
            "us-east-1"
        ),
        "findings_table": config.get(
            "findings_table",
            "aegis-eks-dev-security-findings"
        ),
    }


def get_dynamodb():
    config = get_plugin_config()

    return boto3.client(
        "dynamodb",
        region_name=config["aws_region"]
    )


def get_string(
    item,
    name,
    default="N/A"
):
    return (
        item
        .get(name, {})
        .get("S", default)
    )


def get_number(
    item,
    name,
    default="N/A"
):
    return (
        item
        .get(name, {})
        .get("N", default)
    )


def get_confidence_percent(value):
    """Return a display-safe confidence percentage from DynamoDB data."""

    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None

    if confidence <= 1:
        confidence *= 100

    return max(0, min(100, round(confidence)))


def normalize_finding(item):
    confidence = get_number(
        item,
        "confidence"
    )

    return {
        "incident_id": get_string(
            item,
            "incident_id"
        ),
        "classification": get_string(
            item,
            "classification"
        ),
        "severity": get_string(
            item,
            "severity"
        ),
        "confidence": confidence,
        "confidence_percent": get_confidence_percent(confidence),
        "attack_type": get_string(
            item,
            "attack_type"
        ),
        "reason": get_string(
            item,
            "reason"
        ),
        "recommended_action": get_string(
            item,
            "recommended_action"
        ),
        "waf_action": get_string(
            item,
            "waf_action"
        ),
        "terminating_rule": get_string(
            item,
            "terminating_rule"
        ),
        "matched_rule": get_string(
            item,
            "matched_rule"
        ),
        "country": get_string(
            item,
            "country"
        ),
        "http_method": get_string(
            item,
            "http_method"
        ),
        "uri": get_string(
            item,
            "uri"
        ),
        "review_status": get_string(
            item,
            "review_status"
        ),
        "human_verdict": get_string(
            item,
            "human_verdict",
            ""
        ),
        "human_classification": get_string(
            item,
            "human_classification",
            ""
        ),
        "analyst_note": get_string(
            item,
            "analyst_note",
            ""
        ),
        "event_time": get_string(
            item,
            "event_time"
        ),
        "created_at": get_string(
            item,
            "created_at"
        ),
        "reviewed_at": get_string(
            item,
            "reviewed_at",
            ""
        ),
        "reviewed_by": get_string(
            item,
            "reviewed_by",
            ""
        ),
        "bedrock_model": get_string(
            item,
            "bedrock_model"
        ),
    }


def scan_all_findings():
    dynamodb = get_dynamodb()
    config = get_plugin_config()

    items = []
    scan_kwargs = {
        "TableName": config[
            "findings_table"
        ]
    }

    while True:
        response = dynamodb.scan(
            **scan_kwargs
        )

        items.extend(
            response.get(
                "Items",
                []
            )
        )

        last_key = response.get(
            "LastEvaluatedKey"
        )

        if not last_key:
            break

        scan_kwargs[
            "ExclusiveStartKey"
        ] = last_key

    return items


@analyst_required
def findings_list(request):
    try:
        items = scan_all_findings()
    except (BotoCoreError, ClientError):
        logger.exception("Unable to retrieve AEGIS findings from DynamoDB")
        return render(
            request,
            "aegis_review/findings.html",
            {
                "findings": [],
                "total_count": 0,
                "pending_count": 0,
                "reviewed_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "error_message": (
                    "AEGIS could not retrieve the findings queue. "
                    "No review action was performed."
                ),
            },
            status=503,
        )

    findings = [
        normalize_finding(item)
        for item in items
    ]

    findings.sort(
        key=lambda finding: (
            finding["event_time"]
        ),
        reverse=True
    )

    total_count = len(findings)

    pending_count = sum(
        1
        for finding in findings
        if finding["review_status"]
        == "PENDING_REVIEW"
    )

    reviewed_count = sum(
        1
        for finding in findings
        if finding["review_status"]
        == "REVIEWED"
    )

    critical_count = sum(
        1
        for finding in findings
        if finding["severity"] == "CRITICAL"
    )

    high_count = sum(
        1
        for finding in findings
        if finding["severity"] == "HIGH"
    )

    search_query = request.GET.get("q", "").strip()
    selected_severity = request.GET.get("severity", "").upper()
    selected_status = request.GET.get("status", "").upper()

    if search_query:
        query = search_query.lower()
        findings = [
            finding
            for finding in findings
            if query in " ".join(
                str(finding.get(field, ""))
                for field in (
                    "incident_id",
                    "classification",
                    "attack_type",
                    "uri",
                    "country",
                    "matched_rule",
                )
            ).lower()
        ]

    if selected_severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
        findings = [
            finding
            for finding in findings
            if finding["severity"] == selected_severity
        ]
    else:
        selected_severity = ""

    if selected_status in {"PENDING_REVIEW", "REVIEWED"}:
        findings = [
            finding
            for finding in findings
            if finding["review_status"] == selected_status
        ]
    else:
        selected_status = ""

    return render(
        request,
        "aegis_review/findings.html",
        {
            "findings": findings,
            "total_count": total_count,
            "pending_count": (
                pending_count
            ),
            "reviewed_count": (
                reviewed_count
            ),
            "critical_count": critical_count,
            "high_count": high_count,
            "search_query": search_query,
            "selected_severity": selected_severity,
            "selected_status": selected_status,
        }
    )


@analyst_required
def finding_detail(
    request,
    incident_id
):
    dynamodb = get_dynamodb()
    config = get_plugin_config()

    try:
        response = dynamodb.get_item(
            TableName=config[
                "findings_table"
            ],
            Key={
                "incident_id": {
                    "S": incident_id
                }
            },
            ConsistentRead=True
        )
    except (BotoCoreError, ClientError):
        logger.exception("Unable to retrieve AEGIS finding %s", incident_id)
        return render(
            request,
            "aegis_review/finding_detail.html",
            {
                "finding": None,
                "error_message": (
                    "AEGIS could not load this finding. "
                    "No review action was performed."
                ),
            },
            status=503,
        )

    item = response.get("Item")

    if not item:
        raise Http404(
            "Security finding not found."
        )

    return render(
        request,
        "aegis_review/finding_detail.html",
        {
            "finding": (
                normalize_finding(item)
            )
        }
    )


@analyst_required
@require_POST
def review_finding(
    request,
    incident_id
):
    verdict = request.POST.get(
        "verdict"
    )

    correct_classification = (
        request.POST.get(
            "correct_classification"
        )
    )

    note = (
        request.POST.get(
            "note",
            ""
        )
        .strip()
    )

    if len(note) > MAX_ANALYST_NOTE_LENGTH:
        messages.error(
            request,
            (
                "Analyst notes are limited to "
                f"{MAX_ANALYST_NOTE_LENGTH} characters."
            )
        )

        return redirect(
            "plugins:aegis_review:"
            "finding_detail",
            incident_id=incident_id
        )

    if verdict not in {
        "CORRECT",
        "INCORRECT",
    }:
        messages.error(
            request,
            "Invalid review verdict."
        )

        return redirect(
            "plugins:aegis_review:"
            "finding_detail",
            incident_id=incident_id
        )

    if (
        verdict == "INCORRECT"
        and correct_classification
        not in VALID_CLASSIFICATIONS
    ):
        messages.error(
            request,
            "Select the correct classification."
        )

        return redirect(
            "plugins:aegis_review:"
            "finding_detail",
            incident_id=incident_id
        )

    reviewed_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    feedback_label = (
        "AI_CORRECT"
        if verdict == "CORRECT"
        else "AI_INCORRECT"
    )

    update_expression = (
        "SET review_status = :reviewed, "
        "human_verdict = :verdict, "
        "feedback_label = :feedback, "
        "reviewed_at = :reviewed_at, "
        "reviewed_by = :reviewed_by"
    )

    values = {
        ":pending": {
            "S": "PENDING_REVIEW"
        },
        ":reviewed": {
            "S": "REVIEWED"
        },
        ":verdict": {
            "S": verdict
        },
        ":feedback": {
            "S": feedback_label
        },
        ":reviewed_at": {
            "S": reviewed_at
        },
        ":reviewed_by": {
            "S": request.user.get_username()
        },
    }

    if note:
        update_expression += (
            ", analyst_note = :note"
        )

        values[":note"] = {
            "S": note
        }

    if verdict == "INCORRECT":
        update_expression += (
            ", human_classification "
            "= :classification"
        )

        values[":classification"] = {
            "S": correct_classification
        }

    dynamodb = get_dynamodb()
    config = get_plugin_config()

    try:
        dynamodb.update_item(
            TableName=config[
                "findings_table"
            ],
            Key={
                "incident_id": {
                    "S": incident_id
                }
            },
            UpdateExpression=(
                update_expression
            ),
            ConditionExpression=(
                "review_status = :pending"
            ),
            ExpressionAttributeValues=(
                values
            ),
        )

    except (
        dynamodb.exceptions
        .ConditionalCheckFailedException
    ):
        messages.error(
            request,
            (
                "This incident has already "
                "been reviewed."
            )
        )

        return redirect(
            "plugins:aegis_review:"
            "finding_detail",
            incident_id=incident_id
        )

    except (BotoCoreError, ClientError):
        logger.exception(
            "Unable to record AEGIS review for %s",
            incident_id,
        )
        messages.error(
            request,
            (
                "AWS rejected the review "
                "operation."
            )
        )

        return redirect(
            "plugins:aegis_review:"
            "finding_detail",
            incident_id=incident_id
        )

    messages.success(
        request,
        (
            "Human review recorded "
            "successfully."
        )
    )

    logger.info(
        "AEGIS review recorded for %s by %s",
        incident_id,
        request.user.get_username(),
    )

    return redirect(
        "plugins:aegis_review:"
        "finding_detail",
        incident_id=incident_id
    )
