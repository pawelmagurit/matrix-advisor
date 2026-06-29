## Context

Change **`cut-planner-demo`** delivered a working browser demo in `tools/cut-planner-demo/`. During explore mode we analyzed Extral screenshots (`screenshots/bpsc.jpg`, `historia_zlecen.jpg`, `matryce.jpg`) showing their **EXD web layer** on Impuls data. Key mismatches vs current demo:

| Observed in EXD | Current demo |
|-----------------|--------------|
| Ciąg ~44,2 m (wlewki) | Wiązka 36 m |
| Matryca `E06335-4`, `E10217-24` | Profil `E-08421` |
| kg/m ~5,96–6,05 | 1,2 kg/m |
| Długości 5000/6000/7000 | 3000–7200 |
| Kontrahent REYNAERS B | brak |
| Panel matrycy + rysunek | brak |

This change updates **presentation and sample data only** — cutting algorithm, baseline, metrics, and ROI formulas stay unchanged.

## Goals / Non-Goals

**Goals:**
- Sample data and labels that Extral staff recognize from EXD/Impuls
- Optional `contractor` / `matrixCode` on orders; readonly `MatrixInfo` panel
- CSV import/export compatible with extended columns
- Dark industrial header / tab styling inspired by EXD screenshots
- Tests and README updated for new defaults

**Non-Goals:**
- Impuls / EXD API integration
- Piętka (press butt waste), wlewki, furnace/puller parameters
- Matrix lifecycle charts, GM history, press scheduling
- Full EXD visual clone or proprietary BPSC assets
- Algorithm changes (FFD/BFD/waste-aware unchanged)

## Decisions

### 1. Sample dataset v2 (from screenshots)

**Choice:** Replace `extral-sample.ts` with values grounded in `historia_zlecen.jpg` and `matryce.jpg`:

```typescript
// Config
stockLengthMm: 44_200   // Dł. ciągu 44,2 m
kgPerMeter: 5.958       // Masa rzeczywista (matryce.jpg uses 5958 g/m)
profileCode: 'E06335-4' // matrix doubles as profile id in demo session

// MatrixInfo (readonly)
matrixCode: 'E06335-4'
theoreticalKgPerMeter: 6.051
actualKgPerMeter: 5.958
dieType: 'Komorowa'
cavityCount: 1
pressCode: 'PR-7.1'

// Orders — mix of 5000/6000/7000 mm, contractor REYNAERS B
```

**Rationale:** Concrete numbers from client screens beat negotiated ranges (30–54 m) for demo credibility. 44,2 m is within that range.

**Alternatives:** Keep 36 m and only relabel — rejected; ROI kg numbers would still look wrong.

### 2. profileCode vs matrixCode

**Choice:** Keep `profileCode` as session key for optimization (single profile per session). Add optional `matrixCode` on each `OrderLine`; in sample, both equal `E06335-4`. UI shows **Matryca** column from `matrixCode ?? profileCode`.

**Rationale:** Avoid breaking `optimize.ts` filter on `profileCode`. Real EXD distinguishes matrix from commercial version codes — we defer `commercialVersion` field.

### 3. Matrix panel placement

**Choice:** Show `MatrixPanel` on **Parametry** tab (sidebar or top card), not a new route. Include SVG/placeholder box for "Rysunek techniczny".

**Rationale:** Matches EXD pattern (matrix context near process params) without new navigation complexity.

### 4. EXD-like styling (minimal)

**Choice:** Tailwind updates only:
- Header: `bg-slate-800` / `bg-[#1a2332]` with white text
- Tabs: underline or pill style similar to EXD bottom tabs
- No new CSS framework

**Alternatives:** Separate theme file — overkill for demo delta.

### 5. CSV backward compatibility

**Choice:** Existing CSVs without `contractor`/`matrixCode` still parse. New columns optional. Export includes new columns when present.

### 6. localStorage migration

**Choice:** No automatic migration. Loading sample overwrites state (existing behavior). Document breaking sample change in README.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Higher kg/m makes PLN numbers look large — client questions math | README notes values from real matrix card; formulas unchanged |
| Matrix panel implies live Impuls data | Empty state + README: sample only, integration v1 |
| Dark header reduces contrast on some components | Spot-check all tabs after theme pass |
| Tests hardcode old 36000 / 1.2 constants | Update test fixtures in same PR |

## Migration Plan

1. Merge change into `tools/cut-planner-demo/` on main branch path
2. Run `npm test` and manual smoke on all tabs
3. Optional: archive `cut-planner-demo` change separately if not yet done

Rollback: revert sample + UI files; no database or API impact.

## Open Questions

- Use exact order IDs from screenshot (partially legible) or synthetic `ZL-201` series? → **Synthetic ZL-2xx with REYNAERS B** unless client provides exports.
- Show press code on orders table or matrix panel only? → **Matrix panel only** (Tier A scope).
