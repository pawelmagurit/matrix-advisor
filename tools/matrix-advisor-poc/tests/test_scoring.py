"""Scoring and inner-detail discrimination tests."""

import numpy as np
import cv2

from matrix_advisor.features.geometric import inner_detail_score, extract_geometric_features


def _rect_mask(holes: int = 0) -> np.ndarray:
    m = np.zeros((256, 256), dtype=np.uint8)
    cv2.rectangle(m, (64, 64), (192, 192), 255, -1)
    for i in range(holes):
        cx = 100 + i * 30
        cv2.circle(m, (cx, 128), 12, 0, -1)
    return m


def test_inner_detail_lower_for_different_holes():
    ma, mb = _rect_mask(1), _rect_mask(3)
    fa = extract_geometric_features("a", ma)
    fb = extract_geometric_features("b", mb)
    assert fa and fb
    score_same = inner_detail_score(fa.model_dump(), fa.model_dump(), ma, ma)
    score_diff = inner_detail_score(fa.model_dump(), fb.model_dump(), ma, mb)
    assert score_diff < score_same


def test_weight_aggregation_all_ones():
    from matrix_advisor.query.scoring import ScoringConfig

    cfg = ScoringConfig()
    total_w = cfg.shape_embedding + cfg.outer_contour + cfg.inner_detail + cfg.dimension + cfg.metadata
    assert abs(total_w - 1.0) < 1e-6
