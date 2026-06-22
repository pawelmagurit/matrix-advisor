## Why

Extral posiada ~15 000 profili aluminiowych i historię matryc, ale wybór dostawcy i ocena podobieństwa nowych kształtów opiera się na doświadczeniu narzędziowni. Celem PoC jest pipeline badawczy: wyszukiwanie historycznie podobnych profili po piktogramie (BLOB z bazy), z późniejszym podpięciem matryc, dostawców i skuteczności produkcyjnej. Moduł cut planner pozostaje w repo jako osobny, mniej priorytetowy wątek.

## What Changes

- Nowy pakiet Python `tools/matrix-advisor-poc/` — pipeline: ingest → normalize → features → index → query.
- Model domeny: Profile (1) → Matrix (*), Supplier, MatrixProductionSummary.
- Import z eksportów (CSV + folder piktogramów); brak API Impuls/EXD w PoC.
- Normalizacja konturów (bez skali — tylko kształt).
- Dwa indeksy podobieństwa: geometric baseline + embeddingi obrazów.
- CLI `matrix-advisor query --profile-id … --top-k 10`.
- Syntetyczne dane próbki do testów przed eksportem klienta.
- Spec główna: `openspec/specs/matrix-advisor/001-profile-similarity-foundation/spec.md`.

## Capabilities

### New Capabilities

- `matrix-advisor`: ingestion, normalizacja piktogramów, podobieństwo profili, indeks ANN, query CLI.

### Modified Capabilities

_(brak — greenfield)_

## Impact

- `tools/matrix-advisor-poc/` — nowy kod Python.
- `data/` — katalogi na surowe/przetworzone dane (gitignored).
- `evaluation/` — gold set (później).
- Brak zmian w `tools/cut-planner-demo/`.

## Business Decisions (2026-06-16)

| Temat | Decyzja |
|-------|---------|
| Skuteczność matrycy | % — im wyższa, tym lepiej; wzór dostarczy klient |
| Profil ↔ matryca | 1 profil → wiele matryc; matryca nie współdzielona między profilami |
| Dostawca | nazwa tekstowa, per matryca |
| Piktogram | BLOB/obrazek dla wszystkich profili; bez skali, tylko kontur |
| Źródło danych | eksporty CSV + pliki; bez API |
| Użytkownicy | technolog, planista, narzędziowiec, R&D + handlowcy |
| Podobieństwo | kontur, liczba komór, grubość ścianek |
| Infra PoC | lokalnie; ML/CV bez ograniczeń na start |

**Zaparkowane:** definicja nieudanej pierwszej produkcji, algorytm prób udanych/nieudanych, RODO, normalizacja piktogramów w źródle (weryfikacja po próbce).
