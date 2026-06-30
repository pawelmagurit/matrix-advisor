"""Unified similarity search (profile id or ephemeral mask context)."""

from __future__ import annotations

from matrix_advisor.dxf.pipeline import process_dxf_bytes
from matrix_advisor.index.builder import query_similar, query_similar_by_mask
from matrix_advisor.models import SimilarityMethod
from matrix_advisor.normalization.pipeline import load_mask
from matrix_advisor.query.by_dxf_service import parse_filters_json
from matrix_advisor.query.service import get_matrices_for_profile, get_profile
from matrix_advisor.query.stage2 import apply_stage2


def search_similar(
    *,
    profile_id: str | None = None,
    dxf_bytes: bytes | None = None,
    method: SimilarityMethod = SimilarityMethod.EMBEDDING,
    top_k: int = 30,
    stage: int = 1,
    filters: dict | None = None,
) -> dict:
    mask = None
    if profile_id:
        hits = query_similar(profile_id, method, top_k=max(top_k, 30) if stage >= 2 else top_k)
        mask = load_mask(profile_id)
        query_features = {}
        query_dims = {}
        if mask is not None:
            from matrix_advisor.features.geometric import extract_geometric_features
            from matrix_advisor.query.dimensions_service import get_profile_dimensions

            gf = extract_geometric_features(profile_id, mask)
            if gf:
                query_features = gf.model_dump()
            pd = get_profile_dimensions(profile_id)
            if pd:
                query_dims = {
                    k: pd["dimensions"].get(k)
                    for k in ("width_mm", "height_mm", "wall_thickness_mm", "ocd_mm")
                }
        qid = profile_id
    elif dxf_bytes:
        processed = process_dxf_bytes(dxf_bytes, persist=False)
        mask = processed.mask
        hits = query_similar_by_mask(mask, method, top_k=max(top_k, 30) if stage >= 2 else top_k)
        query_features = processed.features
        query_dims = processed.dimensions_mapped or {}
        qid = "__upload__"
    else:
        raise ValueError("profile_id or dxf_bytes required")

    if mask is None:
        raise ValueError("No mask available for query")

    if stage >= 2:
        rows, meta = apply_stage2(
            hits,
            query_mask=mask,
            query_features=query_features,
            query_dims=query_dims,
            filters=filters,
            top_k=top_k,
        )
        similar = []
        for row in rows:
            pid = row["profile_id"]
            p = get_profile(pid)
            similar.append(
                {
                    "profile_id": pid,
                    "display_name": p["display_name"] if p else None,
                    "rank": row["rank"],
                    "score": row["score"],
                    "score_breakdown": row.get("score_breakdown"),
                    "matrices": get_matrices_for_profile(pid),
                }
            )
        return {"query_profile_id": qid, "stage": stage, "similar": similar, **meta}

    similar = []
    for hit in hits:
        pid = hit.candidate_profile_id
        p = get_profile(pid)
        similar.append(
            {
                "profile_id": pid,
                "display_name": p["display_name"] if p else None,
                "rank": hit.rank,
                "score": round(hit.score, 4),
                "matrices": get_matrices_for_profile(pid),
            }
        )
    return {"query_profile_id": qid, "stage": 1, "similar": similar, "stage1_count": len(similar)}
