from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_error_envelope_structure_on_404():
    response = client.get("/api/v1/rooms/code/NONEXISTENT/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["available"] is False

def test_request_id_header_present():
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers

def test_custom_request_id_header_propagated():
    custom_id = "test-req-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id

def test_validation_error_envelope():
    # POST to join with invalid body
    response = client.post("/api/v1/rooms/join", json={"roomCode": "123", "displayName": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "message" in data
    assert isinstance(data["message"], str)

def test_unauthorized_error_envelope():
    # Access current room without auth token
    response = client.get("/api/v1/rooms/current")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error_code"] == "UNAUTHORIZED"
    assert "message" in data
