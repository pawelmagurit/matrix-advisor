# Matrix Advisor — Extral

Moduł doradczy matryc ekstruzyjnych: przeglądarka **10 877 profili** z eksportu Extral, historia matryc, dostawcy, skuteczność oraz wyszukiwanie **podobnych profili** po piktogramie.

Cut Planner (`tools/cut-planner-demo/`) pozostaje osobnym modułem demo.

## Wymagania

- Python 3.11+
- Node.js 20+ (UI)
- Opcjonalnie `[ml]` dla embeddingów ResNet18 (bez tego — fallback HOG)

## Instalacja

```bash
cd tools/matrix-advisor-poc
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

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
| **Nowe zamówienie** | Upload piktogramu z oferty → podobne profile z historii |
| **Podobne profile** | Zapytanie po kształcie + rekomendacja na podstawie historii matryc |
| **Moduły Extral** | Ekosystem narzędzi (Matrix Advisor aktywny, Cut Planner demo) |

## CLI — najważniejsze komendy

```bash
matrix-advisor ingest-extral              # sam import JSON → SQLite
matrix-advisor normalize                  # maski 256×256 z GIF/PNG
matrix-advisor build-index --method all   # indeks geometryczny + embedding
matrix-advisor query -p E06335-4 -m geometric --table
matrix-advisor serve                      # samo API (:8765)
```

## API (v0.2)

```
GET /api/v1/health
GET /api/v1/stats
GET /api/v1/filters/suppliers|owners|statuses
GET /api/v1/profiles?search=&supplier=&owner=&status=&page=&page_size=
GET /api/v1/profiles/{id}
GET /api/v1/profiles/{id}/pictogram?raw=true
GET /api/v1/profiles/{id}/advisory?method=embedding&top_k=8
POST /api/v1/query/by-image   # multipart: file, method, top_k, label
```

## Struktura danych

```
data/
├── die/matryce - dane v2.json   # eksport klienta
├── raw/pictograms/              # GIF/PNG z base64
├── processed/masks/             # znormalizowane maski
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
