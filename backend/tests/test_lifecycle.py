"""Tests for system lifecycle, health check endpoint, and database migrations."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings


class TestSystemHealth:
    """Tests for GET /api/v1/health."""

    def test_health_check_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "timestamp" in data
        assert "services" in data
        assert "database" in data["services"]
        assert data["services"]["database"] == "connected"


class TestDatabaseMigrations:
    """Verifies that the initial Alembic migration revision exists and is valid."""

    def test_alembic_initial_revision_exists(self) -> None:
        from pathlib import Path

        from alembic.config import Config
        from alembic.script import ScriptDirectory

        backend_dir = Path(__file__).resolve().parent.parent
        ini_path = backend_dir / "alembic.ini"
        script_dir = backend_dir / "alembic"

        alembic_cfg = Config(str(ini_path))
        alembic_cfg.set_main_option("script_location", str(script_dir))
        script = ScriptDirectory.from_config(alembic_cfg)

        heads = script.get_heads()
        assert len(heads) == 1
        assert heads[0] == "002_skill_taxonomy_and_courses"


class TestProductionEnvironmentInvariants:
    """Verifies that production environment fails safely when invariants are violated."""

    def test_production_rejects_sqlite(self) -> None:
        with pytest.raises(ValueError, match="Production environment cannot use SQLite"):
            Settings(environment="production", database_url="sqlite:///./prod.db")

    def test_production_rejects_default_or_weak_jwt_key(self) -> None:
        with pytest.raises(ValueError, match="Production environment requires a secure"):
            Settings(
                environment="production",
                database_url="postgresql://user:pass@localhost:5432/db",
                jwt_secret_key="short",
            )
