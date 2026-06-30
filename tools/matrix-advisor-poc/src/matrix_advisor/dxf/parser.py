"""DXF file parsing via ezdxf."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PARSER_VERSION = "0.1.0"
GEO_TYPES = frozenset({"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "SPLINE", "ELLIPSE"})


@dataclass
class DxfDocument:
    path: Path | None
    dxf_version: str
    insunits: int | None
    entity_counts: dict[str, int] = field(default_factory=dict)
    block_names: list[str] = field(default_factory=list)
    _doc: Any = field(repr=False, default=None)

    @property
    def doc(self) -> Any:
        if self._doc is None:
            raise RuntimeError("DXF document not loaded")
        return self._doc


def _require_ezdxf():
    try:
        import ezdxf
    except ImportError as e:
        raise ImportError(
            "ezdxf is required for DXF processing. Install with: pip install -e '.[cad]'"
        ) from e
    return ezdxf


def file_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_dxf(path: Path | None = None, data: bytes | None = None) -> DxfDocument:
    """Load and inventory a DXF file."""
    ezdxf = _require_ezdxf()
    if path is not None:
        doc = ezdxf.readfile(path)
        src = path
    elif data is not None:
        fd, tmp_path = tempfile.mkstemp(suffix=".dxf")
        try:
            os.write(fd, data)
            os.close(fd)
            doc = ezdxf.readfile(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        src = None
    else:
        raise ValueError("path or data required")

    msp = doc.modelspace()
    counts: dict[str, int] = {}
    for e in msp:
        t = e.dxftype()
        counts[t] = counts.get(t, 0) + 1

    insunits = doc.header.get("$INSUNITS")
    blocks = [b.name for b in doc.blocks if not b.name.startswith("*")]

    return DxfDocument(
        path=src,
        dxf_version=doc.dxfversion,
        insunits=int(insunits) if insunits is not None else None,
        entity_counts=counts,
        block_names=blocks,
        _doc=doc,
    )
