# ── Stage 1: Build Dependencies ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install compilation tools needed for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies into /opt/venv
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ── Stage 2: Runtime Image ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Python runtime optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install only minimal runtime dependencies (curl for healthcheck, libpq5 for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated unprivileged user and group (UID/GID 10001)
RUN groupadd --gid 10001 skillverse && \
    useradd --uid 10001 --gid 10001 --home-dir /home/skillverse --create-home skillverse

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Pre-create storage directory with correct permissions before switching user
RUN mkdir -p /app/uploads/artifacts && \
    chown -R skillverse:skillverse /app /home/skillverse

# Copy application source code with non-root ownership
COPY --chown=skillverse:skillverse . /app

# Switch to unprivileged user
USER skillverse

EXPOSE 8000

# Container healthcheck targeting the actual API health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Exec-form CMD running uvicorn with proxy headers restricted to internal subnets
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=172.19.0.10"]
