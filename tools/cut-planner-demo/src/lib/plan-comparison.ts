import type { CutPlan, CutSessionConfig, OptimizationResult, PlanVariant } from '@/lib/cutting/types'
import { computeUnusedMaterial } from '@/lib/cutting/metrics'

export interface PlanComparisonDeltas {
  stockDelta: number
  unusedMmDelta: number
  unusedKgDelta?: number
  wasteMmDelta: number
  remnantMmDelta: number
  remeltPlnDelta?: number
  identical: boolean
  sameUnusedDifferentSplit: boolean
}

export function comparePlansToBaseline(
  baseline: CutPlan,
  optimized: CutPlan,
  config: CutSessionConfig,
): PlanComparisonDeltas {
  const baseU = computeUnusedMaterial(baseline.stocks, config)
  const optU = computeUnusedMaterial(optimized.stocks, config)

  const stockDelta = baseline.metrics.stockCount - optimized.metrics.stockCount
  const unusedMmDelta = baseU.unusedMm - optU.unusedMm
  const wasteMmDelta = baseU.wasteMm - optU.wasteMm
  const remnantMmDelta = baseU.remnantMm - optU.remnantMm

  let unusedKgDelta: number | undefined
  if (baseU.unusedKg != null && optU.unusedKg != null) {
    unusedKgDelta = baseU.unusedKg - optU.unusedKg
  }

  let remeltPlnDelta: number | undefined
  if (baseline.metrics.remeltCostPln != null && optimized.metrics.remeltCostPln != null) {
    remeltPlnDelta = baseline.metrics.remeltCostPln - optimized.metrics.remeltCostPln
  }

  const identical = stockDelta === 0 && unusedMmDelta === 0

  return {
    stockDelta,
    unusedMmDelta,
    unusedKgDelta,
    wasteMmDelta,
    remnantMmDelta,
    remeltPlnDelta,
    identical,
    /** Ten sam materiał, ale inny podział odpad vs resztka (bez realnej oszczędności) */
    sameUnusedDifferentSplit:
      identical && (wasteMmDelta !== 0 || remnantMmDelta !== 0),
  }
}

export function variantPlans(result: Pick<OptimizationResult, 'min_waste' | 'min_stocks' | 'balanced'>): {
  key: PlanVariant
  plan: CutPlan
}[] {
  return [
    { key: 'min_waste', plan: result.min_waste },
    { key: 'min_stocks', plan: result.min_stocks },
    { key: 'balanced', plan: result.balanced },
  ]
}

export function formatDelta(value: number, unit: string, lowerIsBetter = true): string {
  if (value === 0) return '0'
  const sign = value > 0 ? '−' : '+'
  const abs = Math.abs(value)
  const good = lowerIsBetter ? value > 0 : value < 0
  return `${sign}${abs.toLocaleString('pl-PL')} ${unit}${good ? ' ✓' : ''}`
}
