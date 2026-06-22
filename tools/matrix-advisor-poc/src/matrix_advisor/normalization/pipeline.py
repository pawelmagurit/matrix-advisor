import json
from pathlib import Path

import cv2
import numpy as np
from skimage.measure import label, regionprops

from matrix_advisor.config import CANVAS_SIZE, PROCESSED_MASKS
from matrix_advisor.db import get_connection
from matrix_advisor.ingestion.import_csv import get_pictogram_path, list_profile_ids
from matrix_advisor.models import NormalizationMeta


def _to_binary(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    return binary


def _largest_contour_bbox(binary: np.ndarray) -> tuple[int, int, int, int]:
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        h, w = binary.shape
        return 0, 0, w, h
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    return x, y, w, h


def _count_holes(binary_crop: np.ndarray) -> int:
    """Count enclosed cavities inside the shape (excluding outer background)."""
    filled = binary_crop.copy()
    h, w = filled.shape
    # Flood-fill outer background from corners on inverted image
    inv = 255 - filled
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flood = inv.copy()
    cv2.floodFill(flood, mask, (0, 0), 0)
    cv2.floodFill(flood, mask, (w - 1, 0), 0)
    cv2.floodFill(flood, mask, (0, h - 1), 0)
    cv2.floodFill(flood, mask, (w - 1, h - 1), 0)
    holes = label(flood > 0)
    regions = regionprops(holes)
    # Filter tiny noise
    return sum(1 for r in regions if r.area > 20)


def normalize_grayscale(gray: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Normalize a grayscale image array to canonical mask (no DB writes)."""
    binary = _to_binary(gray)
    x, y, w, h = _largest_contour_bbox(binary)
    flags: list[str] = []

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    crop = binary[y : y + h, x : x + w]
    if crop.size == 0:
        crop = binary
        flags.append("empty_contour")

    ch, cw = crop.shape
    side = max(ch, cw)
    pad_top = (side - ch) // 2
    pad_left = (side - cw) // 2
    square = np.zeros((side, side), dtype=np.uint8)
    square[pad_top : pad_top + ch, pad_left : pad_left + cw] = crop

    scale = CANVAS_SIZE / side
    normalized = cv2.resize(square, (CANVAS_SIZE, CANVAS_SIZE), interpolation=cv2.INTER_AREA)
    _, normalized = cv2.threshold(normalized, 127, 255, cv2.THRESH_BINARY)
    return normalized, flags


def normalize_image(image_path: Path) -> tuple[np.ndarray, NormalizationMeta, list[str]]:
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    normalized, flags = normalize_grayscale(img)
    x, y, w, h = _largest_contour_bbox(_to_binary(img))
    contours, _ = cv2.findContours(_to_binary(img), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    secondary = max(0, len(contours) - 1)
    crop = _to_binary(img)[y : y + h, x : x + w]
    hole_count_hint = _count_holes(crop) if crop.size else 0

    profile_id = image_path.stem
    meta = NormalizationMeta(
        profile_id=profile_id,
        original_asset_id=profile_id,
        crop_box=(x, y, w, h),
        scale=CANVAS_SIZE / max(max(crop.shape) if crop.size else 1, 1),
        canvas_size=CANVAS_SIZE,
        secondary_contour_count=secondary,
        quality_flags=flags,
    )
    meta.quality_flags.append(f"holes_detected:{hole_count_hint}")
    return normalized, meta, flags


def normalize_bytes(data: bytes) -> tuple[np.ndarray, list[str]]:
    """Decode uploaded image bytes and return normalized mask."""
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Cannot decode image bytes")
    return normalize_grayscale(img)


def mask_path_for(profile_id: str) -> Path:
    return PROCESSED_MASKS / f"{profile_id}.png"


def normalize_profile(profile_id: str) -> Path | None:
    src = get_pictogram_path(profile_id)
    if src is None:
        return None
    mask, meta, _ = normalize_image(src)
    PROCESSED_MASKS.mkdir(parents=True, exist_ok=True)
    out = mask_path_for(profile_id)
    cv2.imwrite(str(out), mask)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO normalization_meta
            (profile_id, original_asset_id, crop_box, scale, canvas_size,
             secondary_contour_count, quality_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                meta.original_asset_id,
                json.dumps(meta.crop_box),
                meta.scale,
                meta.canvas_size,
                meta.secondary_contour_count,
                json.dumps(meta.quality_flags),
            ),
        )
    return out


def normalize_all(profile_ids: list[str] | None = None) -> dict[str, int]:
    ids = profile_ids or list_profile_ids()
    stats = {"ok": 0, "failed": 0}
    for pid in ids:
        try:
            if normalize_profile(pid) is not None:
                stats["ok"] += 1
            else:
                stats["failed"] += 1
        except Exception:
            stats["failed"] += 1
    return stats


def load_mask(profile_id: str) -> np.ndarray | None:
    path = mask_path_for(profile_id)
    if not path.exists():
        return None
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return img
