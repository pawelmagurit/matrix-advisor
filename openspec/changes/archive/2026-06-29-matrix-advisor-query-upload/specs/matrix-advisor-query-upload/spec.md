## ADDED Requirements

### Requirement: Ephemeral upload query

The system SHALL accept an uploaded pictogram image and run similarity search against the existing production index **without** persisting a new Profile, Matrix, or index entry.

#### Scenario: Successful upload query

- **WHEN** client sends `POST /api/v1/query/by-image` with a valid GIF, PNG, or JPEG file (max 5 MB)
- **THEN** the system SHALL return ranked similar historical profiles with their matrix history and a recommendation note
- **AND** no row SHALL be inserted into `profiles` or `pictogram_assets`

#### Scenario: Invalid file type

- **WHEN** client uploads a file that is not GIF, PNG, or JPEG
- **THEN** the system SHALL respond with HTTP 400 and a clear error message

#### Scenario: Unreadable pictogram

- **WHEN** the uploaded file cannot be decoded or normalized to a contour mask
- **THEN** the system SHALL respond with HTTP 422 explaining that the pictogram could not be processed

### Requirement: Query methods parity

Upload query SHALL support the same similarity methods as profile advisory: `geometric` and `embedding`, selectable via request parameter.

#### Scenario: Embedding method default

- **WHEN** `method` is omitted on upload query
- **THEN** the system SHALL use `embedding` as the default method

#### Scenario: Geometric method

- **WHEN** `method=geometric` is specified
- **THEN** the system SHALL rank candidates using the pre-built geometric index and weighted L2 distance

### Requirement: Response shape

Upload query response SHALL match the advisory response structure so the UI can reuse result components.

#### Scenario: Response fields

- **WHEN** upload query succeeds
- **THEN** response SHALL include `query_display_name` (optional user label or `"Nowe zamówienie"`), `method`, `similar[]` with `profile_id`, `display_name`, `rank`, `score`, `matrices[]`, and `recommendation_note`

#### Scenario: Preview pictogram

- **WHEN** upload query succeeds
- **THEN** response SHALL include a `query_preview` field with base64 or a temporary preview URL for the normalized query pictogram

### Requirement: New order UI workflow

The web UI SHALL provide a **„Nowe zamówienie”** view for technologists evaluating a new customer order.

#### Scenario: Drag and drop upload

- **WHEN** user drops a pictogram file onto the upload zone
- **THEN** the UI SHALL show a preview and automatically run similarity search (or enable a „Szukaj podobnych” button)

#### Scenario: Results with history

- **WHEN** similar profiles are returned
- **THEN** the UI SHALL display side-by-side: uploaded pictogram, top similar profiles with pictograms, matrix suppliers, and effectiveness badges

#### Scenario: Optional order label

- **WHEN** user enters an optional label (e.g. offer number or customer name)
- **THEN** the label SHALL appear in the results header only for the current session and SHALL NOT be stored server-side

### Requirement: Index prerequisite

Upload query SHALL require a built similarity index; it SHALL NOT trigger bootstrap or index rebuild.

#### Scenario: Missing index

- **WHEN** index files are absent
- **THEN** the system SHALL respond with HTTP 503 and instruct to run `bootstrap-extral` / `build-index` offline

### Requirement: Automated tests

The system SHALL include automated tests for upload query using a sample pictogram file.

#### Scenario: API test with fixture

- **WHEN** pytest runs with a loaded index
- **THEN** `POST /api/v1/query/by-image` with a test GIF SHALL return at least one similar profile with valid scores
