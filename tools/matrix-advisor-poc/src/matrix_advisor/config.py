from pathlib import Path

# Repo root: Extral/
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"
QUERY_TMP_DIR = DATA_ROOT / "tmp" / "queries"

RAW_PICTOGRAMS = DATA_ROOT / "raw" / "pictograms"
PROCESSED_MASKS = DATA_ROOT / "processed" / "masks"
FEATURES_DIR = DATA_ROOT / "features"
INDEX_DIR = DATA_ROOT / "index"
DB_PATH = DATA_ROOT / "matrix_advisor.db"
SAMPLE_DIR = DATA_ROOT / "sample"
EXTRAL_JSON = DATA_ROOT / "die" / "matryce - dane v2.json"

CANVAS_SIZE = 256

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
        PROCESSED_MASKS,
        FEATURES_DIR,
        INDEX_DIR,
        SAMPLE_DIR,
        QUERY_TMP_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
