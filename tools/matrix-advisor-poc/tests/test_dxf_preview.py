"""API tests for DXF preview endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from matrix_advisor.api.server import app
from matrix_advisor.config import REPO_ROOT
from matrix_advisor.db import init_db

client = TestClient(app)
DXF_SAMPLE = REPO_ROOT / "data" / "die" / "rysunki" / "E12223.dxf"


@pytest.fixture(autouse=True)
def _db():
    init_db()


@pytest.mark.skipif(not DXF_SAMPLE.exists(), reason="Sample DXF missing")
def test_dxf_preview():
    pytest.importorskip("ezdxf")
    data = DXF_SAMPLE.read_bytes()
    res = client.post(
        "/api/v1/dxf/preview",
        files={"file": ("E12223.dxf", data, "application/dxf")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["filename"] == "E12223.dxf"
    assert body["profile_id_hint"] == "E12223"
    assert body["query_preview"].startswith("data:image/png;base64,")
    assert body["selection"]["strategy"] == "hatch_widok"
    assert body.get("extracted_dimensions")
