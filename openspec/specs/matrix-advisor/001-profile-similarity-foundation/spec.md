# 001 — Profile Similarity Foundation

**Status:** Accepted (2026-06-16)  
**Capability:** `matrix-advisor`  
**Depends on:** —  
**Blocks:** `002-data-ingestion`, `003-shape-normalization`, `004-geometric-baseline`, `005-visual-embeddings`, `006-clustering`, `007-evaluation-harness`, `008-matrix-recommendation-demo`

## Purpose

Establish the **research foundation** for profile (cross-section) similarity search in an aluminum extrusion die-advisory system. This spec defines the canonical domain model, similarity pipeline boundaries, interfaces between modules, and acceptance criteria for the first PoC milestone — **before** building recommendation logic or production UI.

The PoC answers a narrower question than the full product:

> Given a profile pictogram, can we reliably retrieve historically similar profiles so a technologist can inspect matrices, suppliers, and outcomes?

Full recommendation (“choose supplier X”) is **out of scope** for this spec.

## Context

- ~15 000 aluminum profile shapes in production history.
- Current die/supplier selection relies on tooling-shop experience.
- Available signals today: profile ID, pictogram image (BLOB), matrix ID, supplier, matrix production history, effectiveness KPI, corrections, interruptions.
- Future signals (not required for M1): PDF, DXF, DWG.
- Existing repo module `tools/cut-planner-demo/` (1D cut optimization) remains separate and lower priority.

Reference screenshots: `screenshots/matryce.jpg`, `screenshots/historia_matrycy.jpg` (EXD layer).

## Goals

1. Define stable **domain entities** and relationships: Profile → Matrix → Supplier → ProductionOutcome.
2. Define a **modular similarity pipeline** with pluggable stages (normalize → features → embed → index → query).
3. Specify **interpretable geometric baseline** features as the first similarity method.
4. Specify **visual embedding** similarity as the second method (nearest neighbours).
5. Define **evaluation protocol** with human-rated usefulness metrics.
6. Enable local PoC execution with path to **on-premise** deployment (no cloud-only dependencies).

## Non-Goals

- Automatic supplier or matrix selection.
- Manual categorization of 15 000 profiles.
- PDF/DXF/DWG parsing in M1 (only extension points).
- Integration with BPSC Impuls / EXD APIs.
- 1D cut optimization (separate module).
- Training a custom deep model from scratch in M1.
- Production auth, multi-tenant, HA.

---

## Domain Model

### Entity: Profile

Represents a commercial aluminum profile cross-section (shape), independent of a specific die instance.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `profileId` | string | yes | Canonical ID from source system (e.g. commercial code) |
| `displayName` | string | no | Human label |
| `pictogramAssetId` | string | no | FK to stored pictogram |
| `sourceSystem` | string | no | e.g. `EXD`, `Impuls` |
| `metadata` | object | no | Alloy family, cavity hint, notes — sparse in PoC |

### Entity: PictogramAsset

Raw or normalized image representing profile cross-section.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `assetId` | string | yes | UUID |
| `profileId` | string | yes | FK |
| `format` | enum | yes | `png`, `jpeg`, `bmp`, `unknown` |
| `storagePath` | string | yes | Local path or blob ref |
| `widthPx`, `heightPx` | int | no | Original dimensions |
| `checksum` | string | yes | Dedup / change detection |
| `qualityFlags` | string[] | no | e.g. `low_resolution`, `noisy_scan`, `partial_crop` |

### Entity: Matrix (Die)

A physical extrusion die used to produce one or more profiles.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `matrixId` | string | yes | e.g. `E10217-24` |
| `profileId` | string | yes | Primary profile link |
| `supplierId` | string | no | Die manufacturer |
| `dieType` | string | no | e.g. `Komorowa` |
| `cavityCount` | int | no | Number of holes/cavities |
| `pressCode` | string | no | e.g. `PR-10.1` |

### Entity: Supplier

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `supplierId` | string | yes | |
| `name` | string | yes | |

