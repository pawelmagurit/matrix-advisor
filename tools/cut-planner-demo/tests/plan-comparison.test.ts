import { describe, expect, it } from 'vitest'
import { optimize } from '@/lib/cutting/optimize'
import { comparePlansToBaseline } from '@/lib/plan-comparison'
import { EXTRAL_SAMPLE_CONFIG, EXTRAL_SAMPLE_ORDERS } from '@/data/extral-sample'

describe('comparePlansToBaseline', () => {
  it('EXD sample shows clear improvement on demo', () => {
    const result = optimize(EXTRAL_SAMPLE_ORDERS, EXTRAL_SAMPLE_CONFIG)
    const cmp = comparePlansToBaseline(result.baseline, result.min_waste, EXTRAL_SAMPLE_CONFIG)
    expect(cmp.identical).toBe(false)
    expect(cmp.stockDelta).toBeGreaterThan(0)
    expect(cmp.unusedMmDelta).toBeGreaterThan(0)
    expect(result.baseline.metrics.stockCount).toBeGreaterThan(result.min_waste.metrics.stockCount)
  })
})
