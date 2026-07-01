"""Pick a representative (non-random) set of profiles whose DXFs to request.

We already hold ~10k pictograms + shape embeddings. To learn the DXF→pictogram
convention across *all* drawing styles we want a sample that maximises coverage
of the shape space and of metadata facets (series, contractor, complexity,
size) — not a random draw, which over-samples the common template and misses
rare conventions.

Core method: Farthest Point Sampling (k-center greedy) on the L2-normalised
shape embeddings. It repeatedly adds the profile farthest from everything
already chosen, so the sample spans the manifold including edge cases. We then
top up any metadata stratum that ended up unrepresented.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from matrix_advisor.config import FEATURES_DIR, RAW_DXF
from matrix_advisor.db import get_connection
from matrix_advisor.index.builder import _index_path
from matrix_advisor.models import SimilarityMethod


def _load_embeddings() -> tuple[list[str], np.ndarray]:
    path = _index_path(SimilarityMethod.EMBEDDING)
    if not path.exists():
        raise FileNotFoundError(f"Embedding index not found: {path}. Run build-index first.")
    data = np.load(path, allow_pickle=True)
    ids = [str(x) for x in data["profile_ids"]]
    vecs = np.asarray(data["vectors"], dtype=np.float64)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms < 1e-12] = 1.0
    return ids, vecs / norms


def _load_metadata(ids: list[str]) -> dict[str, dict]:
    meta: dict[str, dict] = {pid: {} for pid in ids}
    with get_connection() as conn:
        for row in conn.execute(
            "SELECT profile_id, owner_contractor, masa_g_m, wall_thickness_mm FROM profiles"
        ).fetchall():
            pid = row["profile_id"]
            if pid in meta:
                meta[pid] = {
                    "owner_contractor": row["owner_contractor"],
                    "masa_g_m": row["masa_g_m"],
                    "wall_thickness_mm": row["wall_thickness_mm"],
                }
    return meta


def _load_geometric_features(ids: set[str]) -> dict[str, dict]:
    path = FEATURES_DIR / "geometric.parquet"
    if not path.exists():
        return {}
    import pandas as pd

    df = pd.read_parquet(path)
    out: dict[str, dict] = {}
    for rec in df.to_dict("records"):
        pid = rec.get("profile_id")
        if pid in ids:
            out[pid] = {
                "hole_count": rec.get("hole_count"),
                "aspect_ratio": rec.get("aspect_ratio"),
                "area_norm": rec.get("area_norm"),
                "solidity": rec.get("solidity"),
            }
    return out


def _series(pid: str) -> str:
    return pid[0] if pid else "?"


def _hole_bucket(n) -> str:
    if n is None:
        return "?"
    n = int(n)
    if n == 0:
        return "solid"
    if n <= 2:
        return "1-2"
    if n <= 5:
        return "3-5"
    return "6+"


def _size_bucket(area_norm) -> str:
    if area_norm is None:
        return "?"
    a = float(area_norm)
    if a < 0.15:
        return "small"
    if a < 0.35:
        return "medium"
    return "large"


def _farthest_point_sampling(X: np.ndarray, k: int, seed_idx: int) -> list[int]:
    n = len(X)
    k = min(k, n)
    selected = [seed_idx]
    dist = 1.0 - X @ X[seed_idx]
    dist[seed_idx] = -1.0
    for _ in range(k - 1):
        i = int(np.argmax(dist))
        if dist[i] < 0:
            break
        selected.append(i)
        dist = np.minimum(dist, 1.0 - X @ X[i])
        dist[i] = -1.0
    return selected


@dataclass
class SampleResult:
    profile_ids: list[str]
    reasons: dict[str, str]
    coverage: dict


# Facets whose every value we guarantee to cover. Contractor is intentionally
# excluded: it is near-unique per profile (~1k values), so forcing one of each
# would blow the sample up to ~1k files. It is reported for transparency only.
_COVERAGE_FACETS = ("series", "holes", "size")


def select_sample(
    n: int = 400,
    *,
    exclude_existing_dxf: bool = True,
    min_per_stratum: int = 1,
) -> SampleResult:
    ids, X = _load_embeddings()

    keep_mask = np.ones(len(ids), dtype=bool)
    have = {p.stem.upper() for p in RAW_DXF.glob("*.dxf")} if exclude_existing_dxf else set()
    for i, pid in enumerate(ids):
        if "SAMPLE" in pid.upper():  # synthetic profiles, not real client DXFs
            keep_mask[i] = False
        elif pid in have:
            keep_mask[i] = False
    idx_keep = np.where(keep_mask)[0]
    ids_k = [ids[i] for i in idx_keep]
    X_k = X[idx_keep]

    meta = _load_metadata(ids_k)
    geom = _load_geometric_features(set(ids_k))

    def strata(pid: str) -> dict[str, str]:
        g = geom.get(pid, {})
        m = meta.get(pid, {})
        return {
            "series": _series(pid),
            "contractor": str(m.get("owner_contractor") or "?"),
            "holes": _hole_bucket(g.get("hole_count")),
            "size": _size_bucket(g.get("area_norm")),
        }

    # 1) Coverage-maximising core via farthest point sampling.
    mean = X_k.mean(axis=0)
    mean /= max(np.linalg.norm(mean), 1e-12)
    seed = int(np.argmax(X_k @ mean))  # medoid-ish: closest to centroid
    core = _farthest_point_sampling(X_k, n, seed)
    reasons: dict[str, str] = {}
    for j, local_i in enumerate(core):
        reasons[ids_k[local_i]] = "coverage_seed" if j == 0 else "coverage_fps"

    selected = set(core)

    # 2) Ensure every metadata stratum is represented (top up rare conventions).
    facet_selected: dict[str, dict[str, int]] = {
        "series": {}, "contractor": {}, "holes": {}, "size": {}
    }
    for local_i in selected:
        for facet, val in strata(ids_k[local_i]).items():
            facet_selected[facet][val] = facet_selected[facet].get(val, 0) + 1

    facet_members: dict[str, dict[str, list[int]]] = {
        "series": {}, "contractor": {}, "holes": {}, "size": {}
    }
    for local_i, pid in enumerate(ids_k):
        for facet, val in strata(pid).items():
            facet_members[facet].setdefault(val, []).append(local_i)

    for facet in _COVERAGE_FACETS:
        members = facet_members[facet]
        for val, member_idxs in members.items():
            have_ct = facet_selected[facet].get(val, 0)
            need = max(0, min_per_stratum - have_ct)
            if need <= 0:
                continue
            candidates = [i for i in member_idxs if i not in selected]
            for i in candidates[:need]:
                selected.add(i)
                reasons[ids_k[i]] = f"stratum:{facet}={val}"

    picked_ids = [ids_k[i] for i in sorted(selected)]

    coverage = {"requested_n": n, "selected": len(picked_ids), "facets": {}}
    for facet in facet_members:
        counts: dict[str, int] = {}
        for pid in picked_ids:
            v = strata(pid)[facet]
            counts[v] = counts.get(v, 0) + 1
        coverage["facets"][facet] = {
            "values_total": len(facet_members[facet]),
            "values_covered": len(counts),
            "distribution": dict(sorted(counts.items(), key=lambda kv: -kv[1])[:20]),
        }

    return SampleResult(profile_ids=picked_ids, reasons=reasons, coverage=coverage)


def write_sample_csv(result: SampleResult, out_path: Path) -> None:
    ids = set(result.profile_ids)
    meta = _load_metadata(list(ids))
    geom = _load_geometric_features(ids)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["profile_id", "reason", "series", "contractor", "hole_count", "area_norm", "aspect_ratio"]
        )
        for pid in result.profile_ids:
            g = geom.get(pid, {})
            m = meta.get(pid, {})
            w.writerow(
                [
                    pid,
                    result.reasons.get(pid, ""),
                    _series(pid),
                    m.get("owner_contractor") or "",
                    g.get("hole_count"),
                    round(g["area_norm"], 4) if g.get("area_norm") is not None else "",
                    round(g["aspect_ratio"], 3) if g.get("aspect_ratio") is not None else "",
                ]
            )
