"""Tests for ad-hoc upload similarity query."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from matrix_advisor.api.server import app
from matrix_advisor.config import RAW_PICTOGRAMS
from matrix_advisor.db import get_connection
from matrix_advisor.query.service import get_stats

pytestmark = pytest.mark.skipif(
    get_stats()["profiles"] < 1000,
    reason="Full Extral dataset not loaded — run bootstrap-extral first",
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_gif_bytes() -> bytes:
    gifs = list(RAW_PICTOGRAMS.glob("*.gif"))
    if not gifs:
        pytest.skip("No pictogram fixtures in data/raw/pictograms")
    return gifs[0].read_bytes()


def test_query_by_image_embedding(client, sample_gif_bytes):
    before = _profile_count()
    r = client.post(
        "/api/v1/query/by-image",
        files={"file": ("test.gif", sample_gif_bytes, "image/gif")},
        data={"method": "embedding", "top_k": "5", "label": "Oferta TEST-001"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["query_display_name"] == "Oferta TEST-001"
    assert body["query_profile_id"] == "__upload__"
    assert body["query_preview"].startswith("data:image/png;base64,")
    assert len(body["similar"]) == 5
    assert body["similar"][0]["rank"] == 1
    scores = [s["score"] for s in body["similar"]]
    assert scores == sorted(scores, reverse=True)
    assert body["recommendation_note"]
    assert _profile_count() == before


def test_query_by_image_geometric(client, sample_gif_bytes):
    r = client.post(
        "/api/v1/query/by-image",
        files={"file": ("test.gif", sample_gif_bytes, "image/gif")},
        data={"method": "geometric", "top_k": "3"},
    )
    assert r.status_code == 200
    assert len(r.json()["similar"]) == 3


def test_query_by_image_invalid_type(client):
    r = client.post(
        "/api/v1/query/by-image",
        files={"file": ("bad.txt", b"not an image", "text/plain")},
    )
    assert r.status_code == 400


def test_query_by_image_empty(client):
    r = client.post(
        "/api/v1/query/by-image",
        files={"file": ("empty.gif", b"", "image/gif")},
    )
    assert r.status_code == 400


def _profile_count() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM profiles").fetchone()["c"]
