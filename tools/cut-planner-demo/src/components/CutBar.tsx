import type { StockBar } from '@/lib/cutting/types'
import { orderColor } from '@/lib/colors'

interface CutBarProps {
  stock: StockBar
  kerfMm: number
  showLabel?: boolean
}

type BarSegment =
  | { kind: 'cut'; orderId: string; lengthMm: number; pieceIndex: number; key: string }
  | { kind: 'kerf'; lengthMm: number; key: string }
  | { kind: 'waste'; lengthMm: number; key: string }
  | { kind: 'remnant'; lengthMm: number; key: string }

function buildSegments(stock: StockBar, kerfMm: number): BarSegment[] {
  const segments: BarSegment[] = []
  stock.cuts.forEach((cut, i) => {
    if (i > 0) {
      segments.push({ kind: 'kerf', lengthMm: kerfMm, key: `kerf-${i}` })
    }
    segments.push({
      kind: 'cut',
      orderId: cut.orderId,
      lengthMm: cut.lengthMm,
      pieceIndex: cut.pieceIndex,
      key: `cut-${cut.orderId}-${cut.pieceIndex}-${i}`,
    })
  })
  if (stock.wasteMm > 0) {
    segments.push({ kind: 'waste', lengthMm: stock.wasteMm, key: 'waste' })
  }
  if (stock.remnantMm > 0) {
    segments.push({ kind: 'remnant', lengthMm: stock.remnantMm, key: 'remnant' })
  }
  return segments
}

function pct(lengthMm: number, totalMm: number): string {
  return `${(lengthMm / totalMm) * 100}%`
}

export function CutBar({ stock, kerfMm, showLabel = true }: CutBarProps) {
  const total = stock.stockLengthMm
  const segments = buildSegments(stock, kerfMm)

  return (
    <div className="mb-4">
      {showLabel && (
        <div className="mb-1 flex items-baseline justify-between text-xs text-slate-600">
          <span className="font-medium">
            Wiązka #{stock.stockIndex} — {(total / 1000).toFixed(1)} m
          </span>
          <span className="font-mono text-slate-400">0 – {total.toLocaleString('pl-PL')} mm</span>
        </div>
      )}
      <div className="relative">
        <div
          className="flex h-12 w-full overflow-hidden rounded border-2 border-slate-400 bg-slate-100"
          style={{ minHeight: 48 }}
          title={`Wiązka ${stock.stockIndex}: ${total} mm`}
        >
          {segments.map((seg) => {
            const width = pct(seg.lengthMm, total)
            if (seg.kind === 'kerf') {
              return (
                <div
                  key={seg.key}
                  className="h-full shrink-0 bg-slate-800"
                  style={{ width }}
                  title={`Rzaz piły: ${seg.lengthMm} mm`}
                />
              )
            }
            if (seg.kind === 'cut') {
              const ratio = seg.lengthMm / total
              return (
                <div
                  key={seg.key}
                  className="flex h-full shrink-0 items-center justify-center overflow-hidden border-r border-white/30 text-[10px] font-semibold text-white"
                  style={{
                    width,
                    backgroundColor: orderColor(seg.orderId),
                    minWidth: ratio > 0.003 ? undefined : '1px',
                  }}
                  title={`${seg.orderId} — ${seg.lengthMm} mm (szt. ${seg.pieceIndex})`}
                >
                  {ratio > 0.04 && (
                    <span className="truncate px-0.5">
                      {seg.orderId} {(seg.lengthMm / 1000).toFixed(1)}m
                    </span>
                  )}
                </div>
              )
            }
            if (seg.kind === 'waste') {
              return (
                <div
                  key={seg.key}
                  className="flex h-full shrink-0 items-center justify-center bg-red-500 text-[10px] font-medium text-white"
                  style={{ width }}
                  title={`Odpad do remeltu: ${seg.lengthMm} mm`}
                >
                  {seg.lengthMm / total > 0.02 && `odpad ${seg.lengthMm}mm`}
                </div>
              )
            }
            return (
              <div
                key={seg.key}
                className="flex h-full shrink-0 items-center justify-center border-l-2 border-dashed border-slate-600 bg-gray-400 text-[10px] font-medium text-slate-800"
                style={{ width }}
                title="Resztka — niewykorzystany materiał na końcu wiązki"
              >
                {seg.lengthMm / total > 0.02 && `resztka ${seg.lengthMm}mm`}
              </div>
            )
          })}
        </div>
        <div className="mt-0.5 flex justify-between font-mono text-[9px] text-slate-400">
          <span>0 m</span>
          <span>{(total / 1000).toFixed(1)} m</span>
        </div>
      </div>
      <div className="mt-0.5 text-[10px] text-slate-500">
        {stock.cuts.length} cięć · kerf łącznie {stock.kerfLossMm} mm
        {stock.remnantMm > 0 && ` · resztka ${stock.remnantMm} mm`}
        {stock.wasteMm > 0 && ` · odpad ${stock.wasteMm} mm`}
      </div>
    </div>
  )
}

export function CutLegend() {
  return (
    <div className="mb-4 flex flex-wrap gap-4 rounded border border-slate-200 bg-white p-3 text-xs text-slate-700">
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-3 w-6 rounded bg-blue-600" />
        Odcinek zamówienia (szer. ∝ długość mm)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-3 w-4 bg-slate-800" />
        Rzaz piły (∝ kerf)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-3 w-6 rounded bg-red-500" />
        Odpad do remeltu
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-3 w-6 rounded border border-dashed border-slate-500 bg-gray-400" />
        Resztka (niewykorzystany materiał)
      </span>
    </div>
  )
}
