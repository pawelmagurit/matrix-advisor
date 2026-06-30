from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from matrix_advisor.db import init_db
from matrix_advisor.models import SimilarityMethod
from matrix_advisor.query.service import (
    browse_profiles,
    build_advisory,
    get_profile,
    get_stats,
    list_filter_owners,
    list_filter_statuses,
    list_filter_suppliers,
    list_profiles,
    pictogram_file,
)
from matrix_advisor.query.by_dxf_service import parse_filters_json, query_by_dxf_bytes
from matrix_advisor.query.dxf_preview_service import preview_dxf_bytes
from matrix_advisor.query.dimensions_service import get_profile_dimensions, get_profile_geometry
from matrix_advisor.query.search_service import search_similar
from matrix_advisor.query.upload_service import query_by_image_bytes

app = FastAPI(title="Matrix Advisor API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/v1/health")
def health() -> dict:
    stats = get_stats()
    return {
        "status": "ok",
        "profiles_indexed": stats["profiles"],
        **stats,
    }


@app.get("/api/v1/stats")
def stats() -> dict:
    return get_stats()


@app.get("/api/v1/filters/suppliers")
def filters_suppliers() -> dict:
    return {"suppliers": list_filter_suppliers()}


@app.get("/api/v1/filters/owners")
def filters_owners() -> dict:
    return {"owners": list_filter_owners()}


@app.get("/api/v1/filters/statuses")
def filters_statuses() -> dict:
    return {"statuses": list_filter_statuses()}


@app.get("/api/v1/profiles")
def profiles(
    search: str | None = None,
    supplier: str | None = None,
    owner: str | None = None,
    has_pictogram: bool | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(48, ge=1, le=200),
) -> dict:
    return browse_profiles(
        search=search,
        supplier=supplier,
        owner=owner,
        has_pictogram=has_pictogram,
        status=status,
        page=page,
        page_size=page_size,
    )


@app.get("/api/v1/profiles/{profile_id}")
def profile_detail(profile_id: str) -> dict:
    p = get_profile(profile_id)
    if p is None:
        raise HTTPException(404, f"Profile not found: {profile_id}")
    return p


@app.get("/api/v1/profiles/{profile_id}/pictogram")
def profile_pictogram(
    profile_id: str,
    raw: bool = Query(False, description="Serve original GIF/PNG instead of normalized mask"),
) -> FileResponse:
    path = pictogram_file(profile_id, raw=raw)
    if path is None or not path.exists():
        raise HTTPException(404, f"Pictogram not found: {profile_id}")
    suffix = path.suffix.lower()
    media = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
    }.get(suffix, "image/png")
    return FileResponse(path, media_type=media)


