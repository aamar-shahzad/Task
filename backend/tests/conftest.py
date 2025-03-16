# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

@pytest.fixture(scope="module")
def client():
    """Fixture to provide the TestClient for making requests."""
    client = TestClient(app)
    yield client
