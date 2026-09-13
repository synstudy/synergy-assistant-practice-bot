from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["intents"] > 0


def test_chat_creates_session_and_replies():
    response = client.post("/api/chat", json={"message": "Привет"})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["reply"]
    assert body["state"] == "idle"


def test_chat_continues_session():
    first = client.post("/api/chat", json={"message": "Здравствуйте"}).json()
    session_id = first["session_id"]
    second = client.post(
        "/api/chat", json={"session_id": session_id, "message": "Какие направления?"}
    ).json()
    assert second["session_id"] == session_id
    assert second["intent"] == "programs"


def test_session_reset():
    session_id = "api-session-reset"
    client.post("/api/chat", json={"session_id": session_id, "message": "Привет"})
    response = client.post("/api/session/reset", json={"session_id": session_id})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_validation_rejects_empty_message():
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
