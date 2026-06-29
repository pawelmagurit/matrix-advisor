# cut-planner Specification

## Purpose

Core cutting-stock optimization engine for the Magurit Cut Planner (moduł Extral): data model, piece expansion and kerf accounting, waste/remnant classification, optimization variants, manual baseline, plan metrics, annual ROI projection, sample dataset, and CSV/JSON I/O.

## Requirements

### Requirement: Order line model

The system SHALL represent cutting orders as `OrderLine` records with fields: `orderId`, `profileCode`, `alloy`, `lengthMm`, `quantity`, optional `tolerancePlusMm` (default 10), `toleranceMinusMm` (default 0), optional `priority`, optional `contractor` (customer name as in EXD), and optional `matrixCode` (die ID in format `E#####-##`, e.g. `E06335-4`).

#### Scenario: Single profile per optimization session

- **WHEN** the user runs optimization
- **THEN** the system SHALL include only order lines sharing the same `profileCode` in one cutting problem

#### Scenario: Matrix code on order line

- **WHEN** an order line includes `matrixCode` `E06335-4`
- **THEN** the system SHALL preserve and display that value without requiring it for optimization math

### Requirement: Cut session configuration

The system SHALL accept `CutSessionConfig` with: `profileCode`, `stockLengthMm`, `kerfMm`, `minOffcutReusableMm`, optional `kgPerMeter`, `remeltCostPerKg` (default 0.30 PLN/kg), and `burnOffPercent` (default 3%).

#### Scenario: Default remelt economics

- **WHEN** the user does not override remelt parameters
- **THEN** the system SHALL use remelt cost 0.30 PLN/kg and burn-off 3% for ROI calculations

### Requirement: Piece expansion and kerf accounting

The system SHALL expand each order line into individual pieces by `quantity` and compute kerf loss as `(n_cuts - 1) * kerfMm` per stock bar.

#### Scenario: Stock length balance

- **WHEN** a cut plan is generated for a stock bar
- **THEN** the sum of cut lengths plus kerf losses plus remnant plus waste SHALL equal `stockLengthMm`

### Requirement: Waste vs reusable remnant classification

The system SHALL classify the trailing offcut of each stock bar as:
- `remnantMm` — length ≥ `minOffcutReusableMm` (potentially reusable on run-out table)
- `wasteMm` — length < `minOffcutReusableMm` (remelt/scrap)

#### Scenario: Small offcut goes to waste

- **WHEN** a stock bar ends with 150 mm offcut and `minOffcutReusableMm` is 200
- **THEN** the system SHALL record 150 mm as `wasteMm` and 0 mm as `remnantMm`

#### Scenario: Large offcut is remnant

- **WHEN** a stock bar ends with 800 mm offcut and `minOffcutReusableMm` is 200
- **THEN** the system SHALL record 800 mm as `remnantMm` and 0 mm as `wasteMm`

### Requirement: Three optimization variants

The system SHALL produce three cut plan variants from the same input:
- `min_waste` — minimize total `wasteMm` plus non-reusable portion of remnants (remnants ≥ threshold count as reusable, not waste)
- `min_stocks` — minimize number of stock bars used
- `balanced` — minimize weighted score: 50% normalized waste + 50% normalized stock count

#### Scenario: All three variants computed

- **WHEN** the user triggers optimization with valid orders and config
- **THEN** the system SHALL return three distinct `CutPlan` objects labeled `min_waste`, `min_stocks`, and `balanced`

### Requirement: Cutting stock algorithm

The system SHALL implement cutting stock optimization using First-Fit Decreasing (FFD) and/or Best-Fit Decreasing (BFD) heuristics. For order batches with ≤ 30 distinct line types, an optional exact or ILP refinement MAY be applied after heuristics.

#### Scenario: Performance on demo dataset

- **WHEN** the Extral sample dataset (5 order lines, 50 total pieces) is optimized
- **THEN** all three variants SHALL be computed in under 1 second

### Requirement: Manual baseline (FIFO)

The system SHALL compute a manual baseline plan using FIFO strategy: process order lines in input order; for each line, place pieces sequentially on the current stock bar; start a new stock bar when the next piece does not fit; do NOT combine pieces from different order lines onto the same bar unless they happen to fit sequentially within the same line's allocation pass.

