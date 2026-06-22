import sqlite3
from contextlib import contextmanager
from pathlib import Path

from matrix_advisor.config import DB_PATH, ensure_data_dirs


SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    profile_id TEXT PRIMARY KEY,
    display_name TEXT,
    source_system TEXT,
    owner_contractor TEXT,
    masa_g_m REAL,
    wall_thickness_mm REAL,
    has_pictogram INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pictogram_assets (
    asset_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
    format TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    width_px INTEGER,
    height_px INTEGER,
    checksum TEXT NOT NULL,
    quality_flags TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS matrices (
    matrix_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
    supplier_id TEXT REFERENCES suppliers(supplier_id),
    die_type TEXT,
    cavity_count INTEGER,
    press_code TEXT,
    status_code TEXT,
    status_label TEXT
);

CREATE TABLE IF NOT EXISTS matrix_production_summary (
    matrix_id TEXT PRIMARY KEY REFERENCES matrices(matrix_id),
    profile_id TEXT NOT NULL,
    effectiveness_pct REAL,
    successful_runs INTEGER,
    failed_runs INTEGER,
    correction_count INTEGER,
    interruption_count INTEGER,
    total_billets INTEGER,
    total_output_kg REAL,
    die_wear_used REAL,
    die_wear_remaining REAL,
    avg_throughput_kg_h REAL,
    last_production_at TEXT
);

CREATE TABLE IF NOT EXISTS normalization_meta (
    profile_id TEXT PRIMARY KEY REFERENCES profiles(profile_id),
    original_asset_id TEXT NOT NULL,
    crop_box TEXT NOT NULL,
    scale REAL NOT NULL,
    canvas_size INTEGER NOT NULL,
    secondary_contour_count INTEGER DEFAULT 0,
    quality_flags TEXT DEFAULT '[]'
);
"""

_PROFILE_MIGRATIONS = [
    "ALTER TABLE profiles ADD COLUMN owner_contractor TEXT",
    "ALTER TABLE profiles ADD COLUMN masa_g_m REAL",
    "ALTER TABLE profiles ADD COLUMN wall_thickness_mm REAL",
    "ALTER TABLE profiles ADD COLUMN has_pictogram INTEGER DEFAULT 0",
]

_MATRIX_MIGRATIONS = [
    "ALTER TABLE matrices ADD COLUMN status_code TEXT",
    "ALTER TABLE matrices ADD COLUMN status_label TEXT",
]


def _migrate(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(profiles)")}
    for sql in _PROFILE_MIGRATIONS:
        col = sql.split("ADD COLUMN ")[1].split()[0]
        if col not in existing:
            conn.execute(sql)
    existing = {row[1] for row in conn.execute("PRAGMA table_info(matrices)")}
    for sql in _MATRIX_MIGRATIONS:
        col = sql.split("ADD COLUMN ")[1].split()[0]
        if col not in existing:
            conn.execute(sql)


def init_db(db_path: Path | None = None) -> Path:
    ensure_data_dirs()
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
    return path


@contextmanager
def get_connection(db_path: Path | None = None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
