"""Ephemeral DXF upload query."""

from __future__ import annotations

import json

from matrix_advisor.dxf.pipeline import process_dxf_bytes
from matrix_advisor.index.builder import get_index_stats, query_similar_by_mask
from matrix_advisor.models import SimilarityMethod
from matrix_advisor.query.service import get_matrices_for_profile, get_profile
from matrix_advisor.query.stage2 import apply_stage2
from matrix_advisor.query.upload_service import UPLOAD_QUERY_ID, _recommendation_note

MAX_DXF_BYTES = 10 * 1024 * 1024
ALLOWED_DXF_EXTENSIONS = {".dxf"}


def _reject_pdf(filename: str | None, content_type: str | None) -> None:
    if filename and filename.lower().endswith(".pdf"):
        raise ValueError("PDF is not supported — upload DXF instead")
    if content_type and "pdf" in content_type.lower():
        raise ValueError("PDF is not supported — upload DXF instead")


def _validate_dxf(data: bytes, filename: str | None, content_type: str | None) -> None:
    _reject_pdf(filename, content_type)
    if len(data) == 0:
        raise ValueError("Empty file")
    if len(data) > MAX_DXF_BYTES:
        raise ValueError(f"File too large (max {MAX_DXF_BYTES // (1024 * 1024)} MB)")
    ext = None
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext and ext not in ALLOWED_DXF_EXTENSIONS:
        if ext == ".pdf":
            raise ValueError("PDF is not supported — upload DXF instead")
        raise ValueError("Unsupported file type — use DXF")
    if content_type and "pdf" in content_type.lower():
        raise ValueError("PDF is not supported — upload DXF instead")


def query_by_dxf_bytes(
    data: bytes,
    *,
    method: SimilarityMethod = SimilarityMethod.EMBEDDING,
    top_k: int = 30,
    stage: int = 1,
    filters: dict | None = None,
    label: str | None = None,
    filename: str | None = None,
    content_type: str | None = None,
) -> dict:
    _validate_dxf(data, filename, content_type)

    try:
        processed = process_dxf_bytes(data, source_name=filename, persist=False)
    except ImportError as e:
        raise ValueError(str(e)) from e
    except ValueError as e:
        raise ValueError(f"Cannot process DXF: {e}") from e

    mask = processed.mask
    if "empty_contour" in processed.quality_flags:
        raise ValueError("Cannot process DXF: no contour detected")

    stage1_k = top_k if stage == 1 else max(top_k, 30)
    similar = query_similar_by_mask(mask, method, top_k=stage1_k)

    query_features = processed.features
    query_dims = processed.dimensions_mapped or {}

    candidates = []
    stage_meta = {"stage1_count": len(similar), "stage2_count": len(similar), "filters_applied": {}}

    if stage >= 2:
        stage2_rows, stage_meta = apply_stage2(
            similar,
            query_mask=mask,
            query_features=query_features,
            query_dims=query_dims,
            filters=filters,
            top_k=top_k,
        )
        for row in stage2_rows:
            pid = row["profile_id"]
            cand_profile = get_profile(pid)
            candidates.append(
                {
                    "profile_id": pid,
                    "display_name": cand_profile["display_name"] if cand_profile else None,
                    "rank": row["rank"],
                    "score": row["score"],
                    "shape_score": row.get("shape_score"),
                    "total_score": row["score"],
                    "score_breakdown": row.get("score_breakdown"),
                    "metadata_match": row.get("metadata_match"),
                    "dimensions": row.get("dimensions"),
                    "features": row.get("features"),
                    "matrices": get_matrices_for_profile(pid),
                }
            )
    else:
        for hit in similar:
            pid = hit.candidate_profile_id
            cand_profile = get_profile(pid)
            candidates.append(
                {
                    "profile_id": pid,
                    "display_name": cand_profile["display_name"] if cand_profile else None,
                    "rank": hit.rank,
                    "score": round(hit.score, 4),
                    "matrices": get_matrices_for_profile(pid),
                }
            )

    display = (label or "").strip() or "Nowe zamówienie"
    idx = get_index_stats()
    index_warning = None
    if idx["embedding_count"] < 100:
        index_warning = (
            f"UWAGA: indeks zawiera tylko {idx['embedding_count']} profili — "
            "uruchom matrix-advisor build-index na pełnych danych Extral."
        )

    result = {
        "query_profile_id": UPLOAD_QUERY_ID,
        "query_display_name": display,
        "method": method.value,
        "stage": stage,
        "query_matrices": [],
        "similar": candidates,
        "recommendation_note": _recommendation_note(candidates),
        "query_preview": processed.preview_data_url,
        "extracted_dimensions": query_dims,
        "quality_flags": processed.quality_flags,
        **stage_meta,
    }
    if index_warning:
        result["index_warning"] = index_warning
    return result


def parse_filters_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid filters JSON") from e
