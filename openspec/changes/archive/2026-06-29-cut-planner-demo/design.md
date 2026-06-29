## Context

Extral operates an aluminum extrusion plant (Żory). Production flow: extrusion → cooling → stretching → **final saw cutting** → aging. Operators manually plan cuts at the saw — remnant on the run-out table, next stock bar, cut layout — with a one-day horizon and no optimizer. ERP is BPSC Impuls; a web layer (PSAW-like) exposes reports but cannot extend Impuls with advisory logic. The technologist referenced historical **Impex** MES as the desired pattern: suggest options, optimize material use.

This change delivers a **browser-only demo** (`tools/cut-planner-demo/`) to sell the conversation — not production deployment. Source prompt: `openspec/specs/prompt-demo-optymalizacja-ciecia.md`. Explore decisions captured here:
- Remnants ≥ threshold → **gray area** in UI (informational; v0 does not carry inventory across sessions)
- Annual ROI → `(baseline − optimized) remelt cost × 12` (user-adjustable sessions/month)
- Manual baseline → **FIFO**, no cross-order combining
- Delivery → **live browser demo**; PDF export deferred

Repo is greenfield (no existing app stack).

## Goals / Non-Goals

**Goals:**
- End-to-end demo: sample data → optimize (3 variants) → visualize → compare vs FIFO baseline
- Correct cutting-stock math with kerf, waste/remnant split, remelt ROI
- Polish UI, industrial tone, < 1 s on sample dataset
- Algorithm covered by unit tests before UI
- JSON export; localStorage persistence
- Clear README with non-goals

**Non-Goals:**
- Impuls / PSAW / PLC integration
- PDF / print export (v1)
- Extrusion length optimization (menu placeholder only)
- Multi-profile sessions, auth, multi-tenant, backend
- Cross-day remnant inventory on run-out table (v1)
- Matrix/shape constraints on max extrusion length

## Decisions

### 1. Stack: Vite + React + TypeScript + Tailwind

**Choice:** Vite SPA in `tools/cut-planner-demo/`.

**Rationale:** Fast scaffold, no backend needed, Vitest integrates cleanly. Next.js adds SSR complexity with no benefit for offline demo.

**Alternatives:** Next.js (heavier), plain HTML+JS (harder to maintain visualization components).

### 2. Algorithm: FFD/BFD heuristics first

**Choice:** Implement FFD and BFD; pick best result per variant objective. Optional ILP only if heuristics fail acceptance on sample data.

**Rationale:** 50 pieces on sample data — heuristics are sufficient and testable. ILP adds dependency (`javascript-lp-solver` or similar) without guaranteed demo win.

**Variant objectives:**
| Variant | Primary objective | Tie-break |
|---------|-------------------|-----------|
| `min_waste` | Minimize `wasteMm` (remnants ≥ threshold excluded from waste) | Fewer stocks |
| `min_stocks` | Minimize stock count | Less waste |
| `balanced` | `0.5 * norm(waste) + 0.5 * norm(stocks)` | — |

### 3. Baseline: FIFO without cross-order packing

**Choice:** Process order lines in table order. For each line, pack pieces sequentially onto current bar; open new bar when piece doesn't fit. Do not backfill with pieces from other orders.

**Rationale:** Matches "operator handles one order at a time" mental model from site visit; produces visibly worse plan than optimizer (demo narrative).

### 4. Remnant visualization: gray, non-persistent

**Choice:** `remnantMm` rendered as gray segment labeled "Resztka (stół biegowy)". Tooltip: *v0 nie kumuluje resztek między sesjami*.

**Rationale:** Acknowledges real process without implementing inventory state machine in v0.

**Color scheme (Tailwind):**
- Order cuts: hue by `orderId` hash
- Kerf: dark thin gap
- Waste: `red-500`
- Remnant: `gray-400` with dashed border optional

### 5. ROI model

**Choice:**
```
wasteKg = totalWasteMm / 1000 * kgPerMeter
effectiveKg = wasteKg * (1 + burnOffPercent/100)
remeltCostPln = effectiveKg * remeltCostPerKg
annualSavings = (baselineRemelt - optimizedRemelt) * sessionsPerMonth * 12 / sessionsPerMonth
             = (baselineRemelt - optimizedRemelt) * 12   // when sessionsPerMonth default 1
```
UI exposes `sessionsPerMonth` (default 1) → annual = monthly delta × 12.

Show secondary tab: external scrap value (informational) using a configurable scrap price per kg.

### 6. Module layout

```
tools/cut-planner-demo/
├── src/
│   ├── lib/cutting/
│   │   ├── types.ts
│   │   ├── expand.ts          # OrderLine → pieces
│   │   ├── pack.ts            # FFD/BFD
│   │   ├── baseline.ts        # FIFO manual
│   │   ├── metrics.ts         # waste, kg, PLN
│   │   └── optimize.ts        # 3 variants orchestrator
│   ├── data/extral-sample.ts
│   ├── components/
│   │   ├── CutBar.tsx         # strip visualization
│   │   ├── VariantCard.tsx
│   │   ├── ComparisonTable.tsx
│   │   └── OrdersTable.tsx
│   ├── pages/ or routes/      # Dashboard, Orders, Params, Results, Compare
│   └── App.tsx
├── tests/cutting/*.test.ts
├── README.md
└── package.json
```

### 7. State management

**Choice:** React `useState` + `localStorage` sync for config and orders. No Redux.

### 8. CSV format

Minimal columns: `orderId,profileCode,alloy,lengthMm,quantity`. Optional: `tolerancePlusMm,toleranceMinusMm,priority`. Use `csv-parse` in browser via FileReader.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Heuristic suboptimal on edge cases | Unit tests on sample + known small instances; document "demo-grade" in README |
| Gray remnant confuses users (looks like waste) | Legend + tooltip explaining reusable vs remelt |
| FIFO baseline too weak or too strong | Validate on sample — must show clear win for optimizer |
| No PDF for first client meeting | Live browser demo is primary; JSON export as fallback artifact |
| Tolerance ignored in cuts | Document as v0 simplification; show tolerance in order table info-only |

## Migration Plan

Greenfield — no migration. Deploy demo via `npm run dev` locally or static build to any host (Vercel/Netlify) if needed for client URL.

Rollback: N/A (new folder, no production system affected).

## Open Questions

- Exact scrap price default for secondary ROI view (suggest 4–6 PLN/kg informational)?
- Should `min_stocks` variant allow sacrificing remnant reuse scoring differently? (defer — use same remnant/waste split rules)
