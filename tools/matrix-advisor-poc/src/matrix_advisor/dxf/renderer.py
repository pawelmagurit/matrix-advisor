"""Rasterize DXF profile geometry to canonical masks."""

from __future__ import annotations

import base64
import math

import cv2
import numpy as np

from matrix_advisor.dxf.contour_builder import entities_bbox, entity_to_polylines
from matrix_advisor.normalization.pipeline import normalize_dxf_raster


def _group_concentric_circles(
    circles: list[tuple[float, float, float]],
    center_tol_mm: float = 0.5,
) -> list[list[tuple[float, float, float]]]:
    groups: list[list[tuple[float, float, float]]] = []
    used = [False] * len(circles)
    for i, (r, x, y) in enumerate(circles):
        if used[i]:
            continue
        group = [(r, x, y)]
        used[i] = True
        for j, (r2, x2, y2) in enumerate(circles):
            if used[j]:
                continue
            if math.hypot(x - x2, y - y2) <= center_tol_mm:
                group.append((r2, x2, y2))
                used[j] = True
        groups.append(group)
    return groups


def _draw_circle_groups(
    img: np.ndarray,
    groups: list[list[tuple[float, float, float]]],
    to_px,
    mm_per_px: float,
) -> None:
    for group in groups:
        group.sort(key=lambda item: -item[0])
        cx, cy = group[0][1], group[0][2]
        px, py = to_px(cx, cy)
        for idx, (radius, _x, _y) in enumerate(group):
            r_px = max(2, int(radius / max(mm_per_px, 1e-6)))
            color = 255 if idx % 2 == 0 else 0
            cv2.circle(img, (px, py), r_px, color, thickness=-1)


def rasterize_entities(entities: list, render_size: int = 1024) -> np.ndarray:
    """Draw DXF entities to a grayscale image (white shape on black)."""
    if not entities:
        raise ValueError("No entities to rasterize")

    xmin, ymin, xmax, ymax = entities_bbox(entities)
    w = xmax - xmin
    h = ymax - ymin
    if w < 1e-6 or h < 1e-6:
        raise ValueError("Degenerate geometry bbox")

    pad = 0.05
    side = max(w, h) * (1 + 2 * pad)
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    mm_per_px = side / max(render_size - 1, 1)

    img = np.zeros((render_size, render_size), dtype=np.uint8)

    def to_px(x: float, y: float) -> tuple[int, int]:
        nx = (x - cx) / side + 0.5
        ny = (y - cy) / side + 0.5
        px = int(nx * (render_size - 1))
        py = int((1 - ny) * (render_size - 1))
        return px, py

    circles = [
        (float(e.dxf.radius), float(e.dxf.center.x), float(e.dxf.center.y))
        for e in entities
        if e.dxftype() == "CIRCLE"
    ]
    circle_groups = _group_concentric_circles(circles)
    if circle_groups:
        _draw_circle_groups(img, circle_groups, to_px, mm_per_px)

    non_circles = [e for e in entities if e.dxftype() != "CIRCLE"]
    for entity in non_circles:
        is_hatch = entity.dxftype() == "HATCH"
        closed = is_hatch or bool(getattr(entity, "closed", False))
        for pl in entity_to_polylines(entity):
            if len(pl) < 2:
                continue
            pts = np.array([to_px(x, y) for x, y in pl], dtype=np.int32)
            if is_hatch:
                cv2.polylines(img, [pts], True, 255, thickness=2)
            elif closed and len(pts) >= 3:
                cv2.fillPoly(img, [pts], 255)
                cv2.polylines(img, [pts], True, 255, 1)
            else:
                cv2.polylines(img, [pts], False, 255, thickness=2)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=2)


def contour_to_mask(entities: list) -> tuple[np.ndarray, list[str]]:
    """DXF entities → 256×256 normalized binary mask."""
    flags: list[str] = []
    try:
        raster = rasterize_entities(entities)
    except ValueError as e:
        raise ValueError(f"Cannot rasterize DXF geometry: {e}") from e

    mask, norm_flags = normalize_dxf_raster(raster)
    flags.extend(norm_flags)
    return mask, flags


def mask_to_preview_data_url(mask: np.ndarray) -> str:
    """Extral pictogram style preview."""
    preview = cv2.bitwise_not(mask)
    ok, buf = cv2.imencode(".png", preview)
    if not ok:
        raise ValueError("Failed to encode preview")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def bbox_mm_from_entities(entities: list) -> dict[str, float]:
    xmin, ymin, xmax, ymax = entities_bbox(entities)
    return {
        "width_mm": round(xmax - xmin, 3),
        "height_mm": round(ymax - ymin, 3),
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
    }
