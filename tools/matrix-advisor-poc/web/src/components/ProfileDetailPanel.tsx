import { useEffect, useState } from 'react'
import { fetchAdvisory, fetchProfile, pictogramUrl, type AdvisoryResponse, type ProfileDetail } from '@/lib/api'

type Props = {
  profileId: string | null
  onClose?: () => void
  showSimilarity?: boolean
}

function EffBadge({ pct }: { pct: number | null }) {
  if (pct == null) return <span className="text-slate-600">—</span>
  const cls =
    pct >= 75
      ? 'text-emerald-400'
      : pct >= 55
        ? 'text-amber-400'
        : 'text-red-400'
  return <span className={`font-mono text-sm font-medium ${cls}`}>{pct.toFixed(1)}%</span>
}

export function ProfileDetailPanel({ profileId, onClose, showSimilarity = true }: Props) {
  const [profile, setProfile] = useState<ProfileDetail | null>(null)
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null)
  const [method, setMethod] = useState<'embedding' | 'geometric'>('embedding')
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'matrices' | 'similar'>('matrices')

  useEffect(() => {
    if (!profileId) {
      setProfile(null)
      setAdvisory(null)
      return
    }
    setLoading(true)
    fetchProfile(profileId)
      .then(setProfile)
      .finally(() => setLoading(false))
  }, [profileId])

  useEffect(() => {
    if (!profileId || !showSimilarity) return
    fetchAdvisory(profileId, method, 6)
      .then(setAdvisory)
      .catch(() => setAdvisory(null))
  }, [profileId, method, showSimilarity])

  if (!profileId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-600">
        Wybierz profil z listy
      </div>
    )
  }

  if (loading && !profile) {
    return <div className="p-6 text-slate-500">Ładowanie…</div>
  }

  if (!profile) return null

  return (
    <div className="flex h-full flex-col overflow-hidden border-l border-white/10 bg-[#12141c]">
      <div className="flex items-start justify-between border-b border-white/10 p-4">
        <div className="flex gap-4">
          <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-lg bg-white p-2">
            {profile.has_pictogram ? (
              <img src={pictogramUrl(profile.profile_id)} alt="" className="max-h-full max-w-full object-contain" />
            ) : (
              <span className="text-xs text-slate-500">brak piktogramu</span>
            )}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">{profile.profile_id}</h2>
            <p className="text-sm text-slate-400">{profile.display_name}</p>
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <dt className="text-slate-600">Właściciel</dt>
              <dd className="text-slate-300">{profile.owner_contractor ?? '—'}</dd>
              <dt className="text-slate-600">Masa</dt>
              <dd className="text-slate-300">{profile.masa_g_m != null ? `${profile.masa_g_m} g/m` : '—'}</dd>
              <dt className="text-slate-600">Ścianka</dt>
              <dd className="text-slate-300">
                {profile.wall_thickness_mm != null ? `${profile.wall_thickness_mm} mm` : '—'}
              </dd>
            </dl>
          </div>
        </div>
        {onClose && (
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-white">
            ✕
          </button>
        )}
      </div>

      {showSimilarity && (
        <div className="flex border-b border-white/10 text-sm">
          <Tab active={tab === 'matrices'} onClick={() => setTab('matrices')}>
            Matryce ({profile.matrices.length})
          </Tab>
          <Tab active={tab === 'similar'} onClick={() => setTab('similar')}>
            Podobne
          </Tab>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4">
        {(!showSimilarity || tab === 'matrices') && (
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-500">
                <th className="pb-2 pr-2">Matryca</th>
                <th className="pb-2 pr-2">Dostawca</th>
                <th className="pb-2 pr-2">Typ</th>
                <th className="pb-2 pr-2">Komory</th>
                <th className="pb-2 pr-2">Skutecz.</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {profile.matrices.map((m) => (
                <tr key={m.matrix_id} className="border-t border-white/5 text-slate-300">
                  <td className="py-2 pr-2 font-mono">{m.matrix_id}</td>
                  <td className="py-2 pr-2">{m.supplier_name ?? '—'}</td>
                  <td className="py-2 pr-2">{m.die_type ?? '—'}</td>
                  <td className="py-2 pr-2">{m.cavity_count ?? '—'}</td>
                  <td className="py-2 pr-2">
                    <EffBadge pct={m.effectiveness_pct} />
                  </td>
                  <td className="py-2 text-slate-500">{m.status_label ?? m.status_code ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {showSimilarity && tab === 'similar' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Metoda:</span>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as 'embedding' | 'geometric')}
                className="rounded border border-white/10 bg-[#1a1d27] px-2 py-1 text-xs text-slate-300"
              >
                <option value="embedding">Embedding (głębokie)</option>
                <option value="geometric">Geometryczne (kontur)</option>
              </select>
            </div>
            {advisory?.recommendation_note && (
              <p className="rounded-lg bg-violet-500/10 px-3 py-2 text-xs leading-relaxed text-violet-200">
                {advisory.recommendation_note}
              </p>
            )}
            <div className="space-y-3">
              {advisory?.similar.map((s) => (
                <div key={s.profile_id} className="flex gap-3 rounded-lg border border-white/10 p-2">
                  <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded bg-white p-1">
                    <img src={pictogramUrl(s.profile_id)} alt="" className="max-h-full max-w-full object-contain" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-white">
                      #{s.rank} {s.profile_id}{' '}
                      <span className="font-mono text-violet-400">{(s.score * 100).toFixed(0)}%</span>
                    </p>
                    <p className="truncate text-xs text-slate-500">{s.display_name}</p>
                    {s.matrices[0] && (
                      <p className="mt-1 text-[10px] text-slate-500">
                        {s.matrices[0].supplier_name} · skutecz.{' '}
                        {s.matrices[0].effectiveness_pct?.toFixed(0) ?? '—'}%
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {advisory?.similar.length === 0 && (
                <p className="text-xs text-slate-500">Brak indeksu — uruchom build-index</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Tab({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-4 py-2 ${active ? 'border-b-2 border-violet-500 text-white' : 'text-slate-500'}`}
    >
      {children}
    </button>
  )
}
