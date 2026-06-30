"""Extract dimensions from DXF DIMENSION entities."""

from __future__ import annotations

from typing import Any


def extract_dimension_values(doc: Any) -> list[float]:
    values: list[float] = []
    for e in doc.modelspace().query("DIMENSION"):
        try:
            v = float(e.dxf.actual_measurement)
            if v > 0:
                values.append(round(v, 4))
        except (AttributeError, TypeError, ValueError):
            pass
    return sorted(set(values))


def map_dimensions(values: list[float]) -> dict[str, float | None]:
    """Heuristic mapping of raw DIMENSION values to technical fields."""
    if not values:
        return {
            "ocd_mm": None,
            "wall_thickness_mm": None,
            "width_mm": None,
            "height_mm": None,
        }

    sorted_vals = sorted(values, reverse=True)
    ocd = max(values) if values else None

    # Wall thickness: smallest positive value often < 5mm (samples: 0.9, 1.4, 1.6)
    small = [v for v in values if 0.05 < v < 6.0]
    wall = min(small) if small else None

    # Width/height from top two distinct mids
    mids = [v for v in sorted_vals if v < (ocd or 999) * 0.95]
    width = mids[0] if mids else None
    height = mids[1] if len(mids) > 1 else width

    return {
        "ocd_mm": ocd,
        "wall_thickness_mm": wall,
        "width_mm": width,
        "height_mm": height,
    }