#### Scenario: Baseline uses input order

- **WHEN** orders are listed ZL-101, ZL-102, ZL-103 in that order
- **THEN** the baseline SHALL process ZL-101 pieces before ZL-102, and ZL-102 before ZL-103

#### Scenario: Baseline does not cross-combine orders

- **WHEN** baseline planning runs
- **THEN** the system SHALL NOT deliberately merge pieces from different order lines onto one stock bar (unlike optimized plans)

### Requirement: Plan metrics

Each `CutPlan` SHALL include metrics: `totalWasteMm`, `wastePercent`, `stockCount`, optional `totalWasteKg` (when `kgPerMeter` provided), and optional `remeltCostPln`.

#### Scenario: Waste percent calculation

- **WHEN** metrics are computed
- **THEN** `wastePercent` SHALL equal total waste material divided by total stock material used, expressed as percentage

#### Scenario: Remelt cost in PLN

- **WHEN** `kgPerMeter` and `remeltCostPerKg` are provided
- **THEN** the system SHALL compute `remeltCostPln` from waste kg adjusted by `burnOffPercent`

### Requirement: Annual ROI projection

The system SHALL project annual remelt savings as: `(baselineRemeltCostPln - optimizedRemeltCostPln) * annualizationFactor`, where `annualizationFactor` defaults to 12 (monthly session volume extrapolated to year). The user MAY override sessions per month.

#### Scenario: Default annualization

- **WHEN** the user views comparison without changing volume assumptions
- **THEN** the system SHALL display estimated PLN/year savings using factor 12

### Requirement: Extral sample dataset

The system SHALL ship a built-in sample dataset aligned with Extral EXD screenshots: matrix `E06335-4`, alloy `6060`, `kgPerMeter` approximately 5.958 (actual mass from matrix card), `stockLengthMm` 44200 (ciąg ~44.2 m from wlewki view), kerf 4 mm, `minOffcutReusableMm` 200 mm, contractor `REYNAERS B`, with order lines using commercial lengths 5000, 6000, and 7000 mm as visible in production history.

#### Scenario: One-click sample load

- **WHEN** the user clicks "Wczytaj przykład Extral"
- **THEN** the system SHALL populate orders and config with the EXD-realistic sample dataset

#### Scenario: Sample uses ciąg length from EXD

- **WHEN** the sample config is loaded
- **THEN** `stockLengthMm` SHALL be 44200 and the parameters UI SHALL label it as długość ciągu (wiązka z naciągarki)

### Requirement: Matrix metadata for sample session

The system SHALL provide optional `MatrixInfo` for the active sample session with fields: `matrixCode`, `theoreticalKgPerMeter`, `actualKgPerMeter`, `dieType` (e.g. Komorowa), `cavityCount`, `pressCode` (e.g. PR-7.1). This data SHALL be informational only and SHALL NOT affect cutting optimization.

#### Scenario: Sample includes matrix metadata

- **WHEN** the EXD-realistic sample is loaded
- **THEN** the system SHALL attach `MatrixInfo` for matrix `E06335-4` with `actualKgPerMeter` matching the sample `kgPerMeter`

### Requirement: CSV import

The system SHALL accept CSV upload mapping to `OrderLine` fields. Required columns: `orderId`, `profileCode`, `alloy`, `lengthMm`, `quantity`. Optional columns: `tolerancePlusMm`, `toleranceMinusMm`, `priority`, `contractor`, `matrixCode`.

#### Scenario: CSV populates order table

- **WHEN** the user uploads a valid CSV file
- **THEN** the system SHALL replace or append order lines according to UI behavior and display them in the orders table

#### Scenario: CSV with contractor and matrix

- **WHEN** the user uploads a CSV containing `contractor` and `matrixCode` columns
- **THEN** the system SHALL map those values onto the corresponding order line fields

### Requirement: JSON export

The system SHALL allow exporting the selected cut plan as JSON.

#### Scenario: Export plan JSON

- **WHEN** the user requests JSON export for a variant
- **THEN** the system SHALL download a JSON file containing the full `CutPlan` structure
