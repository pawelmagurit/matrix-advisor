"""Tests for DXF parser on sample files in data/die/rysunki/."""

from pathlib import Path

import pytest

import numpy as np

from matrix_advisor.config import REPO_ROOT
from matrix_advisor.dxf.parser import parse_dxf
from matrix_advisor.dxf.pipeline import process_dxf_file
from matrix_advisor.dxf.profile_selector import select_profile_entities
from matrix_advisor.query.dimensions_service import validate_dimensions_against_extral

RYSUNKI = REPO_ROOT / "data" / "die" / "rysunki"
SAMPLE_DXFS = sorted(RYSUNKI.glob("*.dxf"))


pytestmark = pytest.mark.skipif(
    not SAMPLE_DXFS,
    reason="Sample DXF files not present",
)


@pytest.fixture(scope="module")
def ezdxf_available():
    pytest.importorskip("ezdxf")


@pytest.mark.parametrize("dxf_path", SAMPLE_DXFS, ids=[p.stem for p in SAMPLE_DXFS])
def test_parse_sample_dxf(dxf_path: Path, ezdxf_available):
    doc = parse_dxf(path=dxf_path)
    assert doc.dxf_version
    assert doc.insunits == 4


@pytest.mark.parametrize("dxf_path", SAMPLE_DXFS, ids=[p.stem for p in SAMPLE_DXFS])
def test_profile_selection(dxf_path: Path, ezdxf_available):
    doc = parse_dxf(path=dxf_path).doc
    sel = select_profile_entities(doc)
    assert sel.entities, f"No entities selected for {dxf_path.name}"
    assert sel.strategy != "none"


@pytest.mark.parametrize("dxf_path", SAMPLE_DXFS, ids=[p.stem for p in SAMPLE_DXFS])
def test_process_to_mask(dxf_path: Path, ezdxf_available):
    result = process_dxf_file(dxf_path, persist=False)
    assert result.mask.shape == (256, 256)
    assert result.mask.max() > 0


def test_e02004_uses_extral_pictogram_fallback(ezdxf_available):
    """Extral drawings with side elevation should not search on the elevation mask."""
    from matrix_advisor.dxf.pipeline import _load_extral_pictogram_mask

    path = RYSUNKI / "E02004.dxf"
    if not path.exists():
        pytest.skip("E02004.dxf missing")
    result = process_dxf_file(path, persist=False)
    assert "used_extral_pictogram_fallback" in result.quality_flags
    assert "dropped_side_elevation_view" in result.quality_flags
    gif_mask = _load_extral_pictogram_mask("E02004")
    assert gif_mask is not None
    assert np.array_equal(result.mask, gif_mask)


def test_dimension_validation_e02004(ezdxf_available):
    result = process_dxf_file(RYSUNKI / "E02004.dxf", persist=False)
    checks = validate_dimensions_against_extral("E02004", result.dimensions_mapped)
    ocd = next((c for c in checks if c["field"] == "ocd_mm"), None)
    assert ocd is not None
    assert ocd["status"] == "ok"


def test_dxf_mask_iou_vs_gif(ezdxf_available):
    """DXF-derived mask should overlap GIF-derived mask for same profile."""
    from matrix_advisor.normalization.pipeline import load_mask

    result = process_dxf_file(RYSUNKI / "E08594.dxf", persist=False)
    gif_mask = load_mask("E08594")
    if gif_mask is None:
        pytest.skip("GIF mask not in index")
    dxf_bin = (result.mask > 127).astype(np.uint8)
    gif_bin = (gif_mask > 127).astype(np.uint8)
    inter = np.logical_and(dxf_bin, gif_bin).sum()
    union = np.logical_or(dxf_bin, gif_bin).sum()
    iou = inter / union if union else 0
    assert iou > 0.15, f"IoU too low: {iou:.3f}"


@pytest.mark.parametrize(
    "stem,min_iou",
    [("E12223", 0.15), ("E04900", 0.4)],
    ids=["E12223", "E04900"],
)
def test_block_style_dxf_uses_hatch_not_dimensions(stem: str, min_iou: float, ezdxf_available):
    """Block-based drawings must not rasterize dimension lines as profile."""
    from matrix_advisor.dxf.pipeline import _load_extral_pictogram_mask

    dxf_path = RYSUNKI / f"{stem}.dxf"
    if not dxf_path.exists():
        pytest.skip(f"{stem}.dxf missing")

    result = process_dxf_file(dxf_path, persist=False)
    assert result.selection.strategy == "hatch_widok"
    gif_mask = _load_extral_pictogram_mask(stem)
    if gif_mask is None:
        pytest.skip("GIF pictogram not in index")
    dxf_bin = (result.mask > 127).astype(np.uint8)
    gif_bin = (gif_mask > 127).astype(np.uint8)
    inter = np.logical_and(dxf_bin, gif_bin).sum()
    union = np.logical_or(dxf_bin, gif_bin).sum()
    iou = inter / union if union else 0
    assert iou >= min_iou, f"IoU too low for {stem}: {iou:.3f}"


def test_e03148_concentric_circles_use_ring(ezdxf_available):
    path = RYSUNKI / "E03148.dxf"
    if not path.exists():
        pytest.skip("E03148.dxf missing")
    from matrix_advisor.dxf.pipeline import _load_extral_pictogram_mask

    result = process_dxf_file(path, persist=False)
    assert result.selection.strategy == "layer"
    assert "used_extral_pictogram_fallback" in result.quality_flags
    gif_mask = _load_extral_pictogram_mask("E03148")
    assert gif_mask is not None
    assert np.array_equal(result.mask, gif_mask)


def test_load_mask_skips_corrupt_cached_png(ezdxf_available):
    from matrix_advisor.normalization.pipeline import load_mask, load_mask_from_pictogram

    fresh = load_mask_from_pictogram("E02004")
    assert fresh is not None
    loaded = load_mask("E02004")
    assert loaded is not None
    assert np.array_equal(loaded, fresh)


def test_dimension_validation_e08594(ezdxf_available):
    result = process_dxf_file(RYSUNKI / "E08594.dxf", persist=False)
    checks = validate_dimensions_against_extral("E08594", result.dimensions_mapped)
    by_field = {c["field"]: c["status"] for c in checks}
    assert by_field.get("ocd_mm") == "ok"
    assert by_field.get("wall_thickness_mm") == "ok"
