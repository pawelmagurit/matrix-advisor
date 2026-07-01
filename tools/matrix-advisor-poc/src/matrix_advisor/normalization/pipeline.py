import json
from pathlib import Path

import cv2
import numpy as np
from skimage.measure import label, regionprops

from matrix_advisor import config
from matrix_advisor.config import CANVAS_SIZE
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


def _fit_mask_to_canvas(binary: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Crop, square-pad, and resize a white-on-black mask to CANVAS_SIZE."""
    flags: list[str] = []
    if binary.size == 0 or binary.max() == 0:
        flags.append("empty_contour")
        return np.zeros((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8), flags

    ys, xs = np.where(binary > 127)
    if len(xs) == 0:
        flags.append("empty_contour")
        return np.zeros((CANVAS_SIZE, CANVAS_SIZE), dtype=np.uint8), flags

    x, y = int(xs.min()), int(ys.min())
    w, h = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
    crop = binary[y : y + h, x : x + w]

    ch, cw = crop.shape
    side = max(ch, cw)
    pad_top = (side - ch) // 2
    pad_left = (side - cw) // 2
    square = np.zeros((side, side), dtype=np.uint8)
    square[pad_top : pad_top + ch, pad_left : pad_left + cw] = crop

    normalized = cv2.resize(square, (CANVAS_SIZE, CANVAS_SIZE), interpolation=cv2.INTER_AREA)
    _, normalized = cv2.threshold(normalized, 127, 255, cv2.THRESH_BINARY)
    return normalized, flags


def _solidify_mask(binary: np.ndarray) -> np.ndarray:
    """Turn line/outline drawings into a filled silhouette."""
    if binary.max() == 0:
        return binary

    if _count_holes(binary) > 0:
        return binary

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    h, w = closed.shape
    inv = (255 - closed).copy()
    flood_mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(inv, flood_mask, (0, 0), 0)
    flood_result = 255 - inv
    if _count_holes(flood_result) > 0:
        return flood_result

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        filled = np.zeros_like(closed)
        chosen = max(contours, key=cv2.contourArea)
        cv2.drawContours(filled, [chosen], -1, 255, thickness=cv2.FILLED)
        if filled.max() > 0:
            return filled

    return flood_result


def normalize_dxf_raster(raster: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Normalize DXF raster (already white shape on black) to canonical mask."""
    binary = (raster > 127).astype(np.uint8) * 255
    binary = _solidify_mask(binary)
    return _fit_mask_to_canvas(binary)


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
    flags: list[str] = []

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        flags.append("empty_contour")

    normalized, fit_flags = _fit_mask_to_canvas(binary)
    flags.extend(fit_flags)
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
    return config.PROCESSED_MASKS / f"{profile_id}.png"


def normalize_profile(profile_id: str) -> Path | None:
    src = get_pictogram_path(profile_id)
    if src is None:
        return None
    mask, meta, _ = normalize_image(src)
    config.PROCESSED_MASKS.mkdir(parents=True, exist_ok=True)
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


def _mask_is_corrupt(mask: np.ndarray) -> bool:
    """Detect normalization artifacts (e.g. full-canvas fill)."""
    if mask is None or mask.size == 0:
        return True
    white = int((mask > 127).sum())
    total = mask.size
    if white < 80:
        return True
    if white > total * 0.85:
        return True
    return False


def load_mask_from_pictogram(profile_id: str) -> np.ndarray | None:
    """Build canonical mask from Extral GIF/PNG source."""
    src = get_pictogram_path(profile_id)
    if src is None:
        return None
    img = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    mask, flags = normalize_grayscale(img)
    if "empty_contour" in flags or mask.max() == 0:
        return None
    return mask


def load_mask(profile_id: str) -> np.ndarray | None:
    path = mask_path_for(profile_id)
    if path.exists():
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is not None and not _mask_is_corrupt(img):
            return img
    return load_mask_from_pictogram(profile_id)


def _mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    a_bin = a > 127
    b_bin = b > 127
    union = np.logical_or(a_bin, b_bin).sum()
    if union == 0:
        return 0.0
    return float(np.logical_and(a_bin, b_bin).sum() / union)


def find_masks_disagreeing_with_pictogram(
    profile_ids: list[str] | None = None,
    iou_threshold: float = 0.9,
) -> list[str]:
    """Return profile ids whose stored mask badly disagrees with the pictogram.

    DXF import can overwrite the canonical pictogram-derived mask with a
    degenerate DXF raster, which then poisons the similarity index (the profile
    stops matching its own pictogram). These are the masks that need repair.
    """
    ids = profile_ids or list_profile_ids()
    out: list[str] = []
    for pid in ids:
        pic = load_mask_from_pictogram(pid)
        if pic is None:
            continue
        path = mask_path_for(pid)
        stored = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) if path.exists() else None
        if stored is None or _mask_iou(stored, pic) < iou_threshold:
            out.append(pid)
    return out


def repair_masks(
    profile_ids: list[str] | None = None,
    iou_threshold: float = 0.9,
) -> list[str]:
    """Regenerate degenerate stored masks from their Extral pictograms.

    Returns the list of repaired profile ids.
    """
    to_fix = find_masks_disagreeing_with_pictogram(profile_ids, iou_threshold)
    repaired: list[str] = []
    for pid in to_fix:
        if normalize_profile(pid) is not None:
            repaired.append(pid)
    return repaired
