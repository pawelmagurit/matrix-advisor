"""DXF vs Extral dimension validation and profile dimension API helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from matrix_advisor.config import DIMENSION_TOLERANCE_MM, DIMENSION_TOLERANCE_PCT, EXTRAL_JSON, PROCESSED_GEOMETRY
from matrix_advisor.db import get_connection


def _load_extral_props(profile_id: str) -> dict[str, str | float | None]:
    if not EXTRAL_JSON.exists():
        return {}
    import json as _json

    with open(EXTRAL_JSON, encoding="utf-8") as f:
        rows = _json.load(f)
    row = next((r for r in rows if r.get("indeks") == profile_id), None)
    if not row:
        return {}

    props: dict[str, str | float | None] = {}
    wlas = row.get("wlasnosci") or {}
    for v in wlas.values():
        if not isinstance(v, dict):
            continue
        label = str(v.get("item1", ""))
        val = v.get("item2")
        if "OCD" in label:
            props["ocd_mm"] = _parse_num(val)
        elif "Grubość" in label or "scianki" in label.lower():
            props["wall_thickness_mm"] = _parse_num(val)
        elif label.startswith("Wysokość"):
            props["height_mm"] = _parse_num(val)
        elif "Obrys" in label:
            props["obrys_mm"] = _parse_num(val)
    return props


def _parse_num(val: Any) -> float | None:
    if val is None:
        return None
    s = str(val).replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _within_tolerance(dxf_val: float | None, extral_val: float | None) -> str:
    if dxf_val is None or extral_val is None:
        return "unknown"
    delta = abs(dxf_val - extral_val)
    pct_ok = extral_val != 0 and delta / abs(extral_val) <= DIMENSION_TOLERANCE_PCT
    abs_ok = delta <= DIMENSION_TOLERANCE_MM
    return "ok" if (pct_ok or abs_ok) else "mismatch"


def validate_dimensions_against_extral(profile_id: str, dims_mapped: dict[str, float | None]) -> list[dict]:
    extral = _load_extral_props(profile_id)
    checks = []
    field_map = [
        ("ocd_mm", "ocd_mm"),
        ("wall_thickness_mm", "wall_thickness_mm"),
        ("height_mm", "height_mm"),
    ]
    with get_connection() as conn:
        for dxf_field, extral_field in field_map:
            dxf_v = dims_mapped.get(dxf_field)
            ex_v = extral.get(extral_field)
            if dxf_v is None and ex_v is None:
                continue
            status = _within_tolerance(dxf_v, ex_v)
            delta = abs(dxf_v - ex_v) if dxf_v is not None and ex_v is not None else None
            conn.execute(
                """
                INSERT OR REPLACE INTO dimension_validation
                (profile_id, field_name, dxf_value, extral_value, delta, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_id, dxf_field, dxf_v, ex_v, delta, status),
            )
            checks.append(
                {
                    "field": dxf_field,
                    "dxf_value": dxf_v,
                    "extral_value": ex_v,
                    "delta": delta,
                    "status": status,
                }
            )
    return checks


def get_profile_dimensions(profile_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profile_dimensions WHERE profile_id = ?", (profile_id,)
        ).fetchone()
        if row is None:
            return None
        validations = conn.execute(
            "SELECT field_name, dxf_value, extral_value, delta, status FROM dimension_validation WHERE profile_id = ?",
            (profile_id,),
        ).fetchall()
    return {
        "profile_id": profile_id,
        "dimensions": dict(row),
        "validation": [dict(v) for v in validations],
    }


def get_profile_geometry(profile_id: str) -> dict | None:
    path = PROCESSED_GEOMETRY / f"{profile_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
