from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SimilarityMethod(str, Enum):
    GEOMETRIC = "geometric"
    EMBEDDING = "embedding"


class Profile(BaseModel):
    profile_id: str
    display_name: str | None = None
    source_system: str | None = "export"


class PictogramAsset(BaseModel):
    asset_id: str
    profile_id: str
    format: str
    storage_path: str
    width_px: int | None = None
    height_px: int | None = None
    checksum: str
    quality_flags: list[str] = Field(default_factory=list)


class Supplier(BaseModel):
    supplier_id: str
    name: str


class Matrix(BaseModel):
    matrix_id: str
    profile_id: str
    supplier_id: str | None = None
    die_type: str | None = None
    cavity_count: int | None = None
    press_code: str | None = None


class MatrixProductionSummary(BaseModel):
    matrix_id: str
    profile_id: str
    effectiveness_pct: float | None = None
    successful_runs: int | None = None
    failed_runs: int | None = None
    correction_count: int | None = None
    interruption_count: int | None = None
    total_billets: int | None = None
    total_output_kg: float | None = None
    die_wear_used: float | None = None
    die_wear_remaining: float | None = None
    avg_throughput_kg_h: float | None = None
    last_production_at: datetime | None = None


class NormalizationMeta(BaseModel):
    profile_id: str
    original_asset_id: str
    crop_box: tuple[int, int, int, int]  # x, y, w, h
    scale: float
    canvas_size: int
    secondary_contour_count: int = 0
    quality_flags: list[str] = Field(default_factory=list)


class GeometricFeatures(BaseModel):
    profile_id: str
    aspect_ratio: float
    hole_count: int
    cavity_count: int = 0
    contour_count: int
    area_norm: float
    perimeter_norm: float
    solidity: float
    extent: float
    hu_moments: list[float]


class SimilarityResult(BaseModel):
    query_profile_id: str
    candidate_profile_id: str
    rank: int
    score: float
    method: SimilarityMethod
    feature_breakdown: dict[str, Any] | None = None


class QueryResponse(BaseModel):
    query_profile_id: str
    method: SimilarityMethod
    results: list[SimilarityResult]
