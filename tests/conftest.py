# tests/conftest.py
import pytest

@pytest.fixture(scope="module")
def app_client():
    # Lazy import so that unit tests do not import FastAPI app on collection
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