### Entity: MatrixProductionSummary

Aggregated production/effectiveness view for recommendation demo (ingested from history).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `matrixId` | string | yes | |
| `profileId` | string | yes | |
| `effectivenessPct` | float | no | e.g. 66.67 — definition must be documented per source |
| `successfulRuns` | int | no | |
| `failedRuns` | int | no | |
| `correctionCount` | int | no | |
| `interruptionCount` | int | no | |
| `totalBillets` | int | no | |
| `totalOutputKg` | float | no | |
| `dieWearUsed` | float | no | Przebieg prod. |
| `dieWearRemaining` | float | no | Pozostały przebieg |
| `avgThroughputKgH` | float | no | |
| `lastProductionAt` | datetime | no | |

### Entity: SimilarityResult

Output of a similarity query (not persisted long-term in PoC).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `queryProfileId` | string | yes | |
| `candidateProfileId` | string | yes | |
| `rank` | int | yes | 1-based |
| `score` | float | yes | Higher = more similar (method-specific) |
| `method` | enum | yes | `geometric_baseline`, `embedding` |
| `featureBreakdown` | object | no | For interpretability (baseline only) |

### Relationships

```
Profile 1──* PictogramAsset
Profile 1──* Matrix
Matrix  *──1 Supplier
Matrix  1──1 MatrixProductionSummary (PoC aggregate; full history in spec 002)
```

---

## Pipeline Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Ingestion  │───▶│  Normalization   │───▶│ Feature Extract │
│  (spec 002) │    │  (spec 003)      │    │ (spec 004/005)  │
└─────────────┘    └──────────────────┘    └────────┬────────┘
                                                     │
                    ┌────────────────────────────────┼────────────────────┐
                    ▼                                ▼                    ▼
            ┌───────────────┐              ┌──────────────┐      ┌──────────────┐
            │ Geometric     │              │  Embedding   │      │  Clustering  │
            │ Baseline Index│              │  Index       │      │  (spec 006)  │
            └───────┬───────┘              └──────┬───────┘      └──────────────┘
                    │                             │
                    └──────────┬──────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Query API / CLI    │
                    │  profile_id → top_k │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Evaluation Harness │
                    │  (spec 007)         │
                    └─────────────────────┘
