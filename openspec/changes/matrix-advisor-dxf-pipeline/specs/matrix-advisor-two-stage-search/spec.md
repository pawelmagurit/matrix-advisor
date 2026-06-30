# matrix-advisor-two-stage-search — Two-Stage Profile Search

**Status:** Proposed  
**Capability:** `matrix-advisor`  
**Depends on:** `matrix-advisor-dxf-pipeline`, `matrix-advisor-multi-criteria-scoring`  
**Blocks:** —

## Purpose

Specify a **two-stage** profile search process: Stage 1 retrieves visually/geometrically similar candidates; Stage 2 applies dimensional filters and multi-criteria reranking for the final ranked list.

Primary query input: uploaded **DXF** for new customer orders not yet in the database.

---

## ADDED Requirements

### Requirement: Stage 1 shape similarity search

The system SHALL perform initial candidate retrieval based primarily on shape embedding and normalized geometry similarity.

#### Scenario: Default top N

- **WHEN** a DXF query is submitted with `stage=1` or default search
- **THEN** the system SHALL return up to `top_n` candidates (default 30, configurable 1–50)

#### Scenario: DXF query input

- **WHEN** client sends `POST /api/v1/query/by-dxf` with a valid DXF file
- **THEN** Stage 1 SHALL parse DXF, render mask, compute query embedding, and search the frozen production index

#### Scenario: Profile ID query input

- **WHEN** client calls `POST /api/v1/search/similar` with `profile_id` of an existing indexed profile
- **THEN** Stage 1 SHALL use that profile's mask/embedding as query vector

#### Scenario: Legacy image upload

- **WHEN** client uses `POST /api/v1/query/by-image` with GIF/PNG/JPEG
- **THEN** Stage 1 SHALL behave as today (embedding or geometric method) without requiring DXF

#### Scenario: Rotation handling

- **WHEN** Stage 1 embedding search runs for a query mask
- **THEN** the system SHALL evaluate up to 4 rotations (0°, 90°, 180°, 270°) and use the best score per candidate profile

### Requirement: Stage 2 filtering and reranking

After Stage 1 produces candidates, the system SHALL optionally apply dimensional filters and rerank using combined multi-criteria scores.

#### Scenario: Apply dimensional filters

- **WHEN** Stage 2 is requested with filters `{ "wall_thickness_mm": { "min": 1.0, "max": 2.0 } }`
- **THEN** candidates outside the filter range SHALL be excluded or marked `filtered_out` in response metadata

#### Scenario: Supported filter fields

- **WHEN** Stage 2 filters are provided
- **THEN** the system SHALL support at minimum: `width_mm`, `height_mm`, `wall_thickness_mm`, `ocd_mm`, `hole_count`, `cavity_count`

#### Scenario: Rerank after filter

- **WHEN** Stage 2 completes on remaining candidates
- **THEN** results SHALL be sorted by `total_score` descending using the multi-criteria scoring model

#### Scenario: Partial candidate dimensions

- **WHEN** a Stage 1 candidate has no DXF-derived dimensions (GIF-only historical profile)
- **THEN** dimension score for that candidate SHALL be omitted or marked `unknown` and SHALL NOT fail the entire query

### Requirement: Unified search API

The system SHALL expose a unified search endpoint supporting stage selection and filters.

#### Scenario: Stage parameter

- **WHEN** `POST /api/v1/search/similar` is called with `stage=2` and optional `filters`
- **THEN** the system SHALL run Stage 1 internally then Stage 2 before returning results

#### Scenario: Ephemeral DXF query stages

- **WHEN** `POST /api/v1/query/by-dxf` is called with `stage=2`
- **THEN** response SHALL include both Stage 1 candidate count and final ranked list after reranking

### Requirement: Query does not persist to database

DXF and image upload searches SHALL remain ephemeral and SHALL NOT insert new profiles or modify the index.

#### Scenario: No DB write on DXF upload

- **WHEN** a new customer DXF is queried
- **THEN** no row SHALL be inserted into `profiles` or `dxf_assets` unless an explicit future import command is used

### Requirement: Response includes search metadata

Search responses SHALL document which stage was executed and how many candidates were filtered.

#### Scenario: Stage 2 metadata

- **WHEN** Stage 2 runs
- **THEN** response SHALL include `stage1_count`, `stage2_count`, and `filters_applied`

### Requirement: Index prerequisite

Both stages SHALL require a built similarity index and SHALL NOT trigger index rebuild at query time.

#### Scenario: Missing index

- **WHEN** index files are absent
- **THEN** the system SHALL respond with HTTP 503 and instructions to run offline `build-index`

### Requirement: Latency budget

Stage 1 on PoC hardware SHALL return top-30 within 10 seconds for a single DXF upload including parse and embedding (CPU acceptable).

#### Scenario: Acceptable response time

- **WHEN** a typical DXF from `data/die/rysunki/` is queried on developer laptop
- **THEN** Stage 1 response SHALL complete within 10 seconds p95 in integration tests

### Requirement: Automated two-stage tests

The system SHALL include tests covering Stage 1 DXF query and Stage 2 filter/rerank on sample data.

#### Scenario: Stage 1 returns candidates

- **WHEN** E08594.dxf is queried against full index
- **THEN** E08594 or geometrically similar profiles SHALL appear in top 30

#### Scenario: Stage 2 filter reduces set

- **WHEN** Stage 2 filter requires `hole_count >= 2` on a synthetic query
- **THEN** results SHALL exclude candidates with `hole_count < 2`
