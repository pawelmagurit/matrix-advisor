# matrix-advisor-dxf-pipeline — DXF-First Processing

**Status:** Proposed  
**Capability:** `matrix-advisor`  
**Depends on:** `001-profile-similarity-foundation`, `003-query-by-upload`  
**Blocks:** `matrix-advisor-two-stage-search`, `matrix-advisor-multi-criteria-scoring`

## Purpose

Define a **DXF-first** import and processing pipeline where the original DXF file is the source of truth and all other representations (normalized geometry JSON, pictogram mask, embeddings, SQLite rows) are **derived and regenerable**.

PDF parsing and OCR are explicitly excluded.

## Scope

| In scope | Out of scope |
|----------|--------------|
| DXF import and parse (AC1018, mm) | PDF, DWG, OCR |
| Geometry normalization for Extral-style drawings | Universal CAD support for all vendors |
| Pictogram rendering from DXF contour | Manual pictogram upload to production DB |
| DIMENSION extraction | Full title-block OCR |
| Derived `geometry.json` per profile | PostgreSQL (SQLite OK for PoC) |
| Processing status tracking | Batch import of all 10k profiles (separate task) |
| Validation sample set: `data/die/rysunki/` | |

---

## ADDED Requirements

### Requirement: DXF as source of truth

The system SHALL treat the original DXF file as the authoritative geometry source for profiles processed through this pipeline.

Derived artifacts (geometry JSON, normalized mask, embeddings, database rows) SHALL be reproducible by re-running the pipeline on the stored DXF without manual intervention.

#### Scenario: Regenerate from DXF

- **WHEN** `matrix-advisor process-dxf --profile-id E08594` is run and a DXF exists in `data/raw/dxf/E08594.dxf`
- **THEN** the system SHALL overwrite derived `geometry.json`, mask PNG, and update processing status without modifying unrelated profiles

#### Scenario: Checksum change detection

- **WHEN** a DXF file checksum changes for a profile
- **THEN** the system SHALL mark the profile as `pending_reprocess` until pipeline completes successfully

### Requirement: DXF file ingestion

The system SHALL accept DXF files as the primary input format with a maximum size of 10 MB per file.

#### Scenario: Valid DXF upload

- **WHEN** a file with `.dxf` extension and valid DXF structure is provided
- **THEN** the system SHALL parse it using a DXF library (ezdxf) and record `source_filename`, `checksum`, and `parser_version`

#### Scenario: Invalid DXF

- **WHEN** a file cannot be parsed as DXF
- **THEN** the system SHALL return HTTP 422 with a clear error and SHALL NOT write partial derived data

#### Scenario: Unsupported DXF version

- **WHEN** DXF version is newer than tested AC1018 family
- **THEN** the system SHALL attempt parse and SHALL set `quality_flags` containing `untested_dxf_version` if parse succeeds

### Requirement: Profile geometry selection

The DXF parser SHALL extract profile cross-section geometry using rules generalized from `data/die/rysunki/` sample files.

Selection priority SHALL be:

1. Layer matching `01.Profil` in modelspace
2. Layer matching `*RYSUNEK_GLOWNY*` or `*GLOWNY*` in modelspace
3. Block names matching `EAL_WYP_*` or `EAL_WKL_*` (exploded)
4. Largest closed contour on layer `07.Widok rzeczywisty` (fallback with quality flag)

#### Scenario: E02004-style drawing

- **WHEN** DXF uses `5. RYSUNEK_GLOWNY_FRAME` layer geometry in modelspace (as in sample E02004)
- **THEN** the parser SHALL select that layer geometry as the profile contour

#### Scenario: E04900-style drawing in block

- **WHEN** profile geometry resides in block `EAL_WYP_DÓŁ` with empty modelspace profile layer (as in sample E04900)
- **THEN** the parser SHALL explode the block and extract profile geometry from it

#### Scenario: Ambiguous selection

- **WHEN** no rule matches with confidence
- **THEN** the system SHALL set `quality_flags` containing `ambiguous_profile_selection` and SHALL NOT silently use frame/table geometry

### Requirement: Geometry normalization output

The normalization stage SHALL produce a canonical internal representation including:

- bounding box in millimeters
- closed or partial contour derived from LINE, ARC, CIRCLE, LWPOLYLINE entities
- `selection` metadata documenting which rule matched
- `quality_flags` list

#### Scenario: Millimeter units

- **WHEN** DXF header `$INSUNITS` indicates millimeters (value 4)
- **THEN** all exported dimensions in geometry JSON SHALL be in millimeters

#### Scenario: Contour to mask

- **WHEN** contour extraction succeeds
- **THEN** the system SHALL render a 256×256 binary mask compatible with the existing similarity pipeline

### Requirement: Pictogram preview generation

