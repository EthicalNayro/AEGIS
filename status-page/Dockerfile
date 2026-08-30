ARG PYTHON_BASE=python:3.12-slim-bookworm@sha256:0f5b26b9518d002b6173fd61daad821fa340635ebfec5bba471013f9ca114579


# ============================================================
# BUILD STAGE
#
# Compilers and development headers exist only here.
# The final runtime image never inherits this stage.
# ============================================================
FROM ${PYTHON_BASE} AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        libpq-dev \
        libssl-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt local_requirements.txt ./

RUN python -m venv "$VIRTUAL_ENV" \
    && python -m pip install --upgrade pip wheel \
    && python -m pip install \
        -r requirements.txt \
        -r local_requirements.txt


# ============================================================
# RUNTIME STAGE
#
# Contains only what AEGIS Status-Page needs at runtime.
# No compiler toolchain or development headers are retained.
# ============================================================
FROM ${PYTHON_BASE} AS runtime

LABEL org.opencontainers.image.title="AEGIS Status-Page"
LABEL org.opencontainers.image.version="v2.5.1-aegis-1"
LABEL aegis.status-page.upstream-version="v2.5.1"
LABEL aegis.status-page.upstream-commit="93bdc1eb606809d4ed32648043130889a4a7e45a"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# Runtime library required by psycopg2/PostgreSQL.
# Development headers remain confined to the builder stage.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Pinned Status-Page source plus native AEGIS plugin.
COPY . /app

# Dedicated non-root runtime identity.
RUN groupadd --gid 1000 status-page \
    && useradd \
        --uid 1000 \
        --gid 1000 \
        --no-create-home \
        --shell /usr/sbin/nologin \
        status-page \
    && chown -R 1000:1000 /app

USER 1000:1000

WORKDIR /app/statuspage

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "statuspage.wsgi:application"]
