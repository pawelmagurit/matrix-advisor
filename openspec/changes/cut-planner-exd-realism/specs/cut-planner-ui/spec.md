## MODIFIED Requirements

### Requirement: Polish industrial UI

The application SHALL use Polish language for all user-facing labels and messages. Visual tone SHALL be industrial and decision-oriented — styled to resemble Extral EXD production screens (dark header bar, tab navigation) without impersonating proprietary BPSC branding.

#### Scenario: Product header

- **WHEN** the application loads
- **THEN** the header SHALL display "Magurit Cut Planner" with a subtitle indicating module for Extral (e.g. "Planer cięcia — moduł Extral")

#### Scenario: EXD-like header styling

- **WHEN** the application loads
- **THEN** the top navigation SHALL use a dark industrial header consistent with EXD screenshot tone (not generic light SaaS chrome)

### Requirement: Orders screen

The orders screen SHALL display an editable table with columns: order ID, matrix code (when present), contractor (when present), alloy, length (mm), quantity, and optional tolerance fields. Profile code MAY be shown when it differs from matrix context.

#### Scenario: Edit order inline

- **WHEN** the user changes quantity or length in the table
- **THEN** the updated values SHALL be used on the next optimization run

#### Scenario: Matrix and contractor visible

- **WHEN** sample data with `matrixCode` and `contractor` is loaded
- **THEN** the orders table SHALL display those columns populated from order lines

### Requirement: Parameters screen

The parameters screen SHALL allow editing: stock length labeled **Dł. ciągu [m]** (ciąg z naciągarki / wiązka na piłę), kerf, kg/m, min offcut reusable, remelt cost per kg, burn-off percent, and sessions per month (for annual ROI). A read-only hint SHALL explain that ciąg corresponds to "Dł. ciągu" from EXD wlewki view (~44 m).

#### Scenario: Persist parameters in localStorage

- **WHEN** the user changes session parameters
- **THEN** the system SHALL persist config to localStorage and restore on next visit

#### Scenario: Ciąg length label

- **WHEN** the user views the parameters screen
- **THEN** the stock length field SHALL be labeled "Dł. ciągu [m]" with mm value editable and optional m display

### Requirement: README documentation

The project README SHALL document: how to run locally, CSV format (including optional `contractor`, `matrixCode`), metric definitions, gray remnant semantics, annual ROI formula, EXD-realistic sample data sources (`screenshots/`), and explicit list of what the demo does NOT do (no Impuls integration, no PDF v0, no cross-day remnant inventory, no press/furnace parameters).

#### Scenario: Non-goals documented

- **WHEN** a developer reads README
- **THEN** they SHALL find a "Czego demo nie robi" section listing out-of-scope items

## ADDED Requirements

### Requirement: Matrix panel (readonly)

The application SHALL display a readonly **Matryca** panel when matrix metadata is available for the session, showing: matrix code, theoretical and actual kg/m, die type, cavity count, press code, and a placeholder area for technical drawing (pictogram).

#### Scenario: Matrix panel on sample load

- **WHEN** the user loads the EXD-realistic sample
- **THEN** the UI SHALL show the Matryca panel with values from `MatrixInfo` for `E06335-4`

#### Scenario: Matrix panel without metadata

- **WHEN** the user imports CSV without matrix metadata and no sample matrix is attached
- **THEN** the Matryca panel SHALL be hidden or show an empty state explaining that matrix data comes from sample or future Impuls integration

### Requirement: Profile pictogram placeholder

The application SHALL show a placeholder pictogram area (cross-section silhouette or "Rysunek techniczny" label) adjacent to or within the matrix panel, matching the EXD layout pattern where profile geometry appears beside production data.

#### Scenario: Pictogram visible with sample

- **WHEN** the EXD-realistic sample is loaded
- **THEN** the UI SHALL display a non-interactive profile pictogram placeholder labeled "Rysunek techniczny"
