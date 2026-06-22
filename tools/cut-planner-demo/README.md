# Magurit — moduły demo Extral

Portal webowy z dwoma modułami PoC:
- **Cut Planner** — optymalizacja cięcia profili
- **Matrix Advisor** — podobne profile, matryce, dostawcy (wymaga API Python)

## Uruchomienie (Cut Planner sam)

```bash
cd tools/cut-planner-demo
npm install
npm run dev
```

## Uruchomienie pełnego demo (Cut Planner + Matrix Advisor)

**Terminal 1** — API i dane syntetyczne:
```bash
cd tools/matrix-advisor-poc
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
matrix-advisor pipeline
matrix-advisor serve
```

**Terminal 2** — UI:
```bash
cd tools/cut-planner-demo
npm run dev
```

Zakładka **Podobne profile** — miniatury kształtów, matryce, skuteczność %, notatka advisory.

Testy algorytmu:

```bash
npm test
```

Build produkcyjny:

```bash
npm run build
npm run preview
```

## Flow demo

1. **Dashboard** → „Wczytaj przykład Extral” lub **Import CSV** (pliki w `public/`)
2. **Parametry** → panel matrycy + dł. ciągu 36 m (demo)
3. **Wynik** → 3 warianty planu + wizualizacja pasków cięcia
4. **Porównanie** → plan ręczny (Next-Fit, kolejność z pliku) vs zoptymalizowany + szac. PLN/rok

## Pliki CSV (import / udostępnienie klientowi)

W katalogu `public/`:

| Plik | Opis |
|------|------|
| `zlecenia-przyklad-extral.csv` | Gotowy zestaw 5 zleceń (matryca E06335-4, REYNAERS B) — importuj w Dashboard |
| `zlecenia-szablon.csv` | Szablon z jednym wierszem przykładowym — wyślij klientowi do uzupełnienia |

W aplikacji: **Pobierz przykład CSV** / **Pobierz szablon CSV** na Dashboardzie.  
Po edycji w Excelu zapisz jako CSV UTF-8 i zaimportuj. Eksport bieżących zleceń: zakładka **Zlecenia → Eksport CSV**.

> **Excel (polska wersja)** zapisuje CSV ze **średnikami** (`;`) zamiast przecinków — import to obsługuje automatycznie. Jeśli zmieniasz nagłówki, wymagane kolumny to: `orderId`, `profileCode`, `alloy`, `lengthMm`, `quantity` (akceptowane też aliasy: `zlecenie`, `profil`, `stop`, `dlugosc`, `ilosc`).

### Kolumny CSV

**Wymagane:**

| Kolumna | Opis | Przykład |
|---------|------|----------|
| `orderId` | Id zlecenia | `ZL-201` |
| `profileCode` | Kod profilu (jeden profil na sesję optymalizacji) | `E06335-4` |
| `alloy` | Stop | `6060` |
| `lengthMm` | Długość cięcia handlowego [mm] | `6000` |
| `quantity` | Liczba sztuk (liczba całkowita) | `6` |

**Opcjonalne:**

| Kolumna | Opis | Przykład |
|---------|------|----------|
| `matrixCode` | Id matrycy (EXD) | `E06335-4` |
| `contractor` | Kontrahent | `REYNAERS B` |
| `tolerancePlusMm` | Tolerancja + (domyślnie 10) | `10` |
| `toleranceMinusMm` | Tolerancja − (domyślnie 0) | `0` |
| `priority` | Priorytet (info) | `1` |

Przykład:

```csv
orderId,profileCode,matrixCode,contractor,alloy,lengthMm,quantity,tolerancePlusMm,toleranceMinusMm,priority
ZL-201,E06335-4,E06335-4,REYNAERS B,6060,7000,4,10,0,
```

## Terminologia (EXD / wizyta Extral)

| Pojęcie | Znaczenie |
|---------|-----------|
| **Dł. ciągu** | Odcinek z naciągarki na piłę (w EXD: kolumna w widoku wlewek; typ. ~44 m, demo: 36 m) |
| **Wiązka** | Synonim ciągu podawanego na piłę końcową |
| **Matryca** | Id narzędzia wyciskowego, np. `E06335-4` |
| **Cięcie handlowe** | Odcinek dla klienta: 3–7,5 m, tolerancja −0 / +10 mm |
| **Resztka (szary)** | Fragment ≥ progu reużywalności — stół biegowy |
| **Odpad (czerwony)** | Fragment &lt; progu → remelt |

### Przykład demo (EXD-realistic, czerwiec 2026)

Dane inspirowane screenshotami `screenshots/historia_zlecen.jpg` i `matryce.jpg`:

