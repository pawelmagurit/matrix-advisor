# 003 — Query by Upload (Nowe zamówienie)

**Status:** Proposed (2026-06-19)  
**Capability:** `matrix-advisor`  
**Depends on:** `002-extral-integration-ui`  
**Blocks:** `004-supplier-ranking`

## Purpose

Enable technologists to evaluate a **new customer order** by uploading a profile pictogram and instantly searching historical production for similar shapes — with matrix history, suppliers, and effectiveness — **without adding the profile to the database**.

## User story

> Jako technolog Extral, przy nowym zamówieniu wrzucam piktogram profilu i chcę zobaczyć, czy robiliśmy coś podobnego, u którego dostawcy i z jaką skutecznością — zanim zamówię matrycę.

## Scope

| In scope | Out of scope |
|----------|--------------|
| Upload GIF/PNG/JPEG (max 5 MB) | PDF/DXF/DWG |
| Ephemeral query vs frozen index | Persist upload to SQLite |
| UI „Nowe zamówienie” | Supplier ranking table (004) |
| geometric + embedding methods | Index rebuild on upload |
| Preview znormalizowanego konturu | Audit log / auth |

## API

```
POST /api/v1/query/by-image
Content-Type: multipart/form-data

file       (required) — pictogram
method     embedding | geometric  (default: embedding)
top_k      1–20  (default: 8)
label      optional string — echoed in response only
```

Response: same shape as `GET /profiles/{id}/advisory` plus `query_preview`.

## Requirements

See change delta: `openspec/changes/matrix-advisor-query-upload/specs/matrix-advisor-query-upload/spec.md`

## Implementation plan

Change: `openspec/changes/matrix-advisor-query-upload/` (proposal, design, tasks)

## Acceptance criteria

1. Upload GIF from Extral export → ≥1 similar profile with matrices
2. No new rows in `profiles` after upload query
3. UI flow: drop file → preview → results in <10s (embedding, CPU)
4. pytest covers upload endpoint with fixture
