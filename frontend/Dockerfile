# Multi-stage Dockerfile for Frontend

# ============================================
# Base Stage - Dependencies
# ============================================
FROM node:20-alpine AS base

# Set working directory
WORKDIR /app

# Install build dependencies for better ARM64 compatibility
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# ============================================
# Development Stage
# ============================================
FROM base AS development

# Install all dependencies (including devDependencies)
RUN npm install

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5173 || exit 1

# Run development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ============================================
# Build Stage - Production Build
# ============================================
FROM base AS builder

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Copy application code
COPY . .

# Build application
RUN npm run build

# ============================================
# Production Stage - Nginx
# ============================================
FROM nginx:alpine AS production

# Install envsubst (gettext package) for environment variable substitution
RUN apk add --no-cache gettext

# Copy custom nginx config template
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Environment variables with defaults
ENV BACKEND_HOST=backend
ENV BACKEND_PORT=8000

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

# Create entrypoint script that substitutes env vars and starts nginx
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo 'echo "Configuring Nginx with BACKEND_HOST=$BACKEND_HOST and BACKEND_PORT=$BACKEND_PORT"' >> /docker-entrypoint.sh && \
    echo 'envsubst '\''$BACKEND_HOST $BACKEND_PORT'\'' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.sh && \
    echo 'echo "Starting Nginx..."' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Run entrypoint script
CMD ["/docker-entrypoint.sh"]

