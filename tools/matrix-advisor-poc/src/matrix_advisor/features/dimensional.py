"""Millimeter-based dimensional features from DXF."""

from __future__ import annotations

from typing import Any


def extract_dimensional_features(
    profile_id: str,
    dims_mapped: dict[str, float | None],
    bbox: dict[str, float],
) -> dict[str, Any]:
    width = dims_mapped.get("width_mm") or bbox.get("width_mm")
    height = dims_mapped.get("height_mm") or bbox.get("height_mm")
    area = None
    if width and height:
        area = round(float(width) * float(height), 3)

    return {
        "profile_id": profile_id,
        "width_mm": width,
        "height_mm": height,
        "wall_thickness_mm": dims_mapped.get("wall_thickness_mm"),
        "ocd_mm": dims_mapped.get("ocd_mm"),
        "area_mm2": area,
    }
