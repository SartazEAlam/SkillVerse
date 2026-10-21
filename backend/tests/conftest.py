"""Test configuration and fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Force test settings before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["ENVIRONMENT"] = "development"

from app.infrastructure.database import Base, get_db
from app.infrastructure.rate_limiter import limiter
from app.main import app

# Use SQLite for tests (no Docker dependency for CI)
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Create all tables before each test and drop after."""
    limiter.reset()
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    limiter.reset()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    """Provide a test HTTP client."""
    return TestClient(app)


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    """Register a test user and return the response data."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecureP@ss1",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_tokens(client: TestClient, registered_user: dict) -> dict:
    """Login a test user and return tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "SecureP@ss1"},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(auth_tokens: dict) -> dict[str, str]:
    """Return Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}
