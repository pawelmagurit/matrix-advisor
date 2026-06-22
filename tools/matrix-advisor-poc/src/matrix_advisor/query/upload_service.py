"""Ad-hoc similarity query from uploaded pictogram (ephemeral, no DB writes)."""

from __future__ import annotations

import base64

import cv2
import numpy as np

from matrix_advisor.index.builder import query_similar_by_mask
from matrix_advisor.index.builder import get_index_stats
from matrix_advisor.models import SimilarityMethod
from matrix_advisor.normalization.pipeline import normalize_bytes
from matrix_advisor.query.service import get_matrices_for_profile, get_profile

UPLOAD_QUERY_ID = "__upload__"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/gif": ".gif",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}
ALLOWED_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg"}


def _mask_preview_data_url(mask: np.ndarray) -> str:
    """Preview in Extral pictogram style: bright contour on dark background."""
    preview = cv2.bitwise_not(mask)
    ok, buf = cv2.imencode(".png", preview)
    if not ok:
        raise ValueError("Failed to encode preview")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _recommendation_note(candidates: list[dict]) -> str:
    best_supplier = None
    best_effectiveness = None
    for c in candidates:
        for m in c["matrices"]:
            eff = m.get("effectiveness_pct")
            if eff is not None and (best_effectiveness is None or eff > best_effectiveness):
                best_effectiveness = eff
                best_supplier = m.get("supplier_name")

    if best_supplier and best_effectiveness is not None:
        return (
            f"Na podstawie {len(candidates)} podobnych profili historycznych: "
            f"najwyższa odnotowana skuteczność matrycy to {best_effectiveness:.1f}% "
            f"(dostawca: {best_supplier}). To podpowiedź — decyzja należy do technologa."
        )
    if candidates:
        return (
            f"Znaleziono {len(candidates)} podobnych profili. "
            "Brak pełnych danych produkcyjnych dla rekomendacji dostawcy."
        )
    return "Brak podobnych profili w indeksie."


def _validate_upload(
    data: bytes,
    content_type: str | None,
    filename: str | None,
) -> None:
    if len(data) == 0:
        raise ValueError("Empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)")

    ext = None
    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else None
    if content_type and content_type.split(";")[0].strip().lower() in ALLOWED_CONTENT_TYPES:
        return
    if ext and ext in ALLOWED_EXTENSIONS:
        return
    raise ValueError("Unsupported file type — use GIF, PNG, or JPEG")


def query_by_image_bytes(
    data: bytes,
    *,
    method: SimilarityMethod = SimilarityMethod.EMBEDDING,
    top_k: int = 8,
    label: str | None = None,
    content_type: str | None = None,
    filename: str | None = None,
) -> dict:
    """Run ephemeral similarity query; does not persist to database."""
    _validate_upload(data, content_type, filename)

    try:
        mask, quality_flags = normalize_bytes(data)
    except ValueError as e:
        raise ValueError(f"Cannot process pictogram: {e}") from e

    if "empty_contour" in quality_flags:
        raise ValueError("Cannot process pictogram: no contour detected")

    try:
        similar = query_similar_by_mask(mask, method, top_k=top_k)
    except FileNotFoundError as e:
        raise FileNotFoundError(str(e)) from e

    candidates = []
    for hit in similar:
        matrices = get_matrices_for_profile(hit.candidate_profile_id)
        cand_profile = get_profile(hit.candidate_profile_id)
        candidates.append(
            {
                "profile_id": hit.candidate_profile_id,
                "display_name": cand_profile["display_name"] if cand_profile else None,
                "rank": hit.rank,
                "score": round(hit.score, 4),
                "matrices": matrices,
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
        "query_matrices": [],
        "similar": candidates,
        "recommendation_note": _recommendation_note(candidates),
        "query_preview": _mask_preview_data_url(mask),
        "quality_flags": quality_flags,
    }
    if index_warning:
        result["index_warning"] = index_warning
    return result
