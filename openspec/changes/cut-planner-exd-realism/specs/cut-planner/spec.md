## MODIFIED Requirements

### Requirement: Order line model

The system SHALL represent cutting orders as `OrderLine` records with fields: `orderId`, `profileCode`, `alloy`, `lengthMm`, `quantity`, optional `tolerancePlusMm` (default 10), `toleranceMinusMm` (default 0), optional `priority`, optional `contractor` (customer name as in EXD), and optional `matrixCode` (die ID in format `E#####-##`, e.g. `E06335-4`).

#### Scenario: Single profile per optimization session

- **WHEN** the user runs optimization
- **THEN** the system SHALL include only order lines sharing the same `profileCode` in one cutting problem

#### Scenario: Matrix code on order line

- **WHEN** an order line includes `matrixCode` `E06335-4`
- **THEN** the system SHALL preserve and display that value without requiring it for optimization math

### Requirement: Extral sample dataset

The system SHALL ship a built-in sample dataset aligned with Extral EXD screenshots: matrix `E06335-4`, alloy `6060`, `kgPerMeter` approximately 5.958 (actual mass from matrix card), `stockLengthMm` 44200 (ciąg ~44.2 m from wlewki view), kerf 4 mm, `minOffcutReusableMm` 200 mm, contractor `REYNAERS B`, with order lines using commercial lengths 5000, 6000, and 7000 mm as visible in production history.

#### Scenario: One-click sample load

- **WHEN** the user clicks "Wczytaj przykład Extral"
- **THEN** the system SHALL populate orders and config with the EXD-realistic sample dataset

#### Scenario: Sample uses ciąg length from EXD

- **WHEN** the sample config is loaded
- **THEN** `stockLengthMm` SHALL be 44200 and the parameters UI SHALL label it as długość ciągu (wiązka z naciągarki)

### Requirement: CSV import

The system SHALL accept CSV upload mapping to `OrderLine` fields. Required columns: `orderId`, `profileCode`, `alloy`, `lengthMm`, `quantity`. Optional columns: `tolerancePlusMm`, `toleranceMinusMm`, `priority`, `contractor`, `matrixCode`.

#### Scenario: CSV populates order table

- **WHEN** the user uploads a valid CSV file
- **THEN** the system SHALL replace or append order lines according to UI behavior and display them in the orders table

#### Scenario: CSV with contractor and matrix

- **WHEN** the user uploads a CSV containing `contractor` and `matrixCode` columns
- **THEN** the system SHALL map those values onto the corresponding order line fields

## ADDED Requirements

### Requirement: Matrix metadata for sample session

The system SHALL provide optional `MatrixInfo` for the active sample session with fields: `matrixCode`, `theoreticalKgPerMeter`, `actualKgPerMeter`, `dieType` (e.g. Komorowa), `cavityCount`, `pressCode` (e.g. PR-7.1). This data SHALL be informational only and SHALL NOT affect cutting optimization.

#### Scenario: Sample includes matrix metadata

- **WHEN** the EXD-realistic sample is loaded
- **THEN** the system SHALL attach `MatrixInfo` for matrix `E06335-4` with `actualKgPerMeter` matching the sample `kgPerMeter`
