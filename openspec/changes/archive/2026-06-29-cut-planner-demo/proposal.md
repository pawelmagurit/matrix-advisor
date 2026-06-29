## Why

Extral (prasownia ekstruzji, Żory) planuje cięcia profili aluminiowych na piłie końcowej ręcznie — operator decyduje o resztkach na stole biegowym i układzie wędek bez narzędzia optymalizującego. Technolog klienta wskazał brak warstwy „podpowiadającej” ponad ERP Impuls (historyczny benchmark: niemiecki Impex). Demo webowe ma pokazać wartość biznesową modułu analitycznego — łączenie zleceń, optymalizacja odpadów z uwzględnieniem kosztu remeltu — bez integracji z produkcją, jako pierwszy klocek większego systemu Magurit dla prasowni.

## What Changes

- Nowa aplikacja webowa **Magurit Cut Planner** w `tools/cut-planner-demo/` — read-only, logika w przeglądarce, polskie UI.
- Import/edycja zleceń cięcia (CSV + formularz) dla jednego profilu w sesji optymalizacji.
- Algorytm cutting stock (FFD/BFD) z trzema wariantami planu: min odpad, min wędki, zbalansowany.
- Baseline „plan ręczny”: FIFO, każde zlecenie na świeżej wędce, bez łączenia.
- Wizualizacja paska cięcia: odcinki zamówień / odpad / rzaz / **resztki na stole (szary obszar, informacyjnie — v0 nie kumuluje między wędkami)**.
- Porównanie baseline vs zoptymalizowany: % odpadu, liczba wędek, kg odpadu, koszt remeltu + szac. PLN/rok (wolumen × 12).
- Wbudowany zestaw przykładowy „Extral-like” + localStorage.
- Placeholder w menu: „Optymalizacja wyciągania — wkrótce”.
- Demo live w przeglądarce; export PDF/print — poza v0 (później).

## Capabilities

### New Capabilities

- `cut-planner`: optymalizacja cięcia profili — model danych, algorytm, warianty planu, baseline FIFO, metryki i ROI remeltu.
- `cut-planner-ui`: interfejs demo — dashboard, zlecenia, parametry, wynik z wizualizacją, porównanie; resztki jako szary obszar.

### Modified Capabilities

_(brak — to greenfield w pustym repo)_

## Impact

- Nowy podfolder `tools/cut-planner-demo/` (Vite + React + TypeScript + Tailwind).
- Brak zmian w Impuls, PSAW, PLC — moduł analityczny obok istniejących systemów klienta.
- Brak backendu, bazy danych, uwierzytelniania w v0.
- Zależności dev: Vitest (testy algorytmu), opcjonalnie `csv-parse`.
