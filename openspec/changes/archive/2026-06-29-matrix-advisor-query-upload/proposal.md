## Why

Technolog Extral przy **nowym zamówieniu** dostaje piktogram profilu, którego jeszcze nie ma w historii (lub nie zna indeksu). Dziś Matrix Advisor pozwala szukać podobieństwa tylko dla profili już w bazie. Potrzebujemy **ad-hoc query**: wrzucam obraz → widzę, czy coś podobnego było robione, z jakimi matrycami i skutecznością — **bez zapisu do bazy produkcyjnej**.

## What Changes

- Nowy endpoint `POST /api/v1/query/by-image` — upload GIF/PNG/JPEG, odpowiedź jak `advisory`
- Pipeline query-time: walidacja → normalizacja tymczasowa → embedding/geometric przeciw istniejącemu indeksowi
- Nowy widok UI **„Nowe zamówienie”** — drag & drop piktogramu, wyniki podobnych profili + historia matryc
- Opcjonalne metadane zamówienia (nr oferty, notatka) — tylko w sesji, nie w SQLite
- Jawny tryb **ephemeral** — upload nie modyfikuje `profiles`, indeksu ani plików w `data/`
- Testy: API upload + query z przykładowym plikiem GIF

## Capabilities

### New Capabilities

- `matrix-advisor-query-upload`: Ad-hoc similarity search from uploaded pictogram for new-order workflow

### Modified Capabilities

- (brak — istniejące API browse/advisory pozostają bez zmian)

## Impact

- `tools/matrix-advisor-poc/src/matrix_advisor/api/server.py` — nowy endpoint POST
- `tools/matrix-advisor-poc/src/matrix_advisor/query/` — serwis ad-hoc query
- `tools/matrix-advisor-poc/web/` — nowy widok + komponent uploadu
- Brak zmian w bootstrap / imporcie JSON
- Runtime: nadal wymaga załadowanego indeksu i modelu embedding (jak dziś przy advisory)
