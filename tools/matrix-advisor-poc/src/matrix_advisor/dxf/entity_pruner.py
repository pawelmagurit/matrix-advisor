"""Remove non-profile drawing artifacts from selected DXF entities."""

from __future__ import annotations

from typing import Any

from matrix_advisor.dxf.contour_builder import entities_bbox


def _entity_bbox_wh(entity: Any) -> tuple[float, float]:
    xmin, ymin, xmax, ymax = entities_bbox([entity])
    return max(xmax - xmin, 0.0), max(ymax - ymin, 0.0)


def _y_overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float], gap: float = 1.0) -> bool:
    return not (a[3] + gap < b[1] or b[3] + gap < a[1])


def prune_drawing_artifacts(entities: list[Any]) -> list[Any]:
    """Drop frame/guide geometry that is not the profile cross-section."""
    if not entities:
        return entities

    pruned: list[Any] = []
    for entity in entities:
        if entity.dxftype() == "LWPOLYLINE":
            w, h = _entity_bbox_wh(entity)
            long_side = max(w, h)
            short_side = max(min(w, h), 1e-6)
            aspect = long_side / short_side
            if aspect >= 6.0 and long_side >= 25.0:
                continue
        if entity.dxftype() == "LINE":
            w, h = _entity_bbox_wh(entity)
            if min(w, h) < 0.45 and max(w, h) > 0.8:
                continue
        pruned.append(entity)

    return pruned if pruned else entities


def select_cross_section_entities(entities: list[Any]) -> tuple[list[Any], list[str]]:
    """Keep cross-section geometry; drop side elevations and drawing frames."""
    flags: list[str] = []
    pruned = prune_drawing_artifacts(entities)
    if len(pruned) < len(entities):
        flags.append("dropped_frame_polylines")

    arcs = [e for e in pruned if e.dxftype() == "ARC"]
    lwps = [e for e in pruned if e.dxftype() == "LWPOLYLINE"]

    if arcs and lwps:
        arc_bb = entities_bbox(arcs)
        lwp_bb = entities_bbox(lwps)
        if not _y_overlaps(arc_bb, lwp_bb):
            y0, y1 = arc_bb[1] - 1.0, arc_bb[3] + 1.0
            cross = [
                e
                for e in pruned
                if e.dxftype() != "LWPOLYLINE"
                and entities_bbox([e])[3] >= y0 - 0.5
                and entities_bbox([e])[1] <= y1 + 0.5
            ]
            if cross:
                flags.append("dropped_side_elevation_view")
                pruned = cross

    if any(e.dxftype() == "ARC" for e in pruned):
        compact: list[Any] = []
        dropped_elongated = False
        for entity in pruned:
            if entity.dxftype() == "LWPOLYLINE":
                w, h = _entity_bbox_wh(entity)
                aspect = max(w, h) / max(min(w, h), 1e-6)
                if aspect >= 2.5:
                    dropped_elongated = True
                    continue
            compact.append(entity)
        if dropped_elongated and compact:
            flags.append("dropped_elongated_polylines")
            pruned = compact

    return pruned, flags
