# Matrix Advisor — Extral

Moduł doradczy matryc ekstruzyjnych: przeglądarka **10 877 profili** z eksportu Extral, historia matryc, dostawcy, skuteczność oraz wyszukiwanie **podobnych profili** po piktogramie.

Cut Planner (`tools/cut-planner-demo/`) pozostaje osobnym modułem demo.

## Wymagania

- Python 3.11+
- Node.js 20+ (UI)
- Opcjonalnie `[ml]` dla embeddingów ResNet18 (bez tego — fallback HOG)
- Opcjonalnie `[cad]` dla importu i uploadu DXF (`ezdxf`)

## Instalacja

```bash
cd tools/matrix-advisor-poc
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"    # zawiera ml + cad (ezdxf)

cd web && npm install && cd ..
```

## Uruchomienie (jedna komenda)

```bash
# 1. Import danych klienta (pierwszy raz; ~2–5 min na pełny JSON + indeks)
matrix-advisor bootstrap-extral          # pełny zestaw ~10k profili
# lub szybki test:
matrix-advisor bootstrap-extral --limit 200 --skip-index

# 2. API + UI
matrix-advisor dev                       # http://127.0.0.1:5173
```

Źródło danych: `data/die/matryce - dane v2.json`

## Co zawiera UI

| Widok | Opis |
|-------|------|
| **Przeglądarka profili** | Siatka piktogramów, filtry: dostawca matrycy, właściciel profilu, status, wyszukiwanie |
| **Nowe zamówienie** | Upload **DXF** (zalecane) lub GIF/PNG → podobne profile, etap 2 z filtrami wymiarowymi |
| **Podobne profile** | Zapytanie po kształcie + rekomendacja na podstawie historii matryc |
| **Moduły Extral** | Ekosystem narzędzi (Matrix Advisor aktywny, Cut Planner demo) |

## CLI — najważniejsze komendy

```bash
matrix-advisor ingest-extral              # sam import JSON → SQLite
matrix-advisor normalize                  # maski 256×256 z GIF/PNG
matrix-advisor build-index --method all   # indeks geometryczny + embedding
matrix-advisor query -p E06335-4 -m geometric --table
matrix-advisor import-dxf --dir ../../data/die/rysunki   # batch DXF → geometry + walidacja
matrix-advisor process-dxf -p E08594                   # jeden profil
matrix-advisor serve                      # samo API (:8765)
```

### DXF pipeline

- **Źródło prawdy:** plik DXF w `data/raw/dxf/`
- **Pochodne:** `data/processed/geometry/*.json`, maski, wymiary w SQLite
- **PDF nie jest obsługiwany** — używaj DXF
- Obsługiwane konwencje rysunków jak w `data/die/rysunki/` (warstwy `01.Profil`, bloki `EAL_*`, wymiary `DIMENSION`)

## API (v0.4)

```
GET /api/v1/health
GET /api/v1/stats
GET /api/v1/filters/suppliers|owners|statuses
GET /api/v1/profiles?search=&supplier=&owner=&status=&page=&page_size=
GET /api/v1/profiles/{id}
GET /api/v1/profiles/{id}/pictogram?raw=true
GET /api/v1/profiles/{id}/advisory?method=embedding&top_k=8
GET /api/v1/profiles/{id}/dimensions
GET /api/v1/profiles/{id}/geometry
POST /api/v1/query/by-image   # multipart: file, method, top_k, label (legacy GIF/PNG)
POST /api/v1/query/by-dxf     # multipart: file, method, top_k, stage, filters, label
POST /api/v1/search/similar   # profile_id lub DXF + stage + filters
```

## Struktura danych

```
data/
├── die/matryce - dane v2.json   # eksport klienta
├── raw/pictograms/              # GIF/PNG z base64
├── raw/dxf/                     # oryginalne DXF (source of truth)
├── processed/masks/             # znormalizowane maski
├── processed/geometry/          # geometry.json z DXF
├── processed/features/          # features.json
├── index/                       # geometric.npz, embedding.npz
└── matrix_advisor.db
```

## Testy

```bash
pytest   # 9 testów: pipeline sample + API na pełnych danych Extral
```

Wymaga wcześniejszego `bootstrap-extral`. Testy integracyjne (`test_api_extral.py`) są pomijane, gdy baza ma &lt;1000 profili.

### Checklist UI (ręczna, ~5 min)

Po `matrix-advisor dev` → http://127.0.0.1:5173

| # | Scenariusz | Oczekiwany wynik |
|---|------------|------------------|
| 1 | Przeglądarka → filtr dostawcy (np. WILKE2) + szukaj `E02098` | Lista się zawęża, wyniki pasują |
| 2 | Klik profil | Panel boczny: piktogram, matryce, skuteczność % |
| 3 | Panel → zakładka „Podobne” | 6 wyników + notatka rekomendacji |
| 4 | Widok „Podobne profile” → zmiana embedding ↔ geometric | Wyniki się odświeżają, score malejąco |
| 5 | Paginacja (strona 2) | Kolejna porcja 48 profili |
| 6 | Profil bez piktogramu (jeśli trafisz) | Brak crashu, placeholder „brak” |
| 7 | **Nowe zamówienie** → wrzuć GIF | Podgląd konturu + lista podobnych + notatka |

### Smoke test API (opcjonalnie)

```bash
curl -s http://127.0.0.1:8765/api/v1/health | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/v1/profiles?page_size=2" | python3 -m json.tool
```

## Następny etap

Change **`matrix-advisor-query-upload`** (planowany):

- Upload nowego piktogramu → wyszukiwanie podobnych bez zapisu do bazy
- Ranking dostawców: ważona skuteczność `Σ(skuteczność% × ilośćProdukcji) / Σ(ilośćProdukcji)` w kontekście podobnych profili

## Specyfikacja

- `openspec/specs/matrix-advisor/001-profile-similarity-foundation/spec.md` — fundament
- `openspec/specs/matrix-advisor/002-extral-integration-ui/spec.md` — ten etap (Extral + UI)
