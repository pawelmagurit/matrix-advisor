# Delta — matrix-advisor-extral-integration-ui

**Base spec:** `openspec/specs/matrix-advisor/002-extral-integration-ui/spec.md`  
**Change:** `matrix-advisor-dxf-pipeline`

---

## ADDED Requirements

### Requirement: DXF-first new order UI

The **„Nowe zamówienie”** view SHALL prioritize DXF upload as the primary input method for new customer profiles.

#### Scenario: DXF upload zone

- **WHEN** user opens „Nowe zamówienie”
- **THEN** the UI SHALL show DXF as the recommended upload format with accepted extension `.dxf`
- **AND** SHALL offer secondary option for GIF/PNG/JPEG (legacy)

#### Scenario: Extracted dimensions display

- **WHEN** DXF upload returns extracted dimensions
- **THEN** the UI SHALL display key values (width, height, wall thickness, OCD) before or alongside search results

### Requirement: Two-stage search UI controls

The UI SHALL support Stage 1 results and optional Stage 2 filtering without requiring a separate page navigation.

#### Scenario: Stage 1 results list

- **WHEN** initial search completes
- **THEN** the UI SHALL show top N results with shape score, pictogram preview, and key dimensions per profile

#### Scenario: Advanced dimensional filters

- **WHEN** user opens advanced filters panel
- **THEN** the UI SHALL allow filtering by at minimum: width, height, wall thickness, hole/cavity count
- **AND** SHALL re-run or apply Stage 2 reranking on current results

### Requirement: Score breakdown display

Result list items SHALL expose why a profile was ranked as it was.

#### Scenario: Breakdown visible

- **WHEN** Stage 2 results are shown
- **THEN** each result SHALL display `total_score` and expandable or summarized `score_breakdown` (shape, outer, inner, dimension, metadata)

#### Scenario: Match type indicators

- **WHEN** a result has high shape score but low dimension score
- **THEN** the UI SHALL visually distinguish „shape match” from „dimension match” (badge or label)

### Requirement: Profile dimension inspection

Profile detail view SHALL show DXF-derived dimensions and validation against Extral metadata when available.

#### Scenario: Dimensions tab

- **WHEN** user views profile detail for a profile with DXF processing
- **THEN** the UI SHALL show DXF values, Extral values, and validation status per field

#### Scenario: GIF-only profile

- **WHEN** profile has no DXF asset
- **THEN** dimensions tab SHALL show Extral `wlasnosci` only with note „brak DXF”

### Requirement: Similarity search view updates

The similarity search view SHALL support selecting an existing profile or referencing upload query results with stage and filter controls consistent with „Nowe zamówienie”.

#### Scenario: Compare scores

- **WHEN** multiple similar profiles are listed
- **THEN** user SHALL be able to compare total score and breakdown across at least two candidates side by side (table or cards)

---

## MODIFIED Requirements

### Requirement: Matrix Advisor web UI

The system SHALL provide a dedicated UI module with views: profile browser, **new order (DXF-first upload)**, similarity search with Stage 2 filters, modules overview.

#### Scenario: Filter and inspect

- **WHEN** a user filters by supplier and selects a profile
- **THEN** the UI SHALL show pictogram, matrix history, effectiveness badges, and dimension/validation data when available
