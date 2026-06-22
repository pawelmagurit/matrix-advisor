export interface OrderLine {
  orderId: string
  profileCode: string
  alloy: string
  lengthMm: number
  quantity: number
  tolerancePlusMm?: number
  toleranceMinusMm?: number
  priority?: number
  /** Kontrahent (np. z widoku EXD / historia zleceń) */
  contractor?: string
  /** Id matrycy w formacie E#####-## (np. E06335-4) */
  matrixCode?: string
}

/** Metadane matrycy — informacyjne, bez wpływu na optymalizację */
export interface MatrixInfo {
  matrixCode: string
  theoreticalKgPerMeter: number
  actualKgPerMeter: number
  dieType: string
  cavityCount: number
  pressCode: string
}

export interface CutSessionConfig {
  profileCode: string
  kgPerMeter?: number
  stockLengthMm: number
  kerfMm: number
  minOffcutReusableMm: number
  remeltCostPerKg?: number
  burnOffPercent?: number
  sessionsPerMonth?: number
  scrapPricePerKg?: number
}

export interface CutPiece {
  orderId: string
  lengthMm: number
  pieceIndex: number
}

export interface StockCut {
  orderId: string
  lengthMm: number
  pieceIndex: number
}

export interface StockBar {
  stockIndex: number
  stockLengthMm: number
  cuts: StockCut[]
  kerfLossMm: number
  remnantMm: number
  wasteMm: number
}

export type PlanVariant = 'min_waste' | 'min_stocks' | 'balanced'

export interface CutPlanMetrics {
  totalWasteMm: number
  totalWasteKg?: number
  wastePercent: number
  stockCount: number
  remeltCostPln?: number
  scrapValuePln?: number
}

export interface CutPlan {
  variant: PlanVariant
  stocks: StockBar[]
  metrics: CutPlanMetrics
}

export interface OptimizationResult {
  min_waste: CutPlan
  min_stocks: CutPlan
  balanced: CutPlan
  baseline: CutPlan
}
