from pathlib import Path

# Repo root: Extral/
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"
QUERY_TMP_DIR = DATA_ROOT / "tmp" / "queries"

RAW_PICTOGRAMS = DATA_ROOT / "raw" / "pictograms"
RAW_DXF = DATA_ROOT / "raw" / "dxf"
PROCESSED_MASKS = DATA_ROOT / "processed" / "masks"
PROCESSED_GEOMETRY = DATA_ROOT / "processed" / "geometry"
PROCESSED_FEATURES = DATA_ROOT / "processed" / "features"
FEATURES_DIR = DATA_ROOT / "features"
INDEX_DIR = DATA_ROOT / "index"
DB_PATH = DATA_ROOT / "matrix_advisor.db"
EXTRAL_JSON = DATA_ROOT / "die" / "matryce - dane v2.json"

CANVAS_SIZE = 256

# Multi-criteria scoring weights (MVP hardcoded)
SCORING_WEIGHTS: dict[str, float] = {
    "shape_embedding": 0.40,
    "outer_contour": 0.15,
    "inner_detail": 0.20,
    "dimension": 0.20,
    "metadata": 0.05,
}

DIMENSION_TOLERANCE_MM = 0.5
DIMENSION_TOLERANCE_PCT = 0.05

# Weighted L2 for geometric baseline (z-scored features)
GEOMETRIC_WEIGHTS: dict[str, float] = {
    "aspect_ratio": 2.0,
    "hole_count": 3.0,
    "area_norm": 1.0,
    "perimeter_norm": 1.0,
    "solidity": 2.0,
    "extent": 1.5,
    "hu_moment_0": 1.0,
    "hu_moment_1": 1.0,
    "hu_moment_2": 1.0,
    "hu_moment_3": 0.5,
    "hu_moment_4": 0.5,
    "hu_moment_5": 0.5,
    "hu_moment_6": 0.5,
}


def ensure_data_dirs() -> None:
    for path in (
        RAW_PICTOGRAMS,
        RAW_DXF,
        PROCESSED_MASKS,
        PROCESSED_GEOMETRY,
        PROCESSED_FEATURES,
        FEATURES_DIR,
        INDEX_DIR,
        QUERY_TMP_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
