## Context

Matrix Advisor (spec 002) serves 10k+ historical Extral profiles with browse + advisory for **known** `profile_id`. Technologists evaluating **new orders** receive a pictogram (often GIF from Impuls or drawing) and need to know: *czy robiliśmy coś podobnego? u kogo? z jaką skutecznością?*

Existing pipeline already supports normalize → embed → query; upload reuses query-time logic with a **temporary mask** instead of a DB profile.

## Goals / Non-Goals

**Goals:**

- One-shot query from uploaded pictogram against frozen production index
- Reuse advisory response shape and UI patterns
- Ephemeral processing — no DB writes, no index mutation
- Support GIF/PNG/JPEG (Extral exports are mostly GIF)
- Clear UX for „nowe zamówienie” workflow

**Non-Goals:**

- Persisting uploaded profiles to SQLite
- Rebuilding index on upload
- PDF/DXF/DWG upload (future)
- Supplier ranking table (spec 004 — separate change)
- Auth / multi-user audit trail
- Batch upload of many files

## Decisions

### D1: Ephemeral temp files vs in-memory only

**Decision:** Write upload to `data/tmp/queries/{uuid}/` (raw + mask), delete after response or TTL 1h cron-less (delete in `finally` block).

**Rationale:** Reuse existing `normalize_image(path)` and `embed_with_rotations` without large refactor.  
**Alternative:** Pure in-memory OpenCV — cleaner but requires refactoring normalization to accept `np.ndarray`.

### D2: API shape

**Decision:** `POST /api/v1/query/by-image` multipart form:

```
file: UploadFile (required)
method: geometric | embedding (default embedding)
top_k: int (default 8, max 20)
label: str (optional, echo only)
```

**Rationale:** Standard FastAPI pattern; easy from UI `FormData`.

### D3: Query implementation

**Decision:** New `query_by_mask(mask: np.ndarray, method, top_k)` in `index/builder.py` — shared by upload and (later) profile advisory refactor.

For **embedding**: `embed_with_rotations_from_mask(mask)` — 4 rotations, cosine vs `embedding.npz`.  
For **geometric**: `extract_geometric_features_from_mask(mask)` → L2 vs index.

**Rationale:** Today `query_similar(profile_id)` re-loads mask from disk by ID; upload has no ID.

### D4: UI placement

**Decision:** New sidebar item **„Nowe zamówienie”** (icon/upload), between „Podobne profile” and „Moduły”.

**Rationale:** Distinct user intent — not browsing history, not picking from list.

### D5: Torch at runtime

**Decision:** Keep embedding method with ResNet/HOG as today. Upload path uses same encoder.

**Rationale:** Best quality for new shapes. On-prem deploy can optimize later (lookup-only mode).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Upload quality differs from Impuls GIF | Show normalized preview; warn if `quality_flags` non-empty |
| Large file DoS | 5 MB limit, reject early |
| Temp file leak | `try/finally` cleanup per request |
| Poor similarity on sketches vs production pictograms | Document expectation: contour-only, no scale; geometric fallback in UI |
| Upload pictogram rotation unknown | Keep 4-rotation embedding query (same as index build) |

## Migration Plan

No data migration. Deploy = API + UI update. Existing browse/advisory unchanged.

## Open Questions

1. Czy Extral przy nowym zamówieniu dostarcza **zawsze GIF jak z Impuls**, czy też skany/PDF? (na start: raster only)
2. Czy wynik uploadu ma trafić do logu audytowego (kto, kiedy, jaki plik)? — na razie nie
3. Czy pokazywać „najbliższy match poniżej progu” jako „brak podobnych”? — proponowany próg score < 0.5 → ostrzeżenie w UI
