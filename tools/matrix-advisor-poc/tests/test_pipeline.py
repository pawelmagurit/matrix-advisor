import json

import pytest

from matrix_advisor.config import DB_PATH, INDEX_DIR
from matrix_advisor.db import init_db
from matrix_advisor.index.builder import build_embedding_index, build_geometric_index, query_similar
from matrix_advisor.ingestion.import_csv import ingest_matrices, ingest_profiles, list_profile_ids
from matrix_advisor.ingestion.sample_data import generate_sample_data
from matrix_advisor.models import SimilarityMethod
from matrix_advisor.normalization.pipeline import normalize_all


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Use temp database and data dirs for each test."""
    data_root = tmp_path / "data"
    monkeypatch.setattr("matrix_advisor.config.DATA_ROOT", data_root)
    monkeypatch.setattr("matrix_advisor.config.RAW_PICTOGRAMS", data_root / "raw" / "pictograms")
    monkeypatch.setattr("matrix_advisor.config.PROCESSED_MASKS", data_root / "processed" / "masks")
    monkeypatch.setattr("matrix_advisor.config.FEATURES_DIR", data_root / "features")
    monkeypatch.setattr("matrix_advisor.config.INDEX_DIR", data_root / "index")
    monkeypatch.setattr("matrix_advisor.config.DB_PATH", data_root / "matrix_advisor.db")
    monkeypatch.setattr("matrix_advisor.config.SAMPLE_DIR", data_root / "sample")
    monkeypatch.setattr("matrix_advisor.db.DB_PATH", data_root / "matrix_advisor.db")
    yield


def test_full_pipeline_sample_data():
    init_db()
    sample_dir = generate_sample_data(count=12)
    ingest_profiles(sample_dir / "profiles.csv", sample_dir / "pictograms")
    ingest_matrices(sample_dir / "matrices.csv")

    assert len(list_profile_ids()) == 12

    norm = normalize_all()
    assert norm["ok"] == 12
    assert norm["failed"] == 0

    build_geometric_index()
    build_embedding_index()

    assert (INDEX_DIR / "geometric.npz").exists()
    assert (INDEX_DIR / "embedding.npz").exists()

    geo = query_similar("E-SAMPLE-001", SimilarityMethod.GEOMETRIC, top_k=5)
    emb = query_similar("E-SAMPLE-001", SimilarityMethod.EMBEDDING, top_k=5)

    assert len(geo) == 5
    assert len(emb) == 5
    assert all(r.candidate_profile_id != "E-SAMPLE-001" for r in geo)
    assert all(r.candidate_profile_id != "E-SAMPLE-001" for r in emb)
    assert geo[0].rank == 1
    assert emb[0].score > 0


def test_query_unknown_profile_raises():
    init_db()
    generate_sample_data(count=6)
    sample_dir = INDEX_DIR.parent / "sample"
    ingest_profiles(sample_dir / "profiles.csv", sample_dir / "pictograms")
    normalize_all()
    build_geometric_index()

    with pytest.raises(ValueError, match="No geometric features"):
        query_similar("NONEXISTENT", SimilarityMethod.GEOMETRIC, top_k=3)
