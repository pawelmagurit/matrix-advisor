## Context

PoC matrix-advisor realizuje spec `001-profile-similarity-foundation`. Cut planner (`tools/cut-planner-demo/`) jest oddzielny. Dane klienta (eksport BLOB + CSV) jeszcze nie dotarły — system musi być gotowy na podpięcie; w międzyczasie syntetyczne piktogramy i manifest CSV.

## Goals / Non-Goals

**Goals:**
- End-to-end pipeline lokalny: ingest → normalize → index → query
- SQLite + filesystem dla assetów
- Geometric baseline (interpretowalny) + embedding (ResNet18 GAP, opcjonalnie HOG fallback)
- CLI Typer; deterministyczny rebuild indeksu
- README z formatem eksportu oczekiwanym od klienta

**Non-Goals:**
- Demo UI rekomendacji (spec 008 — później)
- Clustering, evaluation harness (M2)
- PDF/DXF/DWG, API Impuls
- Automatyczna rekomendacja dostawcy

## Decisions

### 1. Stack: Python 3.11+, Typer, Pydantic v2, OpenCV, scikit-image

**Rationale:** Ekosystem CV/ML; cut planner zostaje w TS.

### 2. Storage: SQLite + katalogi `data/`

```
data/raw/pictograms/          ← eksport BLOB (profile_id.png)
data/processed/masks/         ← znormalizowane maski 256×256
data/features/geometric.parquet
data/index/geometric.npz
data/index/embedding.npz
data/matrix_advisor.db        ← SQLite
```

### 3. Ingestion contract (gotowy na eksport klienta)

**Manifest CSV** (`profiles.csv`):
```csv
profile_id,display_name,pictogram_filename
E06335-4,Profil okienny,E06335-4.png
```

**Matrices CSV** (`matrices.csv`):
```csv
matrix_id,profile_id,supplier_name,die_type,cavity_count,press_code,effectiveness_pct,correction_count,interruption_count
E10217-24,E06335-4,Acme Dies,Komorowa,1,PR-10.1,66.67,2,0
```

Alternatywa: jeden plik `export.zip` z CSV + `pictograms/` — importer rozpakuje.

### 4. Normalization (shape-only, no scale)

1. Grayscale → binary (Otsu + morfologia)
2. Largest outer contour
3. Crop + pad to square, resize 256×256 preserving aspect
4. Store `NormalizationMeta` (crop box, flags)

Rotation at query/index: 4 rotations for embedding search.

### 5. Geometric baseline

Features: aspectRatio, holeCount, area, perimeter, solidity, extent, huMoments[7].  
Distance: weighted L2 on z-scored features (weights in YAML config).

### 6. Embeddings

Primary: **ResNet18** (torchvision, ImageNet weights) on 3×256×256 mask tensor, GAP → 512-d.  
Fallback if torch missing: **HOG** vector (documented degradation).

Index: numpy cosine similarity (brute force OK for ≤15k in PoC).

### 7. CLI commands

```
matrix-advisor init-db
matrix-advisor ingest --manifest profiles.csv --pictograms-dir ./pictograms [--matrices matrices.csv]
matrix-advisor normalize [--all]
matrix-advisor build-index [--method geometric|embedding|all]
matrix-advisor query --profile-id ID --method embedding --top-k 10
matrix-advisor sample-data   # syntetyczne dane demo
```

### 8. Module layout

```
tools/matrix-advisor-poc/
├── pyproject.toml
├── src/matrix_advisor/
│   ├── models.py
│   ├── db.py
│   ├── config.py
│   ├── ingestion/
│   ├── normalization/
│   ├── features/
│   ├── embeddings/
│   ├── index/
│   ├── query/
│   └── cli.py
├── tests/
└── README.md
```

## Risks

| Risk | Mitigation |
|------|------------|
| Piktogramy bez skali — scale mismatch FP | Normalizacja do bbox; ocena po próbce |
| Brak danych klienta | `sample-data` + dokumentacja formatu importu |
| Torch ciężki | HOG fallback; optional extra in pyproject |

## Open Questions

- Dokładny format eksportu BLOB od IT (nazewnictwo plików, encoding).
- Wzór skuteczności % — czekamy na klienta.
