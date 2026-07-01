"""Evaluate raw DXF→mask extraction against the ground-truth Extral pictogram.

The Extral pictogram we already hold for a profile is the label: it tells us
what the "correct" canonical shape looks like. This harness measures how well
we reproduce that shape *from the DXF alone* (pictogram fallback disabled,
because a genuinely new profile has no pictogram at inference time).

Two metrics per DXF:
  * shape fidelity  — IoU(raw DXF mask, pictogram mask)
  * retrievability  — rank at which the profile's own pictogram is retrieved
                      when querying the index with the raw DXF mask
                      (this is the production-relevant proxy: "new DXF finds
                      its true historical match").
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from matrix_advisor.dxf.pipeline import process_dxf_bytes
from matrix_advisor.index.builder import query_similar_by_mask
from matrix_advisor.models import SimilarityMethod
from matrix_advisor.normalization.pipeline import load_mask_from_pictogram

IOU_BUCKETS = [(0.9, "excellent"), (0.7, "good"), (0.5, "weak"), (0.0, "bad")]


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    a_bin = a > 127
    b_bin = b > 127
    union = np.logical_or(a_bin, b_bin).sum()
    if union == 0:
        return 0.0
    return float(np.logical_and(a_bin, b_bin).sum() / union)


def _bucket(iou: float) -> str:
    for threshold, name in IOU_BUCKETS:
        if iou >= threshold:
            return name
    return "bad"


@dataclass
class DxfEvalRow:
    profile_id: str
    file: str
    status: str
    strategy: str | None = None
    quality_flags: list[str] | None = None
    iou: float | None = None
    iou_bucket: str | None = None
    self_rank: int | None = None
    top1_id: str | None = None
    top1_score: float | None = None
    error: str | None = None


def evaluate_dxf_file(
    path: Path,
    *,
    top_k: int = 50,
) -> DxfEvalRow:
    pid = path.stem.upper()
    try:
        data = path.read_bytes()
        proc = process_dxf_bytes(
            data,
            profile_id=pid,
            source_name=path.name,
            persist=False,
            use_pictogram_fallback=False,
        )
    except Exception as e:  # noqa: BLE001 - report, don't crash the batch
        return DxfEvalRow(profile_id=pid, file=path.name, status="error", error=str(e))

    gt = load_mask_from_pictogram(pid)
    if gt is None:
        return DxfEvalRow(
            profile_id=pid,
            file=path.name,
            status="no_pictogram",
            strategy=proc.selection.strategy,
            quality_flags=proc.quality_flags,
        )

    iou = _iou(proc.mask, gt)
    hits = query_similar_by_mask(proc.mask, SimilarityMethod.EMBEDDING, top_k=top_k)
    self_rank = next((h.rank for h in hits if h.candidate_profile_id == pid), None)
    top1 = hits[0] if hits else None

    return DxfEvalRow(
        profile_id=pid,
        file=path.name,
        status="ok",
        strategy=proc.selection.strategy,
        quality_flags=proc.quality_flags,
        iou=round(iou, 4),
        iou_bucket=_bucket(iou),
        self_rank=self_rank,
        top1_id=top1.candidate_profile_id if top1 else None,
        top1_score=round(top1.score, 4) if top1 else None,
    )


def _summarize(rows: list[DxfEvalRow]) -> dict:
    ok = [r for r in rows if r.status == "ok"]
    n = len(ok)
    ious = [r.iou for r in ok if r.iou is not None]
    ranks = [r.self_rank for r in ok]

    def pct(cond) -> float:
        return round(100.0 * sum(1 for r in ok if cond(r)) / n, 1) if n else 0.0

    bucket_counts: dict[str, int] = {name: 0 for _, name in IOU_BUCKETS}
    for r in ok:
        if r.iou_bucket:
            bucket_counts[r.iou_bucket] += 1

    by_strategy: dict[str, dict] = {}
    for r in ok:
        s = r.strategy or "unknown"
        b = by_strategy.setdefault(s, {"count": 0, "iou_sum": 0.0, "retr_at1": 0})
        b["count"] += 1
        b["iou_sum"] += r.iou or 0.0
        if r.self_rank == 1:
            b["retr_at1"] += 1
    for s, b in by_strategy.items():
        b["iou_mean"] = round(b["iou_sum"] / b["count"], 4) if b["count"] else None
        b["retr_at1_pct"] = round(100.0 * b["retr_at1"] / b["count"], 1) if b["count"] else 0.0
        del b["iou_sum"]

    return {
        "total_files": len(rows),
        "evaluated": n,
        "errors": sum(1 for r in rows if r.status == "error"),
        "no_pictogram": sum(1 for r in rows if r.status == "no_pictogram"),
        "iou_mean": round(float(np.mean(ious)), 4) if ious else None,
        "iou_median": round(float(np.median(ious)), 4) if ious else None,
        "iou_buckets": bucket_counts,
        "retrieval_at_1_pct": pct(lambda r: r.self_rank == 1),
        "retrieval_at_5_pct": pct(lambda r: r.self_rank is not None and r.self_rank <= 5),
        "retrieval_at_10_pct": pct(lambda r: r.self_rank is not None and r.self_rank <= 10),
        "not_retrieved_pct": pct(lambda r: r.self_rank is None),
        "by_strategy": by_strategy,
    }


def evaluate_dxf_directory(
    directory: Path,
    *,
    top_k: int = 50,
    out_path: Path | None = None,
) -> dict:
    files = sorted(directory.glob("*.dxf"))
    rows = [evaluate_dxf_file(p, top_k=top_k) for p in files]
    summary = _summarize(rows)
    report = {"summary": summary, "rows": [asdict(r) for r in rows]}
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
