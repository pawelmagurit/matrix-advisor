import type { MatrixInfo } from '@/lib/cutting/types'

interface MatrixPanelProps {
  matrixInfo: MatrixInfo | null
}

function ProfilePictogramPlaceholder() {
  return (
    <div className="flex h-full min-h-[120px] flex-col items-center justify-center rounded border border-dashed border-slate-300 bg-slate-50 p-4 text-center">
      <svg
        viewBox="0 0 80 80"
        className="mb-2 h-16 w-16 text-slate-400"
        aria-hidden
      >
        <rect x="8" y="8" width="64" height="64" fill="none" stroke="currentColor" strokeWidth="2" />
        <path
          d="M20 40 L40 20 L60 40 L40 60 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
        <circle cx="40" cy="40" r="12" fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
      <p className="text-xs font-medium text-slate-500">Rysunek techniczny</p>
      <p className="mt-1 text-[10px] text-slate-400">Przekrój profilu (placeholder)</p>
    </div>
  )
}

export function MatrixPanel({ matrixInfo }: MatrixPanelProps) {
  if (!matrixInfo) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        <p className="font-medium text-slate-700">Matryca</p>
        <p className="mt-1">
          Brak danych matrycy. Wczytaj przykład Extral lub uzupełnij kolumnę{' '}
          <code className="rounded bg-white px-1 text-xs">matrixCode</code> w CSV — metadane matrycy
          (masa, prasa) pochodzą z przykładu demo; integracja z Impuls planowana później.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h3 className="text-base font-semibold text-slate-800">Matryca {matrixInfo.matrixCode}</h3>
        <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
          GOT
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-4 border-b border-slate-100 pb-1">
            <dt className="text-slate-500">Masa teoretyczna</dt>
            <dd className="font-medium">{matrixInfo.theoreticalKgPerMeter.toFixed(3)} kg/m</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 pb-1">
            <dt className="text-slate-500">Masa rzeczywista</dt>
            <dd className="font-medium">{matrixInfo.actualKgPerMeter.toFixed(3)} kg/m</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 pb-1">
            <dt className="text-slate-500">Typ matrycy</dt>
            <dd className="font-medium">{matrixInfo.dieType}</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 pb-1">
            <dt className="text-slate-500">Ilość otworów</dt>
            <dd className="font-medium">{matrixInfo.cavityCount}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Prasa</dt>
            <dd className="font-medium">{matrixInfo.pressCode}</dd>
          </div>
        </dl>

        <ProfilePictogramPlaceholder />
      </div>
    </div>
  )
}
