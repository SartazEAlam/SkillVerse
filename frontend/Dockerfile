# ── Stage 1: Build Frontend Assets ──────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies using package-lock.json
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code and compile
COPY . .
RUN npm run build

# ── Stage 2: Unprivileged Nginx Runtime ──────────────────────────────────────
FROM nginxinc/nginx-unprivileged:alpine-slim AS runtime

# Copy hardened unprivileged Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled SPA static bundle from builder stage
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Explicitly ensure unprivileged user (UID 101)
USER nginx

EXPOSE 8080

# Health check using lightweight busybox wget against local healthz endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --spider -q http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
