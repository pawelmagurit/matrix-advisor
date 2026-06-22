"""Integration tests against production Extral dataset (requires bootstrap-extral)."""

import pytest
from fastapi.testclient import TestClient

from matrix_advisor.api.server import app
from matrix_advisor.query.service import get_stats


pytestmark = pytest.mark.skipif(
    get_stats()["profiles"] < 1000,
    reason="Full Extral dataset not loaded — run bootstrap-extral first",
)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_full_dataset(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["profiles"] == 10877
    assert data["pictograms"] == 10067
    assert data["matrices"] == 18644


def test_browse_pagination(client):
    r = client.get("/api/v1/profiles", params={"page": 1, "page_size": 48})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 10877
    assert len(data["items"]) == 48
    assert "profile_id" in data["items"][0]


def test_browse_search(client):
    r = client.get("/api/v1/profiles", params={"search": "E06335", "page_size": 20})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert any("06335" in i["profile_id"] for i in items)


def test_browse_supplier_filter(client):
    suppliers = client.get("/api/v1/filters/suppliers").json()["suppliers"]
    assert len(suppliers) == 27
    r = client.get("/api/v1/profiles", params={"supplier": suppliers[0], "page_size": 10})
    assert r.status_code == 200
    assert len(r.json()["items"]) > 0


def test_profile_detail_and_pictogram(client):
    listing = client.get("/api/v1/profiles", params={"page_size": 50}).json()["items"]
    pid = next(i["profile_id"] for i in listing if i["has_pictogram"])
    detail = client.get(f"/api/v1/profiles/{pid}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["profile_id"] == pid
    assert isinstance(body["matrices"], list)

    pic = client.get(f"/api/v1/profiles/{pid}/pictogram", params={"raw": True})
    assert pic.status_code == 200
    assert pic.headers["content-type"].startswith("image/")


def test_advisory_both_methods(client):
    listing = client.get("/api/v1/profiles", params={"page_size": 50}).json()["items"]
    pid = next(i["profile_id"] for i in listing if i["has_pictogram"])

    for method in ("embedding", "geometric"):
        r = client.get(
            f"/api/v1/profiles/{pid}/advisory",
            params={"method": method, "top_k": 8},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["query_profile_id"] == pid
        assert 1 <= len(data["similar"]) <= 8
        assert data["similar"][0]["rank"] == 1
        scores = [s["score"] for s in data["similar"]]
        assert scores == sorted(scores, reverse=True)
        assert all(s["profile_id"] != pid for s in data["similar"])
        assert data["recommendation_note"]


def test_unknown_profile_404(client):
    assert client.get("/api/v1/profiles/DOES-NOT-EXIST-XYZ").status_code == 404
