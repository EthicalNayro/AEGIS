import boto3
from collections import Counter


TABLE_NAME = "aegis-eks-dev-security-findings"
REGION = "us-east-1"


session = boto3.Session(
    profile_name="aegis-project",
    region_name=REGION
)

dynamodb = session.client("dynamodb")
cloudwatch = session.client("cloudwatch")

def get_string(item, field, default=""):
    return item.get(
        field,
        {}
    ).get(
        "S",
        default
    )


def get_number(item, field, default=0.0):
    value = item.get(
        field,
        {}
    ).get(
        "N"
    )

    if value is None:
        return default

    return float(value)


# ============================================================
# Read all AEGIS findings
# ============================================================

items = []

scan_kwargs = {
    "TableName": TABLE_NAME
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


# ============================================================
# Separate reviewed and pending findings
# ============================================================

reviewed = [
    item
    for item in items
    if get_string(
        item,
        "review_status"
    ) == "REVIEWED"
]

pending = [
    item
    for item in items
    if get_string(
        item,
        "review_status"
    ) == "PENDING_REVIEW"
]


correct = [
    item
    for item in reviewed
    if get_string(
        item,
        "human_verdict"
    ) == "CORRECT"
]

incorrect = [
    item
    for item in reviewed
    if get_string(
        item,
        "human_verdict"
    ) == "INCORRECT"
]


# ============================================================
# Metrics
# ============================================================

reviewed_count = len(reviewed)
correct_count = len(correct)
incorrect_count = len(incorrect)

accuracy = (
    correct_count
    / reviewed_count
    * 100
    if reviewed_count
    else 0.0
)

error_rate = (
    incorrect_count
    / reviewed_count
    * 100
    if reviewed_count
    else 0.0
)


reviewed_confidences = [
    get_number(
        item,
        "confidence"
    )
    for item in reviewed
]

average_confidence = (
    sum(reviewed_confidences)
    / len(reviewed_confidences)
    if reviewed_confidences
    else 0.0
)


correct_confidences = [
    get_number(
        item,
        "confidence"
    )
    for item in correct
]

correct_avg_confidence = (
    sum(correct_confidences)
    / len(correct_confidences)
    if correct_confidences
    else 0.0
)


incorrect_confidences = [
    get_number(
        item,
        "confidence"
    )
    for item in incorrect
]

incorrect_avg_confidence = (
    sum(incorrect_confidences)
    / len(incorrect_confidences)
    if incorrect_confidences
    else 0.0
)


classification_counts = Counter(
    get_string(
        item,
        "classification",
        "UNKNOWN"
    )
    for item in reviewed
)


# ============================================================
# Human-readable report
# ============================================================

print()
print("===== AEGIS AI QUALITY METRICS =====")
print()

print(
    f"Total Findings:              {len(items)}"
)

print(
    f"Reviewed Findings:           {reviewed_count}"
)

print(
    f"Pending Review:              {len(pending)}"
)

print()

print(
    f"AI Correct:                  {correct_count}"
)

print(
    f"AI Incorrect:                {incorrect_count}"
)

print(
    f"AI Accuracy:                 {accuracy:.2f}%"
)

print(
    f"AI Error Rate:               {error_rate:.2f}%"
)

print()

print(
    f"Average AI Confidence:       {average_confidence:.2f}"
)

print(
    f"Correct Avg Confidence:      {correct_avg_confidence:.2f}"
)

if incorrect_count:
    print(
        f"Incorrect Avg Confidence:    {incorrect_avg_confidence:.2f}"
    )
else:
    print(
        "Incorrect Avg Confidence:    N/A"
    )

print()

print("Reviewed Classification Breakdown:")

for classification in [
    "TRUE_POSITIVE",
    "FALSE_POSITIVE",
    "UNCERTAIN"
]:
    print(
        f"  {classification:<16} "
        f"{classification_counts[classification]}"
    )


# ============================================================
# Dataset maturity indicator
# ============================================================

print()

if reviewed_count == 0:
    maturity = "NO_REVIEWED_DATA"
elif reviewed_count < 5:
    maturity = "EARLY_SAMPLE"
elif reviewed_count < 20:
    maturity = "BUILDING_DATASET"
else:
    maturity = "MEANINGFUL_SAMPLE"

print(
    f"Dataset Status:              {maturity}"
)

if reviewed_count < 5:
    print()
    print(
        "NOTE: Accuracy is preliminary because "
        "the reviewed sample size is still small."
    )

# ============================================================
# Publish AI quality metrics to CloudWatch
# ============================================================

metric_dimensions = [
    {
        "Name": "System",
        "Value": "AEGIS"
    },
    {
        "Name": "Environment",
        "Value": "eks-dev"
    }
]


cloudwatch.put_metric_data(
    Namespace="AEGIS/AIQuality",

    MetricData=[
        {
            "MetricName": "TotalFindings",
            "Dimensions": metric_dimensions,
            "Value": len(items),
            "Unit": "Count"
        },
        {
            "MetricName": "ReviewedFindings",
            "Dimensions": metric_dimensions,
            "Value": reviewed_count,
            "Unit": "Count"
        },
        {
            "MetricName": "PendingReview",
            "Dimensions": metric_dimensions,
            "Value": len(pending),
            "Unit": "Count"
        },
        {
            "MetricName": "CorrectFindings",
            "Dimensions": metric_dimensions,
            "Value": correct_count,
            "Unit": "Count"
        },
        {
            "MetricName": "IncorrectFindings",
            "Dimensions": metric_dimensions,
            "Value": incorrect_count,
            "Unit": "Count"
        },
        {
            "MetricName": "AccuracyPercent",
            "Dimensions": metric_dimensions,
            "Value": accuracy,
            "Unit": "Percent"
        },
        {
            "MetricName": "ErrorRatePercent",
            "Dimensions": metric_dimensions,
            "Value": error_rate,
            "Unit": "Percent"
        },
        {
            "MetricName": "AverageConfidence",
            "Dimensions": metric_dimensions,
            "Value": average_confidence,
            "Unit": "None"
        }
    ]
)


print(
    "CloudWatch Metrics:          PUBLISHED"
)

print(
    "Namespace:                   AEGIS/AIQuality"
)

print()
