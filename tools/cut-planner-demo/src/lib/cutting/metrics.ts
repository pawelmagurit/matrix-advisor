import type { CutSessionConfig, CutPlanMetrics, StockBar } from './types'

export function computeMetrics(stocks: StockBar[], config: CutSessionConfig): CutPlanMetrics {
  const totalWasteMm = stocks.reduce((sum, s) => sum + s.wasteMm, 0)
  const totalStockMaterial = stocks.length * config.stockLengthMm
  const wastePercent = totalStockMaterial > 0 ? (totalWasteMm / totalStockMaterial) * 100 : 0

  let totalWasteKg: number | undefined
  let remeltCostPln: number | undefined
  let scrapValuePln: number | undefined

  if (config.kgPerMeter != null) {
    totalWasteKg = (totalWasteMm / 1000) * config.kgPerMeter
    const burnOff = config.burnOffPercent ?? 3
    const effectiveKg = totalWasteKg * (1 + burnOff / 100)
    const remeltCost = config.remeltCostPerKg ?? 0.3
    remeltCostPln = effectiveKg * remeltCost

    const scrapPrice = config.scrapPricePerKg ?? 5
    scrapValuePln = totalWasteKg * scrapPrice
  }

  return {
    totalWasteMm,
    totalWasteKg,
    wastePercent,
    stockCount: stocks.length,
    remeltCostPln,
    scrapValuePln,
  }
}

export function annualRemeltSavings(
  baselineRemelt: number,
  optimizedRemelt: number,
  sessionsPerMonth: number,
): number {
  const monthly = (baselineRemelt - optimizedRemelt) * sessionsPerMonth
  return monthly * 12
}

export function annualScrapSavings(
  baselineScrap: number,
  optimizedScrap: number,
  sessionsPerMonth: number,
): number {
  const monthly = (baselineScrap - optimizedScrap) * sessionsPerMonth
  return monthly * 12
}

export interface StockSavings {
  count: number
  lengthMmPerStock: number
  totalMaterialMm: number
  totalMaterialM: number
  totalMaterialKg?: number
}

export function computeStockSavings(
  stockDelta: number,
  stockLengthMm: number,
  kgPerMeter?: number,
): StockSavings | null {
  if (stockDelta <= 0) return null
  const totalMaterialMm = stockDelta * stockLengthMm
  return {
    count: stockDelta,
    lengthMmPerStock: stockLengthMm,
    totalMaterialMm,
    totalMaterialM: totalMaterialMm / 1000,
    totalMaterialKg:
      kgPerMeter != null ? (totalMaterialMm / 1000) * kgPerMeter : undefined,
  }
}

/** Odmiana: 1 wiązkę, 2 wiązki, 5 wiązek */
export interface UnusedMaterialMetrics {
  wasteMm: number
  remnantMm: number
  unusedMm: number
  unusedPercent: number
  unusedKg?: number
}

/** Niewykorzystany materiał = odpad do remeltu + reszta na końcu wiązki */
export function computeUnusedMaterial(
  stocks: StockBar[],
  config: CutSessionConfig,
): UnusedMaterialMetrics {
  const wasteMm = stocks.reduce((sum, s) => sum + s.wasteMm, 0)
  const remnantMm = stocks.reduce((sum, s) => sum + s.remnantMm, 0)
  const unusedMm = wasteMm + remnantMm
  const totalStock = stocks.length * config.stockLengthMm
  const unusedPercent = totalStock > 0 ? (unusedMm / totalStock) * 100 : 0
  const unusedKg =
    config.kgPerMeter != null ? (unusedMm / 1000) * config.kgPerMeter : undefined

  return { wasteMm, remnantMm, unusedMm, unusedPercent, unusedKg }
}

export function formatSavedWiązki(count: number): string {
  if (count === 1) return '1 całą wiązkę'
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${count} całe wiązki`
  }
  return `${count} całych wiązek`
}
