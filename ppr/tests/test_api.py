"""Provide unit tests."""

from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_openapi_json() -> None:
    """Test GET request for /openapi.json API endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_get_openapi_yaml() -> None:
    """Test GET request for /openapi.yaml API endpoint."""
    response = client.get("/openapi.yaml")
    assert response.status_code == 200


def test_openapi_yml() -> None:
    """Test GET request for /openapi.yml API endpoint."""
    response = client.get("/openapi.yml")
    assert response.status_code == 200


def test_get_catalogues() -> None:
    """Test GET request for /ping API endpoint."""
    response = client.get("/catalogues")
    assert response.status_code == 200


def test_get_pong() -> None:
    """Test GET request for nonexistent /nonexistent API endpoint."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
