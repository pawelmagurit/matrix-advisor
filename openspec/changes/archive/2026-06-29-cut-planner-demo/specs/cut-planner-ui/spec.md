## ADDED Requirements

### Requirement: Polish industrial UI

The application SHALL use Polish language for all user-facing labels and messages. Visual tone SHALL be industrial and decision-oriented — no AI-hype branding.

#### Scenario: Product header

- **WHEN** the application loads
- **THEN** the header SHALL display "Magurit Cut Planner" or "Planer cięcia — moduł Extral"

### Requirement: Dashboard screen

The dashboard SHALL provide a brief module description, a "Wczytaj przykład Extral" button, and CSV upload entry point.

#### Scenario: Load sample from dashboard

- **WHEN** the user clicks "Wczytaj przykład Extral" on the dashboard
- **THEN** the system SHALL load sample data and navigate to or enable the optimization flow

### Requirement: Orders screen

The orders screen SHALL display an editable table with columns: order ID, profile code, alloy, length (mm), quantity, and optional tolerance fields.

#### Scenario: Edit order inline

- **WHEN** the user changes quantity or length in the table
- **THEN** the updated values SHALL be used on the next optimization run

### Requirement: Parameters screen

The parameters screen SHALL allow editing: stock length, kerf, kg/m, min offcut reusable, remelt cost per kg, burn-off percent, and sessions per month (for annual ROI).

#### Scenario: Persist parameters in localStorage

- **WHEN** the user changes session parameters
- **THEN** the system SHALL persist config to localStorage and restore on next visit

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

### Requirement: README documentation

The project README SHALL document: how to run locally, CSV format, metric definitions, gray remnant semantics, annual ROI formula, and explicit list of what the demo does NOT do (no Impuls integration, no PDF v0, no cross-day remnant inventory).

#### Scenario: Non-goals documented

- **WHEN** a developer reads README
- **THEN** they SHALL find a "Czego demo nie robi" section listing out-of-scope items
