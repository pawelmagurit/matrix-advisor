"""Import Extral export: matryce - dane v2.json"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import uuid
from pathlib import Path

from matrix_advisor.config import RAW_PICTOGRAMS
from matrix_advisor.db import get_connection


def _decode_base64(data: str) -> bytes:
    s = data.strip()
    if s.startswith("data:"):
        s = s.split(",", 1)[1]
    s = re.sub(r"\s+", "", s)
    s += "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s)


def _wl(wlasnosci: dict, key: str) -> str | None:
    item = wlasnosci.get(key)
    if not isinstance(item, dict):
        return None
    val = item.get("item2")
    return str(val).strip() if val not in (None, "") else None


def _parse_float(val: str | None) -> float | None:
    if not val:
        return None
    try:
        return float(str(val).replace(",", "."))
    except ValueError:
        return None


def _slug_id(name: str) -> str:
    return hashlib.md5(name.strip().lower().encode()).hexdigest()[:12]


def _aggregate_skutecznosc(entries: list) -> tuple[float | None, int, int]:
    if not entries:
        return None, 0, 0
    vals = [e["skutecznosc"] for e in entries if e.get("skutecznosc") is not None]
    prods = sum(int(e.get("iloscProdukcji") or 0) for e in entries)
    przerw = sum(int(e.get("iloscPrzerwanych") or 0) for e in entries)
    avg = sum(vals) / len(vals) if vals else None
    return avg, prods, przerw


def _ext_from_mime(mime: str | None) -> str:
    mapping = {"image/gif": ".gif", "image/jpeg": ".jpg", "image/png": ".png"}
    return mapping.get((mime or "").lower(), ".gif")


def ingest_extral_json(
    json_path: Path,
    *,
    limit: int | None = None,
    clear_existing: bool = True,
) -> dict[str, int]:
    """Load Extral JSON export into SQLite + pictogram files."""
    RAW_PICTOGRAMS.mkdir(parents=True, exist_ok=True)
    records = json.loads(json_path.read_text(encoding="utf-8"))
    if limit:
        records = records[:limit]

    stats = {
        "profiles": 0,
        "pictograms": 0,
        "pictograms_missing": 0,
        "matrices": 0,
        "matrices_skipped_duplicate": 0,
        "suppliers": 0,
    }

    with get_connection() as conn:
        if clear_existing:
            for table in (
                "normalization_meta",
                "matrix_production_summary",
                "matrices",
                "pictogram_assets",
                "profiles",
                "suppliers",
            ):
                conn.execute(f"DELETE FROM {table}")

        seen_suppliers: set[str] = set()
        seen_matrices: set[str] = set()

        for rec in records:
            profile_id = (rec.get("indeks") or "").strip()
            if not profile_id:
                continue

            wlas = rec.get("wlasnosci") or {}
            display_name = (rec.get("nazwa") or profile_id).strip()
            owner = _wl(wlas, "wl11")
            masa = _parse_float(_wl(wlas, "wl04"))
            wall = _parse_float(_wl(wlas, "wl09"))

            conn.execute(
                """
                INSERT INTO profiles (
                    profile_id, display_name, source_system,
                    owner_contractor, masa_g_m, wall_thickness_mm, has_pictogram
                ) VALUES (?, ?, 'extral-json', ?, ?, ?, ?)
                """,
                (profile_id, display_name, owner, masa, wall, 0),
            )
            stats["profiles"] += 1

            pic = rec.get("piktogram") or {}
            b64 = pic.get("base64")
            has_pic = 0
            if b64 and len(str(b64)) > 100:
                try:
                    raw = _decode_base64(str(b64))
                    ext = _ext_from_mime(pic.get("mimeType"))
                    dest = RAW_PICTOGRAMS / f"{profile_id}{ext}"
                    dest.write_bytes(raw)
                    checksum = hashlib.sha256(raw).hexdigest()[:16]
                    conn.execute(
                        """
                        INSERT INTO pictogram_assets
                        (asset_id, profile_id, format, storage_path, checksum, quality_flags)
                        VALUES (?, ?, ?, ?, ?, '[]')
                        """,
                        (
                            str(uuid.uuid4()),
                            profile_id,
                            ext.lstrip("."),
                            str(dest),
                            checksum,
                        ),
                    )
                    conn.execute(
                        "UPDATE profiles SET has_pictogram = 1 WHERE profile_id = ?",
                        (profile_id,),
                    )
                    has_pic = 1
                    stats["pictograms"] += 1
                except Exception:
                    stats["pictograms_missing"] += 1
            else:
                stats["pictograms_missing"] += 1

            for m in rec.get("matryce") or []:
                matrix_id = (m.get("indeks") or "").strip()
                if not matrix_id:
                    continue
                if matrix_id in seen_matrices:
                    stats["matrices_skipped_duplicate"] += 1
                    continue
                seen_matrices.add(matrix_id)

                supplier_name = None
                dost = m.get("dostawca") or {}
                if isinstance(dost, dict):
                    supplier_name = (dost.get("kodKontrahenta") or "").strip() or None

                supplier_id = None
                if supplier_name:
                    supplier_id = _slug_id(supplier_name)
                    conn.execute(
                        "INSERT OR IGNORE INTO suppliers (supplier_id, name) VALUES (?, ?)",
                        (supplier_id, supplier_name),
                    )
                    if supplier_name not in seen_suppliers:
                        seen_suppliers.add(supplier_name)
                        stats["suppliers"] += 1

                cavity = m.get("liczbaOtworow")
                try:
                    cavity_i = int(cavity) if cavity is not None else None
                except (TypeError, ValueError):
                    cavity_i = None

                conn.execute(
                    """
                    INSERT INTO matrices (
                        matrix_id, profile_id, supplier_id, die_type, cavity_count,
                        press_code, status_code, status_label
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        matrix_id,
                        profile_id,
                        supplier_id,
                        m.get("typMatrycy"),
                        cavity_i,
                        None,
                        m.get("kodStatusu"),
                        m.get("opisStatusu"),
                    ),
                )
                stats["matrices"] += 1

                eff_avg, prods, przerw = _aggregate_skutecznosc(m.get("skutecznosc") or [])
                conn.execute(
                    """
                    INSERT INTO matrix_production_summary (
                        matrix_id, profile_id, effectiveness_pct,
                        successful_runs, failed_runs, interruption_count,
                        die_wear_used, die_wear_remaining
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        matrix_id,
                        profile_id,
                        eff_avg,
                        prods,
                        przerw,
                        przerw,
                        m.get("aktualneZuzycie"),
                        m.get("przebiegPozostalyM"),
                    ),
                )

    return stats
