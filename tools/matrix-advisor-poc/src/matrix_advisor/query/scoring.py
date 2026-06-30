"""Multi-criteria similarity scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from matrix_advisor.config import SCORING_WEIGHTS
from matrix_advisor.features.geometric import (
    extract_geometric_features,
    inner_detail_score,
    outer_contour_score,
)
from matrix_advisor.query.dimensions_service import get_profile_dimensions


@dataclass
class ScoringConfig:
    shape_embedding: float = SCORING_WEIGHTS["shape_embedding"]
    outer_contour: float = SCORING_WEIGHTS["outer_contour"]
    inner_detail: float = SCORING_WEIGHTS["inner_detail"]
    dimension: float = SCORING_WEIGHTS["dimension"]
    metadata: float = SCORING_WEIGHTS["metadata"]


def _dimension_score(query_dims: dict, cand_dims: dict | None) -> float | None:
    if not cand_dims:
        return None
    fields = ["width_mm", "height_mm", "wall_thickness_mm", "ocd_mm"]
    scores = []
    for f in fields:
        qv, cv = query_dims.get(f), cand_dims.get(f)
        if qv is None or cv is None:
            continue
        denom = max(abs(qv), abs(cv), 1.0)
        scores.append(max(0.0, 1.0 - abs(float(qv) - float(cv)) / denom))
    if not scores:
        return None
    return float(np.mean(scores))


def _metadata_score(validation: list[dict] | None) -> float | None:
    if not validation:
        return None
    ok = sum(1 for v in validation if v.get("status") == "ok")
    if ok == 0:
        return 0.0
    return ok / len(validation)


def compute_score_breakdown(
    query_mask: np.ndarray,
    query_features: dict,
    query_dims: dict,
    candidate_id: str,
    shape_score: float,
    config: ScoringConfig | None = None,
) -> dict[str, Any]:
    cfg = config or ScoringConfig()
    cand_feat = extract_geometric_features(candidate_id)
    breakdown: dict[str, float | None] = {
        "shape_embedding": round(shape_score, 4),
        "outer_contour": None,
        "inner_detail": None,
        "dimension": None,
        "metadata": None,
    }

    if cand_feat:
        cand_mask = None
        from matrix_advisor.normalization.pipeline import load_mask

        cand_mask = load_mask(candidate_id)
        if cand_mask is not None:
            breakdown["outer_contour"] = round(outer_contour_score(query_mask, cand_mask), 4)
            breakdown["inner_detail"] = round(
                inner_detail_score(query_features, cand_feat.model_dump(), query_mask, cand_mask),
                4,
            )

    pd = get_profile_dimensions(candidate_id)
    cand_dims = None
    if pd:
        cand_dims = {
            k: pd["dimensions"][k]
            for k in ("width_mm", "height_mm", "wall_thickness_mm", "ocd_mm")
            if pd["dimensions"].get(k) is not None
        }
        breakdown["dimension"] = (
            round(v, 4) if (v := _dimension_score(query_dims, cand_dims)) is not None else None
        )
        breakdown["metadata"] = (
            round(v, 4) if (v := _metadata_score(pd.get("validation"))) is not None else None
        )

    weights = {
        "shape_embedding": cfg.shape_embedding,
        "outer_contour": cfg.outer_contour,
        "inner_detail": cfg.inner_detail,
        "dimension": cfg.dimension,
        "metadata": cfg.metadata,
    }
    total_w = 0.0
    total = 0.0
    for key, w in weights.items():
        val = breakdown.get(key)
        if val is not None:
            total += w * val
            total_w += w
    total_score = total / total_w if total_w > 0 else shape_score

    metadata_match = {}
    if pd and pd.get("validation"):
        for v in pd["validation"]:
            metadata_match[v["field_name"]] = v["status"]

    return {
        "total_score": round(total_score, 4),
        "score_breakdown": breakdown,
        "metadata_match": metadata_match or None,
        "dimensions": cand_dims,
        "features": {
            "hole_count": cand_feat.hole_count if cand_feat else None,
            "cavity_count": cand_feat.hole_count if cand_feat else None,
        },
    }
