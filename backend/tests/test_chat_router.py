from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_thread_and_get_not_found_message():
    # Create a new thread
    resp = client.post("/chat/thread")
    assert resp.status_code == 200
    body = resp.json()
    assert "thread_id" in body

    # Getting messages for a non-existent thread id should 404
    resp2 = client.get("/chat/some-invalid-thread")
    assert resp2.status_code == 404


def test_post_message_to_missing_thread():
    # Post to a thread that doesn't exist
    resp = client.post("/chat/does-not-exist/message", json={"text": "hello"})
    assert resp.status_code == 404
