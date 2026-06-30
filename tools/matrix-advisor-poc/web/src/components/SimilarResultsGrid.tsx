import type { UploadQueryResponse } from '@/lib/api'

type SimilarHit = UploadQueryResponse['similar'][number]

export function SimilarResultsGrid({
  similar,
  lowScoreWarning,
  showBreakdown = false,
}: {
  similar: SimilarHit[]
  lowScoreWarning?: boolean
  showBreakdown?: boolean
}) {
  if (similar.length === 0) {
    return <p className="text-sm text-slate-500">Brak podobnych profili w indeksie.</p>
  }

  return (
    <>
      {lowScoreWarning && (
        <p className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          Niskie podobieństwo (poniżej 50%) — wyniki mogą być mało trafne. Zweryfikuj jakość pliku.
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {similar.map((s) => (
          <SimilarResultCard key={s.profile_id} hit={s} showBreakdown={showBreakdown} />
        ))}
      </div>
    </>
  )
}

function SimilarResultCard({ hit, showBreakdown }: { hit: SimilarHit; showBreakdown: boolean }) {
  const displayScore = hit.total_score ?? hit.score
  const shapeScore = hit.shape_score ?? hit.score

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
            #{hit.rank} · {(displayScore * 100).toFixed(1)}% łącznie
          </p>
          <p className="font-mono text-sm font-medium text-white">{hit.profile_id}</p>
          <p className="truncate text-xs text-slate-500">{hit.display_name}</p>
          {showBreakdown && hit.shape_score != null && (
            <p className="mt-1 text-[10px] text-slate-500">
              kształt {(shapeScore * 100).toFixed(0)}%
              {hit.score_breakdown?.dimension != null && (
                <> · wymiary {(hit.score_breakdown.dimension * 100).toFixed(0)}%</>
              )}
            </p>
          )}
        </div>
      </div>
      {showBreakdown && hit.score_breakdown && (
        <div className="mt-2 flex flex-wrap gap-1">
          {Object.entries(hit.score_breakdown).map(([k, v]) =>
            v != null ? (
              <span
                key={k}
                className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-400"
                title={k}
              >
                {k.replace('_', ' ').slice(0, 8)} {(v * 100).toFixed(0)}%
              </span>
            ) : null,
          )}
        </div>
      )}
      {hit.matrices.length > 0 && (
        <div className="mt-3 border-t border-white/5 pt-3 text-[11px] text-slate-500">
          Najlepsza matryca: {hit.matrices[0].matrix_id} · {hit.matrices[0].supplier_name ?? '—'} ·{' '}
          {hit.matrices[0].effectiveness_pct?.toFixed(0) ?? '—'}%
        </div>
      )}
    </article>
  )
}
