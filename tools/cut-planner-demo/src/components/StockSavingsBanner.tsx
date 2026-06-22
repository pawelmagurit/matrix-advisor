import { computeStockSavings, formatSavedWiązki, type StockSavings } from '@/lib/cutting/metrics'

interface StockSavingsBannerProps {
  stockDelta: number
  stockLengthMm: number
  kgPerMeter?: number
  /** compact = jedna linia w banerze; prominent = osobna karta */
  variant?: 'compact' | 'prominent'
}

export function getStockSavings(
  stockDelta: number,
  stockLengthMm: number,
  kgPerMeter?: number,
): StockSavings | null {
  return computeStockSavings(stockDelta, stockLengthMm, kgPerMeter)
}

export function StockSavingsBanner({
  stockDelta,
  stockLengthMm,
  kgPerMeter,
  variant = 'prominent',
}: StockSavingsBannerProps) {
  const savings = getStockSavings(stockDelta, stockLengthMm, kgPerMeter)
  if (!savings) return null

  const lengthM = (stockLengthMm / 1000).toFixed(1)
  const label = formatSavedWiązki(savings.count)

  if (variant === 'compact') {
    return (
      <span>
        {', '}
        <strong>{label}</strong> ({savings.count} × {lengthM} m ={' '}
        <strong>{savings.totalMaterialM.toLocaleString('pl-PL', { maximumFractionDigits: 1 })} m</strong>
        {savings.totalMaterialKg != null && (
          <>
            {' '}
            / <strong>{savings.totalMaterialKg.toFixed(1)} kg</strong>
          </>
        )}
        )
      </span>
    )
  }

  return (
    <div className="mb-3 rounded-lg border-2 border-blue-300 bg-blue-50 px-4 py-3">
      <div className="text-sm font-semibold text-blue-900">
        Nie trzeba podawać na piłę: {label}
      </div>
      <div className="mt-1 text-lg font-bold text-blue-800">
        {savings.count} × {lengthM} m ={' '}
        {savings.totalMaterialM.toLocaleString('pl-PL', { maximumFractionDigits: 1 })} m profilu
      </div>
      {savings.totalMaterialKg != null && (
        <div className="mt-0.5 text-sm text-blue-700">
          ≈ {savings.totalMaterialKg.toFixed(1)} kg aluminiumu mniej do przetworzenia na piłzie
        </div>
      )}
      <div className="mt-1 text-xs text-blue-600">
        Całe wiązki z listy standardowej nie są potrzebne dzięki lepszemu układowi cięć.
      </div>
    </div>
  )
}
