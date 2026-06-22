import { useCallback, useEffect, useState } from 'react'
import {
  fetchBrowse,
  fetchOwners,
  fetchStatuses,
  fetchSuppliers,
  pictogramUrl,
  type ProfileListItem,
} from '@/lib/api'

type Props = {
  selectedId: string | null
  onSelect: (id: string) => void
}

function EffBadge({ pct }: { pct: number | null }) {
  if (pct == null) return <span className="text-slate-600">—</span>
  const cls =
    pct >= 75
      ? 'bg-emerald-500/15 text-emerald-400'
      : pct >= 55
        ? 'bg-amber-500/15 text-amber-400'
        : 'bg-red-500/15 text-red-400'
  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>{pct.toFixed(0)}%</span>
}

export function ProfileBrowser({ selectedId, onSelect }: Props) {
  const [search, setSearch] = useState('')
  const [supplier, setSupplier] = useState('')
  const [owner, setOwner] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [items, setItems] = useState<ProfileListItem[]>([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [suppliers, setSuppliers] = useState<string[]>([])
  const [owners, setOwners] = useState<string[]>([])
  const [statuses, setStatuses] = useState<Array<{ code: string; label: string }>>([])

  useEffect(() => {
    Promise.all([fetchSuppliers(), fetchOwners(), fetchStatuses()]).then(
      ([s, o, st]) => {
        setSuppliers(s.suppliers)
        setOwners(o.owners)
        setStatuses(st.statuses.map((x) => ({ code: x.code, label: x.label || x.code })))
      },
    )
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchBrowse({
        search: search || undefined,
        supplier: supplier || undefined,
        owner: owner || undefined,
        status: status || undefined,
        page,
        page_size: 48,
      })
      setItems(data.items)
      setTotal(data.total)
      setPages(data.pages)
    } finally {
      setLoading(false)
    }
  }, [search, supplier, owner, status, page])

  useEffect(() => {
    const t = setTimeout(() => void load(), search ? 300 : 0)
    return () => clearTimeout(t)
  }, [load, search])

  useEffect(() => {
    setPage(1)
  }, [search, supplier, owner, status])

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-white/10 px-6 py-4">
        <h1 className="text-xl font-semibold text-white">Przeglądarka profili</h1>
        <p className="mt-1 text-sm text-slate-500">
          {total.toLocaleString('pl-PL')} profili · filtruj po dostawcy matrycy, właścicielu, statusie
        </p>
      </header>

      <div className="flex flex-wrap gap-3 border-b border-white/10 px-6 py-3">
        <input
          type="search"
          placeholder="Szukaj indeksu lub nazwy…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-[200px] flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:border-violet-500/50 focus:outline-none"
        />
        <select
          value={supplier}
          onChange={(e) => setSupplier(e.target.value)}
          className="rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-slate-300"
        >
          <option value="">Wszyscy dostawcy</option>
          {suppliers.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          className="rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-slate-300"
        >
          <option value="">Wszyscy właściciele</option>
          {owners.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-slate-300"
        >
          <option value="">Wszystkie statusy</option>
          {statuses.map((s) => (
            <option key={s.code} value={s.code}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading && items.length === 0 ? (
          <p className="text-center text-slate-500">Ładowanie…</p>
        ) : items.length === 0 ? (
          <p className="text-center text-slate-500">Brak wyników. Zaimportuj dane: matrix-advisor bootstrap-extral</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
            {items.map((p) => (
              <button
                key={p.profile_id}
                type="button"
                onClick={() => onSelect(p.profile_id)}
                className={`group flex flex-col rounded-xl border p-2 text-left transition hover:border-violet-500/40 hover:bg-white/[0.03] ${
                  selectedId === p.profile_id
                    ? 'border-violet-500/60 bg-violet-500/10 ring-1 ring-violet-500/30'
                    : 'border-white/10 bg-[#161922]'
                }`}
              >
                <div className="flex aspect-square items-center justify-center overflow-hidden rounded-lg bg-white p-1">
                  {p.has_pictogram ? (
                    <img
                      src={pictogramUrl(p.profile_id)}
                      alt=""
                      className="max-h-full max-w-full object-contain"
                      loading="lazy"
                    />
                  ) : (
                    <span className="text-xs text-slate-600">brak</span>
                  )}
                </div>
                <p className="mt-2 truncate text-xs font-medium text-slate-200">{p.profile_id}</p>
                <p className="truncate text-[10px] text-slate-500">{p.display_name}</p>
                <div className="mt-1 flex items-center justify-between text-[10px]">
                  <span className="text-slate-600">{p.matrix_count} matr.</span>
                  <EffBadge pct={p.best_effectiveness_pct} />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {pages > 1 && (
        <footer className="flex items-center justify-between border-t border-white/10 px-6 py-3">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded px-3 py-1 text-sm text-slate-400 disabled:opacity-30"
          >
            ← Poprzednia
          </button>
          <span className="text-sm text-slate-500">
            Strona {page} / {pages}
          </span>
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded px-3 py-1 text-sm text-slate-400 disabled:opacity-30"
          >
            Następna →
          </button>
        </footer>
      )}
    </div>
  )
}
