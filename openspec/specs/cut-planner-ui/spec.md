# cut-planner-ui Specification

## Purpose

User-facing interface for the Magurit Cut Planner (moduł Extral): Polish industrial UI, screens (dashboard, orders, parameters, results, comparison), cut bar visualization, matrix panel, and documentation requirements.

## Requirements

### Requirement: Polish industrial UI

The application SHALL use Polish language for all user-facing labels and messages. Visual tone SHALL be industrial and decision-oriented — styled to resemble Extral EXD production screens (dark header bar, tab navigation) without impersonating proprietary BPSC branding.

#### Scenario: Product header

- **WHEN** the application loads
- **THEN** the header SHALL display "Magurit Cut Planner" with a subtitle indicating module for Extral (e.g. "Planer cięcia — moduł Extral")

#### Scenario: EXD-like header styling

- **WHEN** the application loads
- **THEN** the top navigation SHALL use a dark industrial header consistent with EXD screenshot tone (not generic light SaaS chrome)

### Requirement: Dashboard screen

The dashboard SHALL provide a brief module description, a "Wczytaj przykład Extral" button, and CSV upload entry point.

#### Scenario: Load sample from dashboard

- **WHEN** the user clicks "Wczytaj przykład Extral" on the dashboard
- **THEN** the system SHALL load sample data and navigate to or enable the optimization flow

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

### Requirement: Cut bar visualization

The results screen SHALL render each stock bar as a horizontal strip with color-coded segments:
- Order cuts — distinct colors per order ID
- Kerf — narrow marker or gap indication
- Waste (`wasteMm`) — red or distinct waste color
- Remnant on run-out table (`remnantMm`) — **gray area**, visually distinct from waste

#### Scenario: Remnant shown as gray

- **WHEN** a stock bar has `remnantMm` ≥ `minOffcutReusableMm`
- **THEN** the visualization SHALL render that segment in gray with a label indicating reusable remnant / stół biegowy

#### Scenario: Gray remnant not counted as waste in legend

- **WHEN** the legend or tooltip explains segments
- **THEN** the UI SHALL clarify that gray remnants are not remelt waste in v0 (informational — not carried to next session)

### Requirement: Three variant result cards

The results screen SHALL show three cards for `min_waste`, `min_stocks`, and `balanced` variants, each with key metrics and expandable cut bar details.

#### Scenario: Switch between variants

- **WHEN** the user selects a variant card
- **THEN** the detailed cut bar list SHALL update to show that variant's plan

### Requirement: Comparison screen

The comparison screen SHALL display side-by-side or table format: manual baseline (FIFO) vs selected optimized variant, showing waste %, stock count, waste kg, remelt cost PLN, and estimated PLN/year savings.

#### Scenario: Visible improvement over baseline

- **WHEN** the Extral sample dataset is loaded and optimized
- **THEN** the comparison SHALL show a concrete difference in at least one metric (stocks or waste % or remelt PLN) favoring the optimized plan

#### Scenario: Dual ROI view

- **WHEN** the comparison is displayed
- **THEN** the UI SHALL show remelt cost as primary ROI and MAY show external scrap value as secondary informational view

### Requirement: Future module placeholder

The navigation SHALL include a disabled or placeholder menu item: "Optymalizacja wyciągania — wkrótce".

#### Scenario: Placeholder visible

- **WHEN** the user views the main navigation
- **THEN** the extrusion length optimization placeholder SHALL be visible but not actionable

### Requirement: Live browser demo (no PDF in v0)

The primary deliverable SHALL be a live browser demo. PDF or print export SHALL NOT be required in v0.

#### Scenario: Demo runs in browser only

- **WHEN** the user opens the application in a modern browser
- **THEN** all core flows (load sample, optimize, compare, visualize) SHALL work without a backend or PDF generator

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

### Requirement: README documentation

The project README SHALL document: how to run locally, CSV format (including optional `contractor`, `matrixCode`), metric definitions, gray remnant semantics, annual ROI formula, EXD-realistic sample data sources (`screenshots/`), and explicit list of what the demo does NOT do (no Impuls integration, no PDF v0, no cross-day remnant inventory, no press/furnace parameters).

#### Scenario: Non-goals documented

- **WHEN** a developer reads README
- **THEN** they SHALL find a "Czego demo nie robi" section listing out-of-scope items
