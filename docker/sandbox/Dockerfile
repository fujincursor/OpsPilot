# OpsPilot Sandbox Dockerfile
# Secure execution environment for code generation and testing

# ==============================================================================
# Base Stage - Minimal secure base
# ==============================================================================
FROM python:3.11-slim AS base

LABEL maintainer="OpsPilot Team"
LABEL description="OpsPilot Sandbox Execution Environment"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN if getent group 65534 >/dev/null; then \
      groupmod -n sandbox "$(getent group 65534 | cut -d: -f1)"; \
    else \
      groupadd --gid 65534 sandbox; \
    fi \
 && if getent passwd 65534 >/dev/null; then \
      usermod -l sandbox -g sandbox -s /bin/false "$(getent passwd 65534 | cut -d: -f1)"; \
    else \
      useradd --uid 65534 --gid sandbox --shell /bin/false --no-create-home sandbox; \
    fi

WORKDIR /app

# ==============================================================================
# Development Stage - More permissive for debugging
# ==============================================================================
FROM base AS development

ENV SANDBOX_MODE=development

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    pylint \
    bandit \
    safety

RUN npm install -g \
    eslint \
    prettier \
    typescript \
    jest

RUN mkdir -p /app/workspace && chown sandbox:sandbox /app/workspace

COPY docker/sandbox/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER sandbox

ENTRYPOINT ["/entrypoint.sh"]

# ==============================================================================
# Production Stage - Hardened execution environment
# ==============================================================================
FROM base AS production

ENV SANDBOX_MODE=production

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache

RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    pylint \
    bandit

RUN npm install -g \
    eslint \
    prettier \
    typescript \
    jest \
    && npm cache clean --force

RUN mkdir -p /app/workspace \
    && chown sandbox:sandbox /app/workspace

RUN rm -rf /root/.npm \
    && rm -rf /root/.cache \
    && rm -rf /var/cache/*

RUN chmod 755 /app \
    && chmod 700 /app/workspace

COPY --chown=root:root docker/sandbox/entrypoint.sh /entrypoint.sh
RUN chmod 555 /entrypoint.sh

RUN rm -rf /usr/bin/apt* \
    && rm -rf /usr/bin/dpkg* \
    && rm -rf /var/lib/apt \
    && rm -rf /var/lib/dpkg

USER sandbox

WORKDIR /app/workspace

ENTRYPOINT ["/entrypoint.sh"]
