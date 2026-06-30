"""DXF preview without similarity search."""

from __future__ import annotations

from matrix_advisor.dxf.pipeline import process_dxf_bytes
from matrix_advisor.query.by_dxf_service import _validate_dxf

_PREVIEW_NOTES = {
    "used_extral_pictogram_fallback": (
        "DXF nie zawiera pełnego przekroju profilu — podgląd i wyszukiwanie używają piktogramu Extral "
        "dla tego indeksu."
    ),
    "incomplete_dxf_cross_section": (
        "DXF nie zawiera czytelnego przekroju — wyniki wyszukiwania mogą być niedokładne."
    ),
    "dropped_side_elevation_view": "Z rysunku DXF pominięto widok z boku (zostawiono przekrój).",
}


def _preview_warning(flags: list[str]) -> str | None:
    for flag in flags:
        if flag in _PREVIEW_NOTES:
            return _PREVIEW_NOTES[flag]
    return None


def preview_dxf_bytes(
    data: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> dict:
    _validate_dxf(data, filename, content_type)

    try:
        processed = process_dxf_bytes(data, source_name=filename, persist=False)
    except ImportError as e:
        raise ValueError(str(e)) from e
    except ValueError as e:
        raise ValueError(f"Cannot process DXF: {e}") from e

    if "empty_contour" in processed.quality_flags:
        raise ValueError("Cannot process DXF: no contour detected")

    stem = None
    if filename and "." in filename:
        stem = filename.rsplit(".", 1)[0]

    return {
        "filename": filename,
        "profile_id": processed.profile_id,
        "profile_id_hint": stem.upper() if stem else processed.profile_id,
        "query_preview": processed.preview_data_url,
        "extracted_dimensions": processed.dimensions_mapped,
        "quality_flags": processed.quality_flags,
        "preview_warning": _preview_warning(processed.quality_flags),
        "selection": {
            "strategy": processed.selection.strategy,
            "layer": processed.selection.layer,
            "block": processed.selection.block,
        },
    }
