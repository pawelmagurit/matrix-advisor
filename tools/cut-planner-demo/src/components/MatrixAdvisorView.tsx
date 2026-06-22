import { useCallback, useEffect, useState } from 'react'
import {
  fetchAdvisory,
  fetchHealth,
  fetchProfiles,
  pictogramUrl,
  type AdvisoryResponse,
  type ProfileListItem,
} from '@/lib/matrix-advisor-api'

function PictogramThumb({ profileId, label }: { profileId: string; label?: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded border border-slate-200 bg-white p-1">
        <img
          src={pictogramUrl(profileId)}
          alt={`Piktogram ${profileId}`}
          className="max-h-full max-w-full object-contain"
          onError={(e) => {
            ;(e.target as HTMLImageElement).style.display = 'none'
          }}
        />
      </div>
      {label && <span className="max-w-[6rem] truncate text-center text-[10px] text-slate-500">{label}</span>}
    </div>
  )
}

function EffectivenessBadge({ pct }: { pct: number | null }) {
  if (pct == null) return <span className="text-slate-400">—</span>
  const color =
    pct >= 75 ? 'bg-emerald-100 text-emerald-800' : pct >= 55 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${color}`}>{pct.toFixed(1)}%</span>
}

export function MatrixAdvisorView() {
  const [apiOk, setApiOk] = useState<boolean | null>(null)
  const [profiles, setProfiles] = useState<ProfileListItem[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [method, setMethod] = useState<'embedding' | 'geometric'>('embedding')
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth()
      .then(() => {
        setApiOk(true)
        return fetchProfiles()
      })
      .then((p) => {
        setProfiles(p)
        setSelectedId((prev) => prev || (p[0]?.profile_id ?? ''))
      })
      .catch(() => setApiOk(false))
  }, [])

  const loadAdvisory = useCallback(async () => {
    if (!selectedId) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAdvisory(selectedId, method, 8)
      setAdvisory(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Błąd API')
      setAdvisory(null)
    } finally {
      setLoading(false)
    }
  }, [selectedId, method])

  useEffect(() => {
    if (apiOk && selectedId) void loadAdvisory()
  }, [apiOk, selectedId, method, loadAdvisory])

  if (apiOk === false) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        <h2 className="text-lg font-semibold">Matrix Advisor — API niedostępne</h2>
        <p className="mt-2">
          Uruchom backend w drugim terminalu (dane syntetyczne + indeks):
        </p>
        <pre className="mt-3 overflow-x-auto rounded bg-white p-3 text-xs text-slate-800">
{`cd tools/matrix-advisor-poc
source .venv/bin/activate
matrix-advisor pipeline
matrix-advisor serve`}
        </pre>
        <p className="mt-3 text-xs text-amber-800">
          Następnie odśwież tę stronę. API domyślnie: <code>http://127.0.0.1:8765</code>
        </p>
      </section>
    )
  }

  if (apiOk === null) {
    return <p className="text-sm text-slate-500">Łączenie z Matrix Advisor API…</p>
  }

  return (
    <section className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-800">Dobór matryc — podobne profile</h2>
        <p className="mt-1 text-sm text-slate-600">
          Nowy profil? System pokazuje historycznie podobne kształty, użyte matryce, dostawców i
          skuteczność. <strong>Podpowiedź decyzyjna</strong> — nie automatyczny wybór.
        </p>

        <div className="mt-4 flex flex-wrap items-end gap-4">
          <label className="block text-sm">
            <span className="text-slate-600">Profil zapytania</span>
            <select
              className="mt-1 block min-w-[200px] rounded border border-slate-200 px-3 py-2"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {profiles.map((p) => (
                <option key={p.profile_id} value={p.profile_id}>
                  {p.profile_id}
                  {p.display_name ? ` — ${p.display_name}` : ''}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-slate-600">Metoda</span>
            <select
              className="mt-1 block rounded border border-slate-200 px-3 py-2"
              value={method}
              onChange={(e) => setMethod(e.target.value as 'embedding' | 'geometric')}
            >
              <option value="embedding">Embedding (wizualny)</option>
              <option value="geometric">Geometric (interpretowalny)</option>
            </select>
          </label>
          <button
            type="button"
            onClick={() => void loadAdvisory()}
            disabled={loading}
            className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {loading ? 'Szukam…' : 'Odśwież'}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {advisory && (
        <>
          <div className="grid gap-4 lg:grid-cols-[auto_1fr]">
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Zapytanie</p>
              <p className="mt-1 font-semibold text-slate-800">{advisory.query_profile_id}</p>
              <div className="mt-3">
                <PictogramThumb profileId={advisory.query_profile_id} />
              </div>
            </div>
            <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
              <p className="font-medium">Rekomendacja (advisory)</p>
              <p className="mt-2">{advisory.recommendation_note}</p>
            </div>
          </div>

          <div>
            <h3 className="mb-3 text-base font-semibold text-slate-800">
              Top {advisory.similar.length} podobnych profili
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {advisory.similar.map((s) => (
                <div
                  key={s.profile_id}
                  className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-mono text-sm font-semibold">{s.profile_id}</p>
                      <p className="text-xs text-slate-500">#{s.rank} · score {s.score.toFixed(3)}</p>
                    </div>
                    <PictogramThumb profileId={s.profile_id} />
                  </div>
                  {s.matrices.length > 0 ? (
                    <ul className="mt-2 space-y-1 border-t border-slate-100 pt-2 text-xs">
                      {s.matrices.map((m) => (
                        <li key={m.matrix_id} className="text-slate-600">
                          <span className="font-medium text-slate-800">{m.matrix_id}</span>
                          {m.supplier_name && <> · {m.supplier_name}</>}
                          <div className="mt-0.5">
                            Skuteczność: <EffectivenessBadge pct={m.effectiveness_pct} />
                            {m.correction_count != null && m.correction_count > 0 && (
                              <span className="ml-1 text-amber-700">· {m.correction_count} korekt</span>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-xs text-slate-400">Brak danych matrycy</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {advisory.query_matrices.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-slate-700">Matryce zapytania</h3>
              <table className="mt-2 w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-slate-500">
                    <th className="py-1">Matryca</th>
                    <th>Dostawca</th>
                    <th>Skuteczność</th>
                    <th>Prasa</th>
                  </tr>
                </thead>
                <tbody>
                  {advisory.query_matrices.map((m) => (
                    <tr key={m.matrix_id} className="border-b border-slate-50">
                      <td className="py-1.5 font-mono">{m.matrix_id}</td>
                      <td>{m.supplier_name ?? '—'}</td>
                      <td><EffectivenessBadge pct={m.effectiveness_pct} /></td>
                      <td>{m.press_code ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  )
}
