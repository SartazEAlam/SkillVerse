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
        assert heads[0] == "003_activities_and_assessments"

    def test_postgresql_migration_sql_has_no_duplicate_enum_creations(self) -> None:
        """Regression test: verify each PostgreSQL enum type is created exactly once during upgrade."""
        import io
        import os
        import re
        import sys
        from collections import Counter
        from pathlib import Path

        from alembic.config import Config

        from alembic import command

        backend_dir = Path(__file__).resolve().parent.parent
        ini_path = backend_dir / "alembic.ini"
        alembic_cfg = Config(str(ini_path))

        orig_db = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = "postgresql+psycopg2://mock:mock@localhost:5432/mock"
        try:
            old_stdout = sys.stdout
            sys.stdout = buf = io.StringIO()
            try:
                command.upgrade(alembic_cfg, "head", sql=True)
            finally:
                sys.stdout = old_stdout
            sql = buf.getvalue()
        finally:
            if orig_db is not None:
                os.environ["DATABASE_URL"] = orig_db
            else:
                os.environ.pop("DATABASE_URL", None)

        creates = re.findall(r"CREATE TYPE (\w+)", sql)
        counts = Counter(creates)
        expected_enums = ["user_role", "skill_difficulty", "course_difficulty", "course_status"]

        # Ensure all expected enums are created
        assert set(creates) == set(expected_enums)
        # Ensure none are created more than once
        for enum_name in expected_enums:
            assert counts[enum_name] == 1, f"Enum '{enum_name}' was created {counts[enum_name]} times (expected 1)"

    def test_postgresql_downgrade_sql_drops_enums_safely(self) -> None:
        """Regression test: verify each enum type is dropped safely and after dependent tables."""
        import io
        import os
        import re
        import sys
        from collections import Counter
        from pathlib import Path

        from alembic.config import Config

        from alembic import command

        backend_dir = Path(__file__).resolve().parent.parent
        ini_path = backend_dir / "alembic.ini"
        alembic_cfg = Config(str(ini_path))

        orig_db = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = "postgresql+psycopg2://mock:mock@localhost:5432/mock"
        try:
            old_stdout = sys.stdout
            sys.stdout = buf = io.StringIO()
            try:
                command.downgrade(alembic_cfg, "head:base", sql=True)
            finally:
                sys.stdout = old_stdout
            sql = buf.getvalue()
        finally:
            if orig_db is not None:
                os.environ["DATABASE_URL"] = orig_db
            else:
                os.environ.pop("DATABASE_URL", None)

        drops = re.findall(r"DROP TYPE (\w+)", sql)
        counts = Counter(drops)
        expected_enums = ["course_status", "course_difficulty", "skill_difficulty", "user_role"]

        assert set(drops) == set(expected_enums)
        for enum_name in expected_enums:
            assert counts[enum_name] == 1, f"Enum '{enum_name}' was dropped {counts[enum_name]} times (expected 1)"

        # Tables using enum columns must be dropped before the respective enum types
        assert sql.index("DROP TABLE users") < sql.index("DROP TYPE user_role")
        assert sql.index("DROP TABLE courses") < sql.index("DROP TYPE course_status")
        assert sql.index("DROP TABLE courses") < sql.index("DROP TYPE course_difficulty")
        assert sql.index("DROP TABLE skills") < sql.index("DROP TYPE skill_difficulty")


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
