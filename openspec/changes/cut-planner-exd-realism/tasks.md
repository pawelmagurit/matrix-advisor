## 1. Model i dane sample

- [x] 1.1 Rozszerzyć `OrderLine` w `types.ts` o opcjonalne `contractor` i `matrixCode`
- [x] 1.2 Dodać typ `MatrixInfo` i eksport sample metadata w `extral-sample.ts`
- [x] 1.3 Zaktualizować sample: ciąg 44 200 mm, kg/m 5.958, matryca E06335-4, kontrahent REYNAERS B, długości 5000/6000/7000
- [x] 1.4 Podłączyć `MatrixInfo` w `loadExtralSample()` i stanie aplikacji (`useCutPlannerState`)

## 2. Import CSV

- [x] 2.1 Rozszerzyć `csv.ts` o opcjonalne kolumny `contractor`, `matrixCode`
- [x] 2.2 Upewnić się, że eksport CSV (jeśli istnieje) uwzględnia nowe pola
- [x] 2.3 Dodać pliki `public/zlecenia-przyklad-extral.csv` i `public/zlecenia-szablon.csv` + linki pobierania w UI

## 3. UI — tabela zleceń i parametry

- [x] 3.1 Dodać kolumny Matryca i Kontrahent w `OrdersTable.tsx`
- [x] 3.2 Zmienić etykietę długości wiązki na „Dł. ciągu [m]” na ekranie parametrów (+ podpowiedź EXD)
- [x] 3.3 Utworzyć `MatrixPanel.tsx` (readonly: masa teo/rzecz, typ, otwory, prasa, placeholder rysunku)
- [x] 3.4 Wyświetlić `MatrixPanel` na zakładce Parametry; ukryć / empty state gdy brak metadata

## 4. UI — styl EXD

- [x] 4.1 Ciemny header i dopasowane zakładki w `App.tsx` (industrial tone)
- [x] 4.2 Placeholder „Rysunek techniczny” / piktogram profilu w panelu matrycy

## 5. Testy i dokumentacja

- [x] 5.1 Zaktualizować testy używające starych stałych sample (np. `pack.test.ts`)
- [x] 5.2 Zaktualizować README: nowy format CSV, źródło danych EXD, breaking change sample
- [x] 5.3 Ręczna weryfikacja: wczytaj sample → optymalizuj → porównanie (metryki i PLN z nowym kg/m)
