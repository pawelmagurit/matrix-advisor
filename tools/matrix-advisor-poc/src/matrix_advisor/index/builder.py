import json
from pathlib import Path

import numpy as np
import pandas as pd

from matrix_advisor import config
from matrix_advisor.embeddings.encoder import (
    embed_with_rotations,
    embedding_backend_name,
)
from matrix_advisor.features.geometric import (
    extract_geometric_features,
    feature_vector,
    weight_vector,
    zscore_matrix,
)
from matrix_advisor.ingestion.import_csv import list_profile_ids
from matrix_advisor.models import SimilarityMethod, SimilarityResult


def _index_path(method: SimilarityMethod) -> Path:
    return config.INDEX_DIR / f"{method.value}.npz"


def _production_profile_ids(profile_ids: list[str] | None = None) -> list[str]:
    ids = list_profile_ids() if profile_ids is None else profile_ids
    if profile_ids is None:
        ids = [pid for pid in ids if not pid.startswith("E-SAMPLE-")]
    return ids


def build_geometric_index(profile_ids: list[str] | None = None) -> Path:
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    config.FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    ids = _production_profile_ids(profile_ids)
    rows = []
    vectors = []
    valid_ids = []

    for pid in ids:
        feat = extract_geometric_features(pid)
        if feat is None:
            continue
        rows.append(feat.model_dump())
        vectors.append(feature_vector(feat))
        valid_ids.append(pid)

    if not vectors:
        raise RuntimeError("No geometric features extracted — run normalize first")

    mat = np.vstack(vectors)
    zmat, mean, std = zscore_matrix(mat)
    weights = weight_vector()

    parquet_path = config.FEATURES_DIR / "geometric.parquet"
    pd.DataFrame(rows).to_parquet(parquet_path, index=False)

    path = _index_path(SimilarityMethod.GEOMETRIC)
    np.savez(
        path,
        profile_ids=np.array(valid_ids),
        vectors=zmat,
        mean=mean,
        std=std,
        weights=weights,
    )
    return path


def build_embedding_index(profile_ids: list[str] | None = None) -> Path:
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    ids = _production_profile_ids(profile_ids)
    valid_ids = []
    vectors = []

    backend = embedding_backend_name()
    for pid in ids:
        rots = embed_with_rotations(pid, backend="auto")
        if not rots:
            continue
        # Store primary (0°) vector; rotations used at query time via re-embed query
        valid_ids.append(pid)
        vectors.append(rots[0])

    if not vectors:
        raise RuntimeError("No embeddings extracted — run normalize first")

    mat = np.vstack(vectors)
    path = _index_path(SimilarityMethod.EMBEDDING)
    np.savez(
        path,
        profile_ids=np.array(valid_ids),
        vectors=mat,
        backend=backend,
    )
    return path


def update_index_rows(profile_ids: list[str]) -> dict[str, int]:
    """Recompute index vectors for specific profiles in place.

    Cheaper than a full rebuild when only a handful of masks changed (e.g. after
    repair_masks). Rows already present are overwritten; new ids are appended.
    """
    from matrix_advisor.embeddings.encoder import embed_with_rotations

    updated = {"embedding": 0, "geometric": 0}
    if not profile_ids:
        return updated

    # Embedding index (stores primary 0deg vector per profile).
    emb_path = _index_path(SimilarityMethod.EMBEDDING)
    if emb_path.exists():
        data = np.load(emb_path, allow_pickle=True)
        ids = list(data["profile_ids"])
        vectors = data["vectors"]
        backend = str(data.get("backend", ""))
        id_to_row = {pid: i for i, pid in enumerate(ids)}
        for pid in profile_ids:
            rots = embed_with_rotations(pid, backend="auto")
            if not rots:
                continue
            vec = rots[0]
            if pid in id_to_row:
                vectors[id_to_row[pid]] = vec
            else:
                ids.append(pid)
                vectors = np.vstack([vectors, vec[None, :]])
                id_to_row[pid] = len(ids) - 1
            updated["embedding"] += 1
        np.savez(emb_path, profile_ids=np.array(ids), vectors=vectors, backend=backend)

    # Geometric index (z-scored against stored mean/std).
    geo_path = _index_path(SimilarityMethod.GEOMETRIC)
    if geo_path.exists():
        data = np.load(geo_path, allow_pickle=True)
        ids = list(data["profile_ids"])
        vectors = data["vectors"]
        mean, std = data["mean"], data["std"]
        id_to_row = {pid: i for i, pid in enumerate(ids)}
        for pid in profile_ids:
            feat = extract_geometric_features(pid)
            if feat is None:
                continue
            zvec = (feature_vector(feat) - mean) / std
            if pid in id_to_row:
                vectors[id_to_row[pid]] = zvec
            else:
                ids.append(pid)
                vectors = np.vstack([vectors, zvec[None, :]])
                id_to_row[pid] = len(ids) - 1
            updated["geometric"] += 1
        np.savez(
            geo_path,
            profile_ids=np.array(ids),
            vectors=vectors,
            mean=mean,
            std=std,
            weights=data["weights"],
        )

    return updated


