FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="AEGIS Status-Page"
LABEL org.opencontainers.image.version="v2.5.1-aegis-1"
LABEL aegis.status-page.upstream-version="v2.5.1"
LABEL aegis.status-page.upstream-commit="93bdc1eb606809d4ed32648043130889a4a7e45a"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Status-Page native build/runtime dependencies.
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

WORKDIR /app

# Install Python dependencies before copying application
# source to maximize Docker layer reuse.
COPY requirements.txt local_requirements.txt ./

RUN python -m pip install --upgrade pip wheel \
    && python -m pip install \
        -r requirements.txt \
        -r local_requirements.txt

# Copy pinned Status-Page source plus AEGIS plugin.
COPY . /app

# Build documentation bundled by the upstream project.

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
