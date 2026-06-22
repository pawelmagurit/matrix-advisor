import type { CutPlan } from '@/lib/cutting/types'
import {
  annualRemeltSavings,
  annualScrapSavings,
  computeUnusedMaterial,
} from '@/lib/cutting/metrics'
import { StockSavingsBanner } from './StockSavingsBanner'

interface ComparisonTableProps {
  baseline: CutPlan
  optimized: CutPlan
  sessionsPerMonth: number
  roiView: 'remelt' | 'scrap'
  minOffcutReusableMm: number
  stockLengthMm: number
  kgPerMeter?: number
}

function isLowerBetter(label: string): boolean {
  return !label.includes('(szczegół)')
}

function cellClass(label: string, baselineVal: number, optimizedVal: number): string {
  if (!isLowerBetter(label)) {
    return optimizedVal >= baselineVal ? 'text-emerald-700 font-medium' : 'text-slate-900'
  }
  if (optimizedVal < baselineVal) return 'text-emerald-700 font-medium'
  if (optimizedVal > baselineVal) return 'text-red-600 font-medium'
  return 'text-slate-900'
}

export function ComparisonTable({
  baseline,
  optimized,
  sessionsPerMonth,
  roiView,
  minOffcutReusableMm,
  stockLengthMm,
  kgPerMeter,
}: ComparisonTableProps) {
  const stockDelta = baseline.metrics.stockCount - optimized.metrics.stockCount
  const cfg = {
    profileCode: '',
    stockLengthMm,
    kerfMm: 4,
    minOffcutReusableMm,
    kgPerMeter,
  }
  const baseUnused = computeUnusedMaterial(baseline.stocks, cfg)
  const optUnused = computeUnusedMaterial(optimized.stocks, cfg)

  const rows = [
    {
      label: 'Liczba wiązek',
      baseline: baseline.metrics.stockCount,
      optimized: optimized.metrics.stockCount,
      format: (v: number) => String(v),
    },
    {
      label: 'Niewykorzystany materiał (mm)',
      baseline: baseUnused.unusedMm,
      optimized: optUnused.unusedMm,
      format: (v: number) => String(v),
    },
    {
      label: 'Niewykorzystany materiał (%)',
      baseline: baseUnused.unusedPercent,
      optimized: optUnused.unusedPercent,
      format: (v: number) => v.toFixed(1) + '%',
    },
    {
      label: 'w tym do remeltu (mm) (szczegół)',
      baseline: baseUnused.wasteMm,
      optimized: optUnused.wasteMm,
      format: (v: number) => String(v),
    },
    {
      label: 'w tym reszta na końcu wiązki (mm) (szczegół)',
      baseline: baseUnused.remnantMm,
      optimized: optUnused.remnantMm,
      format: (v: number) => String(v),
    },
    {
      label: 'Niewykorzystane (kg)',
      baseline: baseUnused.unusedKg ?? NaN,
      optimized: optUnused.unusedKg ?? NaN,
      format: (v: number) => (Number.isFinite(v) ? v.toFixed(1) : '—'),
    },
    {
      label: 'Koszt remeltu (PLN)',
      baseline: baseline.metrics.remeltCostPln ?? NaN,
      optimized: optimized.metrics.remeltCostPln ?? NaN,
      format: (v: number) => (Number.isFinite(v) ? v.toFixed(2) : '—'),
    },
    {
      label: 'Wartość złomu zewn. (PLN)',
      baseline: baseline.metrics.scrapValuePln ?? NaN,
      optimized: optimized.metrics.scrapValuePln ?? NaN,
      format: (v: number) => (Number.isFinite(v) ? v.toFixed(2) : '—'),
    },
  ]

  const remeltAnnual =
    baseline.metrics.remeltCostPln != null && optimized.metrics.remeltCostPln != null
      ? annualRemeltSavings(
          baseline.metrics.remeltCostPln,
          optimized.metrics.remeltCostPln,
          sessionsPerMonth,
        )
      : null

  const scrapAnnual =
    baseline.metrics.scrapValuePln != null && optimized.metrics.scrapValuePln != null
      ? annualScrapSavings(
          baseline.metrics.scrapValuePln,
          optimized.metrics.scrapValuePln,
          sessionsPerMonth,
        )
      : null

  const unusedImproved = optUnused.unusedMm < baseUnused.unusedMm

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        <strong>Niewykorzystany materiał</strong> = odpad do remeltu (czerwony) + reszta na końcu
        wiązki (szary). Remelt w PLN dotyczy tylko fragmentów &lt; {minOffcutReusableMm} mm.
      </p>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left">
              <th className="p-3 font-semibold">Metryka</th>
              <th className="p-3 font-semibold">Standard (kolejność z listy)</th>
              <th className="p-3 font-semibold">Plan zoptymalizowany</th>
              <th className="p-3 font-semibold">Zmiana</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const delta = row.optimized - row.baseline
              const deltaStr =
                !Number.isFinite(row.baseline) || !Number.isFinite(row.optimized)
                  ? '—'
                  : delta === 0
                    ? '='
                    : delta > 0
                      ? `+${row.format(Math.abs(delta)).replace('—', String(Math.abs(delta)))}`
                      : `−${row.format(Math.abs(delta)).replace('%', '').replace('—', String(Math.abs(delta)))}${row.label.includes('%') ? '%' : ''}`

              return (
                <tr key={row.label} className="border-b border-slate-100">
                  <td className="p-3 text-slate-700">{row.label}</td>
                  <td className="p-3 font-mono">{row.format(row.baseline)}</td>
                  <td
                    className={`p-3 font-mono ${cellClass(row.label, row.baseline, row.optimized)}`}
                  >
                    {row.format(row.optimized)}
                  </td>
                  <td className="p-3 font-mono text-xs text-slate-500">{deltaStr}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <StockSavingsBanner
        stockDelta={stockDelta}
        stockLengthMm={stockLengthMm}
        kgPerMeter={kgPerMeter}
        variant="prominent"
      />

      {roiView === 'remelt' && remeltAnnual != null && (
        <div
          className={`rounded-lg border p-4 ${
            remeltAnnual > 0
              ? 'border-emerald-200 bg-emerald-50'
              : 'border-amber-200 bg-amber-50'
          }`}
        >
          <div
            className={`text-sm font-semibold ${remeltAnnual > 0 ? 'text-emerald-900' : 'text-amber-900'}`}
          >
            Szac. oszczędność remeltu
          </div>
          <div
            className={`mt-1 text-2xl font-bold ${remeltAnnual > 0 ? 'text-emerald-800' : 'text-amber-800'}`}
          >
            {remeltAnnual > 0 ? '' : '−'}
            {Math.abs(remeltAnnual).toFixed(0)} PLN / rok
          </div>
          <div
            className={`mt-1 text-xs ${remeltAnnual > 0 ? 'text-emerald-700' : 'text-amber-700'}`}
          >
            {remeltAnnual > 0
              ? `Przy ${sessionsPerMonth} sesji/mies. × 12 miesięcy`
              : 'Optymalizacja nie poprawia odpadu względem baseline — sprawdź wariant „Najmniej odpadu”'}
            {!unusedImproved && remeltAnnual <= 0 && (
              <span> (standard ma mniej niewykorzystanego materiału przy tym zestawie)</span>
            )}
          </div>
        </div>
      )}

      {roiView === 'scrap' && scrapAnnual != null && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="text-sm font-semibold text-amber-900">
            Szac. oszczędność — wartość złomu zewnętrznego (informacyjnie)
          </div>
          <div className="mt-1 text-2xl font-bold text-amber-800">
            {scrapAnnual > 0 ? '' : '−'}
            {Math.abs(scrapAnnual).toFixed(0)} PLN / rok
          </div>
          <div className="mt-1 text-xs text-amber-700">
            Extral ma własny Re-Melt — ten widok służy tylko do porównania
          </div>
        </div>
      )}
    </div>
  )
}
