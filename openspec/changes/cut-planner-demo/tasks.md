## 1. Project scaffold

- [x] 1.1 Utworzyć `tools/cut-planner-demo/` — Vite + React + TypeScript + Tailwind
- [x] 1.2 Dodać Vitest i skrypt testów; skonfigurować alias `@/` do `src/`
- [x] 1.3 Dodać zależność `csv-parse` (import CSV w przeglądarce)

## 2. Model danych i dane przykładowe

- [x] 2.1 Zdefiniować typy: `OrderLine`, `CutSessionConfig`, `CutPlan`, `StockBar`, `CutPiece` w `src/lib/cutting/types.ts`
- [x] 2.2 Zaimplementować `src/data/extral-sample.ts` — profil E-08421, 5 zleceń ZL-101…105
- [x] 2.3 Dodać helper `expandOrderLines()` — rozwinięcie quantity → lista sztuk z `orderId` i `pieceIndex`

## 3. Algorytm cutting stock (testy najpierw)

- [x] 3.1 Testy: bilans długości wędki (cięcia + kerf + remnant + waste = stockLengthMm)
- [x] 3.2 Testy: klasyfikacja offcut — poniżej `minOffcutReusableMm` → waste, powyżej → remnant
- [x] 3.3 Zaimplementować FFD i BFD w `src/lib/cutting/pack.ts`
- [x] 3.4 Zaimplementować `optimize.ts` — warianty `min_waste`, `min_stocks`, `balanced`
- [x] 3.5 Zaimplementować baseline FIFO w `src/lib/cutting/baseline.ts` (kolejność wejścia, bez łączenia zleceń)
- [x] 3.6 Zaimplementować `metrics.ts` — waste %, kg, remelt PLN, burn-off
- [x] 3.7 Test integracyjny: dataset Extral — optymalizacja < 1 s, wyraźna poprawa vs baseline

## 4. UI — szkielet i nawigacja

- [x] 4.1 Layout aplikacji: nagłówek „Magurit Cut Planner”, nawigacja (Dashboard, Zlecenia, Parametry, Wynik, Porównanie)
- [x] 4.2 Placeholder menu: „Optymalizacja wyciągania — wkrótce” (disabled)
- [x] 4.3 Hook localStorage — persystencja zleceń i `CutSessionConfig`

## 5. UI — ekrany

- [x] 5.1 Dashboard — opis modułu, przycisk „Wczytaj przykład Extral”, upload CSV
- [x] 5.2 Zlecenia — edytowalna tabela (orderId, profil, stop, długość, ilość, tolerancje info)
- [x] 5.3 Parametry — stockLengthMm, kerf, kg/m, minOffcutReusable, remeltCost, burnOff, sessionsPerMonth
- [x] 5.4 Parser CSV → `OrderLine[]` z walidacją i komunikatem błędu po polsku

## 6. UI — wizualizacja i wyniki

- [x] 6.1 Komponent `CutBar` — pasek poziomy: cięcia (kolor per orderId), kerf, waste (czerwony), **remnant (szary)** + etykieta „stół biegowy”
- [x] 6.2 Legenda/tooltip: szary = resztka reużywalna, v0 nie kumuluje między sesjami
- [x] 6.3 Trzy karty wariantów z metrykami; wybór wariantu → lista wędek z `CutBar`
- [x] 6.4 Ekran Porównanie — tabela baseline FIFO vs wybrany wariant: % odpadu, wędki, kg, PLN remeltu, **szac. PLN/rok** (× 12)
- [x] 6.5 Widok ROI: domyślnie koszt remeltu; opcjonalnie wartość złomu zewnętrznego (informacyjnie)

## 7. Export i dokumentacja

- [x] 7.1 Export JSON wybranego planu cięcia (download)
- [x] 7.2 README: uruchomienie, format CSV, definicje metryk, szary obszar, formuła PLN/rok, sekcja „Czego demo nie robi”

## 8. Weryfikacja końcowa

- [x] 8.1 Przejść kryteria akceptacji z promptu (sample 1 klik, 3 warianty < 1 s, porównanie z baseline, czytelny pasek)
- [x] 8.2 Demo live w przeglądarce — pełny flow bez backendu
