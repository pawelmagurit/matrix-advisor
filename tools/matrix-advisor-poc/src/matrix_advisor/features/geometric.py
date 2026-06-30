import cv2
import numpy as np
from skimage.measure import label, regionprops

from matrix_advisor.config import CANVAS_SIZE, GEOMETRIC_WEIGHTS
from matrix_advisor.models import GeometricFeatures
from matrix_advisor.normalization.pipeline import load_mask


def _count_holes(mask: np.ndarray) -> int:
    inv = 255 - mask
    h, w = inv.shape
    flood = inv.copy()
    mask_ff = np.zeros((h + 2, w + 2), np.uint8)
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        cv2.floodFill(flood, mask_ff, seed, 0)
    holes = label(flood > 0)
    return sum(1 for r in regionprops(holes) if r.area > 20)


def extract_geometric_features(profile_id: str, mask: np.ndarray | None = None) -> GeometricFeatures | None:
    if mask is None:
        mask = load_mask(profile_id)
    if mask is None:
        return None

    binary = (mask > 127).astype(np.uint8)
    contours, hierarchy = cv2.findContours(
        binary * 255, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None

    outer = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(outer)
    perimeter = cv2.arcLength(outer, True)
    x, y, w, h = cv2.boundingRect(outer)
    aspect = w / h if h else 1.0
    hull = cv2.convexHull(outer)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area else 0.0
    extent = area / (w * h) if w * h else 0.0

    moments = cv2.moments(outer)
    hu = cv2.HuMoments(moments).flatten()
    # Log-scale Hu for stability
    hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-12)

    hole_count = _count_holes(mask)
    cavity_count = hole_count  # topological cavities inside outer contour
    contour_count = len(contours)

    canvas_area = CANVAS_SIZE * CANVAS_SIZE
    return GeometricFeatures(
        profile_id=profile_id,
        aspect_ratio=float(aspect),
        hole_count=hole_count,
        cavity_count=cavity_count,
        contour_count=contour_count,
        area_norm=float(area / canvas_area),
        perimeter_norm=float(perimeter / (4 * CANVAS_SIZE)),
        solidity=float(solidity),
        extent=float(extent),
        hu_moments=[float(v) for v in hu],
    )


def feature_vector(f: GeometricFeatures) -> np.ndarray:
    return np.array(
        [
            f.aspect_ratio,
            float(f.hole_count),
            f.area_norm,
            f.perimeter_norm,
            f.solidity,
            f.extent,
            *f.hu_moments,
        ],
        dtype=np.float64,
    )


FEATURE_NAMES = [
    "aspect_ratio",
    "hole_count",
    "area_norm",
    "perimeter_norm",
    "solidity",
    "extent",
    "hu_moment_0",
    "hu_moment_1",
    "hu_moment_2",
    "hu_moment_3",
    "hu_moment_4",
    "hu_moment_5",
    "hu_moment_6",
]


def weight_vector() -> np.ndarray:
    weights = []
    for name in FEATURE_NAMES:
        weights.append(GEOMETRIC_WEIGHTS.get(name, 1.0))
    return np.array(weights, dtype=np.float64)


def zscore_matrix(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = vectors.mean(axis=0)
    std = vectors.std(axis=0)
    std[std < 1e-8] = 1.0
    return (vectors - mean) / std, mean, std


def _outer_contour(mask: np.ndarray):
    binary = (mask > 127).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def outer_contour_score(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Hu-moment similarity of outer contours (0–1)."""
    ca, cb = _outer_contour(mask_a), _outer_contour(mask_b)
    if ca is None or cb is None:
        return 0.0
    ma = cv2.moments(ca)
    mb = cv2.moments(cb)
    hua = cv2.HuMoments(ma).flatten()
    hub = cv2.HuMoments(mb).flatten()
    hua = -np.sign(hua) * np.log10(np.abs(hua) + 1e-12)
    hub = -np.sign(hub) * np.log10(np.abs(hub) + 1e-12)
    dist = float(np.linalg.norm(hua - hub))
    return max(0.0, 1.0 / (1.0 + dist))


def inner_detail_score(
    query_features: dict,
    cand_features: dict,
    mask_a: np.ndarray,
    mask_b: np.ndarray,
) -> float:
    """Penalize mismatched holes/cavities; blend with inner region overlap."""
    qh = query_features.get("hole_count", query_features.get("cavity_count", 0))
    ch = cand_features.get("hole_count", cand_features.get("cavity_count", 0))
    hole_sim = 1.0 if qh == ch else max(0.0, 1.0 - abs(int(qh) - int(ch)) * 0.35)

    inner_a = cv2.bitwise_not(_outer_contour_mask(mask_a))
    inner_b = cv2.bitwise_not(_outer_contour_mask(mask_b))
    inter = np.logical_and(inner_a > 0, inner_b > 0).sum()
    union = np.logical_or(inner_a > 0, inner_b > 0).sum()
    iou = float(inter / union) if union else 0.0
    return 0.6 * hole_sim + 0.4 * iou


def _outer_contour_mask(mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(mask)
    c = _outer_contour(mask)
    if c is not None:
        cv2.drawContours(out, [c], -1, 255, thickness=cv2.FILLED)
    return out