@app.get("/api/v1/profiles/{profile_id}/similar")
def profile_similar(
    profile_id: str,
    method: str = Query("embedding", pattern="^(geometric|embedding)$"),
    top_k: int = Query(10, ge=1, le=50),
) -> dict:
    if get_profile(profile_id) is None:
        raise HTTPException(404, f"Profile not found: {profile_id}")
    try:
        results = build_advisory(
            profile_id,
            method=SimilarityMethod(method),
            top_k=top_k,
        )
        return results
    except FileNotFoundError:
        raise HTTPException(
            503,
            "Indeks podobieństwa nie istnieje. Uruchom: matrix-advisor build-index",
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/v1/profiles/{profile_id}/advisory")
def profile_advisory(
    profile_id: str,
    method: str = Query("embedding", pattern="^(geometric|embedding)$"),
    top_k: int = Query(8, ge=1, le=20),
) -> dict:
    return profile_similar(profile_id, method=method, top_k=top_k)


@app.post("/api/v1/query/by-image")
async def query_by_image(
    file: UploadFile = File(...),
    method: str = Form("embedding"),
    top_k: int = Form(8),
    label: str | None = Form(None),
) -> dict:
    if method not in ("geometric", "embedding"):
        raise HTTPException(400, "method must be geometric or embedding")
    if top_k < 1 or top_k > 20:
        raise HTTPException(400, "top_k must be between 1 and 20")

    data = await file.read()
    try:
        return query_by_image_bytes(
            data,
            method=SimilarityMethod(method),
            top_k=top_k,
            label=label,
            content_type=file.content_type,
            filename=file.filename,
        )
    except FileNotFoundError:
        raise HTTPException(
            503,
            "Indeks podobieństwa nie istnieje. Uruchom: matrix-advisor build-index",
        )
    except ValueError as e:
        msg = str(e)
        if "Cannot process" in msg or "contour" in msg.lower():
            raise HTTPException(422, msg)
        raise HTTPException(400, msg)


@app.post("/api/v1/dxf/preview")
async def dxf_preview(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    try:
        return preview_dxf_bytes(
            data,
            filename=file.filename,
            content_type=file.content_type,
        )
    except ValueError as e:
        msg = str(e)
        if "Cannot process" in msg or "contour" in msg.lower():
            raise HTTPException(422, msg)
        raise HTTPException(400, msg)


@app.post("/api/v1/query/by-dxf")
async def query_by_dxf(
    file: UploadFile = File(...),
    method: str = Form("embedding"),
    top_k: int = Form(30),
    stage: int = Form(1),
    filters: str | None = Form(None),
    label: str | None = Form(None),
) -> dict:
    if method not in ("geometric", "embedding"):
        raise HTTPException(400, "method must be geometric or embedding")
    if top_k < 1 or top_k > 50:
        raise HTTPException(400, "top_k must be between 1 and 50")
    if stage not in (1, 2):
        raise HTTPException(400, "stage must be 1 or 2")

    data = await file.read()
    try:
        flt = parse_filters_json(filters)
        return query_by_dxf_bytes(
            data,
            method=SimilarityMethod(method),
            top_k=top_k,
            stage=stage,
            filters=flt,
            label=label,
            filename=file.filename,
            content_type=file.content_type,
        )
    except FileNotFoundError:
        raise HTTPException(
            503,
            "Indeks podobieństwa nie istnieje. Uruchom: matrix-advisor build-index",
        )
    except ValueError as e:
        msg = str(e)
        if "Cannot process" in msg or "contour" in msg.lower():
            raise HTTPException(422, msg)
        raise HTTPException(400, msg)


@app.post("/api/v1/search/similar")
async def search_similar_endpoint(
    profile_id: str | None = Form(None),
    file: UploadFile | None = File(None),
    method: str = Form("embedding"),
    top_k: int = Form(30),
    stage: int = Form(1),
    filters: str | None = Form(None),
) -> dict:
    if method not in ("geometric", "embedding"):
        raise HTTPException(400, "method must be geometric or embedding")
    dxf_bytes = None
    if file is not None:
        dxf_bytes = await file.read()
    if not profile_id and not dxf_bytes:
        raise HTTPException(400, "Provide profile_id or DXF file")
    try:
        return search_similar(
            profile_id=profile_id,
            dxf_bytes=dxf_bytes,
            method=SimilarityMethod(method),
            top_k=top_k,
            stage=stage,
            filters=parse_filters_json(filters),
        )
    except FileNotFoundError:
        raise HTTPException(503, "Indeks podobieństwa nie istnieje.")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/v1/profiles/{profile_id}/dimensions")
def profile_dimensions(profile_id: str) -> dict:
    if get_profile(profile_id) is None:
        raise HTTPException(404, f"Profile not found: {profile_id}")
    data = get_profile_dimensions(profile_id)
    if data is None:
        return {"profile_id": profile_id, "dimensions": None, "validation": [], "note": "brak DXF"}
    return data


@app.get("/api/v1/profiles/{profile_id}/geometry")
def profile_geometry(profile_id: str) -> dict:
    if get_profile(profile_id) is None:
        raise HTTPException(404, f"Profile not found: {profile_id}")
    geo = get_profile_geometry(profile_id)
    if geo is None:
        raise HTTPException(404, f"No geometry artifact for {profile_id}")
    return geo
