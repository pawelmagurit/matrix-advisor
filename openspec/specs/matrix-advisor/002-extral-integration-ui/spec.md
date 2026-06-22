# 002 — Extral Integration & Browser UI

**Status:** Accepted (2026-06-19)  
**Capability:** `matrix-advisor`  
**Depends on:** `001-profile-similarity-foundation`  
**Blocks:** `003-query-by-upload`, `004-supplier-ranking`

## Purpose

Deliver Matrix Advisor on **real Extral client data** (`matryce - dane v2.json`): import, browse, filter, and similarity advisory via dedicated web UI and HTTP API.

## Delivered scope (matrix-advisor-poc change)

- 10 877 profiles, 10 067 pictograms, 18 644 matrices, 27 suppliers imported
- Geometric + ResNet18 embedding index on production dataset
- React web app (`tools/matrix-advisor-poc/web/`)
- Single-command dev: `matrix-advisor dev`

---

## Requirements

### Requirement: Extral JSON ingestion

The system SHALL import profiles, base64 pictograms, matrices, suppliers, and production summaries from `data/die/matryce - dane v2.json`.

#### Scenario: Full bootstrap

- **WHEN** `matrix-advisor bootstrap-extral` is run
- **THEN** SQLite and pictogram files SHALL be populated and normalization + index build SHALL complete

#### Scenario: Duplicate matrix rows

- **WHEN** the same `matrixId` appears twice in one profile's `matryce` array
- **THEN** the importer SHALL keep the first occurrence and skip duplicates without failing

### Requirement: Profile browser API

The system SHALL expose paginated profile listing with filters: `search`, `supplier`, `owner`, `status`, `has_pictogram`.

#### Scenario: Paginated browse

- **WHEN** `GET /api/v1/profiles?page=1&page_size=48` is called
- **THEN** the response SHALL include `items`, `total`, `page`, `page_size`, `pages`

#### Scenario: Supplier filter

- **WHEN** `GET /api/v1/profiles?supplier=WILKE2` is called
- **THEN** only profiles with at least one matrix from that supplier SHALL be returned

### Requirement: Profile detail and advisory API

The system SHALL return full profile with matrices and top-k similar profiles with recommendation note.

#### Scenario: Advisory embedding

- **WHEN** `GET /api/v1/profiles/{id}/advisory?method=embedding&top_k=8` is called for an indexed profile
- **THEN** the response SHALL include ranked `similar` results and `recommendation_note`

### Requirement: Matrix Advisor web UI

The system SHALL provide a dedicated UI module with views: profile browser, similarity search, modules overview.

#### Scenario: Filter and inspect

- **WHEN** a user filters by supplier and selects a profile
- **THEN** the UI SHALL show pictogram, matrix history, and effectiveness badges

### Requirement: Integration test coverage

The system SHALL include pytest integration tests against the full Extral dataset when loaded.

#### Scenario: API smoke on production data

- **WHEN** `pytest` runs after `bootstrap-extral`
- **THEN** tests in `tests/test_api_extral.py` SHALL pass

---

## Out of scope (next change)

- Upload ad-hoc pictogram for similarity query without DB insert
- Supplier ranking by weighted production effectiveness
- E2E browser automation tests

## Implementation references

- `tools/matrix-advisor-poc/`
- `tools/matrix-advisor-poc/README.md` — manual UI checklist
- Archived change: `openspec/changes/archive/2026-06-19-matrix-advisor-poc/`
