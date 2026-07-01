"""Build point samples from DXF entities for rasterization."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def _arc_points(cx: float, cy: float, r: float, a1_deg: float, a2_deg: float, n: int = 32) -> list[tuple[float, float]]:
    a1, a2 = math.radians(a1_deg), math.radians(a2_deg)
    if a2 < a1:
        a2 += 2 * math.pi
    ts = np.linspace(a1, a2, max(n, 4))
    return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in ts]


def entity_to_polylines(entity: Any) -> list[list[tuple[float, float]]]:
    """Convert a DXF entity to one or more polylines in mm."""
    dt = entity.dxftype()
    polylines: list[list[tuple[float, float]]] = []

    if dt == "LINE":
        p1 = (float(entity.dxf.start.x), float(entity.dxf.start.y))
        p2 = (float(entity.dxf.end.x), float(entity.dxf.end.y))
        polylines.append([p1, p2])
    elif dt == "ARC":
        c = entity.dxf.center
        polylines.append(
            _arc_points(float(c.x), float(c.y), float(entity.dxf.radius), float(entity.dxf.start_angle), float(entity.dxf.end_angle))
        )
    elif dt == "CIRCLE":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        polylines.append(_arc_points(float(c.x), float(c.y), r, 0, 360, n=64))
    elif dt == "LWPOLYLINE":
        pts = [(float(p[0]), float(p[1])) for p in entity.get_points("xy")]
        if pts:
            polylines.append(pts)
    elif dt == "SPLINE":
        try:
            from ezdxf import path as ezdxf_path

            p = ezdxf_path.make_path(entity)
            pts = [(float(v.x), float(v.y)) for v in p.flattening(0.1)]
            if pts:
                polylines.append(pts)
        except Exception:
            pass
    elif dt == "HATCH":
        try:
            from ezdxf import path as ezdxf_path

            for boundary in entity.paths:
                p = ezdxf_path.from_hatch_boundary_path(boundary)
                pts = [(float(v.x), float(v.y)) for v in p.flattening(0.05)]
                if pts:
                    polylines.append(pts)
        except Exception:
            pass

    return polylines


def entities_bbox(entities: list[Any]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for e in entities:
        for pl in entity_to_polylines(e):
            for x, y in pl:
                xs.append(x)
                ys.append(y)
    if not xs:
        return 0.0, 0.0, 1.0, 1.0
    return min(xs), min(ys), max(xs), max(ys)
