import { useState } from 'react'
import type { CutPlan, CutSessionConfig, PlanVariant } from '@/lib/cutting/types'
import { computeUnusedMaterial } from '@/lib/cutting/metrics'
import { VARIANT_LABELS } from '@/lib/colors'
import {
  comparePlansToBaseline,
  formatDelta,
  variantPlans,
  type PlanComparisonDeltas,
} from '@/lib/plan-comparison'
import type { OptimizationResult } from '@/lib/cutting/types'
import { CutBar } from './CutBar'
import { StockSavingsBanner } from './StockSavingsBanner'

interface PlanComparisonViewProps {
  baseline: CutPlan
  result: OptimizationResult
  config: CutSessionConfig
  selectedVariant: PlanVariant
  onVariantChange: (variant: PlanVariant) => void
  onExportJson?: (plan: CutPlan) => void
}

function fmtMm(mm: number) {
  return `${mm.toLocaleString('pl-PL')} mm`
}

function MetricsTable({
  baseline,
  optimized,
  config,
  deltas,
}: {
  baseline: CutPlan
  optimized: CutPlan
  config: CutSessionConfig
  deltas: PlanComparisonDeltas
}) {
  const baseU = computeUnusedMaterial(baseline.stocks, config)
  const optU = computeUnusedMaterial(optimized.stocks, config)

  const rows: {
    label: string
    base: string
    opt: string
    delta: string
    highlight?: boolean
  }[] = [
    {
      label: 'Liczba wiązek',
      base: String(baseline.metrics.stockCount),
      opt: String(optimized.metrics.stockCount),
      delta: formatDelta(deltas.stockDelta, '', true),
      highlight: deltas.stockDelta !== 0,
    },
    {
      label: 'Niewykorzystany materiał',
      base: `${fmtMm(baseU.unusedMm)} (${baseU.unusedPercent.toFixed(1)}%)`,
      opt: `${fmtMm(optU.unusedMm)} (${optU.unusedPercent.toFixed(1)}%)`,
      delta:
        deltas.unusedMmDelta === 0
          ? '0'
          : `−${deltas.unusedMmDelta.toLocaleString('pl-PL')} mm ✓`,
      highlight: deltas.unusedMmDelta > 0,
    },
    {
      label: 'w tym odpad do remeltu',
      base: fmtMm(baseU.wasteMm),
      opt: fmtMm(optU.wasteMm),
      delta: formatDelta(deltas.wasteMmDelta, 'mm', true),
      highlight: deltas.wasteMmDelta > 0,
    },
    {
      label: 'w tym resztka (stół biegowy)',
      base: fmtMm(baseU.remnantMm),
      opt: fmtMm(optU.remnantMm),
      delta: formatDelta(deltas.remnantMmDelta, 'mm', true),
      highlight: deltas.remnantMmDelta > 0,
    },
  ]

  if (baseU.unusedKg != null && optU.unusedKg != null) {
    rows.push({
      label: 'Masa niewykorzystana',
      base: `≈ ${baseU.unusedKg.toFixed(1)} kg`,
      opt: `≈ ${optU.unusedKg.toFixed(1)} kg`,
      delta:
        deltas.unusedKgDelta != null && deltas.unusedKgDelta > 0
          ? `−${deltas.unusedKgDelta.toFixed(1)} kg ✓`
          : '0',
      highlight: (deltas.unusedKgDelta ?? 0) > 0,
    })
  }

  if (baseline.metrics.remeltCostPln != null && optimized.metrics.remeltCostPln != null) {
    rows.push({
      label: 'Koszt remeltu',
      base: `${baseline.metrics.remeltCostPln.toFixed(2)} PLN`,
      opt: `${optimized.metrics.remeltCostPln.toFixed(2)} PLN`,
      delta:
        deltas.remeltPlnDelta != null && deltas.remeltPlnDelta > 0
          ? `−${deltas.remeltPlnDelta.toFixed(2)} PLN ✓`
          : '0',
      highlight: (deltas.remeltPlnDelta ?? 0) > 0,
    })
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left">
            <th className="p-3 font-medium text-slate-600">Metryka</th>
            <th className="p-3 font-medium text-slate-600">Standard (kolejność z pliku)</th>
            <th className="p-3 font-medium text-slate-600">Zoptymalizowany</th>
            <th className="p-3 font-medium text-slate-600">Oszczędność</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-b border-slate-100 last:border-0">
              <td className="p-3 text-slate-700">{row.label}</td>
              <td className="p-3 font-mono text-slate-900">{row.base}</td>
              <td className="p-3 font-mono text-slate-900">{row.opt}</td>
              <td
                className={`p-3 font-mono ${
                  row.highlight ? 'font-medium text-emerald-700' : 'text-slate-500'
                }`}
              >
                {row.delta}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function PlanComparisonView({
  baseline,
  result,
  config,
  selectedVariant,
  onVariantChange,
  onExportJson,
}: PlanComparisonViewProps) {
  const optimized =
    result[selectedVariant === 'min_waste' || selectedVariant === 'min_stocks' || selectedVariant === 'balanced'
      ? selectedVariant
      : 'min_waste']

  const deltas = comparePlansToBaseline(baseline, optimized, config)
  const [barView, setBarView] = useState<'baseline' | 'optimized' | 'both'>(
    deltas.identical ? 'optimized' : 'both',
  )

  const variants = variantPlans(result)

  return (
    <div className="space-y-5">
      <div>
        <p className="mb-2 text-sm text-slate-600">
          <strong>Standard</strong> — cięcia w kolejności z CSV, wiązka po wiązce (Next-Fit).{' '}
          <strong>Zoptymalizowany</strong> — ta sama lista zleceń, inna kolejność cięć.
        </p>

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Wariant optymalizacji:
          </span>
          {variants.map(({ key, plan }) => {
            const vDelta = comparePlansToBaseline(baseline, plan, config)
            const badge =
              vDelta.stockDelta > 0
                ? `−${vDelta.stockDelta} wiąz.`
                : vDelta.unusedMmDelta > 0
                  ? `−${(vDelta.unusedMmDelta / 1000).toFixed(1)} m`
                  : null

            return (
              <button
                key={key}
                type="button"
                onClick={() => onVariantChange(key)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                  selectedVariant === key
                    ? 'bg-slate-800 text-white'
                    : 'border border-slate-300 bg-white text-slate-700 hover:border-slate-500'
                }`}
              >
                {VARIANT_LABELS[key] ?? key}
                {badge && (
                  <span
                    className={`ml-1.5 text-xs ${
                      selectedVariant === key ? 'text-emerald-300' : 'text-emerald-600'
                    }`}
                  >
                    {badge}
                  </span>
                )}
              </button>
            )
          })}
          {onExportJson && (
            <button
              type="button"
              onClick={() => onExportJson(optimized)}
              className="ml-auto rounded border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
            >
              Export JSON
            </button>
          )}
        </div>
      </div>

      {deltas.identical ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          <strong>Brak oszczędności materiału vs standard.</strong> Ta sama liczba wiązek i ten sam
          niewykorzystany materiał ({fmtMm(computeUnusedMaterial(baseline.stocks, config).unusedMm)}).
          {deltas.sameUnusedDifferentSplit && (
            <>
              {' '}
              Optymalizacja zmienia tylko podział na odpad do remeltu vs resztkę na stół — bez
              zysku kg.
            </>
          )}
          {!deltas.sameUnusedDifferentSplit && (
            <>
              {' '}
              Przy ciągu {(config.stockLengthMm / 1000).toFixed(1)} m i tej kolejności zleceń
              wszystkie warianty dają ten sam układ.
            </>
          )}
        </div>
      ) : (
        <StockSavingsBanner
          stockDelta={deltas.stockDelta}
          stockLengthMm={config.stockLengthMm}
          kgPerMeter={config.kgPerMeter}
          variant="prominent"
        />
      )}

      <MetricsTable
        baseline={baseline}
        optimized={optimized}
        config={config}
        deltas={deltas}
      />

      <div>
        <div className="mb-3 flex flex-wrap gap-2">
          <span className="self-center text-xs font-medium uppercase tracking-wide text-slate-500">
            Paski cięcia:
          </span>
          {(
            [
              ['baseline', 'Standard'],
              ['optimized', 'Zoptymalizowany'],
              ['both', 'Obok siebie'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setBarView(id)}
              className={`rounded px-3 py-1 text-sm ${
                barView === id
                  ? 'bg-slate-800 text-white'
                  : 'border border-slate-300 bg-white hover:bg-slate-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {barView === 'both' ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <h4 className="mb-2 text-sm font-semibold text-slate-700">Standard</h4>
              <div className="rounded-lg border border-slate-300 bg-white p-4">
                {baseline.stocks.map((stock) => (
                  <CutBar key={stock.stockIndex} stock={stock} kerfMm={config.kerfMm} />
                ))}
              </div>
            </div>
            <div>
              <h4 className="mb-2 text-sm font-semibold text-slate-700">
                Zoptymalizowany ({VARIANT_LABELS[selectedVariant]})
              </h4>
              <div className="rounded-lg border-2 border-emerald-400 bg-white p-4">
                {optimized.stocks.map((stock) => (
                  <CutBar key={stock.stockIndex} stock={stock} kerfMm={config.kerfMm} />
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div
            className={`rounded-lg bg-white p-4 ${
              barView === 'optimized'
                ? 'border-2 border-emerald-400'
                : 'border border-slate-300'
            }`}
          >
            {(barView === 'baseline' ? baseline : optimized).stocks.map((stock) => (
              <CutBar key={stock.stockIndex} stock={stock} kerfMm={config.kerfMm} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