- **Dł. ciągu:** 36 000 mm (36 m) — celowo krótszy niż typowy odczyt EXD (~44 m), żeby demo pokazało **5→4 wiązki** i ~215 kg oszczędności
- **Matryca:** E06335-4, kontrahent REYNAERS B
- **Masa:** 5,958 kg/m
- **Zlecenia:** 3000–7200 mm (32 szt.), stop 6060

> W **Parametrach** możesz ustawić 44 200 mm jak w EXD — przy tym CSV optymalizacja często nie poprawia wyniku względem kolejności z pliku.

## Metryki

| Metryka | Opis |
|---------|------|
| **Niewykorzystany materiał** | Odpad + resztka (szary) — cały materiał poza cięciami handlowymi |
| **Odpad (waste)** | Fragment &lt; `minOffcutReusableMm` → remelt |
| **Resztka (remnant)** | Fragment ≥ progu → potencjalnie reużywalna |
| **Koszt remeltu** | `wasteKg × (1 + burn-off%) × PLN/kg` |
| **PLN/rok** | `(remelt_baseline − remelt_optimized) × sessionsPerMonth × 12` |

### Baseline „plan ręczny”

**Next-Fit w kolejności z pliku** — bez optymalizacji:

1. Zlecenia rozwijane w kolejności wierszy CSV / tabeli (najpierw wszystkie sztuki zlecenia 1, potem 2 itd.).
2. Każda sztuka trafia na **bieżącą wiązkę**, jeśli zmieści się wraz z rzazem.
3. Gdy się nie mieści — otwierana jest **nowa wiązka** i cięcie idzie tam.
4. Różne zlecenia i długości **mogą współdzielić wiązkę** — ważna jest tylko kolejność z listy, nie grupowanie po `orderId`.
5. **Nie ma** zmiany kolejności cięć ani „cofania się”, żeby lepiej wypełnić poprzednią wiązkę.

To model operatora, który tnie po kolei z kartki / wydruku, bez liczenia optymalnego układu.

### Algorytm optymalizacji

Problem to klasyczny **cutting stock** (1D bin packing): dane długości cięć, stała długość wiązki, koszt rzazu między cięciami.

Dla każdego wariantu uruchamiane są **cztery heurystyki**; wybierany jest plan z najlepszym wynikiem wg celu wariantu:

| Heurystyka | Opis |
|------------|------|
| **FFD** (First-Fit Decreasing) | Sortuj cięcia malejąco po długości; każde wstaw w **pierwszą** wiązkę, gdzie się mieści |
| **BFD** (Best-Fit Decreasing) | Sortuj malejąco; wstaw w wiązkę, która po wstawieniu ma **najmniejszą** pozostałą resztę |
| **WFD** (Worst-Fit Decreasing) | Sortuj malejąco; wstaw w wiązkę z **największą** wolną przestrzenią (więcej miejsca na kolejne krótkie odcinki) |
| **Waste-aware** | Jak BFD, ale **unika** resztek krótszych niż `minOffcutReusableMm` (odpad do remeltu zamiast „prawie dobrej” resztki) |

**Warianty planu** (z powyższych wyników wybierany jest najlepszy):

| Wariant | Cel |
|---------|-----|
| `min_waste` | Minimalizuj odpad do remeltu (`wasteMm`); przy remisie — mniej wiązek |
| `min_stocks` | Minimalizuj liczbę wiązek; przy remisie — mniej odpadu |
| `balanced` | 50% znormalizowany odpad + 50% znormalizowana liczba wiązek |

Każde cięcie na wiązce uwzględnia **rzaz** (`kerfMm`) między sąsiednimi cięciami. Końcówka wiązki dzieli się na **resztkę** (≥ próg → szary, potencjalnie reużywalna) lub **odpad** (&lt; próg → remelt).

To heurystyki demo — nie gwarantują optimum globalnego (NP-trudne), ale na zestawach typu Extral dają wyraźną poprawę względem baseline.

Przy bardzo długim ciągu (np. 44,2 m) i umiarkowanej liczbie cięć **Next-Fit w kolejności pliku** bywa już całkiem dobry — wtedy zysk z optymalizacji może być mały lub zerowy. Różnica rośnie przy krótszej wiązce, wielu długościach i „nieszczęśliwej” kolejności w CSV.

Implementacja: `src/lib/cutting/baseline.ts`, `pack.ts`, `optimize.ts`.

## Czego demo nie robi

- Integracja z BPSC Impuls, EXD, PSAW, PLC (matryca w panelu — tylko sample)
- Export PDF / print
- Optymalizacja długości wyciągania na prasie (placeholder w menu)
- Piętka, wlewki, parametry pieca / pullera
- Kumulacja resztek między dniami
- Uwierzytelnianie, backend
- Tolerancje w algorytmie (tylko info w tabeli)

## Stack

Vite + React + TypeScript + Tailwind CSS + Vitest + csv-parse
