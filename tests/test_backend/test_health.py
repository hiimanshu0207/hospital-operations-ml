"""
Test the /health endpoint.

Verifies that the FastAPI application starts and responds correctly.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


def test_health_returns_200(client):
    """GET /health should return 200 with status 'healthy'."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body(client):
    """GET /health response should contain expected keys and values."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
