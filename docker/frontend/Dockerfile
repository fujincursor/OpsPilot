# OpsPilot Frontend Dockerfile
# Multi-stage build for Vite + React/Vue application

# ==============================================================================
# Base Stage - Node.js base
# ==============================================================================
FROM node:20-alpine AS base

LABEL maintainer="OpsPilot Team"
LABEL description="OpsPilot Frontend Service"

WORKDIR /app

RUN apk add --no-cache libc6-compat

# ==============================================================================
# Dependencies Stage - Install dependencies
# ==============================================================================
FROM base AS deps

COPY src/frontend/package*.json ./
COPY src/frontend/pnpm-lock.yaml* ./
COPY src/frontend/yarn.lock* ./

RUN corepack enable && corepack prepare pnpm@latest --activate || true

RUN if [ -f pnpm-lock.yaml ]; then \
      pnpm install --frozen-lockfile; \
    elif [ -f yarn.lock ]; then \
      yarn install --frozen-lockfile; \
    else \
      npm ci; \
    fi

# ==============================================================================
# Development Stage - Development server with hot reload
# ==============================================================================
FROM base AS development

ENV NODE_ENV=development

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY src/frontend ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ==============================================================================
# Builder Stage - Build production assets
# ==============================================================================
FROM base AS builder

ENV NODE_ENV=production

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY src/frontend ./

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ==============================================================================
# Production Stage - Nginx serving static files
# ==============================================================================
FROM nginx:alpine AS production

LABEL maintainer="OpsPilot Team"
LABEL description="OpsPilot Frontend Service - Production"

RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist /usr/share/nginx/html

COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

RUN addgroup -g 1000 -S appgroup \
    && adduser -u 1000 -S appuser -G appgroup

RUN chown -R appuser:appgroup /var/cache/nginx \
    && chown -R appuser:appgroup /var/log/nginx \
    && chown -R appuser:appgroup /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R appuser:appgroup /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
