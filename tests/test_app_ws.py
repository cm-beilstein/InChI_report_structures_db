
import pytest
from fastapi.testclient import TestClient
from app.app_ws import app

# def test_health_unauthorized(monkeypatch, tmp_path):
#     # create a tokens file with one valid token (we won't send it)
#     token_file = tmp_path / "tokens.txt"
#     token_file.write_text("validtoken\n")
#     monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

#     client = TestClient(app)
#     resp = client.get("/health")  # no Authorization header
#     assert resp.status_code == 401
#     assert "error" in resp.json()

# def test_health_authorized(monkeypatch, tmp_path):
#     token = "validtoken"
#     token_file = tmp_path / "tokens.txt"
#     token_file.write_text(token + "\n")
#     monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

#     client = TestClient(app)
#     resp = client.get("/health", headers={"Authorization": token})
#     assert resp.status_code == 200
#     assert resp.json() == {"status": "ok"}

def test_ingest_issue_authorized(monkeypatch, tmp_path):
    # Prepare token file and env var
    token = "validtoken"
    token_file = tmp_path / "tokens.txt"
    token_file.write_text(token + "\n")
    monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

    # Mock the DB session provider used as a FastAPI dependency
    monkeypatch.setattr("app.app_ws.get_session", lambda: object())

    # Mock Issues.add to avoid touching the real DB
    class MockIssue:
        def __init__(self, id):
            self.id = id

    def fake_add(session, **data):
        # optional: assert expected payload fields are present
        assert "user" in data and "description" in data
        return MockIssue(123)

    monkeypatch.setattr("app.app_ws.Issues.add", fake_add)

    client = TestClient(app)
    payload = {"user": "alice", "description": "test issue"}
    resp = client.post("/ingest_issue", headers={"Authorization": token}, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["issue_id"] == 123

def test_get_issues_authorized(monkeypatch, tmp_path):
    # Prepare token file and env var
    token = "validtoken"
    token_file = tmp_path / "tokens.txt"
    token_file.write_text(token + "\n")
    monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

    # Mock the DB session provider
    monkeypatch.setattr("app.app_ws.get_session", lambda: object())

    # Mock Issues.get_all_sorted_by_date to return sample issues
    class MockIssue:
        def __init__(self, id, user, description, date_created, molfile, inchi, auxinfo, inchikey, logs, options, inchi_version):
            self.id = id
            self.user = user
            self.description = description
            self.date_created = date_created
            self.molfile = molfile
            self.inchi = inchi
            self.auxinfo = auxinfo
            self.inchikey = inchikey
            self.logs = logs
            self.options = options
            self.inchi_version = inchi_version

    mock_issues = [
        MockIssue(1, "alice", "issue1", "2025-01-01", "mol1", "inchi1", "aux1", "key1", "log1", "opt1", "1.05"),
        MockIssue(2, "bob", "issue2", "2025-01-02", "mol2", "inchi2", "aux2", "key2", "log2", "opt2", "1.05"),
    ]

    def fake_get_all(session):
        return mock_issues

    monkeypatch.setattr("app.app_ws.Issues.get_all_sorted_by_date", fake_get_all)

    client = TestClient(app)
    resp = client.get("/get_all_issues", headers={"Authorization": token})

    assert resp.status_code == 200
    body = resp.json()
    assert "issues" in body
    assert len(body["issues"]) == 2
    assert body["issues"][0]["id"] == 1
    assert body["issues"][0]["user"] == "alice"
    assert body["issues"][1]["id"] == 2
    assert body["issues"][1]["user"] == "bob"

def test_get_issues_unauthorized(monkeypatch, tmp_path):
    # Test without authorization token
    token_file = tmp_path / "tokens.txt"
    token_file.write_text("validtoken\n")
    monkeypatch.setenv("INCHI_TOKENS_FILE", str(token_file))

    client = TestClient(app)
    resp = client.get("/get_all_issues")  # no Authorization header
    assert resp.status_code == 401
    assert "error" in resp.json()