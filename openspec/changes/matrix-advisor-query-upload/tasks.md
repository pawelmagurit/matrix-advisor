## 1. Backend — mask-based query

- [x] 1.1 Refactor `embed_with_rotations` / `extract_geometric_features` to accept mask array (not only `profile_id`)
- [x] 1.2 Add `query_similar_by_mask(mask, method, top_k)` in `index/builder.py`
- [x] 1.3 Add `query/upload_service.py` — save temp file, normalize, query, cleanup, build advisory response
- [x] 1.4 Add `POST /api/v1/query/by-image` (multipart, validation, 5 MB limit)
- [x] 1.5 Extend CORS / methods to allow POST

## 2. Frontend — Nowe zamówienie

- [x] 2.1 Add `fetchQueryByImage` in `web/src/lib/api.ts`
- [x] 2.2 Create `NewOrderView.tsx` — dropzone, preview, optional label, method selector
- [x] 2.3 Reuse result cards from `SimilarityView` for similar profiles + matrices
- [x] 2.4 Add nav item „Nowe zamówienie” in `Layout.tsx` and route in `App.tsx`
- [x] 2.5 Low-similarity warning when top score < 0.5

## 3. Tests & docs

- [x] 3.1 Add test fixture GIF + `test_query_by_image.py`
- [x] 3.2 Update README with upload workflow
- [x] 3.3 Manual checklist row for upload in UI checklist table