The system SHALL generate a pictogram preview image from the normalized DXF contour for frontend display.

#### Scenario: Preview style

- **WHEN** preview is generated for UI or API response
- **THEN** the preview SHALL use Extral pictogram style (bright contour on dark background) consistent with existing `query_preview` behavior

#### Scenario: Preview without DB persist on query

- **WHEN** DXF is uploaded for ephemeral query
- **THEN** preview SHALL be returned in the API response and SHALL NOT require persisting a new profile row

### Requirement: Dimension extraction from DXF

The system SHALL extract numeric dimensions from DXF `DIMENSION` entities where present.

#### Scenario: Dimension values captured

- **WHEN** DXF contains DIMENSION entities with `actual_measurement`
- **THEN** geometry JSON SHALL include `dimensions_extracted` as a list of values in millimeters

#### Scenario: Mapped technical fields

- **WHEN** dimensions are extracted for a known sample profile in `data/die/rysunki/`
- **THEN** the system SHALL map at minimum: `ocd_mm`, `wall_thickness_mm`, `width_mm`, `height_mm` where inferable from dimension set

### Requirement: Deterministic feature extraction from geometry

The system SHALL extract deterministic technical features separate from ML embeddings, including at minimum:

- outer bounding box width and height (mm)
- `hole_count` and `cavity_count` from normalized mask
- approximate area and perimeter when contour is closed
- presence flag for internal grooves/channels

#### Scenario: Features stored separately

- **WHEN** DXF processing completes for a persisted profile
- **THEN** features SHALL be stored in `features.json` or equivalent structured store keyed by `profile_id`

### Requirement: Embedding generation from DXF-derived mask

The system SHALL generate shape embeddings from the DXF-derived mask using the existing embedding backend (ResNet18 or HOG fallback).

#### Scenario: Index compatibility

- **WHEN** a profile is indexed after DXF processing
- **THEN** its embedding vector SHALL be comparable with existing GIF-derived index vectors via the same similarity method

### Requirement: Derived data storage model

SQLite and JSON files SHALL store derived data only. Schema SHALL include:

- `dxf_assets` — path, checksum, parser_version, status, processed_at
- `profile_dimensions` — width, height, wall, ocd, area, source (`dxf` | `extral` | `estimated`)
- `processing_status` on profile — `gif_only` | `dxf_ready` | `indexed` | `failed`

#### Scenario: JSON geometry artifact

- **WHEN** DXF processing succeeds
- **THEN** `data/processed/geometry/{profile_id}.json` SHALL be written with parser version and selection metadata

#### Scenario: Database portability

- **WHEN** data access is implemented
- **THEN** processing logic SHALL NOT depend on SQLite-specific features beyond standard SQL so migration to PostgreSQL remains feasible

### Requirement: Dimension validation against Extral metadata

When both DXF-derived dimensions and Extral `wlasnosci` exist for the same profile, the system SHALL compute validation results.

#### Scenario: Matching dimensions

- **WHEN** DXF `ocd_mm` is within configured tolerance of Extral OCD (e.g. ±5% or ±0.5 mm)
- **THEN** validation record SHALL mark field `ocd` as `ok`

#### Scenario: Mismatch flagged

- **WHEN** DXF wall thickness differs from Extral `Grubość ścianki` beyond tolerance
- **THEN** validation SHALL mark field `wall_thickness` as `mismatch` and include both values in API response

### Requirement: Repeatable CLI processing

The system SHALL expose CLI commands for DXF pipeline operations.

#### Scenario: Process single profile

- **WHEN** `matrix-advisor process-dxf --profile-id E08594` is run
- **THEN** full pipeline steps (parse → normalize → render → features → optional index update) SHALL execute

#### Scenario: Process validation folder

- **WHEN** `matrix-advisor import-dxf --dir data/die/rysunki` is run
- **THEN** all `*.dxf` files SHALL be processed and a summary report SHALL list success, warnings, and failures per file

### Requirement: Modular pipeline stages

The pipeline SHALL be decomposed into independent stages: ingestion, parsing, geometry normalization, pictogram rendering, feature extraction, embedding generation, index update, metadata storage.

#### Scenario: Stage isolation

- **WHEN** embedding generation is skipped via CLI flag
- **THEN** parse and geometry JSON stages SHALL still complete successfully

### Requirement: Automated tests on sample DXF set

The system SHALL include tests using all five DXF files in `data/die/rysunki/`.

#### Scenario: Sample parse success

- **WHEN** pytest runs DXF parser tests
- **THEN** all five sample files SHALL parse without error

#### Scenario: Dimension validation on samples

- **WHEN** dimension validation runs for E02004 and E08594
- **THEN** at least OCD and wall thickness SHALL validate as `ok` against Extral metadata
