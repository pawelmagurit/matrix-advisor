import hashlib
import json
import shutil
import uuid
from pathlib import Path

import pandas as pd

from matrix_advisor import config
from matrix_advisor.db import get_connection
from matrix_advisor.models import Matrix, MatrixProductionSummary, Profile, Supplier


def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def _slug_supplier_id(name: str) -> str:
    return hashlib.md5(name.strip().lower().encode()).hexdigest()[:12]


def upsert_supplier(conn, name: str) -> str:
    supplier_id = _slug_supplier_id(name)
    conn.execute(
        "INSERT OR IGNORE INTO suppliers (supplier_id, name) VALUES (?, ?)",
        (supplier_id, name.strip()),
    )
    return supplier_id


def ingest_profiles(manifest_path: Path, pictograms_dir: Path) -> dict[str, int]:
    """Import profiles.csv + copy pictograms to data/raw/pictograms/."""
    config.RAW_PICTOGRAMS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(manifest_path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]

    stats = {"imported": 0, "skipped": 0, "warnings": 0}

    with get_connection() as conn:
        for _, row in df.iterrows():
            profile_id = row.get("profile_id", "").strip()
            filename = row.get("pictogram_filename", "").strip()
            if not profile_id or not filename:
                stats["skipped"] += 1
                continue

            src = pictograms_dir / filename
            flags: list[str] = []
            if not src.exists():
                flags.append("missing_pictogram")
                stats["warnings"] += 1

            display_name = row.get("display_name", "").strip() or None
            conn.execute(
                """
                INSERT INTO profiles (profile_id, display_name, source_system)
                VALUES (?, ?, 'export')
                ON CONFLICT(profile_id) DO UPDATE SET
                    display_name=excluded.display_name
                """,
                (profile_id, display_name),
            )

            if src.exists():
                ext = src.suffix.lower().lstrip(".") or "unknown"
                dest = config.RAW_PICTOGRAMS / f"{profile_id}{src.suffix.lower() or '.png'}"
                shutil.copy2(src, dest)
                checksum = _checksum(dest)

                import cv2

                img = cv2.imread(str(dest), cv2.IMREAD_UNCHANGED)
                h, w = (img.shape[:2] if img is not None else (None, None))

                asset_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pictogram_assets
                    (asset_id, profile_id, format, storage_path, width_px, height_px,
                     checksum, quality_flags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset_id,
                        profile_id,
                        ext,
                        str(dest),
                        w,
                        h,
                        checksum,
                        json.dumps(flags),
                    ),
                )
            else:
                asset_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pictogram_assets
                    (asset_id, profile_id, format, storage_path, width_px, height_px,
                     checksum, quality_flags)
                    VALUES (?, ?, 'unknown', ?, NULL, NULL, 'missing', ?)
                    """,
                    (asset_id, profile_id, str(src), json.dumps(flags)),
                )

            stats["imported"] += 1

    return stats


def ingest_matrices(matrices_path: Path) -> dict[str, int]:
    df = pd.read_csv(matrices_path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    stats = {"imported": 0, "skipped": 0}

    with get_connection() as conn:
        for _, row in df.iterrows():
            matrix_id = row.get("matrix_id", "").strip()
            profile_id = row.get("profile_id", "").strip()
            if not matrix_id or not profile_id:
                stats["skipped"] += 1
                continue

            supplier_id = None
            supplier_name = row.get("supplier_name", "").strip()
            if supplier_name:
                supplier_id = upsert_supplier(conn, supplier_name)

            cavity = row.get("cavity_count", "").strip()
            matrix = Matrix(
                matrix_id=matrix_id,
                profile_id=profile_id,
                supplier_id=supplier_id,
                die_type=row.get("die_type", "").strip() or None,
                cavity_count=int(cavity) if cavity.isdigit() else None,
                press_code=row.get("press_code", "").strip() or None,
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO matrices
                (matrix_id, profile_id, supplier_id, die_type, cavity_count, press_code)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    matrix.matrix_id,
                    matrix.profile_id,
                    matrix.supplier_id,
                    matrix.die_type,
                    matrix.cavity_count,
                    matrix.press_code,
                ),
            )

            eff = row.get("effectiveness_pct", "").strip()
            corr = row.get("correction_count", "").strip()
            intr = row.get("interruption_count", "").strip()
            summary = MatrixProductionSummary(
                matrix_id=matrix_id,
                profile_id=profile_id,
                effectiveness_pct=float(eff) if eff else None,
                correction_count=int(corr) if corr.isdigit() else None,
                interruption_count=int(intr) if intr.isdigit() else None,
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO matrix_production_summary
                (matrix_id, profile_id, effectiveness_pct, correction_count,
                 interruption_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    summary.matrix_id,
                    summary.profile_id,
                    summary.effectiveness_pct,
                    summary.correction_count,
                    summary.interruption_count,
                ),
            )
            stats["imported"] += 1

    return stats


def list_profile_ids() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT profile_id FROM profiles ORDER BY profile_id"
        ).fetchall()
    return [r["profile_id"] for r in rows]


def get_pictogram_path(profile_id: str) -> Path | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT storage_path, quality_flags FROM pictogram_assets
            WHERE profile_id = ? ORDER BY asset_id DESC LIMIT 1
            """,
            (profile_id,),
        ).fetchone()
    if row is None:
        return None
    flags = json.loads(row["quality_flags"] or "[]")
    if "missing_pictogram" in flags:
        return None
    path = Path(row["storage_path"])
    return path if path.exists() else None
