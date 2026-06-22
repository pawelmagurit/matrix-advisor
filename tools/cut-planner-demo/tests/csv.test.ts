import { describe, expect, it } from 'vitest'
import { parseOrdersCsv, serializeOrdersCsv } from '@/lib/csv'
import type { OrderLine } from '@/lib/cutting/types'

const sampleRow: OrderLine = {
  orderId: 'ZL-201',
  profileCode: 'E06335-4',
  matrixCode: 'E06335-4',
  contractor: 'REYNAERS B',
  alloy: '6060',
  lengthMm: 7000,
  quantity: 4,
  tolerancePlusMm: 10,
  toleranceMinusMm: 0,
}

describe('CSV import/export', () => {
  it('parses optional contractor and matrixCode', () => {
    const csv = serializeOrdersCsv([sampleRow])
    const { orders, error } = parseOrdersCsv(csv)
    expect(error).toBeUndefined()
    expect(orders).toHaveLength(1)
    expect(orders[0].matrixCode).toBe('E06335-4')
    expect(orders[0].contractor).toBe('REYNAERS B')
  })

  it('parses CSV without optional columns', () => {
    const csv = `orderId,profileCode,alloy,lengthMm,quantity
A,E06335-4,6060,6000,2`
    const { orders, error } = parseOrdersCsv(csv)
    expect(error).toBeUndefined()
    expect(orders[0].contractor).toBeUndefined()
  })

  it('rejects missing required column', () => {
    const { error } = parseOrdersCsv('orderId,alloy\nx,6060')
    expect(error).toContain('profileCode')
  })

  it('parses semicolon-separated CSV (Excel PL)', () => {
    const csv = `orderId;profileCode;matrixCode;contractor;alloy;lengthMm;quantity
ZL-201;E06335-4;E06335-4;REYNAERS B;6060;7000;4`
    const { orders, error } = parseOrdersCsv(csv)
    expect(error).toBeUndefined()
    expect(orders[0].orderId).toBe('ZL-201')
    expect(orders[0].contractor).toBe('REYNAERS B')
  })

  it('accepts Polish header aliases', () => {
    const csv = `zlecenie;profil;stop;dlugosc;ilosc
ZL-99;E06335-4;6060;6000;3`
    const { orders, error } = parseOrdersCsv(csv)
    expect(error).toBeUndefined()
    expect(orders[0].orderId).toBe('ZL-99')
    expect(orders[0].lengthMm).toBe(6000)
  })
})
