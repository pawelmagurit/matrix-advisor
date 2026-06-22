import csv
from pathlib import Path

import cv2
import numpy as np

from matrix_advisor.config import SAMPLE_DIR


def _draw_rect_profile(path: Path, outer: tuple, holes: list[tuple]) -> None:
    canvas = np.ones((200, 200), dtype=np.uint8) * 255
    ox, oy, ow, oh = outer
    cv2.rectangle(canvas, (ox, oy), (ox + ow, oy + oh), 0, 2)
    for hx, hy, hw, hh in holes:
        cv2.rectangle(canvas, (hx, hy), (hx + hw, hy + hh), 0, 2)
    cv2.imwrite(str(path), canvas)


def _draw_hollow_profile(path: Path, outer: tuple, inner: tuple) -> None:
    canvas = np.ones((200, 200), dtype=np.uint8) * 255
    ox, oy, ow, oh = outer
    cv2.rectangle(canvas, (ox, oy), (ox + ow, oy + oh), 0, 3)
    ix, iy, iw, ih = inner
    cv2.rectangle(canvas, (ix, iy), (ix + iw, iy + ih), 255, -1)
    cv2.rectangle(canvas, (ix, iy), (ix + iw, iy + ih), 0, 2)
    cv2.imwrite(str(path), canvas)


def _draw_circle_profile(path: Path, r: int) -> None:
    canvas = np.ones((200, 200), dtype=np.uint8) * 255
    cv2.circle(canvas, (100, 100), r, 0, 2)
    cv2.imwrite(str(path), canvas)


def generate_sample_data(count: int = 24) -> Path:
    """Create synthetic pictograms + CSV manifests under data/sample/."""
    pictograms = SAMPLE_DIR / "pictograms"
    pictograms.mkdir(parents=True, exist_ok=True)

    profiles: list[dict[str, str]] = []
    matrices: list[dict[str, str]] = []

    drawers = [
        lambda p: _draw_rect_profile(p, (40, 30, 120, 140), []),
        lambda p: _draw_rect_profile(p, (40, 30, 120, 140), [(80, 70, 40, 60)]),
        lambda p: _draw_hollow_profile(p, (30, 20, 140, 160), (60, 50, 80, 100)),
        lambda p: _draw_circle_profile(p, 60),
        lambda p: _draw_circle_profile(p, 45),
        lambda p: _draw_rect_profile(p, (50, 40, 100, 120), [(70, 60, 30, 40), (110, 60, 30, 40)]),
    ]

    for i in range(count):
        pid = f"E-SAMPLE-{i + 1:03d}"
        png = pictograms / f"{pid}.png"
        drawers[i % len(drawers)](png)
        profiles.append(
            {
                "profile_id": pid,
                "display_name": f"Sample profile {pid}",
                "pictogram_filename": f"{pid}.png",
            }
        )
        if i % 3 == 0:
            matrices.append(
                {
                    "matrix_id": f"{pid}-M1",
                    "profile_id": pid,
                    "supplier_name": "Demo Supplier A" if i % 2 == 0 else "Demo Supplier B",
                    "die_type": "Komorowa",
                    "cavity_count": "1",
                    "press_code": "PR-10.1",
                    "effectiveness_pct": str(55 + (i % 40)),
                    "correction_count": str(i % 4),
                    "interruption_count": str(i % 2),
                }
            )

    profiles_path = SAMPLE_DIR / "profiles.csv"
    with profiles_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["profile_id", "display_name", "pictogram_filename"])
        w.writeheader()
        w.writerows(profiles)

    matrices_path = SAMPLE_DIR / "matrices.csv"
    with matrices_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "matrix_id",
                "profile_id",
                "supplier_name",
                "die_type",
                "cavity_count",
                "press_code",
                "effectiveness_pct",
                "correction_count",
                "interruption_count",
            ],
        )
        w.writeheader()
        w.writerows(matrices)

    return SAMPLE_DIR
