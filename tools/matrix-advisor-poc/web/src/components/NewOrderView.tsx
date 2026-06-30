import { useCallback, useRef, useState } from 'react'
import {
  fetchDxfPreview,
  fetchQueryByDxf,
  fetchQueryByImage,
  type DxfPreviewResponse,
  type UploadQueryResponse,
} from '@/lib/api'
import { SimilarResultsGrid } from './SimilarResultsGrid'

const LOW_SCORE_THRESHOLD = 0.5

export function NewOrderView() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [dxfPreview, setDxfPreview] = useState<DxfPreviewResponse | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [label, setLabel] = useState('')
  const [method, setMethod] = useState<'embedding' | 'geometric'>('embedding')
  const [stage, setStage] = useState<1 | 2>(2)
  const [wallMin, setWallMin] = useState('')
  const [wallMax, setWallMax] = useState('')
  const [result, setResult] = useState<UploadQueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const buildFilters = () => {
    const f: Record<string, { min?: number; max?: number }> = {}
    if (wallMin || wallMax) {
      f.wall_thickness_mm = {}
      if (wallMin) f.wall_thickness_mm.min = parseFloat(wallMin)
      if (wallMax) f.wall_thickness_mm.max = parseFloat(wallMax)
    }
    return Object.keys(f).length ? f : undefined
  }

  const loadDxfPreview = useCallback(async (f: File) => {
    setPreviewLoading(true)
    setDxfPreview(null)
    try {
      const preview = await fetchDxfPreview(f)
      setDxfPreview(preview)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nie udało się wygenerować podglądu DXF')
      setDxfPreview(null)
    } finally {
      setPreviewLoading(false)
    }
  }, [])

  const searchWithFile = useCallback(
    async (f: File, searchMethod: 'embedding' | 'geometric', searchLabel: string) => {
      setLoading(true)
      setError(null)
      try {
        const isDxf = /\.dxf$/i.test(f.name)
        const filters = stage === 2 ? buildFilters() : undefined
        const data = isDxf
          ? await fetchQueryByDxf(f, searchMethod, 30, stage, searchLabel || undefined, filters)
          : await fetchQueryByImage(f, searchMethod, 8, searchLabel || undefined)
        setResult(data)
        if (isDxf && data.query_preview) {
          setDxfPreview((prev) =>
            prev?.query_preview === data.query_preview
              ? prev
              : {
                  filename: f.name,
                  profile_id: prev?.profile_id ?? f.name.replace(/\.dxf$/i, '').toUpperCase(),
                  profile_id_hint: f.name.replace(/\.dxf$/i, '').toUpperCase(),
                  query_preview: data.query_preview,
                  extracted_dimensions: data.extracted_dimensions,
                  quality_flags: data.quality_flags,
                },
          )
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Błąd wyszukiwania')
        setResult(null)
      } finally {
        setLoading(false)
      }
    },
    [stage, wallMin, wallMax],
  )

  const acceptFile = useCallback(
    (f: File) => {
      const isDxf = /\.dxf$/i.test(f.name)
      const isImage = /\.(gif|png|jpe?g)$/i.test(f.name)
      if (!isDxf && !isImage) {
        setError('Dozwolone: DXF (zalecane) lub GIF/PNG/JPEG')
        return
      }
      const max = isDxf ? 10 * 1024 * 1024 : 5 * 1024 * 1024
      if (f.size > max) {
        setError(`Plik za duży (max ${isDxf ? 10 : 5} MB)`)
        return
      }
      setError(null)
      setFile(f)
      setResult(null)
      setDxfPreview(null)
      if (isImage) {
        setPreviewUrl((prev) => {
          if (prev?.startsWith('blob:')) URL.revokeObjectURL(prev)
          return URL.createObjectURL(f)
        })
      } else {
        setPreviewUrl(null)
        void loadDxfPreview(f)
      }
    },
    [loadDxfPreview],
  )

  const topScore = result?.similar[0]?.score ?? 0
  const lowScore = result != null && result.similar.length > 0 && topScore < LOW_SCORE_THRESHOLD
  const activePreview = dxfPreview?.query_preview ?? previewUrl
  const dimensions = dxfPreview?.extracted_dimensions ?? result?.extracted_dimensions

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <header className="border-b border-white/10 px-6 py-4">
        <h1 className="text-xl font-semibold text-white">Nowe zamówienie</h1>
        <p className="mt-1 text-sm text-slate-500">
          Wrzuć plik DXF z przekrojem profilu — wyszukamy podobne kształty w historii produkcji
        </p>
      </header>

      <div className="grid flex-1 gap-6 p-6 lg:grid-cols-[340px_1fr]">
        <div className="space-y-4">
          <div
            role="button"
            tabIndex={0}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragOver(false)
              const f = e.dataTransfer.files[0]
              if (f) acceptFile(f)
            }}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
            className={`flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition ${
              dragOver
                ? 'border-violet-500 bg-violet-500/10'
                : 'border-white/20 bg-[#161922] hover:border-violet-500/40'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".dxf,image/gif,image/png,image/jpeg"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) acceptFile(f)
              }}
            />
            <p className="text-3xl text-slate-600">↑</p>
            <p className="mt-2 text-sm font-medium text-slate-300">Przeciągnij DXF lub kliknij</p>
            <p className="mt-1 text-xs text-slate-500">DXF (zalecane) · GIF/PNG max 5 MB</p>
            {file && (
              <p className="mt-3 max-w-full truncate text-xs text-violet-300" title={file.name}>
                {file.name}
              </p>
            )}
          </div>

          {(previewLoading || activePreview || dxfPreview) && (
            <div className="rounded-xl border border-white/10 bg-[#161922] p-3">
              <p className="text-xs uppercase text-slate-500">
                {dxfPreview ? 'Piktogram z DXF' : 'Podgląd zapytania'}
              </p>
              {dxfPreview && (
                <div className="mt-1 space-y-0.5 text-xs text-slate-400">
                  <p>
                    Plik: <span className="font-mono text-slate-200">{dxfPreview.filename}</span>
                  </p>
                  {dxfPreview.profile_id_hint && (
                    <p>
                      Indeks:{' '}
                      <span className="font-mono text-violet-300">{dxfPreview.profile_id_hint}</span>
                    </p>
                  )}
                </div>
              )}
              <div className="mt-2 flex h-40 items-center justify-center rounded-lg bg-black p-2">
                {previewLoading ? (
                  <p className="text-xs text-slate-500">Generuję piktogram…</p>
                ) : activePreview ? (
                  <img
                    src={activePreview}
                    alt="Podgląd przekroju profilu"
                    className="max-h-full max-w-full object-contain"
                  />
                ) : null}
              </div>
              {dxfPreview?.preview_warning && (
                <p className="mt-2 rounded border border-amber-500/30 bg-amber-500/10 px-2 py-1.5 text-[11px] leading-relaxed text-amber-200">
                  {dxfPreview.preview_warning}
                </p>
              )}
              {dxfPreview?.selection && (
                <p className="mt-2 text-[10px] text-slate-600">
                  Geometria: {dxfPreview.selection.strategy}
                  {dxfPreview.selection.layer ? ` · ${dxfPreview.selection.layer}` : ''}
                  {dxfPreview.selection.block ? ` · ${dxfPreview.selection.block}` : ''}
                </p>
              )}
            </div>
          )}

          <input
            type="text"
            placeholder="Etykieta (np. nr oferty) — opcjonalnie"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-600"
          />

          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as 'embedding' | 'geometric')}
            className="w-full rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-slate-300"
          >
            <option value="embedding">Embedding (głębokie)</option>
            <option value="geometric">Geometryczne (kontur)</option>
          </select>

          <select
            value={stage}
            onChange={(e) => setStage(Number(e.target.value) as 1 | 2)}
            className="w-full rounded-lg border border-white/10 bg-[#1a1d27] px-3 py-2 text-sm text-slate-300"
          >
            <option value={1}>Etap 1 — tylko kształt</option>
            <option value={2}>Etap 2 — kształt + wymiary (reranking)</option>
          </select>

          {stage === 2 && (
            <div className="rounded-lg border border-white/10 bg-[#161922] p-3 text-xs text-slate-400">
              <p className="mb-2 font-medium text-slate-300">Filtr grubości ścianki [mm]</p>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="min"
                  value={wallMin}
                  onChange={(e) => setWallMin(e.target.value)}
                  className="w-full rounded border border-white/10 bg-white/5 px-2 py-1 text-white"
                />
                <input
                  type="number"
                  placeholder="max"
                  value={wallMax}
                  onChange={(e) => setWallMax(e.target.value)}
                  className="w-full rounded border border-white/10 bg-white/5 px-2 py-1 text-white"
                />
              </div>
            </div>
          )}

          <button
            type="button"
            disabled={!file || loading || previewLoading || (file && /\.dxf$/i.test(file.name) && !dxfPreview)}
            onClick={() => file && void searchWithFile(file, method, label)}
            className="w-full rounded-lg bg-violet-600 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-40"
          >
            {loading ? 'Szukam podobnych…' : 'Szukaj podobnych'}
          </button>

          {error && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          )}

          {dimensions && (
            <div className="rounded-xl border border-white/10 bg-[#161922] p-3 text-xs">
              <p className="text-slate-500">Wymiary z DXF</p>
              <dl className="mt-2 grid grid-cols-2 gap-1 text-slate-300">
                {Object.entries(dimensions).map(([k, v]) =>
                  v != null ? (
                    <span key={k} className="col-span-2">
                      {k}: <span className="font-mono text-white">{v}</span>
                    </span>
                  ) : null,
                )}
              </dl>
            </div>
          )}
        </div>

        <div>
          {result ? (
            <div className="space-y-4">
              {result.index_warning && (
                <p className="rounded-lg border border-amber-500/40 bg-amber-500/15 px-3 py-2 text-sm text-amber-200">
                  {result.index_warning}
                </p>
              )}
              <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-4">
                <p className="text-xs uppercase text-violet-400">Wynik dla</p>
                <p className="text-lg font-medium text-white">{result.query_display_name}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">{result.recommendation_note}</p>
                {result.stage === 2 && result.stage2_count != null && (
                  <p className="mt-1 text-xs text-slate-500">
                    Etap 2: {result.stage2_count} / {result.stage1_count} kandydatów po filtrach
                  </p>
                )}
              </div>
              <h2 className="text-sm font-medium uppercase tracking-wider text-slate-500">
                Top {result.similar.length} podobnych profili
              </h2>
              <SimilarResultsGrid similar={result.similar} lowScoreWarning={lowScore} showBreakdown={stage === 2} />
            </div>
          ) : (
            <div className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-white/10 bg-[#161922] text-sm text-slate-600">
              {loading
                ? 'Przetwarzanie…'
                : previewLoading
                  ? 'Generuję podgląd piktogramu…'
                  : 'Wgraj DXF profilu, sprawdź podgląd i kliknij „Szukaj podobnych”'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
