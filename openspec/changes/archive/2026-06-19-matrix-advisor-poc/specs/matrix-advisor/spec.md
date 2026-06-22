## ADDED Requirements

### Requirement: Domain model

The system SHALL persist Profile, PictogramAsset, Matrix, Supplier, and MatrixProductionSummary entities as defined in `openspec/specs/matrix-advisor/001-profile-similarity-foundation/spec.md`.

#### Scenario: One profile many matrices

- **WHEN** a profile has three historical matrix instances
- **THEN** the database SHALL store three Matrix rows with the same `profileId` and distinct `matrixId` values

#### Scenario: Matrix not shared across profiles

- **WHEN** ingesting matrices
- **THEN** each `matrixId` SHALL link to exactly one `profileId`

### Requirement: CSV ingestion

The system SHALL import profiles from a manifest CSV with columns `profile_id`, `pictogram_filename` and copy pictogram files from a directory into the raw data store.

#### Scenario: Missing pictogram file

- **WHEN** a manifest row references a missing file
- **THEN** the importer SHALL record a warning and skip or flag the profile with `qualityFlags` containing `missing_pictogram`

### Requirement: Matrix and supplier ingestion

The system SHALL import optional `matrices.csv` with `matrix_id`, `profile_id`, `supplier_name`, and optional production summary fields including `effectiveness_pct` (higher is better).

#### Scenario: Supplier by name

- **WHEN** `supplier_name` is provided without supplier ID
- **THEN** the system SHALL create or match Supplier by name string

### Requirement: Shape normalization

The system SHALL produce a 256×256 binary mask per pictogram, cropped to outer contour, preserving aspect ratio, without assuming absolute scale.

#### Scenario: Contour-only pictogram

- **WHEN** input is a line drawing without dimension annotations
- **THEN** normalization SHALL succeed using outer contour detection

### Requirement: Geometric baseline index

The system SHALL extract interpretable geometric features and support top-k similarity queries ranked by weighted L2 distance.

#### Scenario: Top-10 baseline query

- **WHEN** `query --method geometric --top-k 10` is run for an indexed profile
- **THEN** the system SHALL return up to 10 results excluding the query profile itself

### Requirement: Embedding index

The system SHALL build an image embedding index and support top-k nearest neighbour queries with rotation handling (0/90/180/270°).

#### Scenario: Embedding query under 500ms

- **WHEN** the index contains up to 15 000 profiles
- **THEN** a single top-10 query SHALL complete in under 500 ms on CPU

### Requirement: CLI query output

Query results SHALL be JSON including `queryProfileId`, `method`, and ranked `results` with `profileId`, `score`, `rank`.

#### Scenario: JSON stdout

- **WHEN** query succeeds
- **THEN** CLI SHALL print valid JSON to stdout

### Requirement: Sample data generator

The system SHALL provide a command to generate synthetic pictograms and CSV manifests for pipeline testing without client export.

#### Scenario: End-to-end on sample

- **WHEN** user runs `sample-data`, then `ingest`, `normalize`, `build-index`, `query`
- **THEN** the pipeline SHALL complete without error

### Requirement: Export-ready architecture

Ingestion SHALL NOT require live database or API connection to client systems; only filesystem CSV and image exports.

#### Scenario: Plug-in client export

- **WHEN** client provides `profiles.csv` and `pictograms/` matching documented format
- **THEN** no code changes SHALL be required beyond pointing ingest paths
