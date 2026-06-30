# matrix-advisor-multi-criteria-scoring — Multi-Criteria Similarity

**Status:** Proposed  
**Capability:** `matrix-advisor`  
**Depends on:** `matrix-advisor-dxf-pipeline`  
**Blocks:** `matrix-advisor-two-stage-search`

## Purpose

Similarity SHALL NOT be a single opaque score. The system SHALL combine ML shape embeddings with deterministic geometric features and metadata into a **weighted multi-dimensional score** with transparent breakdown — enabling distinction between profiles that look similar but differ in internal channels, cavities, wall thickness, or key dimensions.

---

## ADDED Requirements

### Requirement: Multiple similarity dimensions

The scoring model SHALL support the following dimensions, each producing a normalized score in range 0.0–1.0:

| Dimension | Description |
|-----------|-------------|
| `shape_embedding` | Overall visual shape similarity (ResNet18 cosine) |
| `outer_contour` | Outer boundary similarity |
| `inner_detail` | Internal cavities, channels, grooves |
| `dimension` | Width, height, wall, OCD similarity |
| `metadata` | Extral technical metadata match when available |

#### Scenario: Breakdown in response

- **WHEN** Stage 2 search returns results
- **THEN** each candidate SHALL include `score_breakdown` object with all computed dimension scores

#### Scenario: Total score aggregation

- **WHEN** `total_score` is computed
- **THEN** it SHALL equal the weighted sum of dimension scores using configured weights

### Requirement: Weighted scoring configuration

The system SHALL combine dimension scores using configurable weights.

Default MVP weights SHALL be:

- `shape_embedding`: 0.40
- `outer_contour`: 0.15
- `inner_detail`: 0.20
- `dimension`: 0.20
- `metadata`: 0.05

#### Scenario: Hardcoded MVP weights

- **WHEN** scoring runs in MVP
- **THEN** weights SHALL be loaded from application config and documented in design

#### Scenario: Future configurable weights

- **WHEN** scoring module is initialized
- **THEN** weight source SHALL be abstracted (e.g. `ScoringConfig`) so user-adjustable weights can be added without changing scorer interface

### Requirement: Shape embedding dimension

The `shape_embedding` score SHALL be derived from the existing embedding index cosine similarity.

#### Scenario: Embedding score mapping

- **WHEN** cosine similarity between query and candidate is `0.85`
- **THEN** `shape_embedding` score in breakdown SHALL be `0.85` (or documented linear mapping)

### Requirement: Outer contour dimension

The `outer_contour` score SHALL compare outer boundary features independently of internal detail.

#### Scenario: Outer contour features

- **WHEN** outer contour score is computed
- **THEN** it SHALL use at minimum Hu moments and/or outer mask IoU between query and candidate

### Requirement: Inner detail dimension

The `inner_detail` score SHALL distinguish profiles with different internal structure.

#### Scenario: Different hole counts penalized

- **WHEN** query has `hole_count=1` and candidate has `hole_count=3` with otherwise similar outer shape
- **THEN** `inner_detail` score SHALL be lower than when `hole_count` matches

#### Scenario: Channel presence

- **WHEN** internal groove/channel detection flags differ between query and candidate
- **THEN** `inner_detail` score SHALL reflect the mismatch

### Requirement: Dimension similarity dimension

The `dimension` score SHALL compare numeric technical dimensions when available for both query and candidate.

Compared fields SHALL include at minimum: `width_mm`, `height_mm`, `wall_thickness_mm`, `ocd_mm`.

#### Scenario: Normalized L1 distance

- **WHEN** query `ocd_mm=25` and candidate `ocd_mm=26`
- **THEN** dimension score SHALL be higher than when candidate `ocd_mm=40`

#### Scenario: Missing dimensions on candidate

- **WHEN** candidate lacks DXF dimensions
- **THEN** `dimension` score SHALL be `null` in breakdown and weight SHALL be redistributed or ignored per documented policy

### Requirement: Metadata similarity dimension

The `metadata` score SHALL compare Extral `wlasnosci` fields when query dimensions were mapped to the same semantic fields.

#### Scenario: Metadata match indicators

- **WHEN** results are returned
- **THEN** each candidate MAY include `metadata_match` map with per-field status: `ok`, `mismatch`, `unknown`

### Requirement: Embeddings plus deterministic features

ML embeddings and deterministic features SHALL be computed and stored separately.

#### Scenario: Independent feature paths

- **WHEN** a profile is processed from DXF
- **THEN** embedding vector and deterministic feature record SHALL both be persisted without merging into a single opaque blob

#### Scenario: Different questions answered

- **WHEN** a technologist inspects results
- **THEN** UI SHALL allow distinguishing "shape match" from "dimension match" using breakdown fields

### Requirement: Scoring extensibility

The scoring registry SHALL allow registering additional feature extractors and score dimensions without changing Stage 1 search interface.

#### Scenario: New dimension hook

- **WHEN** a new scorer module is registered under a string key
- **THEN** Stage 2 reranking SHALL include it in breakdown if weight > 0

### Requirement: Automated scoring tests

The system SHALL include unit tests for score aggregation and inner-detail discrimination.

#### Scenario: Weight sum

- **WHEN** all dimension scores are `1.0`
- **THEN** `total_score` SHALL equal `1.0`

#### Scenario: Inner detail test case

- **WHEN** two synthetic masks differ only in internal hole count
- **THEN** `inner_detail` score SHALL be lower than `shape_embedding` score when outer contour is identical