```

### Requirement: Pipeline stage isolation

Each stage SHALL be invocable independently via CLI with explicit inputs and outputs on disk (Parquet/JSON + image folders).

#### Scenario: Re-run normalization without re-ingesting

- **WHEN** raw pictograms already exist in the data store
- **THEN** the normalization stage SHALL produce normalized images without requiring a new import from source systems

### Requirement: Method registry

The system SHALL support multiple similarity methods registered under string keys (`geometric_baseline`, `embedding_v1`, …) and return results tagged with the method name.

#### Scenario: Compare two methods on same query set

- **WHEN** evaluation harness runs against a gold query set
- **THEN** the harness SHALL produce separate metric reports per method

### Requirement: Future geometry source extension point

The `Profile` entity and pipeline SHALL reserve optional fields `vectorAssetId` and `geometryFormat` (`dxf`, `dwg`, `pdf`) without implementing parsers in M1.

#### Scenario: Geometry field absent

- **WHEN** only a pictogram is available
- **THEN** the pipeline SHALL still process the profile through normalization and similarity stages

---

## Shape Normalization (M1 scope summary; detail in spec 003)

### Requirement: Normalized pictogram output

For each input pictogram, the normalization stage SHALL produce a **canonical binary mask image** plus metadata JSON.

#### Scenario: Standard pictogram

- **WHEN** input is a line drawing on white background with clear outer contour
- **THEN** output mask SHALL be cropped to the outer contour bounding box, padded uniformly, and scaled to a fixed canvas (default **256×256**) preserving aspect ratio

#### Scenario: Multiple disconnected contours

- **WHEN** the image contains multiple contours
- **THEN** the system SHALL keep the largest outer contour by area as primary and record `secondaryContourCount` in metadata

### Requirement: Normalization audit trail

Each normalized asset SHALL store: `originalAssetId`, transform parameters (scale, crop box), and `qualityFlags`.

---

## Geometric Baseline Features (M1; detail in spec 004)

### Requirement: Interpretable feature vector

The baseline extractor SHALL compute at minimum:

| Feature | Description |
|---------|-------------|
| `aspectRatio` | width / height of outer bbox |
| `contourCount` | number of significant contours |
| `holeCount` | enclosed cavities (topological) |
| `area` | pixel area of filled shape |
| `perimeter` | outer contour perimeter |
| `solidity` | area / convex hull area |
| `extent` | area / bbox area |
| `bboxWidth`, `bboxHeight` | normalized |
| `huMoments` | optional — 7 values for rotation-ish invariance |

#### Scenario: Feature vector stored

- **WHEN** extraction completes for a profile
- **THEN** features SHALL be persisted as JSON/Parquet row keyed by `profileId`

### Requirement: Baseline similarity score

The baseline index SHALL rank candidates using a weighted L1/L2 distance on **scale-normalized** features, with weights documented in config.

#### Scenario: Top-k query

- **WHEN** `queryProfileId` and `k=10` are provided
- **THEN** the system SHALL return up to 10 distinct `SimilarityResult` rows sorted by ascending distance (mapped to descending similarity score)

---

## Visual Embeddings (M1; detail in spec 005)

### Requirement: Embedding model

M1 SHALL use a **pretrained** image embedding model (no custom training). Acceptable options (choose one at implementation time, document in design):

- CLIP ViT-B/32 image encoder
- ResNet50 global average pooling (ImageNet)
- SigLIP or similar if licensing permits on-prem

#### Scenario: Embedding dimension fixed

- **WHEN** index is built
- **THEN** all vectors for a given model version SHALL have consistent dimensionality

### Requirement: Nearest neighbour index

The system SHALL build an ANN index (FAISS or hnswlib) over embedding vectors and support `top_k` queries.

#### Scenario: Query latency on PoC dataset

- **WHEN** index contains up to 15 000 profiles
- **THEN** single query SHALL return top-10 in under **500 ms** on a developer laptop (CPU acceptable for PoC)

### Requirement: Orientation handling

Because pictograms may be rotated arbitrarily, M1 SHALL generate **4 rotational variants** (0°, 90°, 180°, 270°) at index time OR use rotation-invariant embedding augmentation; query uses best-match rotation score.

#### Scenario: Rotated duplicate ranks highly

- **WHEN** query pictogram is a 90° rotation of an indexed profile
- **THEN** that profile SHALL appear in top-10 for embedding search

---

## Query Interface

### Requirement: CLI query command

```
matrix-advisor query --profile-id <id> --method <method> --top-k 10 --output results.json
```

#### Scenario: Unknown profile

- **WHEN** `profileId` does not exist
- **THEN** CLI SHALL exit with non-zero code and a clear error message

### Requirement: HTTP query endpoint (PoC-local)

A minimal local API MAY expose `GET /api/v1/profiles/{id}/similar?method=embedding&top_k=10` for demo UI consumption.

#### Scenario: JSON response shape

- **WHEN** query succeeds
- **THEN** response SHALL include `queryProfileId`, `method`, `results[]` with `profileId`, `score`, `rank`, and optional `featureBreakdown`

---

## Evaluation Foundation (M1; detail in spec 007)

### Requirement: Gold query set format

Evaluation SHALL use a YAML/JSON file:

```yaml
queries:
  - queryProfileId: E06335-4
    reviewer: technologist_initials
    relevantProfileIds: [E06335-2, E10217-24, ...]  # optional ground truth
    notes: "Similar cavity layout"
