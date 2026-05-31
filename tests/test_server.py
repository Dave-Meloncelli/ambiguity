from ambiguity.server import app, AnalyzeRequest, ReviewRequest
from fastapi.testclient import TestClient


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


def test_root_redirects():
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert "/docs" in resp.headers.get("location", "")


def test_analyze_endpoint():
    resp = client.post("/analyze", json={"prompt": "write a function"})
    assert resp.status_code == 200
    body = resp.json()
    assert "version" in body
    assert "ambiguity_score" in body or "total" in str(body)


def test_analyze_endpoint_empty():
    resp = client.post("/analyze", json={"prompt": ""})
    assert resp.status_code == 200


def test_review_endpoint():
    resp = client.post("/review", json={
        "prompt": "write a function",
        "response": "here is a function",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "command" in body
    assert body["command"] == "review"


def test_review_endpoint_empty():
    resp = client.post("/review", json={
        "prompt": "", "response": "",
    })
    assert resp.status_code == 200


def test_analyze_request_model():
    r = AnalyzeRequest(prompt="test")
    assert r.prompt == "test"


def test_review_request_model():
    r = ReviewRequest(prompt="a", response="b")
    assert r.prompt == "a"
    assert r.response == "b"
