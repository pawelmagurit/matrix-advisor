import { expandOrderLines } from './expand'
import { allPackStrategies, packByStrategy } from './pack'
import { computeMetrics } from './metrics'
import type {
  CutPlan,
  CutSessionConfig,
  OptimizationResult,
  OrderLine,
  PlanVariant,
  StockBar,
} from './types'
import { computeBaseline } from './baseline'

function scorePlan(
  stocks: StockBar[],
  config: CutSessionConfig,
  variant: PlanVariant,
  reference?: { maxWaste: number; maxStocks: number },
): number {
  const metrics = computeMetrics(stocks, config)
  const totalWaste = metrics.totalWasteMm
  const stockCount = metrics.stockCount

  if (variant === 'min_waste') {
    return totalWaste * 10000 + stockCount
  }
  if (variant === 'min_stocks') {
    return stockCount * 10000 + totalWaste
  }

  const maxWaste = (reference?.maxWaste ?? totalWaste) || 1
  const maxStocks = (reference?.maxStocks ?? stockCount) || 1
  const normWaste = totalWaste / maxWaste
  const normStocks = stockCount / maxStocks
  return normWaste * 0.5 + normStocks * 0.5
}

function pickBestPlan(
  stocksOptions: StockBar[][],
  config: CutSessionConfig,
  variant: PlanVariant,
  reference?: { maxWaste: number; maxStocks: number },
): StockBar[] {
  let best = stocksOptions[0]
  let bestScore = Infinity

  for (const stocks of stocksOptions) {
    const score = scorePlan(stocks, config, variant, reference)
    if (score < bestScore) {
      bestScore = score
      best = stocks
    }
  }

  return best
}

function buildPlan(stocks: StockBar[], variant: PlanVariant, config: CutSessionConfig): CutPlan {
  return {
    variant,
    stocks,
    metrics: computeMetrics(stocks, config),
  }
}

function allPackingOptions(pieces: ReturnType<typeof expandOrderLines>, config: CutSessionConfig) {
  return allPackStrategies().map((strategy) => packByStrategy(pieces, config, strategy))
}

export function optimize(
  orders: OrderLine[],
  config: CutSessionConfig,
): OptimizationResult {
  const pieces = expandOrderLines(orders)
  const options = allPackingOptions(pieces, config)
  const baseline = computeBaseline(orders, config)

  const minWasteStocks = pickBestPlan(options, config, 'min_waste')
  const minStocksStocks = pickBestPlan(options, config, 'min_stocks')

  const ref = {
    maxWaste: Math.max(
      ...options.map((s) => computeMetrics(s, config).totalWasteMm),
      baseline.metrics.totalWasteMm,
    ),
    maxStocks: Math.max(
      ...options.map((s) => s.length),
      baseline.stocks.length,
    ),
  }

  const balancedStocks = pickBestPlan(options, config, 'balanced', ref)

  return {
    min_waste: buildPlan(minWasteStocks, 'min_waste', config),
    min_stocks: buildPlan(minStocksStocks, 'min_stocks', config),
    balanced: buildPlan(balancedStocks, 'balanced', config),
    baseline,
  }
}

export function optimizeAllVariants(orders: OrderLine[], config: CutSessionConfig): OptimizationResult {
  return optimize(orders, config)
}
