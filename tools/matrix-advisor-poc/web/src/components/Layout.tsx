import type { ReactNode } from 'react'
import type { Stats } from '@/lib/api'

export type View = 'browse' | 'new-order' | 'similarity' | 'modules'

type Props = {
  view: View
  onViewChange: (v: View) => void
  stats: Stats | null
  children: ReactNode
}

const NAV: { id: View; label: string; desc: string }[] = [
  { id: 'browse', label: 'Przeglądarka profili', desc: '10k+ profili z filtrowaniem' },
  { id: 'new-order', label: 'Nowe zamówienie', desc: 'Upload piktogramu z oferty' },
  { id: 'similarity', label: 'Podobne profile', desc: 'Wyszukiwanie w historii' },
  { id: 'modules', label: 'Moduły Extral', desc: 'Ekosystem narzędzi' },
]

export function Layout({ view, onViewChange, stats, children }: Props) {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r border-white/10 bg-[#12141c]">
        <div className="border-b border-white/10 px-5 py-6">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-600 text-lg font-bold text-white">
              M
            </span>
            <div>
              <p className="text-sm font-semibold tracking-wide text-white">Matrix Advisor</p>
              <p className="text-[10px] uppercase tracking-widest text-violet-300/80">Extral · MagurIT</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onViewChange(item.id)}
              className={`w-full rounded-lg px-3 py-2.5 text-left transition ${
                view === item.id
                  ? 'bg-violet-600/20 text-violet-200 ring-1 ring-violet-500/40'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              <p className="text-sm font-medium">{item.label}</p>
              <p className="text-[11px] text-slate-500">{item.desc}</p>
            </button>
          ))}
        </nav>

        {stats && (
          <div className="border-t border-white/10 p-4 text-[11px] text-slate-500">
            <p className="mb-2 font-medium uppercase tracking-wider text-slate-400">Dane</p>
            {stats.index_warning && (
              <p className="mb-2 rounded bg-amber-500/15 px-2 py-1.5 text-[10px] leading-snug text-amber-300">
                {stats.index_warning}
              </p>
            )}
            <div className="grid grid-cols-2 gap-2">
              <Stat label="Profile" value={stats.profiles} />
              <Stat label="Piktogramy" value={stats.pictograms} />
              <Stat label="Matryce" value={stats.matrices} />
              <Stat label="Dostawcy" value={stats.suppliers} />
            </div>
          </div>
        )}
      </aside>

      <main className="flex flex-1 flex-col overflow-hidden bg-[#0f1117]">{children}</main>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-white/5 px-2 py-1.5">
      <p className="text-slate-500">{label}</p>
      <p className="font-mono text-sm text-slate-300">{value.toLocaleString('pl-PL')}</p>
    </div>
  )
}
