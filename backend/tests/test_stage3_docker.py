"""Phase 10 — Stage 3 Docker Hardening & Configuration Tests.

Validates:
1. Backend Dockerfile multi-stage structure, non-root user (UID 10001), healthcheck, exec-form CMD.
2. Backend .dockerignore exclusions (secrets, virtualenvs, caches, tests, uploads).
3. Frontend Dockerfile multi-stage structure, lockfile usage (npm ci), unprivileged Nginx, healthcheck.
4. Frontend .dockerignore exclusions (node_modules, dist, secrets).
5. Frontend nginx.conf configuration (port 8080, security headers, caching, proxying, SPA routing).
6. docker-compose.yml service definitions (127.0.0.1 bindings, health checks, persistent volumes, frontend service).
7. Storage path alignment with container volume mount.
"""

import re
from pathlib import Path

import yaml

from app.config import settings

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Backend Dockerfile Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_backend_dockerfile_multi_stage():
    """Verify backend Dockerfile uses multi-stage build without build tools in runtime."""
    dockerfile = (BACKEND_DIR / "Dockerfile").read_text(encoding="utf-8")

    stages = re.findall(r"FROM\s+([^\s]+)\s+AS\s+([^\s\n]+)", dockerfile, re.IGNORECASE)
    assert len(stages) >= 2, f"Expected at least 2 stages, found {stages}"

    stage_names = [s[1].lower() for s in stages]
    assert "builder" in stage_names, "Expected 'builder' stage"
    assert "runtime" in stage_names, "Expected 'runtime' stage"

    # Split stages
    runtime_part = dockerfile.split("FROM", 2)[-1]

    # Verify build tools (gcc, libpq-dev) are not in runtime stage
    assert "gcc" not in runtime_part, "Compiler 'gcc' must not be installed in the runtime stage"
    assert "libpq-dev" not in runtime_part, "Header package 'libpq-dev' must not be in the runtime stage"
    assert "libpq5" in runtime_part, "Runtime library 'libpq5' should be present for PostgreSQL"


def test_backend_dockerfile_non_root_user():
    """Verify backend Dockerfile creates and runs as dedicated unprivileged user 10001."""
    dockerfile = (BACKEND_DIR / "Dockerfile").read_text(encoding="utf-8")

    # User & group creation
    assert "10001" in dockerfile, "Expected UID/GID 10001 to be declared"
    assert "skillverse" in dockerfile, "Expected user 'skillverse' to be created"

    # USER instruction
    assert re.search(r"USER\s+skillverse", dockerfile), "Dockerfile must switch to USER skillverse"

    # Ownership assignment
    assert "--chown=skillverse:skillverse" in dockerfile, "Files must be copied with skillverse ownership"
    assert "mkdir -p /app/uploads/artifacts" in dockerfile, "Uploads directory must be pre-created"


def test_backend_dockerfile_healthcheck_and_cmd():
    """Verify backend Dockerfile declares healthcheck and exec-form CMD with proxy headers."""
    dockerfile = (BACKEND_DIR / "Dockerfile").read_text(encoding="utf-8")

    # HEALTHCHECK directive
    assert "HEALTHCHECK" in dockerfile, "HEALTHCHECK must be declared"
    assert "/api/v1/health" in dockerfile, "HEALTHCHECK must target /api/v1/health"
    assert "--interval=" in dockerfile, "HEALTHCHECK must specify interval"
    assert "--timeout=" in dockerfile, "HEALTHCHECK must specify timeout"

    # CMD directive
    cmd_match = re.search(r'CMD\s*(\[[^\]]+\])', dockerfile)
    assert cmd_match, "CMD must be formatted as exec-form JSON array"
    cmd_str = cmd_match.group(1)
    assert "uvicorn" in cmd_str, "CMD must invoke uvicorn"
    assert "app.main:app" in cmd_str, "CMD must target app.main:app"
    assert "--proxy-headers" in cmd_str, "CMD must enable --proxy-headers"
    assert "--forwarded-allow-ips" in cmd_str, "CMD must specify restricted --forwarded-allow-ips"
    assert "*" not in cmd_str, "CMD must not trust forwarded IPs from wildcard '*'"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Backend .dockerignore Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_backend_dockerignore_exclusions():
    """Verify backend .dockerignore excludes sensitive and unneeded paths."""
    dockerignore_path = BACKEND_DIR / ".dockerignore"
    assert dockerignore_path.exists(), ".dockerignore must exist in backend/"

    content = dockerignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    expected_exclusions = [
        ".git",
        ".env*",
        "__pycache__/",
        "tests/",
        "uploads/",
    ]
    for pattern in expected_exclusions:
        assert any(pattern in line for line in lines), f"Missing expected pattern '{pattern}' in backend/.dockerignore"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Frontend Dockerfile Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_frontend_dockerfile_multi_stage():
    """Verify frontend Dockerfile uses multi-stage build, npm ci, and unprivileged Nginx."""
    dockerfile_path = FRONTEND_DIR / "Dockerfile"
    assert dockerfile_path.exists(), "Dockerfile must exist in frontend/"

    dockerfile = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage check
    stages = re.findall(r"FROM\s+([^\s]+)\s+AS\s+([^\s\n]+)", dockerfile, re.IGNORECASE)
    assert len(stages) >= 2, f"Expected at least 2 stages, found {stages}"

    # Builder uses node and npm ci
    assert "node:" in dockerfile.lower(), "Builder stage should use node image"
    assert "npm ci" in dockerfile, "Must use 'npm ci' to respect package-lock.json"
    assert "npm run build" in dockerfile, "Must run 'npm run build'"

    # Runtime uses unprivileged nginx
    assert "nginx-unprivileged" in dockerfile, "Runtime must use nginx-unprivileged base image"
    assert re.search(r"USER\s+nginx", dockerfile), "Must explicitly declare USER nginx"
    assert "EXPOSE 8080" in dockerfile, "Must expose unprivileged port 8080"

    # Static assets copy with chown
    assert "--from=builder" in dockerfile, "Must copy dist from builder stage"
    assert "--chown=nginx:nginx" in dockerfile, "Must assign nginx ownership to static files"

    # Healthcheck
    assert "HEALTHCHECK" in dockerfile, "Frontend Dockerfile must declare HEALTHCHECK"
    assert "/healthz" in dockerfile, "Frontend HEALTHCHECK must probe health endpoint"


