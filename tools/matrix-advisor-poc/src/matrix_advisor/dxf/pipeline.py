"""Orchestrate DXF → geometry JSON, mask, features, DB."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from matrix_advisor.config import (
    PROCESSED_FEATURES,
    PROCESSED_GEOMETRY,
    PROCESSED_MASKS,
    RAW_DXF,
    ensure_data_dirs,
)
from matrix_advisor.db import get_connection
from matrix_advisor.dxf.dimensions import extract_dimension_values, map_dimensions
from matrix_advisor.dxf.entity_pruner import select_cross_section_entities
from matrix_advisor.dxf.parser import PARSER_VERSION, file_checksum, parse_dxf
from matrix_advisor.dxf.profile_selector import ProfileSelection, select_profile_entities
from matrix_advisor.dxf.renderer import bbox_mm_from_entities, contour_to_mask, mask_to_preview_data_url
from matrix_advisor.features.dimensional import extract_dimensional_features
from matrix_advisor.features.geometric import extract_geometric_features
from matrix_advisor.query.dimensions_service import validate_dimensions_against_extral


def _mask_content_aspect(mask: np.ndarray) -> float:
    ys, xs = np.where(mask > 127)
    if len(xs) == 0:
        return 1.0
    w = int(xs.max() - xs.min() + 1)
    h = int(ys.max() - ys.min() + 1)
    return max(w, h) / max(min(w, h), 1)


def _dims_aspect(dims: dict[str, float | None]) -> float | None:
    width = dims.get("width_mm")
    height = dims.get("height_mm")
    if not width or not height:
        return None
    return max(width, height) / min(width, height)


def _dxf_mask_looks_wrong(mask: np.ndarray, dims: dict[str, float | None]) -> bool:
    mask_aspect = _mask_content_aspect(mask)
    dim_aspect = _dims_aspect(dims)
    width = dims.get("width_mm") or 0
    ocd = dims.get("ocd_mm") or 0

    if width > 0 and ocd > 0 and ocd / width > 2.0 and mask_aspect > 2.0:
        return False

    if dim_aspect:
        ratio = mask_aspect / dim_aspect
        if 1 / 1.8 <= ratio <= 1.8:
            return False

    if mask_aspect > 2.5 and (dim_aspect is None or dim_aspect < 2.0):
        return True
    if dim_aspect and mask_aspect / dim_aspect > 1.8:
        return True
    return False


def _mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    a_bin = (a > 127).astype(np.uint8)
    b_bin = (b > 127).astype(np.uint8)
    union = np.logical_or(a_bin, b_bin).sum()
    if union == 0:
        return 0.0
    return float(np.logical_and(a_bin, b_bin).sum() / union)


def _load_extral_pictogram_mask(profile_id: str) -> np.ndarray | None:
    """Normalize Extral GIF pictogram to canonical mask."""
    from matrix_advisor.normalization.pipeline import load_mask_from_pictogram

    return load_mask_from_pictogram(profile_id)


def _canonical_index_mask(profile_id: str, dxf_mask: np.ndarray) -> np.ndarray:
    """Pick the mask stored for indexing.

    The similarity index and the DXF-upload query both fall back to the Extral
    pictogram whenever the DXF cross-section is incomplete. Persisting a
    degenerate DXF-derived mask (e.g. a solid hatch blob) here would poison the
    index so the profile can no longer match its own pictogram. Prefer the
    pictogram mask whenever it disagrees with the DXF mask.
    """
    gif_mask = _load_extral_pictogram_mask(profile_id)
    if gif_mask is None:
        return dxf_mask
    if _mask_iou(dxf_mask, gif_mask) < 0.6:
        return gif_mask
    return dxf_mask


def _try_extral_pictogram_fallback(profile_id: str, mask: np.ndarray, dims: dict[str, float | None]) -> tuple[np.ndarray, list[str]]:
    flags: list[str] = []
    gif_mask = _load_extral_pictogram_mask(profile_id)
    if gif_mask is None:
        if _dxf_mask_looks_wrong(mask, dims):
            flags.append("incomplete_dxf_cross_section")
        return mask, flags

    if _dxf_mask_looks_wrong(mask, dims) or _mask_iou(mask, gif_mask) < 0.45:
        flags.append("used_extral_pictogram_fallback")
        return gif_mask, flags

    return mask, flags


@dataclass
class DxfProcessResult:
    profile_id: str
    mask: np.ndarray
    preview_data_url: str
    geometry: dict[str, Any]
    features: dict[str, Any]
    dimensions_mapped: dict[str, float | None]
    quality_flags: list[str]
    selection: ProfileSelection


def _profile_id_from_path(path: Path) -> str:
    return path.stem.upper()


def process_dxf_bytes(
    data: bytes,
    *,
    profile_id: str | None = None,
    source_name: str | None = None,
    persist: bool = False,
    use_pictogram_fallback: bool = True,
) -> DxfProcessResult:
    """Parse DXF bytes → mask + metadata. Optionally persist to data/.

    ``use_pictogram_fallback`` swaps a bad DXF-derived mask for the profile's
    Extral pictogram when one exists. In production the uploaded profile has no
    pictogram, so evaluation of raw DXF→mask quality must disable it.
    """
    ensure_data_dirs()
    dxf_doc = parse_dxf(data=data)
    doc = dxf_doc.doc
    pid = profile_id or (Path(source_name).stem.upper() if source_name else "UPLOAD")

    selection = select_profile_entities(doc)
    quality = list(selection.quality_flags)
    if not selection.entities:
        raise ValueError("Cannot process DXF: no profile geometry found")

    draw_entities, prune_flags = select_cross_section_entities(selection.entities)
    quality.extend(prune_flags)

    mask, mask_flags = contour_to_mask(draw_entities)
    quality.extend(mask_flags)

    dim_values = extract_dimension_values(doc)
    dims_mapped = map_dimensions(dim_values)

    if use_pictogram_fallback:
        mask, fallback_flags = _try_extral_pictogram_fallback(pid, mask, dims_mapped)
        quality.extend(fallback_flags)
    elif _dxf_mask_looks_wrong(mask, dims_mapped):
        quality.append("incomplete_dxf_cross_section")
    bbox = bbox_mm_from_entities(draw_entities)

    geom_feat = extract_geometric_features(pid, mask=mask)
    if geom_feat is None:
        raise ValueError("Cannot extract features from DXF-derived mask")

    dim_feat = extract_dimensional_features(pid, dims_mapped, bbox)
    preview = mask_to_preview_data_url(mask)

    geometry = {
        "profile_id": pid,
        "source_dxf": source_name,
        "parser_version": PARSER_VERSION,
        "units": "mm",
        "dxf_version": dxf_doc.dxf_version,
        "selection": {
            "strategy": selection.strategy,
            "layer": selection.layer,
            "block": selection.block,
        },
        "bbox_mm": bbox,
        "dimensions_extracted": dim_values,
        "dimensions_mapped": dims_mapped,
        "quality_flags": quality,
    }

    features = {
        **geom_feat.model_dump(),
        **dim_feat,
        "cavity_count": geom_feat.hole_count,
    }

    if persist:
        _persist_dxf(pid, data, geometry, features, mask)

    return DxfProcessResult(
        profile_id=pid,
        mask=mask,
        preview_data_url=preview,
        geometry=geometry,
        features=features,
        dimensions_mapped=dims_mapped,
        quality_flags=quality,
        selection=selection,
    )


def process_dxf_file(path: Path, *, persist: bool = True) -> DxfProcessResult:
    data = path.read_bytes()
    pid = _profile_id_from_path(path)
    return process_dxf_bytes(data, profile_id=pid, source_name=path.name, persist=persist)


def _persist_dxf(
    profile_id: str,
    data: bytes,
    geometry: dict,
    features: dict,
    mask: np.ndarray,
) -> None:
    checksum = file_checksum(data)
    dxf_path = RAW_DXF / f"{profile_id}.dxf"
    dxf_path.write_bytes(data)

    geom_path = PROCESSED_GEOMETRY / f"{profile_id}.json"
    geom_path.write_text(json.dumps(geometry, indent=2, ensure_ascii=False), encoding="utf-8")

    feat_path = PROCESSED_FEATURES / f"{profile_id}.json"
    feat_path.write_text(json.dumps(features, indent=2, ensure_ascii=False), encoding="utf-8")

    PROCESSED_MASKS.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(PROCESSED_MASKS / f"{profile_id}.png"), _canonical_index_mask(profile_id, mask))

    dims = geometry.get("dimensions_mapped") or {}
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO dxf_assets
            (profile_id, storage_path, checksum, parser_version, status, processed_at)
            VALUES (?, ?, ?, ?, 'ready', datetime('now'))
            """,
            (profile_id, str(dxf_path), checksum, PARSER_VERSION),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO profile_dimensions
            (profile_id, width_mm, height_mm, wall_thickness_mm, ocd_mm, area_mm2, source)
            VALUES (?, ?, ?, ?, ?, ?, 'dxf')
            """,
            (
                profile_id,
                dims.get("width_mm"),
                dims.get("height_mm"),
                dims.get("wall_thickness_mm"),
                dims.get("ocd_mm"),
                features.get("area_mm2"),
            ),
        )
        conn.execute(
            "UPDATE profiles SET processing_status = 'dxf_ready' WHERE profile_id = ?",
            (profile_id,),
        )

    validate_dimensions_against_extral(profile_id, dims)


def import_dxf_directory(directory: Path) -> list[dict]:
    """Process all DXF files in a directory; return per-file report."""
    reports = []
    for path in sorted(directory.glob("*.dxf")):
        entry = {"file": path.name, "profile_id": path.stem.upper(), "status": "ok"}
        try:
            result = process_dxf_file(path, persist=True)
            entry["strategy"] = result.selection.strategy
            entry["quality_flags"] = result.quality_flags
            entry["dimensions"] = result.dimensions_mapped
        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
        reports.append(entry)
    return reports
