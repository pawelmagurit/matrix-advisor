import type { CutSessionConfig, MatrixInfo, OrderLine } from '@/lib/cutting/types'

/**
 * Dane przykładowe — Extral / EXD (matryca, kontrahent) + zestaw zleceń pod widoczną
 * optymalizację na demo.
 *
 * Dł. ciągu 36 m — środek dolnego zakresu z wizyty (30–54 m). Przy typowym ciągu ~44 m
 * z EXD ten sam CSV często daje identyczny wynik co kolejność z pliku; 36 m pokazuje
 * realną różnicę (5→4 wiązki). W parametrach można ustawić 44 200 mm jak w EXD.
 */
export const EXTRAL_SAMPLE_ORDERS: OrderLine[] = [
  {
    orderId: 'ZL-201',
    profileCode: 'E06335-4',
    matrixCode: 'E06335-4',
    contractor: 'REYNAERS B',
    alloy: '6060',
    lengthMm: 4500,
    quantity: 6,
    tolerancePlusMm: 10,
    toleranceMinusMm: 0,
  },
  {
    orderId: 'ZL-202',
    profileCode: 'E06335-4',
    matrixCode: 'E06335-4',
    contractor: 'REYNAERS B',
    alloy: '6060',
    lengthMm: 6000,
    quantity: 5,
    tolerancePlusMm: 10,
    toleranceMinusMm: 0,
  },
  {
    orderId: 'ZL-203',
    profileCode: 'E06335-4',
    matrixCode: 'E06335-4',
    contractor: 'REYNAERS B',
    alloy: '6060',
    lengthMm: 3600,
    quantity: 10,
    tolerancePlusMm: 10,
    toleranceMinusMm: 0,
  },
  {
    orderId: 'ZL-204',
    profileCode: 'E06335-4',
    matrixCode: 'E06335-4',
    contractor: 'REYNAERS B',
    alloy: '6060',
    lengthMm: 3000,
    quantity: 8,
    tolerancePlusMm: 10,
    toleranceMinusMm: 0,
  },
  {
    orderId: 'ZL-205',
    profileCode: 'E06335-4',
    matrixCode: 'E06335-4',
    contractor: 'REYNAERS B',
    alloy: '6060',
    lengthMm: 7200,
    quantity: 3,
    tolerancePlusMm: 10,
    toleranceMinusMm: 0,
  },
]

/** 36 m — wiązka na piłę (demo: wyraźna różnica vs optymalizacja; typowy EXD ~44 m) */
export const EXTRAL_STOCK_LENGTH_MM = 36_000

export const EXTRAL_SAMPLE_MATRIX: MatrixInfo = {
  matrixCode: 'E06335-4',
  theoreticalKgPerMeter: 6.051,
  actualKgPerMeter: 5.958,
  dieType: 'Komorowa',
  cavityCount: 1,
  pressCode: 'PR-7.1',
}

export const EXTRAL_SAMPLE_CONFIG: CutSessionConfig = {
  profileCode: 'E06335-4',
  kgPerMeter: 5.958,
  stockLengthMm: EXTRAL_STOCK_LENGTH_MM,
  kerfMm: 4,
  minOffcutReusableMm: 200,
  remeltCostPerKg: 0.3,
  burnOffPercent: 3,
  sessionsPerMonth: 1,
  scrapPricePerKg: 5,
}

export function loadExtralSample(): {
  orders: OrderLine[]
  config: CutSessionConfig
  matrixInfo: MatrixInfo
} {
  return {
    orders: EXTRAL_SAMPLE_ORDERS.map((o) => ({ ...o })),
    config: { ...EXTRAL_SAMPLE_CONFIG },
    matrixInfo: { ...EXTRAL_SAMPLE_MATRIX },
  }
}