def test_frontend_dockerignore_exclusions():
    """Verify frontend .dockerignore excludes node_modules, build outputs, and git."""
    dockerignore_path = FRONTEND_DIR / ".dockerignore"
    assert dockerignore_path.exists(), ".dockerignore must exist in frontend/"

    content = dockerignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    expected_exclusions = [
        ".git",
        "node_modules/",
        "dist/",
        ".env*",
    ]
    for pattern in expected_exclusions:
        assert any(pattern in line for line in lines), f"Missing expected pattern '{pattern}' in frontend/.dockerignore"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Frontend Nginx Configuration Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_frontend_nginx_configuration():
    """Verify frontend/nginx.conf adheres to unprivileged, SPA, caching, and proxy requirements."""
    nginx_conf_path = FRONTEND_DIR / "nginx.conf"
    assert nginx_conf_path.exists(), "nginx.conf must exist in frontend/"

    conf = nginx_conf_path.read_text(encoding="utf-8")

    # Port 8080 & version hiding
    assert "listen 8080;" in conf, "Nginx must listen on unprivileged port 8080"
    assert "server_tokens off;" in conf, "Nginx must disable server_tokens"

    # Security headers
    assert 'add_header X-Content-Type-Options "nosniff"' in conf, "Must include X-Content-Type-Options"
    assert 'add_header X-Frame-Options "DENY"' in conf, "Must include X-Frame-Options DENY"
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin"' in conf, "Must include Referrer-Policy"

    # Compression
    assert "gzip on;" in conf, "Gzip compression must be enabled"

    # Health check
    assert "location = /healthz" in conf, "Must define /healthz endpoint"

    # Caching policies
    assert "location /assets/" in conf, "Must define /assets/ caching block"
    assert "immutable" in conf, "Assets caching must use immutable"
    assert "location = /index.html" in conf, "Must define /index.html revalidation block"
    assert "no-cache" in conf, "index.html must require revalidation"

    # API Proxying
    assert "location /api/" in conf, "Must define /api/ proxy block"
    assert "proxy_pass http://api:8000;" in conf, "API requests must proxy to http://api:8000"
    assert "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;" in conf, "Must set X-Forwarded-For"
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in conf, "Must set X-Forwarded-Proto"

    # SPA fallback
    assert "try_files $uri $uri/ /index.html;" in conf, "Must support client-side SPA routing fallback"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Docker Compose Hardening Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_compose_configuration():
    """Verify docker-compose.yml defines hardened network, service, and storage settings."""
    compose_path = ROOT_DIR / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist at repository root"

    with open(compose_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    assert "postgres" in services, "postgres service must be defined"
    assert "redis" in services, "redis service must be defined"
    assert "api" in services, "api service must be defined"
    assert "frontend" in services, "frontend service must be defined"

    # Port restriction for databases: must bind only to 127.0.0.1
    postgres_ports = services["postgres"].get("ports", [])
    assert any("127.0.0.1:5432" in str(p) for p in postgres_ports), (
        f"PostgreSQL port must bind to 127.0.0.1, found: {postgres_ports}"
    )

    redis_ports = services["redis"].get("ports", [])
    assert any("127.0.0.1:6379" in str(p) for p in redis_ports), (
        f"Redis port must bind to 127.0.0.1, found: {redis_ports}"
    )

    api_ports = services["api"].get("ports", [])
    assert any("127.0.0.1:8000" in str(p) for p in api_ports), (
        f"API port must bind to 127.0.0.1, found: {api_ports}"
    )

    # API Healthcheck
    api_health = services["api"].get("healthcheck", {})
    assert "test" in api_health, "API must have a healthcheck"
    test_cmd = str(api_health["test"])
    assert "/api/v1/health" in test_cmd, "API healthcheck must target /api/v1/health"

    # API Volumes
    api_volumes = services["api"].get("volumes", [])
    assert any("artifact_data:/app/uploads" in str(v) for v in api_volumes), (
        f"API service must mount artifact_data volume to /app/uploads, found: {api_volumes}"
    )

    # Frontend depends_on api healthy
    frontend_depends = services["frontend"].get("depends_on", {})
    assert "api" in frontend_depends, "Frontend must depend on API"
    if isinstance(frontend_depends, dict):
        assert frontend_depends["api"].get("condition") == "service_healthy", (
            "Frontend must depend on API service_healthy"
        )

    # Top-level volumes
    volumes = data.get("volumes", {})
    assert "pgdata" in volumes, "pgdata volume must be declared"
    assert "artifact_data" in volumes, "artifact_data volume must be declared"


def test_storage_root_path_alignment():
    """Verify application storage configuration aligns with Docker volume mount."""
    # Relative path "uploads/artifacts" resolves under /app/uploads inside container
    storage_root = settings.storage_local_root
    assert storage_root.startswith("uploads"), (
        f"Storage root '{storage_root}' must be relative to uploads directory for container volume mapping"
    )