```

#### Scenario: Manual usefulness rating

- **WHEN** reviewer rates top-10 results for a query
- **THEN** each result SHALL be marked `useful | partially_useful | not_useful` with optional error tag

### Requirement: Error taxonomy

Evaluation UI/spreadsheet SHALL support error tags:

| Tag | Meaning |
|-----|---------|
| `scale_mismatch` | Similar shape, different scale |
| `technology_mismatch` | Similar contour, different extrusion technology |
| `cavity_count_mismatch` | Wrong number of chambers |
| `missing_production_data` | Good visual match but no matrix history |
| `bad_source_image` | Pictogram unreadable or corrupt |
| `false_positive_other` | Other FP reason |

### Requirement: Metrics

For each method and query set, the harness SHALL compute:

- `top1_usefulness_rate`
- `top5_usefulness_rate`
- `top10_usefulness_rate`
- `false_positive_rate` (not_useful in top-k)
- `false_negative_rate` (relevant profiles missing from top-k) — only when ground truth provided

---

## Data Storage (PoC)

### Requirement: Local analytical store

PoC SHALL use **SQLite** or **DuckDB** for relational entities and **filesystem** for images. Embeddings and features in Parquet.

#### Scenario: Reproducible rebuild

- **WHEN** `make ingest && make index` is run on a fresh clone with provided sample data
- **THEN** identical index files SHALL be produced (deterministic seeds)

---

## Technology Constraints

| Area | PoC choice | Rationale |
|------|------------|-----------|
| Language | Python 3.11+ | CV/ML ecosystem |
| Images | OpenCV, scikit-image | Normalization, contours |
| Embeddings | PyTorch + pretrained model | Quality vs effort |
| Index | FAISS or hnswlib | ANN at 15k scale |
| CLI | Typer or Click | Research workflow |
| Demo UI | Optional thin React or Streamlit | Decision demo only |
| Deploy target | Docker Compose on-prem | No hard cloud dependency |

Cut planner remains TypeScript in `tools/cut-planner-demo/` — no shared runtime with matrix PoC in M1.

---

## Milestone M1 Acceptance (this spec)

M1 is complete when ALL of the following hold:

1. **≥ 200 profiles** ingested with pictograms (sample or export).
2. Normalization pipeline runs end-to-end with audit metadata.
3. Geometric baseline index returns top-10 for any indexed profile.
4. Embedding index returns top-10 for any indexed profile.
5. Evaluation harness produces usefulness report for **≥ 20 manually selected query profiles**.
6. Documentation explains known failure modes with examples.

---

---

## Business Decisions (accepted 2026-06-16)

| Topic | Decision |
|-------|----------|
| Skuteczność matrycy | % — im wyższa, tym lepiej; wzór wyliczy klient |
| Profil ↔ matryca | 1 profil → wiele matryc; matryca nie współdzielona między profilami |
| Dostawca | nazwa tekstowa, przypisanie per matryca |
| Piktogram | BLOB/obrazek dla wszystkich profili; tylko kontur, bez skali |
| Źródło danych | eksporty CSV + pliki; brak API Impuls/EXD |
| Użytkownicy | technolog, planista, narzędziowiec, R&D, handlowcy |
| Kryteria podobieństwa | kontur, liczba komór, grubość ścianek |
| Infra PoC | lokalnie; ML/CV bez ograniczeń na start |

**Zaparkowane:** nieudana pierwsza produkcja, algorytm prób udanych/nieudanych, RODO, normalizacja piktogramów w źródle (weryfikacja po próbce).

---

## Open Questions (remaining)

1. Is `effectivenessPct` comparable across presses and alloys? _(wzór od klienta)_
2. ~~Can one matrix map to multiple profiles?~~ **Resolved:** nie — matryca przypisana do jednego profilu.
3. ~~Pictograms outer contour only?~~ **Resolved:** tak, bez skali.
4. Expected image resolution range? _(po próbce eksportu)_

---

## References

- `openspec/explore/zarzadzanie-matrycami.md`
- `screenshots/matryce.jpg`, `screenshots/historia_matrycy.jpg`
- `tools/cut-planner-demo/` — separate module, not in dependency chain
