# Delta — matrix-advisor-query-upload

**Base spec:** `openspec/specs/matrix-advisor/003-query-by-upload/spec.md`  
**Change:** `matrix-advisor-dxf-pipeline`

---

## MODIFIED Requirements

### Requirement: Ephemeral upload query

The system SHALL accept an uploaded profile file and run similarity search against the existing production index **without** persisting a new Profile, Matrix, or index entry.

Supported upload formats:

- **Primary:** DXF (max 10 MB) via `POST /api/v1/query/by-dxf`
- **Legacy:** GIF, PNG, JPEG (max 5 MB) via `POST /api/v1/query/by-image`

#### Scenario: Successful DXF upload query

- **WHEN** client sends `POST /api/v1/query/by-dxf` with a valid DXF file (max 10 MB)
- **THEN** the system SHALL parse DXF, render a normalized mask, run similarity search, and return ranked similar historical profiles with matrix history
- **AND** no row SHALL be inserted into `profiles`, `pictogram_assets`, or `dxf_assets`

#### Scenario: Successful image upload query

- **WHEN** client sends `POST /api/v1/query/by-image` with a valid GIF, PNG, or JPEG file (max 5 MB)
- **THEN** the system SHALL return ranked similar historical profiles with their matrix history and a recommendation note
- **AND** no row SHALL be inserted into `profiles` or `pictogram_assets`

#### Scenario: Invalid file type

- **WHEN** client uploads a file that is not a supported format for the chosen endpoint
- **THEN** the system SHALL respond with HTTP 400 and a clear error message

#### Scenario: Unreadable input

- **WHEN** the uploaded file cannot be parsed (DXF) or decoded to a contour mask (image)
- **THEN** the system SHALL respond with HTTP 422 explaining that the file could not be processed

### Requirement: New order UI workflow

The web UI SHALL provide a **„Nowe zamówienie”** view for technologists evaluating a new customer order.

#### Scenario: DXF drag and drop upload

- **WHEN** user drops a DXF file onto the upload zone
- **THEN** the UI SHALL show rendered pictogram preview, extracted dimensions when available, and run similarity search

#### Scenario: Drag and drop image upload

- **WHEN** user drops a pictogram image file onto the upload zone
- **THEN** the UI SHALL show a preview and run similarity search (legacy path)

#### Scenario: Results with history

- **WHEN** similar profiles are returned
- **THEN** the UI SHALL display side-by-side: uploaded preview, top similar profiles with pictograms, matrix suppliers, effectiveness badges, and score breakdown when Stage 2 is enabled

#### Scenario: Optional order label

- **WHEN** user enters an optional label (e.g. offer number or customer name)
- **THEN** the label SHALL appear in the results header only for the current session and SHALL NOT be stored server-side

---

## ADDED Requirements

### Requirement: DXF upload endpoint

The system SHALL expose `POST /api/v1/query/by-dxf` accepting multipart form data.

#### Scenario: DXF endpoint parameters

- **WHEN** client sends DXF upload
- **THEN** accepted parameters SHALL include: `file` (required), `method` (`embedding` | `geometric`, default `embedding`), `top_n` (1–50, default 30), `stage` (1 | 2, default 1), `filters` (optional JSON for Stage 2), `label` (optional echo string)

#### Scenario: DXF response extensions

- **WHEN** DXF upload query succeeds
- **THEN** response SHALL include `query_preview`, `extracted_dimensions`, `quality_flags`, and `score_breakdown` per candidate when `stage=2`

### Requirement: PDF explicitly unsupported

The system SHALL NOT accept PDF files on upload endpoints.

#### Scenario: PDF rejected

- **WHEN** client uploads a PDF to any query endpoint
- **THEN** the system SHALL respond with HTTP 400 indicating PDF is not supported; user SHALL provide DXF instead

### Requirement: Two-stage upload query

Upload endpoints SHALL support optional Stage 2 filtering and reranking when `stage=2` is specified.

#### Scenario: Stage 2 on DXF upload

- **WHEN** `POST /api/v1/query/by-dxf` is called with `stage=2` and optional dimensional filters
- **THEN** the system SHALL return final ranked list after multi-criteria reranking per `matrix-advisor-two-stage-search` spec

---

## REMOVED Requirements

_None — all existing image upload behavior is preserved as legacy path._
