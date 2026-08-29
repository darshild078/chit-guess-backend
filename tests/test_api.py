from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

def test_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_check_availability_invalid_code():
    response = client.get("/api/v1/rooms/code/INVALID/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["available"] is False
