import { classifyOffcut } from './classify'
import type { CutPiece, CutSessionConfig, StockBar, StockCut } from './types'

interface MutableStock {
  cuts: StockCut[]
}

function usedLength(stock: MutableStock, kerfMm: number): number {
  if (stock.cuts.length === 0) return 0
  const cutSum = stock.cuts.reduce((sum, c) => sum + c.lengthMm, 0)
  return cutSum + (stock.cuts.length - 1) * kerfMm
}

function remainingAfterPlace(
  stock: MutableStock,
  piece: CutPiece,
  config: CutSessionConfig,
): number | null {
  const kerfNeeded = stock.cuts.length > 0 ? config.kerfMm : 0
  const needed = usedLength(stock, config.kerfMm) + kerfNeeded + piece.lengthMm
  if (needed > config.stockLengthMm) return null
  return config.stockLengthMm - needed
}

function canFit(stock: MutableStock, piece: CutPiece, config: CutSessionConfig): boolean {
  return remainingAfterPlace(stock, piece, config) != null
}

/** 0 = OK (pełne wypełnienie lub resztka reużywalna), >0 = odpad do remeltu */
function interimWasteCost(remaining: number, minReusable: number): number {
  if (remaining <= 0) return 0
  if (remaining >= minReusable) return 0
  return remaining
}

function finalizeStock(
  stock: MutableStock,
  stockIndex: number,
  config: CutSessionConfig,
): StockBar {
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

function placePiece(stock: MutableStock, piece: CutPiece) {
  stock.cuts.push({
    orderId: piece.orderId,
    lengthMm: piece.lengthMm,
    pieceIndex: piece.pieceIndex,
  })
}

type PackStrategy = 'ffd' | 'bfd' | 'wfd' | 'waste-aware'

function packWithStrategy(
  pieces: CutPiece[],
  config: CutSessionConfig,
  strategy: PackStrategy,
): StockBar[] {
  const sorted = [...pieces].sort((a, b) => b.lengthMm - a.lengthMm)
  const mutableStocks: MutableStock[] = []

  for (const piece of sorted) {
    let target: MutableStock | undefined

    if (strategy === 'ffd') {
      target = mutableStocks.find((s) => canFit(s, piece, config))
    } else if (strategy === 'bfd') {
      let bestRemaining = Infinity
      for (const stock of mutableStocks) {
        const remaining = remainingAfterPlace(stock, piece, config)
        if (remaining == null) continue
        if (remaining < bestRemaining) {
          bestRemaining = remaining
          target = stock
        }
      }
    } else if (strategy === 'wfd') {
      let bestRemaining = -1
      for (const stock of mutableStocks) {
        const remaining = remainingAfterPlace(stock, piece, config)
        if (remaining == null) continue
        if (remaining > bestRemaining) {
          bestRemaining = remaining
          target = stock
        }
      }
    } else {
      // waste-aware: unikaj resztek < minOffcutReusableMm
      let bestKey: [number, number, number] = [Infinity, Infinity, Infinity]

      for (let i = 0; i < mutableStocks.length; i++) {
        const stock = mutableStocks[i]
        const remaining = remainingAfterPlace(stock, piece, config)
        if (remaining == null) continue
        const waste = interimWasteCost(remaining, config.minOffcutReusableMm)
        const key: [number, number, number] = [
          waste,
          waste > 0 ? remaining : -remaining,
          i,
        ]
        if (
          key[0] < bestKey[0] ||
          (key[0] === bestKey[0] && key[1] < bestKey[1]) ||
          (key[0] === bestKey[0] && key[1] === bestKey[1] && key[2] < bestKey[2])
        ) {
          bestKey = key
          target = stock
        }
      }

      const newRemaining = config.stockLengthMm - piece.lengthMm
      const newWaste = interimWasteCost(newRemaining, config.minOffcutReusableMm)
      const newKey: [number, number, number] = [newWaste, newRemaining, Infinity]
      if (
        !target ||
        newKey[0] < bestKey[0] ||
        (newKey[0] === bestKey[0] && newKey[1] < bestKey[1])
      ) {
        target = { cuts: [] }
        mutableStocks.push(target)
        placePiece(target, piece)
        continue
      }
    }

    if (!target) {
      target = { cuts: [] }
      mutableStocks.push(target)
    }

    placePiece(target, piece)
  }

  return mutableStocks.map((stock, index) => finalizeStock(stock, index + 1, config))
}

export function packFFD(pieces: CutPiece[], config: CutSessionConfig): StockBar[] {
  return packWithStrategy(pieces, config, 'ffd')
}

export function packBFD(pieces: CutPiece[], config: CutSessionConfig): StockBar[] {
  return packWithStrategy(pieces, config, 'bfd')
}

export function packWFD(pieces: CutPiece[], config: CutSessionConfig): StockBar[] {
  return packWithStrategy(pieces, config, 'wfd')
}

export function packWasteAware(pieces: CutPiece[], config: CutSessionConfig): StockBar[] {
  return packWithStrategy(pieces, config, 'waste-aware')
}

export function allPackStrategies(): PackStrategy[] {
  return ['waste-aware', 'wfd', 'ffd', 'bfd']
}

export function packByStrategy(
  pieces: CutPiece[],
  config: CutSessionConfig,
  strategy: PackStrategy,
): StockBar[] {
  return packWithStrategy(pieces, config, strategy)
}

export function stockBalance(stock: StockBar): boolean {
  const cutSum = stock.cuts.reduce((sum, c) => sum + c.lengthMm, 0)
  return cutSum + stock.kerfLossMm + stock.remnantMm + stock.wasteMm === stock.stockLengthMm
}

export function totalWasteMm(stocks: StockBar[]): number {
  return stocks.reduce((sum, s) => sum + s.wasteMm, 0)
}

export function totalRemnantMm(stocks: StockBar[]): number {
  return stocks.reduce((sum, s) => sum + s.remnantMm, 0)
}
