"""API tests for DXF upload query."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from matrix_advisor.api.server import app
from matrix_advisor.config import REPO_ROOT
from matrix_advisor.db import init_db

client = TestClient(app)
DXF_SAMPLE = REPO_ROOT / "data" / "die" / "rysunki" / "E08594.dxf"


@pytest.fixture(autouse=True)
def _db():
    init_db()


def test_reject_pdf_upload():
    res = client.post(
        "/api/v1/query/by-image",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


@pytest.mark.skipif(not DXF_SAMPLE.exists(), reason="Sample DXF missing")
def test_query_by_dxf():
    pytest.importorskip("ezdxf")
    data = DXF_SAMPLE.read_bytes()
    res = client.post(
        "/api/v1/query/by-dxf",
        files={"file": ("E08594.dxf", data, "application/dxf")},
        data={"top_k": "30", "stage": "1"},
    )
    if res.status_code == 503:
        pytest.skip("Index not built")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["query_preview"].startswith("data:image/png;base64,")
    assert body.get("extracted_dimensions")
    assert len(body["similar"]) >= 1
    ids = [s["profile_id"] for s in body["similar"]]
    assert "E08594" in ids or body["similar"][0]["score"] > 0.5


@pytest.mark.skipif(not DXF_SAMPLE.exists(), reason="Sample DXF missing")
def test_query_by_dxf_stage2():
    pytest.importorskip("ezdxf")
    data = DXF_SAMPLE.read_bytes()
    res = client.post(
        "/api/v1/query/by-dxf",
        files={"file": ("E08594.dxf", data, "application/dxf")},
        data={
            "top_k": "10",
            "stage": "2",
            "filters": '{"wall_thickness_mm": {"min": 1.0, "max": 2.0}}',
        },
    )
    if res.status_code == 503:
        pytest.skip("Index not built")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["stage"] == 2
    for hit in body["similar"]:
        assert "score_breakdown" in hit
