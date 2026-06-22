## 1. Scaffold

- [x] 1.1 Utworzyć `tools/matrix-advisor-poc/` — pyproject.toml, pakiet `matrix_advisor`, `.gitignore` dla `data/`
- [x] 1.2 Dodać README z formatem eksportu CSV + uruchomieniem pipeline

## 2. Model i baza

- [x] 2.1 Zdefiniować modele Pydantic i schemat SQLite (`models.py`, `db.py`)
- [x] 2.2 CLI `init-db` i konfiguracja ścieżek `data/`

## 3. Ingestion

- [x] 3.1 Importer `profiles.csv` + katalog piktogramów
- [x] 3.2 Importer opcjonalny `matrices.csv` (dostawca, skuteczność)
- [x] 3.3 Generator `sample-data` (syntetyczne kontury)

## 4. Normalizacja

- [x] 4.1 Pipeline binaryzacji, crop, resize 256×256, metadata JSON
- [x] 4.2 CLI `normalize`

## 5. Geometric baseline

- [x] 5.1 Ekstrakcja cech (aspect, holes, area, perimeter, solidity, Hu moments)
- [x] 5.2 Indeks + odległość L2; zapis `data/index/geometric.npz`

## 6. Embeddings

- [x] 6.1 ResNet18 embedding (+ HOG fallback bez torch)
- [x] 6.2 Indeks cosine + 4 rotacje; zapis `data/index/embedding.npz`

## 7. Query i testy

- [x] 7.1 CLI `build-index` i `query --profile-id --method --top-k`
- [x] 7.2 Testy: ingest sample → normalize → index → query zwraca wyniki
## 8. Extral production data (completed 2026-06-19)

- [x] 8.1 Importer `ingest-extral` z `matryce - dane v2.json` (base64 GIF, matryce, dostawcy)
- [x] 8.2 Rozszerzenie schematu DB (owner, masa, ścianka, status matrycy)
- [x] 8.3 API v0.2: browse, filtry, stats, advisory
- [x] 8.4 Web UI Matrix Advisor (`web/`) — przeglądarka, podobieństwo, moduły
- [x] 8.5 `bootstrap-extral` + `matrix-advisor dev` (jedno uruchomienie)
- [x] 8.6 Testy integracyjne `test_api_extral.py` (9 passed na pełnym zbiorze)
