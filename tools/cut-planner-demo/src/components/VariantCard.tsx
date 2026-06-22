import type { CutPlan, PlanVariant } from '@/lib/cutting/types'
import { VARIANT_LABELS } from '@/lib/colors'

function unusedPercent(plan: CutPlan): number {
  if (plan.stocks.length === 0) return 0
  const stockLen = plan.stocks[0].stockLengthMm
  const unused = plan.stocks.reduce((s, b) => s + b.wasteMm + b.remnantMm, 0)
  return (unused / (plan.stocks.length * stockLen)) * 100
}

interface VariantCardProps {
  plan: CutPlan
  selected: boolean
  onSelect: () => void
}

export function VariantCard({ plan, selected, onSelect }: VariantCardProps) {
  const label = VARIANT_LABELS[plan.variant] ?? plan.variant

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`rounded-lg border p-4 text-left transition ${
        selected
          ? 'border-slate-800 bg-slate-800 text-white shadow-md'
          : 'border-slate-200 bg-white text-slate-900 hover:border-slate-400'
      }`}
    >
      <div className="text-sm font-semibold">{label}</div>
      <div className={`mt-2 space-y-1 text-xs ${selected ? 'text-slate-200' : 'text-slate-600'}`}>
        <div>Wiązki: {plan.metrics.stockCount}</div>
        <div>Niewykorzystane: {unusedPercent(plan).toFixed(1)}%</div>
        {plan.metrics.remeltCostPln != null && (
          <div>Remelt: {plan.metrics.remeltCostPln.toFixed(2)} PLN</div>
        )}
      </div>
    </button>
  )
}

export function variantPlans(result: {
  min_waste: CutPlan
  min_stocks: CutPlan
  balanced: CutPlan
}): { key: PlanVariant; plan: CutPlan }[] {
  return [
    { key: 'min_waste', plan: result.min_waste },
    { key: 'min_stocks', plan: result.min_stocks },
    { key: 'balanced', plan: result.balanced },
  ]
}
