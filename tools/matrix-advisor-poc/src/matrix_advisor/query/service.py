from pathlib import Path

from matrix_advisor.db import get_connection
from matrix_advisor.index.builder import query_similar
from matrix_advisor.index.builder import get_index_stats
from matrix_advisor.models import SimilarityMethod


def _profile_row(r) -> dict:
    return {
        "profile_id": r["profile_id"],
        "display_name": r["display_name"],
        "owner_contractor": r["owner_contractor"] if "owner_contractor" in r.keys() else None,
        "masa_g_m": r["masa_g_m"] if "masa_g_m" in r.keys() else None,
        "wall_thickness_mm": r["wall_thickness_mm"] if "wall_thickness_mm" in r.keys() else None,
        "has_pictogram": bool(r["has_pictogram"]) if "has_pictogram" in r.keys() else False,
        "matrix_count": r["matrix_count"] if "matrix_count" in r.keys() else 0,
        "best_effectiveness_pct": r["best_effectiveness_pct"]
        if "best_effectiveness_pct" in r.keys()
        else None,
        "supplier_names": r["supplier_names"] if "supplier_names" in r.keys() else None,
    }


def browse_profiles(
    *,
    search: str | None = None,
    supplier: str | None = None,
    owner: str | None = None,
    has_pictogram: bool | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 48,
) -> dict:
    clauses: list[str] = []
    params: list = []

    if search:
        clauses.append("(p.profile_id LIKE ? OR p.display_name LIKE ?)")
        q = f"%{search}%"
        params.extend([q, q])
    if owner:
        clauses.append("p.owner_contractor = ?")
        params.append(owner)
    if has_pictogram is True:
        clauses.append("p.has_pictogram = 1")
    elif has_pictogram is False:
        clauses.append("p.has_pictogram = 0")
    if supplier:
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM matrices mx
                JOIN suppliers s ON s.supplier_id = mx.supplier_id
                WHERE mx.profile_id = p.profile_id AND s.name = ?
            )
            """
        )
        params.append(supplier)
    if status:
        clauses.append(
            "EXISTS (SELECT 1 FROM matrices mx WHERE mx.profile_id = p.profile_id AND mx.status_code = ?)"
        )
        params.append(status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    offset = max(0, (page - 1) * page_size)

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(DISTINCT p.profile_id) AS c FROM profiles p {where}",
            params,
        ).fetchone()["c"]

        rows = conn.execute(
            f"""
            SELECT
                p.profile_id, p.display_name, p.owner_contractor,
                p.masa_g_m, p.wall_thickness_mm, p.has_pictogram,
                (SELECT COUNT(*) FROM matrices m WHERE m.profile_id = p.profile_id) AS matrix_count,
                (
                    SELECT MAX(ps.effectiveness_pct)
                    FROM matrices m2
                    JOIN matrix_production_summary ps ON ps.matrix_id = m2.matrix_id
                    WHERE m2.profile_id = p.profile_id
                ) AS best_effectiveness_pct,
                (
                    SELECT GROUP_CONCAT(DISTINCT s.name)
                    FROM matrices m3
                    LEFT JOIN suppliers s ON s.supplier_id = m3.supplier_id
                    WHERE m3.profile_id = p.profile_id AND s.name IS NOT NULL
                ) AS supplier_names
            FROM profiles p
            {where}
            ORDER BY p.profile_id
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()

    return {
        "items": [_profile_row(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


def list_profiles() -> list[dict]:
    return browse_profiles(page_size=100_000)["items"]


def get_stats() -> dict:
    with get_connection() as conn:
        profiles = conn.execute("SELECT COUNT(*) AS c FROM profiles").fetchone()["c"]
        pictograms = conn.execute(
            "SELECT COUNT(*) AS c FROM profiles WHERE has_pictogram = 1"
        ).fetchone()["c"]
        matrices = conn.execute("SELECT COUNT(*) AS c FROM matrices").fetchone()["c"]
        suppliers = conn.execute("SELECT COUNT(*) AS c FROM suppliers").fetchone()["c"]
        owners = conn.execute(
            "SELECT COUNT(DISTINCT owner_contractor) AS c FROM profiles WHERE owner_contractor IS NOT NULL"
        ).fetchone()["c"]
        avg_eff = conn.execute(
            "SELECT AVG(effectiveness_pct) AS a FROM matrix_production_summary WHERE effectiveness_pct IS NOT NULL"
        ).fetchone()["a"]

    idx = get_index_stats()
    indexed = idx["embedding_count"]
    index_ok = indexed >= max(100, int(pictograms * 0.5))

    return {
        "profiles": profiles,
        "pictograms": pictograms,
        "matrices": matrices,
        "suppliers": suppliers,
        "owners": owners,
        "avg_effectiveness_pct": round(avg_eff, 1) if avg_eff else None,
        "source": "extral-json",
        "index_embedding_count": indexed,
        "index_geometric_count": idx["geometric_count"],
        "index_embedding_backend": idx.get("embedding_backend"),
        "index_ok": index_ok,
        "index_warning": None
        if index_ok
        else (
            f"Indeks podobieństwa nieaktualny ({indexed} profili vs {pictograms} piktogramów). "
            "Uruchom: matrix-advisor build-index --method all"
        ),
    }


def list_filter_suppliers() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM suppliers ORDER BY name"
        ).fetchall()
    return [r["name"] for r in rows]


def list_filter_owners() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT owner_contractor AS name
            FROM profiles
            WHERE owner_contractor IS NOT NULL AND owner_contractor != ''
            ORDER BY owner_contractor
            """
        ).fetchall()
    return [r["name"] for r in rows]


def list_filter_statuses() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT status_code AS code,
                   MAX(status_label) AS label,
                   COUNT(*) AS count
            FROM matrices
            WHERE status_code IS NOT NULL
            GROUP BY status_code
            ORDER BY count DESC
            """
        ).fetchall()
    return [{"code": r["code"], "label": r["label"], "count": r["count"]} for r in rows]


def get_profile(profile_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT profile_id, display_name, owner_contractor,
                   masa_g_m, wall_thickness_mm, has_pictogram, source_system
            FROM profiles WHERE profile_id = ?
            """,
            (profile_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "profile_id": row["profile_id"],
        "display_name": row["display_name"],
        "owner_contractor": row["owner_contractor"],
        "masa_g_m": row["masa_g_m"],
        "wall_thickness_mm": row["wall_thickness_mm"],
        "has_pictogram": bool(row["has_pictogram"]),
        "source_system": row["source_system"],
        "matrices": get_matrices_for_profile(profile_id),
    }


def get_matrices_for_profile(profile_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT m.matrix_id, m.profile_id, m.die_type, m.cavity_count, m.press_code,
                   m.status_code, m.status_label,
                   s.name AS supplier_name,
                   ps.effectiveness_pct, ps.successful_runs, ps.failed_runs,
                   ps.interruption_count, ps.die_wear_used, ps.die_wear_remaining
            FROM matrices m
            LEFT JOIN suppliers s ON s.supplier_id = m.supplier_id
            LEFT JOIN matrix_production_summary ps ON ps.matrix_id = m.matrix_id
            WHERE m.profile_id = ?
            ORDER BY COALESCE(ps.effectiveness_pct, -1) DESC, m.matrix_id
            """,
            (profile_id,),
        ).fetchall()
    return [
        {
            "matrix_id": r["matrix_id"],
            "profile_id": r["profile_id"],
            "supplier_name": r["supplier_name"],
            "die_type": r["die_type"],
            "cavity_count": r["cavity_count"],
            "press_code": r["press_code"],
            "status_code": r["status_code"],
            "status_label": r["status_label"],
            "effectiveness_pct": r["effectiveness_pct"],
            "successful_runs": r["successful_runs"],
            "failed_runs": r["failed_runs"],
            "interruption_count": r["interruption_count"],
            "die_wear_used": r["die_wear_used"],
            "die_wear_remaining": r["die_wear_remaining"],
        }
        for r in rows
    ]


def pictogram_file(profile_id: str, *, prefer_mask: bool = True, raw: bool = False) -> Path | None:
    from matrix_advisor.normalization.pipeline import load_mask, mask_path_for
    from matrix_advisor.ingestion.import_csv import get_pictogram_path

    if raw:
        return get_pictogram_path(profile_id)

    if prefer_mask:
        mask_path = mask_path_for(profile_id)
        if mask_path.exists():
            return mask_path
        mask = load_mask(profile_id)
        if mask is not None:
            return mask_path
    return get_pictogram_path(profile_id)


def build_advisory(
    profile_id: str,
    method: SimilarityMethod = SimilarityMethod.EMBEDDING,
    top_k: int = 10,
) -> dict:
    profile = get_profile(profile_id)
    if profile is None:
        raise KeyError(profile_id)

    similar = query_similar(profile_id, method, top_k=top_k)
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

    query_matrices = profile["matrices"]
    best_supplier = None
    best_effectiveness = None
    for c in candidates:
        for m in c["matrices"]:
            eff = m.get("effectiveness_pct")
            if eff is not None and (best_effectiveness is None or eff > best_effectiveness):
                best_effectiveness = eff
                best_supplier = m.get("supplier_name")

    if best_supplier and best_effectiveness is not None:
        note = (
            f"Na podstawie {len(candidates)} podobnych profili historycznych: "
            f"najwyższa odnotowana skuteczność matrycy to {best_effectiveness:.1f}% "
            f"(dostawca: {best_supplier}). To podpowiedź — decyzja należy do technologa."
        )
    elif candidates:
        note = (
            f"Znaleziono {len(candidates)} podobnych profili. "
            "Brak pełnych danych produkcyjnych dla rekomendacji dostawcy."
        )
    else:
        note = "Brak podobnych profili w indeksie."

    return {
        "query_profile_id": profile_id,
        "query_display_name": profile["display_name"],
        "method": method.value,
        "query_matrices": query_matrices,
        "similar": candidates,
        "recommendation_note": note,
    }
