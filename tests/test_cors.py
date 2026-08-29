from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_options_preflight():
    response = client.options(
        "/api/v1/rooms",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_get_origin_header():
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

def test_cors_127_origin_header():
    response = client.get(
        "/health",
        headers={"Origin": "http://127.0.0.1:5173"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
