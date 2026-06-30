"""Stage 2 filtering and reranking."""

from __future__ import annotations

from typing import Any

from matrix_advisor.index.builder import SimilarityResult
from matrix_advisor.query.scoring import compute_score_breakdown


def _passes_filters(features: dict | None, dims: dict | None, filters: dict) -> bool:
    if not filters:
        return True

    def in_range(val: float | None, spec: dict | None) -> bool:
        if spec is None or val is None:
            return True
        if "min" in spec and val < spec["min"]:
            return False
        if "max" in spec and val > spec["max"]:
            return False
        return True

    if dims:
        for key in ("width_mm", "height_mm", "wall_thickness_mm", "ocd_mm"):
            if key in filters and not in_range(dims.get(key), filters[key]):
                return False

    if features:
        for key in ("hole_count", "cavity_count"):
            if key in filters and not in_range(features.get(key), filters[key]):
                return False

    return True


def apply_stage2(
    stage1_hits: list[SimilarityResult],
    *,
    query_mask,
    query_features: dict,
    query_dims: dict,
    filters: dict | None = None,
    top_k: int = 20,
) -> tuple[list[dict], dict]:
    """Rerank Stage 1 candidates with multi-criteria scoring and optional filters."""
    filters = filters or {}
    enriched: list[dict] = []

    for hit in stage1_hits:
        scored = compute_score_breakdown(
            query_mask,
            query_features,
            query_dims,
            hit.candidate_profile_id,
            hit.score,
        )
        if not _passes_filters(scored.get("features"), scored.get("dimensions"), filters):
            continue
        enriched.append(
            {
                "profile_id": hit.candidate_profile_id,
                "rank": 0,
                "score": scored["total_score"],
                "shape_score": hit.score,
                **scored,
            }
        )

    enriched.sort(key=lambda x: -x["score"])
    enriched = enriched[:top_k]
    for i, row in enumerate(enriched, start=1):
        row["rank"] = i

    meta = {
        "stage1_count": len(stage1_hits),
        "stage2_count": len(enriched),
        "filters_applied": filters,
    }
    return enriched, meta
