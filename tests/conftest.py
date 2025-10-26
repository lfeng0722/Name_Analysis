import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def app_client():
    return TestClient(app)
