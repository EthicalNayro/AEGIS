import argparse
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = "aegis-eks-dev-security-findings"
REGION = "us-east-1"


def get_value(item, name, default="N/A"):
    value = item.get(name)

    if not value:
        return default

    if "S" in value:
        return value["S"]

    if "N" in value:
        return value["N"]

    return default


parser = argparse.ArgumentParser(
    description="AEGIS Human Security Finding Review"
)

parser.add_argument(
    "--incident-id",
    required=True
)

parser.add_argument(
    "--verdict",
    required=True,
    choices=[
        "CORRECT",
        "INCORRECT"
    ]
)

parser.add_argument(
    "--correct-classification",
    choices=[
        "TRUE_POSITIVE",
        "FALSE_POSITIVE",
        "UNCERTAIN"
    ]
)

parser.add_argument(
    "--note",
    default=""
)

args = parser.parse_args()


if (
    args.verdict == "INCORRECT"
    and not args.correct_classification
):
    parser.error(
        "--correct-classification is required "
        "when verdict is INCORRECT"
    )


# ============================================================
# AWS session
#
# Human review uses aegis-project-role.
# ============================================================

session = boto3.Session(
    profile_name="aegis-project",
    region_name=REGION
)

dynamodb = session.client(
    "dynamodb"
)


# ============================================================
# Read finding before review
# ============================================================

response = dynamodb.get_item(
    TableName=TABLE_NAME,

    Key={
        "incident_id": {
            "S": args.incident_id
        }
    },

    ConsistentRead=True
)

item = response.get("Item")

if not item:
    raise SystemExit(
        f"Incident not found: {args.incident_id}"
    )


print()
print("===== AEGIS SECURITY FINDING REVIEW =====")
print()

print(
    "Incident ID:",
    get_value(item, "incident_id")
)

print(
    "AI Classification:",
    get_value(item, "classification")
)

print(
    "Severity:",
    get_value(item, "severity")
)

print(
    "Confidence:",
    get_value(item, "confidence")
)

print(
    "Attack Type:",
    get_value(item, "attack_type")
)

print(
    "Current Review Status:",
    get_value(item, "review_status")
)

print()


# ============================================================
# Build human feedback
# ============================================================

reviewed_at = datetime.now(
    timezone.utc
).isoformat()

feedback_label = (
    "AI_CORRECT"
    if args.verdict == "CORRECT"
    else "AI_INCORRECT"
)


expression = (
    "SET review_status = :reviewed, "
    "human_verdict = :verdict, "
    "feedback_label = :feedback, "
    "reviewed_at = :reviewed_at"
)

values = {
    ":pending": {
        "S": "PENDING_REVIEW"
    },

    ":reviewed": {
        "S": "REVIEWED"
    },

    ":verdict": {
        "S": args.verdict
    },

    ":feedback": {
        "S": feedback_label
    },

    ":reviewed_at": {
        "S": reviewed_at
    }
}


if args.note:
    expression += ", analyst_note = :note"

    values[":note"] = {
        "S": args.note
    }


if args.correct_classification:
    expression += (
        ", human_classification = :classification"
    )

    values[":classification"] = {
        "S": args.correct_classification
    }


# ============================================================
# Conditional update
#
# Only findings currently in PENDING_REVIEW can be reviewed.
# This prevents accidental double-review.
# ============================================================

try:
    response = dynamodb.update_item(
        TableName=TABLE_NAME,

        Key={
            "incident_id": {
                "S": args.incident_id
            }
        },

        UpdateExpression=expression,

        ConditionExpression=(
            "review_status = :pending"
        ),

        ExpressionAttributeValues=values,

        ReturnValues="ALL_NEW"
    )

except ClientError as exc:
    if (
        exc.response["Error"]["Code"]
        == "ConditionalCheckFailedException"
    ):
        raise SystemExit(
            "Review rejected: incident is not "
            "in PENDING_REVIEW state."
        )

    raise


updated = response["Attributes"]


# ============================================================
# Human-readable result
# ============================================================

print(
    "===== AEGIS HUMAN REVIEW RECORDED ====="
)

print()

print(
    "Incident ID:",
    get_value(updated, "incident_id")
)

print(
    "AI Classification:",
    get_value(updated, "classification")
)

print(
    "AI Confidence:",
    get_value(updated, "confidence")
)

print(
    "Human Verdict:",
    get_value(updated, "human_verdict")
)

if args.correct_classification:
    print(
        "Human Classification:",
        get_value(
            updated,
            "human_classification"
        )
    )

print(
    "Feedback Label:",
    get_value(updated, "feedback_label")
)

print(
    "Review Status:",
    get_value(updated, "review_status")
)

print(
    "Reviewed At:",
    get_value(updated, "reviewed_at")
)

if args.note:
    print(
        "Analyst Note:",
        get_value(updated, "analyst_note")
    )
