## 1. Dependencies and scaffolding

- [x] 1.1 Add optional `[cad]` extra in `pyproject.toml` with `ezdxf>=1.0`
- [x] 1.2 Create `src/matrix_advisor/dxf/` package skeleton (`parser`, `profile_selector`, `contour_builder`, `renderer`, `dimensions`)
- [x] 1.3 Extend `config.py` with paths: `RAW_DXF`, `PROCESSED_GEOMETRY`, scoring weights, validation tolerances
- [x] 1.4 Add SQLite migration: `dxf_assets`, `profile_dimensions`, `dimension_validation`, `processing_status` column on profiles

## 2. DXF parser (validation set: `data/die/rysunki/`)

- [x] 2.1 Implement `parse_dxf(path) -> DxfDocument` with ezdxf, entity inventory, units detection
- [x] 2.2 Implement `profile_selector` with priority rules (01.Profil → RYSUNEK_GLOWNY → EAL_* blocks → 07.Widok rzeczywisty fallback)
- [x] 2.3 Implement block explode for INSERT references (E04900, E03148 cases)
- [x] 2.4 Implement `contour_builder` from LINE/ARC entities → polygon or polyline list
- [x] 2.5 Unit tests: all 5 sample DXF files parse; selection strategy logged per file

## 3. Geometry normalization and pictogram renderer

- [x] 3.1 Implement `renderer.contour_to_mask()` → 256×256 binary mask (reuse normalization padding/scaling)
- [x] 3.2 Implement `renderer.mask_to_preview()` — Extral style (bright on dark)
- [x] 3.3 Write `geometry.json` artifact with bbox, selection, dimensions_extracted, quality_flags
- [x] 3.4 CLI: `matrix-advisor process-dxf --profile-id <id>` and `import-dxf --dir data/die/rysunki`
- [x] 3.5 Test: DXF-derived mask for E08594 visually aligns with GIF-derived mask (IoU or manual snapshot)

## 4. Dimension extraction and validation

- [x] 4.1 Implement `dimensions.py` — extract DIMENSION entities, map to ocd/wall/width/height heuristics
- [x] 4.2 Persist `profile_dimensions` and write `dimension_validation` vs Extral `wlasnosci`
- [x] 4.3 API: `GET /api/v1/profiles/{id}/dimensions` and `GET /api/v1/profiles/{id}/geometry`
- [x] 4.4 Tests: E02004 OCD=33, E08594 OCD=25 and wall=1.4 validate as `ok` against Extral

## 5. Deterministic feature extensions

- [x] 5.1 Extend geometric features: `cavity_count`, outer-only contour features, inner mask IoU helpers
- [x] 5.2 New `features/dimensional.py` for mm-based feature vector
- [x] 5.3 Write `features.json` per processed DXF profile
- [x] 5.4 Test: synthetic masks differing only in hole count produce lower `inner_detail` score

## 6. Stage 1 — DXF upload query

- [x] 6.1 Implement `query/by_dxf_service.py` — ephemeral parse → mask → Stage 1 search
- [x] 6.2 API: `POST /api/v1/query/by-dxf` (file, method, top_n, stage, filters, label)
- [x] 6.3 Reject PDF with HTTP 400 on all upload endpoints
- [x] 6.4 Keep `by-image` unchanged; integration tests for both paths
- [x] 6.5 Test: query E08594.dxf returns E08594 or close neighbors in top 30

## 7. Multi-criteria scoring (Stage 2 foundation)

- [x] 7.1 Implement `query/scoring.py` with `ScoringConfig`, dimension scorers, breakdown aggregation
- [x] 7.2 Implement `query/stage2.py` — filter + rerank on Stage 1 candidates
- [x] 7.3 API: `POST /api/v1/search/similar` unified endpoint with stage and filters
- [x] 7.4 Extend advisory/upload response with `score_breakdown`, `metadata_match`, `extracted_dimensions`
- [x] 7.5 Unit tests for weight aggregation and missing-dimension handling

## 8. Frontend — DXF upload and Stage 2 UI

- [x] 8.1 Update `NewOrderView`: DXF primary upload, dimension preview, stage selector
- [x] 8.2 Results list: total score, breakdown bars/badges, key dimensions per candidate
- [x] 8.3 Advanced filters panel: width, height, wall, hole/cavity count → Stage 2 request
- [x] 8.4 Profile detail: dimensions tab with DXF vs Extral validation
- [x] 8.5 Similarity view: compare two candidates' scores side by side

## 9. Batch validation and documentation

- [x] 9.1 Run `import-dxf` on `data/die/rysunki/` — document per-file report (success/warnings)
- [x] 9.2 README section: DXF pipeline, supported drawing conventions, PDF not supported
- [x] 9.3 Record open questions resolution status in design.md as samples grow

## 10. Stage 2 completion and acceptance

- [x] 10.1 End-to-end test: DXF upload → Stage 1 → Stage 2 with wall thickness filter
- [x] 10.2 Acceptance: 5 sample files process without error; dimension validation passes for E02004, E08594
- [x] 10.3 Acceptance: UI shows breakdown distinguishing shape vs dimension match on test case
- [ ] 10.4 Archive change and sync specs to `openspec/specs/matrix-advisor/004-*` after review
