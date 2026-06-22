import { useCallback, useEffect, useState } from 'react'
import {
  fetchAdvisory,
  fetchBrowse,
  pictogramUrl,
  type AdvisoryResponse,
  type ProfileListItem,
} from '@/lib/api'
import { ProfileDetailPanel } from './ProfileDetailPanel'
import { SimilarResultsGrid } from './SimilarResultsGrid'

export function SimilarityView() {
  const [profiles, setProfiles] = useState<ProfileListItem[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [search, setSearch] = useState('')
  const [method, setMethod] = useState<'embedding' | 'geometric'>('embedding')
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchBrowse({ has_pictogram: true, page_size: 200 }).then((d) => {
      setProfiles(d.items)
      if (d.items[0]) setSelectedId(d.items[0].profile_id)
    })
  }, [])

  const filtered = profiles.filter(
    (p) =>
      !search ||
      p.profile_id.toLowerCase().includes(search.toLowerCase()) ||
      (p.display_name ?? '').toLowerCase().includes(search.toLowerCase()),
  )

  const load = useCallback(async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      setAdvisory(await fetchAdvisory(selectedId, method, 10))
    } catch {
      setAdvisory(null)
    } finally {
      setLoading(false)
    }
  }, [selectedId, method])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="flex h-full">
      <div className="flex w-72 shrink-0 flex-col border-r border-white/10">
        <header className="border-b border-white/10 px-4 py-4">
          <h1 className="text-lg font-semibold text-white">Podobne profile</h1>
          <p className="text-xs text-slate-500">Wyszukiwanie po kształcie piktogramu</p>
          <input
            className="mt-3 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            placeholder="Filtruj listę…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </header>
        <ul className="flex-1 overflow-y-auto">
          {filtered.map((p) => (
            <li key={p.profile_id}>
              <button
                type="button"
                onClick={() => setSelectedId(p.profile_id)}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm ${
                  selectedId === p.profile_id ? 'bg-violet-600/20 text-white' : 'text-slate-400 hover:bg-white/5'
                }`}
              >
                <span className="truncate font-mono text-xs">{p.profile_id}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center gap-4 border-b border-white/10 px-6 py-3">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as 'embedding' | 'geometric')}
            className="rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm"
          >
            <option value="embedding">Embedding (ResNet/HOG)</option>
            <option value="geometric">Cechy geometryczne</option>
          </select>
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
          >
            {loading ? 'Szukam…' : 'Odśwież'}
          </button>
        </div>

        {advisory && (
          <div className="flex-1 overflow-y-auto p-6">
            <div className="mb-6 flex items-start gap-6">
              <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-4">
                <p className="text-xs uppercase text-violet-400">Profil zapytania</p>
                <div className="mt-2 flex h-32 w-32 items-center justify-center rounded-lg bg-white p-2">
                  <img src={pictogramUrl(advisory.query_profile_id)} alt="" className="max-h-full max-w-full" />
                </div>
                <p className="mt-2 font-mono text-sm text-white">{advisory.query_profile_id}</p>
              </div>
              <p className="max-w-xl rounded-xl border border-white/10 bg-[#161922] p-4 text-sm leading-relaxed text-slate-300">
                {advisory.recommendation_note}
              </p>
            </div>

            <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-slate-500">
              Top {advisory.similar.length} podobnych
            </h3>
            <SimilarResultsGrid similar={advisory.similar} />
          </div>
        )}
      </div>

      <div className="hidden w-96 xl:block">
        <ProfileDetailPanel profileId={selectedId} showSimilarity={false} />
      </div>
    </div>
  )
}
