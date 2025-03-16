import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app


client = TestClient(app)

def test_health_check(client: TestClient):
    """Test if the health check endpoint is running."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Excel Query API (with Gemini) is running!",
        "timestamp": response.json()["timestamp"]
    }


def test_cors(client: TestClient):
    """Test if CORS is correctly configured."""
    response = client.options("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


