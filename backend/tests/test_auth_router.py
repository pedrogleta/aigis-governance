from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_validation_error():
    # Missing required fields should return 422
    resp = client.post("/auth/register", json={})
    assert resp.status_code == 422


def test_me_requires_authentication():
    resp = client.get("/auth/me")
    # With no Authorization header, should be 401 or 403 depending on dependency
    assert resp.status_code in (401, 403, 422)
