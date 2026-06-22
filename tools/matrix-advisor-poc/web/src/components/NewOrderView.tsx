import { useCallback, useRef, useState } from 'react'
import { fetchQueryByImage, type UploadQueryResponse } from '@/lib/api'
import { SimilarResultsGrid } from './SimilarResultsGrid'

const LOW_SCORE_THRESHOLD = 0.5

export function NewOrderView() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [label, setLabel] = useState('')
  const [method, setMethod] = useState<'embedding' | 'geometric'>('embedding')
  const [result, setResult] = useState<UploadQueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const searchWithFile = useCallback(
    async (f: File, searchMethod: 'embedding' | 'geometric', searchLabel: string) => {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchQueryByImage(f, searchMethod, 8, searchLabel || undefined)
        setResult(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Błąd wyszukiwania')
        setResult(null)
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const acceptFile = useCallback(
    (f: File, autoSearch = false) => {
      if (!/\.(gif|png|jpe?g)$/i.test(f.name)) {
        setError('Dozwolone formaty: GIF, PNG, JPEG')
        return
      }
      if (f.size > 5 * 1024 * 1024) {
        setError('Plik za duży (max 5 MB)')
        return
      }
      setError(null)
      setFile(f)
      setResult(null)
      setPreviewUrl((prev) => {
        if (prev?.startsWith('blob:')) URL.revokeObjectURL(prev)
        return URL.createObjectURL(f)
      })
      if (autoSearch) void searchWithFile(f, method, label)
    },
    [method, label, searchWithFile],
  )

  const topScore = result?.similar[0]?.score ?? 0
  const lowScore = result != null && result.similar.length > 0 && topScore < LOW_SCORE_THRESHOLD

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <header className="border-b border-white/10 px-6 py-4">
        <h1 className="text-xl font-semibold text-white">Nowe zamówienie</h1>
        <p className="mt-1 text-sm text-slate-500">
          Wrzuć piktogram profilu — sprawdzimy, czy robiliście coś podobnego w historii produkcji
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
              if (f) acceptFile(f, true)
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
              accept="image/gif,image/png,image/jpeg"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) acceptFile(f, false)
              }}
            />
            <p className="text-3xl text-slate-600">↑</p>
            <p className="mt-2 text-sm font-medium text-slate-300">Przeciągnij piktogram lub kliknij</p>
            <p className="mt-1 text-xs text-slate-500">GIF, PNG, JPEG · max 5 MB</p>
          </div>

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

          <button
            type="button"
            disabled={!file || loading}
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

          {(result?.query_preview || previewUrl) && (
            <div className="rounded-xl border border-white/10 bg-[#161922] p-3">
              <p className="text-xs uppercase text-slate-500">
                {result?.query_preview ? 'Znormalizowany kontur' : 'Podgląd zapytania'}
              </p>
              <div className="mt-2 flex h-40 items-center justify-center rounded-lg bg-black p-2">
                <img
                  src={result?.query_preview ?? previewUrl ?? ''}
                  alt="Podgląd"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
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
              </div>
              <h2 className="text-sm font-medium uppercase tracking-wider text-slate-500">
                Top {result.similar.length} podobnych profili
              </h2>
              <SimilarResultsGrid similar={result.similar} lowScoreWarning={lowScore} />
            </div>
          ) : (
            <div className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-white/10 bg-[#161922] text-sm text-slate-600">
              {loading ? 'Przetwarzanie…' : 'Wgraj piktogram, aby zobaczyć podobne profile z historii'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
