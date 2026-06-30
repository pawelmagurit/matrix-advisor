"""Select profile cross-section geometry from Extral-style DXF drawings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

GEO_TYPES = frozenset(
    {"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "SPLINE", "ELLIPSE", "HATCH"}
)

# Layers used for dimensions, labels, scaling — not profile outline.
_ANNOTATION_LAYER_MARKERS = (
    "wymiar",
    "wymiary",
    "tekst",
    "teksty",
    "skalow",
    "tabel",
    "frame",
    "ramka",
)

_PROFILE_LAYER_MARKERS = (
    "01.profil",
    "profil",
    "rysunek_glowny",
    "glowny",
    "widok rzeczywisty",
)


@dataclass
class ProfileSelection:
    strategy: str
    layer: str | None
    block: str | None
    entities: list[Any]
    quality_flags: list[str]


def _layer_match(layer: str, pattern: str) -> bool:
    return pattern.lower() in layer.lower()


def _is_annotation_layer(layer: str) -> bool:
    low = layer.lower()
    return any(m in low for m in _ANNOTATION_LAYER_MARKERS)


def _is_profile_layer(layer: str) -> bool:
    low = layer.lower().replace(" ", "_").replace(".", "")
    return any(m.replace(" ", "_").replace(".", "") in low for m in _PROFILE_LAYER_MARKERS)


def _entities_on_layer(entities: Iterable[Any], pattern: str) -> list[Any]:
    out = []
    for e in entities:
        if not hasattr(e, "dxf"):
            continue
        layer = getattr(e.dxf, "layer", "")
        if _layer_match(layer, pattern) and e.dxftype() in GEO_TYPES:
            out.append(e)
    return out


def _filter_profile_entities(entities: list[Any]) -> list[Any]:
    """Drop dimension/text geometry when profile layers are present."""
    profile = [e for e in entities if _is_profile_layer(getattr(e.dxf, "layer", ""))]
    if profile:
        return profile
    non_ann = [e for e in entities if not _is_annotation_layer(getattr(e.dxf, "layer", ""))]
    return non_ann


def _block_geo_entities(doc: Any, block_name: str) -> list[Any]:
    try:
        block = doc.blocks.get(block_name)
    except KeyError:
        return []
    return [e for e in block if e.dxftype() in GEO_TYPES]


def _bbox_area(entities: list[Any]) -> float:
    from ezdxf import bbox as ezbbox

    if not entities:
        return 0.0
    try:
        ext = ezbbox.extents(entities)
        if ext.has_data:
            w = ext.extmax.x - ext.extmin.x
            h = ext.extmax.y - ext.extmin.y
            return w * h
    except Exception:
        pass
    return 0.0


def _hatch_widok_entities(msp: list[Any]) -> list[Any]:
    """Filled profile cross-section on Extral 'widok rzeczywisty' layer."""
    return [
        e
        for e in msp
        if e.dxftype() == "HATCH"
        and _layer_match(getattr(e.dxf, "layer", ""), "Widok rzeczywisty")
        and not _is_annotation_layer(getattr(e.dxf, "layer", ""))
    ]


def select_profile_entities(doc: Any) -> ProfileSelection:
    """Pick entities representing the profile cross-section."""
    msp = list(doc.modelspace())
    quality: list[str] = []

    # 1. Layer 01.Profil in modelspace
    ents = _entities_on_layer(msp, "01.Profil")
    if ents:
        return ProfileSelection("layer", "01.Profil", None, ents, quality)

    # 2. RYSUNEK_GLOWNY / GLOWNY in modelspace
    for pattern in ("RYSUNEK_GLOWNY", "GLOWNY"):
        ents = _entities_on_layer(msp, pattern)
        if ents:
            return ProfileSelection("layer", pattern, None, ents, quality)

    # 3. HATCH on widok rzeczywisty (common for block-based Extral drawings)
    ents = _hatch_widok_entities(msp)
    if ents:
        return ProfileSelection("hatch_widok", "07.Widok rzeczywisty", None, ents, quality)

    # 4. EAL_* blocks — profile geometry only (skip pure dimension blocks)
    eal_blocks = [n for n in doc.blocks.block_names() if re.search(r"EAL_WY[PK]", n, re.I)]
    best_block = None
    best_area = 0.0
    best_ents: list[Any] = []
    for name in eal_blocks:
        if name.startswith("*"):
            continue
        block_ents = _filter_profile_entities(_block_geo_entities(doc, name))
        if not block_ents:
            continue
        area = _bbox_area(block_ents)
        if area > best_area:
            best_area = area
            best_block = name
            best_ents = block_ents
    if best_ents:
        return ProfileSelection("block", None, best_block, best_ents, quality)

    # 5. Fallback: line/arc geometry on widok rzeczywisty
    ents = _entities_on_layer(msp, "07.Widok rzeczywisty")
    if ents:
        quality.append("fallback_widok_rzeczywisty")
        return ProfileSelection("layer_fallback", "07.Widok rzeczywisty", None, ents, quality)

    quality.append("ambiguous_profile_selection")
    return ProfileSelection("none", None, None, [], quality)
