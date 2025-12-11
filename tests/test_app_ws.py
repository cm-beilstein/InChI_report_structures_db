

from fastapi.testclient import TestClient
from app.app_ws import app

def test_health_unauthorized(monkeypatch, tmp_path):
    # create a tokens file with one valid token (we won't send it)
    token_file = tmp_path / "tokens.txt"
    token_file.write_text("validtoken\n")
    monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

    client = TestClient(app)
    resp = client.get("/health")  # no Authorization header
    assert resp.status_code == 401
    assert "error" in resp.json()

def test_health_authorized(monkeypatch, tmp_path):
    token = "validtoken"
    token_file = tmp_path / "tokens.txt"
    token_file.write_text(token + "\n")
    monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

    client = TestClient(app)
    resp = client.get("/health", headers={"Authorization": token})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_ingest_issue_authorized(monkeypatch, tmp_path):
    # Prepare token file and env var
    token = "validtoken"
    token_file = tmp_path / "tokens.txt"
    token_file.write_text(token + "\n")
    monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

    # Mock the DB session provider used as a FastAPI dependency
    monkeypatch.setattr("app.app_ws.get_session", lambda: object())

    # Mock Issues.add to avoid touching the real DB
    class DummyIssue:
        def __init__(self, id):
            self.id = id

    def fake_add(session, **data):
        # optional: assert expected payload fields are present
        assert "user" in data and "description" in data
        return DummyIssue(123)

    monkeypatch.setattr("app.app_ws.Issues.add", fake_add)

    client = TestClient(app)
    payload = {"user": "alice", "description": "test issue"}
    resp = client.post("/ingest_issue", headers={"Authorization": token}, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["issue_id"] == 123