import { useEffect, useState } from 'react'
import { fetchHealth, type Stats } from '@/lib/api'
import { Layout, type View } from './components/Layout'
import { ProfileBrowser } from './components/ProfileBrowser'
import { ProfileDetailPanel } from './components/ProfileDetailPanel'
import { SimilarityView } from './components/SimilarityView'
import { NewOrderView } from './components/NewOrderView'

function ModulesView() {
  const modules = [
    {
      name: 'Matrix Advisor',
      status: 'aktywny',
      desc: 'Przeglądarka profili, historia matryc, wyszukiwanie podobieństwa po piktogramie.',
      color: 'border-violet-500/40 bg-violet-500/10',
    },
    {
      name: 'Cut Planner',
      status: 'demo',
      desc: 'Optymalizacja cięć 1D — osobne demo w tools/cut-planner-demo.',
      color: 'border-slate-600 bg-white/5',
      href: 'http://localhost:5175',
    },
    {
      name: 'Synchronizacja Impuls',
      status: 'planowany',
      desc: 'Regularny import eksportów JSON/DXF — bez bezpośredniego API.',
      color: 'border-slate-600 bg-white/5',
    },
    {
      name: 'Klasteryzacja profili',
      status: 'planowany',
      desc: 'Grupowanie profili o podobnej geometrii dla analityki portfolio.',
      color: 'border-slate-600 bg-white/5',
    },
  ]

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-white">Moduły Extral Intelligence</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Matrix Advisor to centralny moduł doradczy matryc. Pozostałe narzędzia rozszerzają ekosystem produkcyjny
        Extral.
      </p>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {modules.map((m) => (
          <div key={m.name} className={`rounded-xl border p-5 ${m.color}`}>
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-white">{m.name}</h2>
              <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-400">
                {m.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-400">{m.desc}</p>
            {'href' in m && m.href && (
              <a
                href={m.href}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-block text-sm text-violet-400 hover:text-violet-300"
              >
                Otwórz demo →
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState<View>('browse')
  const [stats, setStats] = useState<Stats | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth()
      .then((h) => setStats(h))
      .catch(() => setApiError('API niedostępne — uruchom: matrix-advisor dev'))
  }, [])

  if (apiError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f1117] p-8">
        <div className="max-w-md rounded-xl border border-amber-500/30 bg-amber-500/10 p-6 text-center">
          <h1 className="text-lg font-semibold text-amber-200">Matrix Advisor</h1>
          <p className="mt-2 text-sm text-amber-100/80">{apiError}</p>
          <pre className="mt-4 rounded bg-black/30 p-3 text-left text-xs text-slate-400">
            cd tools/matrix-advisor-poc{'\n'}
            .venv/bin/matrix-advisor bootstrap-extral --limit 500{'\n'}
            .venv/bin/matrix-advisor dev
          </pre>
        </div>
      </div>
    )
  }

  return (
    <Layout view={view} onViewChange={setView} stats={stats}>
      {view === 'browse' && (
        <div className="flex h-screen">
          <div className={selectedId ? 'flex-1' : 'w-full'}>
            <ProfileBrowser selectedId={selectedId} onSelect={setSelectedId} />
          </div>
          {selectedId && (
            <div className="w-[420px] shrink-0">
              <ProfileDetailPanel profileId={selectedId} onClose={() => setSelectedId(null)} />
            </div>
          )}
        </div>
      )}
      {view === 'new-order' && <NewOrderView />}
      {view === 'similarity' && <SimilarityView />}
      {view === 'modules' && <ModulesView />}
    </Layout>
  )
}
