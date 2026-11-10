# OpsPilot Backend Dockerfile
# Multi-stage build for FastAPI application

# ==============================================================================
# Base Stage - Common dependencies
# ==============================================================================
FROM python:3.11-slim AS base

LABEL maintainer="OpsPilot Team"
LABEL description="OpsPilot Backend API Service"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ==============================================================================
# Development Stage
# ==============================================================================
FROM base AS development

ENV ENVIRONMENT=development \
    DEBUG=true

RUN pip install --upgrade pip

COPY src/backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY src/backend/requirements-dev.txt ./requirements-dev.txt
RUN pip install -r requirements-dev.txt || true

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==============================================================================
# Builder Stage - Build dependencies for production
# ==============================================================================
FROM base AS builder

COPY src/backend/requirements.txt ./requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# ==============================================================================
# Production Stage
# ==============================================================================
FROM python:3.11-slim AS production

LABEL maintainer="OpsPilot Team"
LABEL description="OpsPilot Backend API Service - Production"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    ENVIRONMENT=production \
    DEBUG=false

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

COPY --chown=appuser:appgroup src/backend /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
