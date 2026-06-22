import { expandOrderLines } from './expand'
import { classifyOffcut } from './classify'
import type { CutSessionConfig, CutPlan, OrderLine, StockBar, StockCut } from './types'
import { computeMetrics } from './metrics'

interface MutableStock {
  cuts: StockCut[]
}

function usedLength(stock: MutableStock, kerfMm: number): number {
  if (stock.cuts.length === 0) return 0
  const cutSum = stock.cuts.reduce((sum, c) => sum + c.lengthMm, 0)
  return cutSum + (stock.cuts.length - 1) * kerfMm
}

function finalize(stock: MutableStock, stockIndex: number, config: CutSessionConfig): StockBar {
  const kerfLossMm = stock.cuts.length > 0 ? (stock.cuts.length - 1) * config.kerfMm : 0
  const cutSum = stock.cuts.reduce((sum, c) => sum + c.lengthMm, 0)
  const offcut = config.stockLengthMm - cutSum - kerfLossMm
  const { remnantMm, wasteMm } = classifyOffcut(offcut, config.minOffcutReusableMm)
  return {
    stockIndex,
    stockLengthMm: config.stockLengthMm,
    cuts: [...stock.cuts],
    kerfLossMm,
    remnantMm,
    wasteMm,
  }
}

/**
 * Plan ręczny (baseline): **Next-Fit w kolejności z pliku**.
 * Zlecenia rozwijane wiersz po wierszu jak w CSV; każda sztuka idzie na bieżącą wiązkę,
 * jeśli się mieści (z rzazem). Nowa wiązka tylko gdy brak miejsca — bez względu na to,
 * czy następna sztuka należy do innego zlecenia. Bez zmiany kolejności i bez szukania
 * lepszego układu.
 */
export function computeBaseline(orders: OrderLine[], config: CutSessionConfig): CutPlan {
  const pieces = expandOrderLines(orders)
  const mutableStocks: MutableStock[] = []
  let currentStock: MutableStock | null = null

  for (const piece of pieces) {
    const fits = (stock: MutableStock): boolean => {
      if (stock.cuts.length === 0) {
        return piece.lengthMm <= config.stockLengthMm
      }
      return (
        usedLength(stock, config.kerfMm) + config.kerfMm + piece.lengthMm <= config.stockLengthMm
      )
    }

    if (!currentStock || !fits(currentStock)) {
      currentStock = { cuts: [] }
      mutableStocks.push(currentStock)
    }

    currentStock.cuts.push({
      orderId: piece.orderId,
      lengthMm: piece.lengthMm,
      pieceIndex: piece.pieceIndex,
    })
  }

  const stocks = mutableStocks.map((s, i) => finalize(s, i + 1, config))
  return {
    variant: 'min_waste',
    stocks,
    metrics: computeMetrics(stocks, config),
  }
}
