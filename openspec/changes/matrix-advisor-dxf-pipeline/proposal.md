## Why

Główny use case Matrix Advisor to **nowe zamówienie**: klient wysyła profil, którego jeszcze nie ma w bazie Extral, a technolog musi znaleźć historycznie podobne kształty i ocenić matryce/dostawców. Dziś workflow opiera się na **GIF/piktogramie** — format pochodny, bez wymiarów i bez precyzyjnej geometrii wewnętrznej.

Mamy próbki rzeczywistych rysunków CAD (`data/die/rysunki/`: 5 par DXF+PDF dla E02004, E03148, E04900, E08594, E12223). Analiza pokazuje, że z **DXF** da się wyciągnąć kontur, wymiary (`DIMENSION`), grubość ścianki i metadane tabelki — dane niedostępne w GIF. **PDF odpuszczamy** jako ścieżkę przetwarzania (brak tekstu, gorsze niż DXF).

Potrzebujemy DXF-first pipeline, dwuetapowego wyszukiwania (kształt → filtry/reranking) oraz wielokryteriowego scoringu, żeby odróżniać profile „podobne zewnętrznie”, ale różniące się kanałami, kieszeniami lub wymiarami.

## What Changes

- **DXF-first pipeline**: import → parser → normalizacja geometrii → renderer piktogramu → embedding + cechy deterministyczne → indeks + SQLite/JSON pochodne
- **Źródło prawdy**: oryginalny plik DXF (nie JSON Extral, nie PDF); JSON/SQLite jako dane pochodne z możliwością regeneracji
- **Upload DXF** jako główny input w „Nowe zamówienie” (GIF/PNG pozostaje kompatybilnością wsteczną dla istniejącej bazy ~10k profili)
- **Dwuetapowe wyszukiwanie**: Stage 1 — top N (~20–30) po kształcie; Stage 2 — filtry wymiarowe + reranking wielokryteriowy
- **Wielokryteriowy scoring**: shape embedding, kontur zewnętrzny, szczegóły wewnętrzne (kieszenie/kanały), wymiary, metadane — wagi na MVP hardcoded, architektura pod konfigurację
- **Wzbogacenie advisory**: wymiary z DXF + walidacja vs metadane Extral (`wlasnosci`)
- **UI**: upload DXF, podgląd piktogramu, wyniki z rozbiciem score, filtry wymiarowe, wskaźniki dopasowania metadanych
- **Generalizacja parsera** na poziomie plików jak w `data/die/rysunki/` (dwa style rysunku, geometria w modelspace vs blokach `EAL_*`)
- **Bez PDF/OCR**, bez DWG w MVP (DXF jako standard wymiany; DWG → konwersja poza scope)
- **Bez** rekomendacji matrycy/dostawcy, predykcji skuteczności, integracji Impuls — przygotowanie architektury pod przyszłe moduły

## Capabilities

### New Capabilities

- `matrix-advisor-dxf-pipeline`: Parser DXF, normalizacja geometrii, renderer piktogramu, ekstrakcja wymiarów/cech, model danych pochodnych, status przetwarzania, regeneracja z DXF
- `matrix-advisor-two-stage-search`: Stage 1 shape search (top N), Stage 2 filtry wymiarowe i reranking, API i kontrakt odpowiedzi
- `matrix-advisor-multi-criteria-scoring`: Wymiary podobieństwa, wagi, breakdown score w API/UI, rozróżnianie profili z różną geometrią wewnętrzną

### Modified Capabilities

- `matrix-advisor-query-upload`: Główny format uploadu → DXF; rozszerzenie o Stage 2 i scoring breakdown; GIF/PNG jako legacy fallback
- `matrix-advisor-extral-integration-ui`: UI wyników z filtrami wymiarowymi, breakdown score, metadane/walidacja, upload DXF

## Impact

- `tools/matrix-advisor-poc/src/matrix_advisor/` — nowe moduły: `dxf/` (parser, normalizer, renderer), rozszerzenie `features/`, `query/`, `index/`
- `pyproject.toml` — zależność `ezdxf` (opcjonalnie `[cad]` extra obok `[ml]`)
- `data/` — `raw/dxf/`, `processed/geometry/` (JSON), istniejące `processed/masks/` generowane z DXF lub GIF
- API: `POST /api/v1/query/by-dxf`, rozszerzenie advisory/search o `stage`, `filters`, `score_breakdown`
- Frontend: `NewOrderView`, lista wyników, panel filtrów Stage 2
- Istniejący bootstrap Extral (GIF z JSON) **bez zmian** w pierwszej fazie; migracja profili na DXF jako osobny batch później
- Blokuje / współpracuje z: `004-supplier-ranking` (później), nie implementuje go teraz
