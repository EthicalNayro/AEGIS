import json
import os
from pathlib import Path

import boto3


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

REGION = os.environ["AWS_REGION"]

RDS_SECRET_ARN = os.environ["RDS_SECRET_ARN"]

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "statuspage")

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

SITE_URL = os.environ["SITE_URL"]


# ---------------------------------------------------------
# Runtime files
# ---------------------------------------------------------

SECRET_KEY_FILE = Path(
    "/var/run/aegis-secret/django-secret-key"
)

OUTPUT_FILE = Path(
    "/runtime/configuration.py"
)


# ---------------------------------------------------------
# Django SECRET_KEY validation
# ---------------------------------------------------------

if not SECRET_KEY_FILE.exists():
    raise RuntimeError(
        "Django SECRET_KEY file is missing."
    )

django_secret_key = (
    SECRET_KEY_FILE
    .read_text()
    .strip()
)

if len(django_secret_key) < 50:
    raise RuntimeError(
        "Django SECRET_KEY is unexpectedly short."
    )


# ---------------------------------------------------------
# Retrieve RDS credentials from AWS Secrets Manager
# ---------------------------------------------------------

secretsmanager = boto3.client(
    "secretsmanager",
    region_name=REGION,
)

response = secretsmanager.get_secret_value(
    SecretId=RDS_SECRET_ARN
)

secret_payload = json.loads(
    response["SecretString"]
)

db_username = secret_payload["username"]
db_password = secret_payload["password"]


# ---------------------------------------------------------
# Generate Status-Page runtime configuration
# ---------------------------------------------------------

configuration = f"""
ALLOWED_HOSTS = [
    "app.aegis-project.ddnsfree.com",
    "localhost",
    "127.0.0.1",
]

DATABASE = {{
    "NAME": {DB_NAME!r},
    "USER": {db_username!r},
    "PASSWORD": {db_password!r},
    "HOST": {DB_HOST!r},
    "PORT": {DB_PORT!r},
    "CONN_MAX_AGE": 300,
}}

REDIS = {{
    "tasks": {{
        "HOST": {REDIS_HOST!r},
        "PORT": {REDIS_PORT},
        "PASSWORD": "",
        "DATABASE": 0,
        "SSL": True,
    }},
    "caching": {{
        "HOST": {REDIS_HOST!r},
        "PORT": {REDIS_PORT},
        "PASSWORD": "",
        "DATABASE": 1,
        "SSL": True,
    }},
}}

SITE_URL = {SITE_URL!r}

SECRET_KEY = {django_secret_key!r}

DEBUG = False

# The public HTTPS connection terminates at the AWS ALB.
# Trust X-Forwarded-Proto so Django knows the original request
# was HTTPS even though ALB -> Nginx uses internal HTTP.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

CSRF_TRUSTED_ORIGINS = [
    "https://app.aegis-project.ddnsfree.com",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]

PLUGINS = [
    "aegis_review",
]

PLUGINS_CONFIG = {{
    "aegis_review": {{
        "aws_region": "us-east-1",
        "findings_table": "aegis-eks-dev-security-findings",
    }}
}}

TIME_ZONE = "UTC"
""".lstrip()


# ---------------------------------------------------------
# Write configuration to in-memory runtime volume
# ---------------------------------------------------------

OUTPUT_FILE.write_text(
    configuration
)

OUTPUT_FILE.chmod(0o600)


# ---------------------------------------------------------
# Safe startup diagnostics
# ---------------------------------------------------------

print(
    "AEGIS Status-Page runtime configuration "
    "rendered successfully."
)

print(
    "Database credentials loaded from "
    "AWS Secrets Manager."
)

print(
    "HTTPS reverse-proxy awareness enabled."
)

print(
    "AEGIS Review plugin enabled."
)
