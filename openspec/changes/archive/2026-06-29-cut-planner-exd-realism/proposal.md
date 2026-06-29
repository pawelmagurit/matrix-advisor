## Why

Demo Cut Planner działa, ale dane przykładowe i etykiety UI są generyczne (profil `E-08421`, wiązka 36 m, 1,2 kg/m) — nie odzwierciedlają systemu **EXD / Impuls**, który klient pokazał na screenshotach (matryce `E06335-4`, ciąg ~44,2 m, ~6 kg/m, kontrahent REYNAERS, długości 5000/6000/7000). Przed prezentacją warto dopasować demo do ich języka i liczb, żeby moduł wyglądał jak warstwa analityczna **obok** istniejącego systemu, a nie osobny produkt SaaS.

## What Changes

- Aktualizacja zestawu przykładowego **Extral-like v2** — liczby i identyfikatory ze screenshotów EXD (`screenshots/`).
- Rozszerzenie modelu zlecenia o opcjonalne pola **kontrahent** i **matryca** (format `E#####-##`).
- Etykiety parametrów zgodne z EXD: **Dł. ciągu [m]** zamiast ogólnego „długość wiązki”, **Matryca** w tabeli zleceń.
- Panel **Matryca (readonly)** — masa teoretyczna/rzeczywista, typ, prasa, placeholder rysunku technicznego.
- Rozszerzony format CSV importu o opcjonalne kolumny `contractor`, `matrixCode`.
- Dopasowanie tonu wizualnego nagłówka / zakładek do stylu EXD (industrial, ciemny header — bez kopiowania pełnego brandingu).
- Aktualizacja README i testów odwołujących się do starych wartości sample.

**BREAKING:** Domyślny sample zmienia `stockLengthMm` (36 000 → 44 200), `kgPerMeter` (1,2 → ~5,958), kody profilu/matrycy i zestaw zleceń — istniejące dane w localStorage użytkownika mogą być nadpisane po „Wczytaj przykład”.

## Capabilities

### New Capabilities

_(brak — rozszerzamy istniejące capability demo)_

### Modified Capabilities

- `cut-planner`: rozszerzony model zlecenia (kontrahent, matryca), zaktualizowany sample dataset EXD-realistic, rozszerzony CSV.
- `cut-planner-ui`: kolumny i etykiety EXD, panel matrycy readonly, dopasowany header/zakładki, placeholder piktogramu profilu.

## Impact

- `tools/cut-planner-demo/src/data/extral-sample.ts` — nowe wartości sample.
- `tools/cut-planner-demo/src/lib/cutting/types.ts` — opcjonalne pola `contractor`, `matrixCode`; opcjonalny typ `MatrixInfo`.
- `tools/cut-planner-demo/src/components/` — `OrdersTable`, ekran parametrów, nowy `MatrixPanel.tsx`.
- `tools/cut-planner-demo/src/App.tsx` — layout header / zakładki.
- Testy w `tests/cutting/` — aktualizacja stałych sample.
- Brak zmian w algorytmie optymalizacji, Impuls, backendzie.
