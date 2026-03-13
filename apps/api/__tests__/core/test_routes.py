"""Integration tests for core routes (/, /health)."""

from fastapi.testclient import TestClient


class TestCoreRoutes:
    def test_root_returns_message_and_version(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == "0.1.0"

    def test_health_returns_healthy(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