def _load_index(method: SimilarityMethod) -> dict:
    path = _index_path(method)
    if not path.exists():
        raise FileNotFoundError(f"Index not found: {path}. Run build-index first.")
    data = np.load(path, allow_pickle=True)
    return {
        "profile_ids": list(data["profile_ids"]),
        "vectors": data["vectors"],
        "mean": data.get("mean"),
        "std": data.get("std"),
        "weights": data.get("weights"),
        "backend": str(data.get("backend", "")),
    }


def get_index_stats() -> dict:
    """Return counts of profiles in on-disk similarity indexes."""
    stats: dict = {
        "embedding_count": 0,
        "geometric_count": 0,
        "embedding_backend": None,
    }
    emb_path = _index_path(SimilarityMethod.EMBEDDING)
    if emb_path.exists():
        data = np.load(emb_path, allow_pickle=True)
        stats["embedding_count"] = len(data["profile_ids"])
        backend = data.get("backend")
        if backend is not None and str(backend):
            stats["embedding_backend"] = str(backend)
    geo_path = _index_path(SimilarityMethod.GEOMETRIC)
    if geo_path.exists():
        data = np.load(geo_path, allow_pickle=True)
        stats["geometric_count"] = len(data["profile_ids"])
    return stats


def _geometric_distance(
    query_vec: np.ndarray,
    index: dict,
    exclude_id: str | None,
    top_k: int,
) -> list[SimilarityResult]:
    mean, std, weights = index["mean"], index["std"], index["weights"]
    q = (query_vec - mean) / std
    q = q * weights
    mat = index["vectors"] * weights

    dists = np.linalg.norm(mat - q, axis=1)
    ids = index["profile_ids"]
    ranked = sorted(
        [
            (ids[i], float(dists[i]))
            for i in range(len(ids))
            if not exclude_id or ids[i] != exclude_id
        ],
        key=lambda x: x[1],
    )[:top_k]

    query_label = exclude_id or "__upload__"
    results = []
    for rank, (cid, dist) in enumerate(ranked, start=1):
        score = 1.0 / (1.0 + dist)
        results.append(
            SimilarityResult(
                query_profile_id=query_label,
                candidate_profile_id=cid,
                rank=rank,
                score=score,
                method=SimilarityMethod.GEOMETRIC,
            )
        )
    return results


def _embedding_similarity_from_rotations(
    query_rots: list[np.ndarray],
    index: dict,
    exclude_id: str | None,
    top_k: int,
) -> list[SimilarityResult]:
    if not query_rots:
        return []

    mat = index["vectors"]
    ids = index["profile_ids"]
    query_label = exclude_id or "__upload__"

    best_scores: dict[str, float] = {}
    for qvec in query_rots:
        sims = mat @ qvec
        for i, cid in enumerate(ids):
            if exclude_id and cid == exclude_id:
                continue
            best_scores[cid] = max(best_scores.get(cid, -1.0), float(sims[i]))

    ranked = sorted(best_scores.items(), key=lambda x: -x[1])[:top_k]
    results = []
    for rank, (cid, score) in enumerate(ranked, start=1):
        results.append(
            SimilarityResult(
                query_profile_id=query_label,
                candidate_profile_id=cid,
                rank=rank,
                score=score,
                method=SimilarityMethod.EMBEDDING,
            )
        )
    return results


def _embedding_similarity(
    query_id: str,
    index: dict,
    top_k: int,
) -> list[SimilarityResult]:
    from matrix_advisor.embeddings.encoder import embed_with_rotations

    query_rots = embed_with_rotations(query_id, backend="auto")
    return _embedding_similarity_from_rotations(query_rots, index, query_id, top_k)


def query_similar_by_mask(
    mask: np.ndarray,
    method: SimilarityMethod,
    top_k: int = 10,
) -> list[SimilarityResult]:
    """Similarity search from an in-memory mask (upload / ad-hoc query)."""
    from matrix_advisor.embeddings.encoder import embed_with_rotations_from_mask

    index = _load_index(method)

    if method == SimilarityMethod.GEOMETRIC:
        feat = extract_geometric_features("__upload__", mask=mask)
        if feat is None:
            raise ValueError("Cannot extract geometric features from uploaded pictogram")
        qvec = feature_vector(feat)
        return _geometric_distance(qvec, index, None, top_k)

    query_rots = embed_with_rotations_from_mask(mask, backend="auto")
    return _embedding_similarity_from_rotations(query_rots, index, None, top_k)


def query_similar(
    profile_id: str,
    method: SimilarityMethod,
    top_k: int = 10,
) -> list[SimilarityResult]:
    index = _load_index(method)

    if method == SimilarityMethod.GEOMETRIC:
        feat = extract_geometric_features(profile_id)
        if feat is None:
            raise ValueError(f"No geometric features for profile {profile_id}")
        qvec = feature_vector(feat)
        return _geometric_distance(qvec, index, profile_id, top_k)

    return _embedding_similarity(profile_id, index, top_k)
