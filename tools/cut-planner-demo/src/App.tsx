import { useMemo, useState } from 'react'
import { CutLegend } from '@/components/CutBar'
import { ComparisonTable } from '@/components/ComparisonTable'
import { MatrixAdvisorView } from '@/components/MatrixAdvisorView'
import { MatrixPanel } from '@/components/MatrixPanel'
import { OrdersTable } from '@/components/OrdersTable'
import { PlanComparisonView } from '@/components/PlanComparisonView'
import { useCutPlannerState } from '@/hooks/useCutPlannerState'
import { downloadOrdersCsv, readCsvFile } from '@/lib/csv'
import { optimize } from '@/lib/cutting/optimize'
import type { CutPlan, PlanVariant } from '@/lib/cutting/types'

type Tab = 'dashboard' | 'orders' | 'params' | 'results' | 'compare' | 'matrices'

const TABS: { id: Tab; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'matrices', label: 'Podobne profile' },
  { id: 'orders', label: 'Zlecenia' },
  { id: 'params', label: 'Parametry' },
  { id: 'results', label: 'Wynik' },
  { id: 'compare', label: 'Porównanie' },
]

function exportPlanJson(plan: CutPlan) {
  const blob = new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `plan-${plan.variant}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export default function App() {
  const {
    orders,
    setOrders,
    config,
    setConfig,
    matrixInfo,
    loadSample,
    clearMatrixInfo,
  } = useCutPlannerState()
  const [tab, setTab] = useState<Tab>('dashboard')
  const [csvError, setCsvError] = useState<string | null>(null)
  const [selectedVariant, setSelectedVariant] = useState<PlanVariant>('min_waste')
  const [roiView, setRoiView] = useState<'remelt' | 'scrap'>('remelt')

  const result = useMemo(() => {
    if (orders.length === 0) return null
    try {
      return optimize(orders, config)
    } catch {
      return null
    }
  }, [orders, config])

  const ciagMetry = (config.stockLengthMm / 1000).toFixed(1)

  const handleCsv = async (file: File) => {
    const { orders: parsed, error } = await readCsvFile(file)
    if (error) {
      setCsvError(error)
      return
    }
    setCsvError(null)
    setOrders(parsed)
    clearMatrixInfo()
    if (parsed.length > 0) {
      const profile = parsed[0].profileCode
      setConfig((c) => ({ ...c, profileCode: profile }))
    }
    setTab('orders')
  }

  const handleLoadSample = () => {
    loadSample()
    setTab('results')
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-700 bg-[#1a2332] text-white shadow-md">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="text-xl font-bold tracking-tight">Magurit — moduły Extral</h1>
          <p className="text-sm text-slate-300">Cut Planner · Matrix Advisor (demo PoC)</p>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-0.5 overflow-x-auto border-t border-slate-700/80 px-4">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                tab === t.id
                  ? 'border-sky-400 bg-slate-800/50 text-white'
                  : 'border-transparent text-slate-400 hover:border-slate-500 hover:text-slate-200'
              }`}
            >
              {t.label}
            </button>
          ))}
          <span
            className="ml-auto cursor-not-allowed self-center whitespace-nowrap px-3 py-1.5 text-xs text-slate-500"
            title="Moduł planowany w kolejnej wersji"
          >
            Optymalizacja wyciągania — wkrótce
          </span>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {tab === 'matrices' && <MatrixAdvisorView />}

        {tab === 'dashboard' && (
          <section className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Optymalizacja cięcia profili aluminiowych</h2>
              <p className="mt-2 text-sm text-slate-600">
                Demo modułu analitycznego dla piły końcowej — łączy zlecenia na ten sam profil,
                minimalizuje odpad (koszt remeltu) i liczbę wiązek. Warstwa obok EXD / Impuls — bez
                integracji na żywo.
              </p>
              <div className="mt-3 rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <p className="font-medium">Dane z systemu Extral (EXD / screenshoty Impuls)</p>
                <ul className="mt-1 list-inside list-disc space-y-1 text-slate-600">
                  <li>
                    <strong>Dł. ciągu</strong> — w przykładzie demo 36 m (w EXD często ~44 m; zmienisz w
                    Parametrach).
                  </li>
                  <li>
                    <strong>Matryca</strong> — E06335-4; <strong>kontrahent</strong> — REYNAERS B.
                  </li>
                  <li>
                    Zlecenia: 3000–7200 mm, 32 szt. — zestaw pokazujący 5→4 wiązki po optymalizacji.
                  </li>
                </ul>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => setTab('matrices')}
                  className="rounded bg-sky-700 px-4 py-2 text-sm font-medium text-white hover:bg-sky-600"
                >
                  Podobne profile (Matrix Advisor)
                </button>
                <button
                  type="button"
                  onClick={handleLoadSample}
                  className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
                >
                  Wczytaj przykład Extral
                </button>
                <label className="cursor-pointer rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50">
                  Import CSV
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) void handleCsv(file)
                    }}
                  />
                </label>
                <a
                  href={`${import.meta.env.BASE_URL}zlecenia-przyklad-extral.csv`}
                  download="zlecenia-przyklad-extral.csv"
                  className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
                >
                  Pobierz przykład CSV
                </a>
                <a
                  href={`${import.meta.env.BASE_URL}zlecenia-szablon.csv`}
                  download="zlecenia-szablon.csv"
                  className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
                >
                  Pobierz szablon CSV
                </a>
              </div>
              {csvError && <p className="mt-2 text-sm text-red-600">{csvError}</p>}
              <p className="mt-3 text-xs text-slate-500">
                Wyślij klientowi <strong>szablon CSV</strong> do uzupełnienia własnymi zleceniami,
                albo rozszerz <strong>przykład CSV</strong> i zaimportuj w aplikacji. Szczegóły kolumn
                — w README.
              </p>
            </div>
          </section>
        )}

        {tab === 'orders' && (
          <section>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">Zlecenia cięcia</h2>
              {orders.length > 0 && (
                <button
                  type="button"
                  onClick={() => downloadOrdersCsv(orders, 'zlecenia-export.csv')}
                  className="rounded border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium hover:bg-slate-50"
                >
                  Eksport CSV
                </button>
              )}
            </div>
            {orders.length === 0 ? (
              <p className="text-sm text-slate-600">
                Brak zleceń — wczytaj przykład, importuj CSV (
                <a
                  href={`${import.meta.env.BASE_URL}zlecenia-przyklad-extral.csv`}
                  className="text-sky-700 underline"
                >
                  pobierz plik
                </a>
                ) lub użyj szablonu.
              </p>
            ) : (
              <OrdersTable orders={orders} onChange={setOrders} />
            )}
          </section>
        )}

        {tab === 'params' && (
          <section className="space-y-4">
            <MatrixPanel matrixInfo={matrixInfo} />
            <div className="max-w-lg space-y-3 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Parametry piły / materiału</h2>
              <p className="text-xs text-slate-500">
                Dł. ciągu odpowiada polu „Dł. ciągu [m]” w EXD (wlewki). Obecnie:{' '}
                <strong>{ciagMetry} m</strong> = {config.stockLengthMm.toLocaleString('pl-PL')} mm.
              </p>
              {(
                [
                  ['profileCode', 'Kod profilu / matrycy (sesja)', 'text'],
                  ['stockLengthMm', 'Dł. ciągu [m] — długość wiązki [mm]', 'number'],
                  ['kerfMm', 'Szerokość rzazu [mm]', 'number'],
                  ['kgPerMeter', 'Masa [kg/m]', 'number'],
                  ['minOffcutReusableMm', 'Min. resztka reużywalna [mm]', 'number'],
                  ['remeltCostPerKg', 'Koszt remeltu [PLN/kg]', 'number'],
                  ['burnOffPercent', 'Burn-off [%]', 'number'],
                  ['sessionsPerMonth', 'Sesje optymalizacji / miesiąc', 'number'],
                  ['scrapPricePerKg', 'Cena złomu zewn. [PLN/kg] (info)', 'number'],
                ] as const
              ).map(([key, label, type]) => (
                <label key={key} className="block text-sm">
                  <span className="text-slate-700">{label}</span>
                  <input
                    type={type}
                    className="mt-1 w-full rounded border border-slate-200 px-3 py-2"
                    value={config[key] ?? ''}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        [key]: type === 'number' ? Number(e.target.value) : e.target.value,
                      })
                    }
                  />
                </label>
              ))}
            </div>
          </section>
        )}

        {tab === 'results' && (
          <section>
            <h2 className="mb-3 text-lg font-semibold">Wynik optymalizacji</h2>
            {!result ? (
              <p className="text-sm text-slate-600">Dodaj zlecenia, aby wyliczyć plan.</p>
            ) : (
              <>
                <CutLegend />
                <PlanComparisonView
                  baseline={result.baseline}
                  result={result}
                  config={config}
                  selectedVariant={selectedVariant}
                  onVariantChange={setSelectedVariant}
                  onExportJson={exportPlanJson}
                />
              </>
            )}
          </section>
        )}

        {tab === 'compare' && (
          <section>
            <h2 className="mb-3 text-lg font-semibold">Porównanie: ręcznie vs zoptymalizowany</h2>
            {!result ? (
              <p className="text-sm text-slate-600">Brak danych do porównania.</p>
            ) : (
              <>
                <p className="mb-3 text-sm text-slate-600">
                  Porównanie względem wariantu <strong>Najmniej odpadu</strong> (min. materiału do
                  remeltu).
                </p>
                <div className="mb-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => setRoiView('remelt')}
                    className={`rounded px-3 py-1.5 text-sm ${
                      roiView === 'remelt'
                        ? 'bg-slate-800 text-white'
                        : 'border border-slate-300 bg-white'
                    }`}
                  >
                    ROI — koszt remeltu
                  </button>
                  <button
                    type="button"
                    onClick={() => setRoiView('scrap')}
                    className={`rounded px-3 py-1.5 text-sm ${
                      roiView === 'scrap'
                        ? 'bg-amber-600 text-white'
                        : 'border border-slate-300 bg-white'
                    }`}
                  >
                    ROI — złom zewnętrzny (info)
                  </button>
                </div>
                <ComparisonTable
                  baseline={result.baseline}
                  optimized={result.min_waste}
                  sessionsPerMonth={config.sessionsPerMonth ?? 1}
                  roiView={roiView}
                  minOffcutReusableMm={config.minOffcutReusableMm}
                  stockLengthMm={config.stockLengthMm}
                  kgPerMeter={config.kgPerMeter}
                />
              </>
            )}
          </section>
        )}
      </main>
    </div>
  )
}
