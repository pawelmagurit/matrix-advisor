import { describe, expect, it } from 'vitest'
import { computeBaseline } from '@/lib/cutting/baseline'
import { classifyOffcut } from '@/lib/cutting/classify'
import { packFFD } from '@/lib/cutting/pack'
import { stockBalance } from '@/lib/cutting/pack'
import { expandOrderLines } from '@/lib/cutting/expand'
import { optimize } from '@/lib/cutting/optimize'
import { computeUnusedMaterial } from '@/lib/cutting/metrics'
import { EXTRAL_SAMPLE_CONFIG, EXTRAL_SAMPLE_ORDERS } from '@/data/extral-sample'
import type { CutSessionConfig } from '@/lib/cutting/types'

const config: CutSessionConfig = {
  profileCode: 'TEST',
  stockLengthMm: 6500,
  kerfMm: 4,
  minOffcutReusableMm: 200,
  kgPerMeter: 1.2,
}

describe('stock balance', () => {
  it('cuts + kerf + remnant + waste = stockLengthMm', () => {
    const pieces = expandOrderLines([
      { orderId: 'A', profileCode: 'T', alloy: '6060', lengthMm: 4200, quantity: 2 },
      { orderId: 'B', profileCode: 'T', alloy: '6060', lengthMm: 1500, quantity: 3 },
    ])
    const stocks = packFFD(pieces, config)
    for (const stock of stocks) {
      expect(stockBalance(stock)).toBe(true)
      const cutSum = stock.cuts.reduce((s, c) => s + c.lengthMm, 0)
      expect(cutSum + stock.kerfLossMm + stock.remnantMm + stock.wasteMm).toBe(stock.stockLengthMm)
    }
  })
})

describe('offcut classification', () => {
  it('below threshold is waste', () => {
    expect(classifyOffcut(150, 200)).toEqual({ remnantMm: 0, wasteMm: 150 })
  })

  it('above threshold is remnant', () => {
    expect(classifyOffcut(800, 200)).toEqual({ remnantMm: 800, wasteMm: 0 })
  })

  it('zero offcut', () => {
    expect(classifyOffcut(0, 200)).toEqual({ remnantMm: 0, wasteMm: 0 })
  })
})

describe('baseline next-fit', () => {
  it('shares a stock bar across orders in file order', () => {
    const plan = computeBaseline(
      [
        { orderId: 'A', profileCode: 'T', alloy: '6060', lengthMm: 4000, quantity: 1 },
        { orderId: 'B', profileCode: 'T', alloy: '6060', lengthMm: 2000, quantity: 1 },
      ],
      config,
    )
    expect(plan.stocks).toHaveLength(1)
    expect(plan.stocks[0].cuts.map((c) => c.orderId)).toEqual(['A', 'B'])
  })
})

describe('Extral sample integration', () => {
  it('optimizes faster than 1s and is never worse than baseline', () => {
    const start = performance.now()
    const result = optimize(EXTRAL_SAMPLE_ORDERS, EXTRAL_SAMPLE_CONFIG)
    const elapsed = performance.now() - start

    expect(elapsed).toBeLessThan(1000)

    const baseline = result.baseline
    const optimized = result.min_waste
    const baseUnused = computeUnusedMaterial(baseline.stocks, EXTRAL_SAMPLE_CONFIG)
    const optUnused = computeUnusedMaterial(optimized.stocks, EXTRAL_SAMPLE_CONFIG)

    expect(optimized.metrics.stockCount).toBeLessThanOrEqual(baseline.metrics.stockCount)
    expect(optUnused.unusedMm).toBeLessThanOrEqual(baseUnused.unusedMm)
  })

  it('beats next-fit when bar is shorter and lengths are mixed', () => {
    const orders = [
      { orderId: 'ZL-201', profileCode: 'E06335-4', alloy: '6060', lengthMm: 7200, quantity: 3 },
      { orderId: 'ZL-202', profileCode: 'E06335-4', alloy: '6060', lengthMm: 6000, quantity: 5 },
      { orderId: 'ZL-203', profileCode: 'E06335-4', alloy: '6060', lengthMm: 4500, quantity: 6 },
      { orderId: 'ZL-204', profileCode: 'E06335-4', alloy: '6060', lengthMm: 3600, quantity: 10 },
      { orderId: 'ZL-205', profileCode: 'E06335-4', alloy: '6060', lengthMm: 3000, quantity: 8 },
    ]
    const shortBar = { ...EXTRAL_SAMPLE_CONFIG, stockLengthMm: 36_000 }
    const result = optimize(orders, shortBar)
    const baseUnused = computeUnusedMaterial(result.baseline.stocks, shortBar)
    const optUnused = computeUnusedMaterial(result.min_waste.stocks, shortBar)
    const improved =
      result.min_waste.metrics.stockCount < result.baseline.metrics.stockCount ||
      optUnused.unusedMm < baseUnused.unusedMm
    expect(improved).toBe(true)
  })
})
