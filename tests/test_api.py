from fastapi.testclient import TestClient

from app.server import build_app


def test_health_endpoint():
    client = TestClient(build_app())
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_ingest_then_query_happy_path():
    client = TestClient(build_app())
    ingest = client.post(
        "/ingest",
        json={
            "doc_id": "horarios",
            "tenant_id": "demo",
            "title": "Horarios",
            "body": "Atendemos de lunes a viernes de 9 a 18 hs. Sabados de 9 a 13 hs.",
        },
    )
    assert ingest.status_code == 200
    assert ingest.json()["chunks_written"] >= 1

    q = client.post(
        "/query",
        json={"query": "Atendemos de lunes a viernes", "tenant_id": "demo", "limit": 3},
    )
    assert q.status_code == 200
    hits = q.json()["hits"]
    assert len(hits) >= 1


def test_ingest_rejects_empty_body():
    client = TestClient(build_app())
    r = client.post(
        "/ingest",
        json={"doc_id": "x", "tenant_id": "t", "title": "y", "body": "   "},
    )
    assert r.status_code == 400


def test_query_rejects_empty():
    client = TestClient(build_app())
    r = client.post("/query", json={"query": "  ", "tenant_id": "t"})
    assert r.status_code == 400
