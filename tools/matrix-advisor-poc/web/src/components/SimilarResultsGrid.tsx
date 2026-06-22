import type { AdvisoryResponse } from '@/lib/api'

type SimilarHit = AdvisoryResponse['similar'][number]

export function SimilarResultsGrid({
  similar,
  lowScoreWarning,
}: {
  similar: SimilarHit[]
  lowScoreWarning?: boolean
}) {
  if (similar.length === 0) {
    return <p className="text-sm text-slate-500">Brak podobnych profili w indeksie.</p>
  }

  return (
    <>
      {lowScoreWarning && (
        <p className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          Niskie podobieństwo (poniżej 50%) — wyniki mogą być mało trafne. Zweryfikuj jakość
          piktogramu.
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {similar.map((s) => (
          <SimilarResultCard key={s.profile_id} hit={s} />
        ))}
      </div>
    </>
  )
}

function SimilarResultCard({ hit }: { hit: SimilarHit }) {
  return (
    <article className="rounded-xl border border-white/10 bg-[#161922] p-4 transition hover:border-violet-500/30">
      <div className="flex gap-3">
        <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-lg bg-white p-1">
          <img
            src={`/api/v1/profiles/${encodeURIComponent(hit.profile_id)}/pictogram?raw=true`}
            alt=""
            className="max-h-full max-w-full object-contain"
          />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-violet-400">
            #{hit.rank} · {(hit.score * 100).toFixed(1)}% podobieństwa
          </p>
          <p className="font-mono text-sm font-medium text-white">{hit.profile_id}</p>
          <p className="truncate text-xs text-slate-500">{hit.display_name}</p>
        </div>
      </div>
      {hit.matrices.length > 0 && (
        <div className="mt-3 border-t border-white/5 pt-3 text-[11px] text-slate-500">
          Najlepsza matryca: {hit.matrices[0].matrix_id} · {hit.matrices[0].supplier_name ?? '—'} ·{' '}
          {hit.matrices[0].effectiveness_pct?.toFixed(0) ?? '—'}%
        </div>
      )}
    </article>
  )
}
