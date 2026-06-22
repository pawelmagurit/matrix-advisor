# Prompt: demo „Optymalizacja cięcia” dla Extral (Magurit)

Skopiuj poniższy blok do Cursora / agenta budującego prototyp.

---

## PROMPT (kopiuj od tej linii)

Zbuduj **wstępne demo webowe** modułu **Optymalizacja cięcia profili aluminiowych** — pierwszy klocek większego systemu analitycznego dla prasowni ekstruzji (klient: Extral, Żory). Demo ma pokazać **wartość biznesową bez integracji z ERP/PLC** — read-only, dane z CSV lub formularza.

### Kontekst biznesowy

Prasownia wyciska profile aluminiowe na długie odcinki (wędki), potem **piła końcowa** tnie je na długości handlowe z zamówień. Dziś operator po zakończeniu zlecenia **ręcznie** planuje: jaką resztkę zostawić na stole biegowym, jaką następną wędkę założyć, jak rozłożyć cięcia — patrząc głównie na **jeden dzień**, bez narzędzia optymalizującego.

Historyczny benchmark (opisany przez technologa klienta): niemiecki MES **Impex** — warstwa produkcyjna, która **dobierała długości**, pokazywała operatorowi **kilka opcji** (np. przy danej długości wyciągania i temperaturze) i optymalizowała wykorzystanie materiału.

**Nasz produkt (MVP):** „Impex-lite” — **plan cięcia + symulacja odpadów**, nie sterowanie maszyną.

**Ekonomia odpadów u tego klienta:** offcuty nie idą na złom zewnętrzny — firma ma **własny Re-Melt** (przetop). Oszczędność = głównie **koszt przetopu** (energia ~200–400 PLN/t, burn-off 2–5%, logistyka, segregacja stopów), **nie** różnica „cena profilu − cena złomu”. W UI pokaż oba widoki ROI, domyślnie **koszt remeltu**.

---

### Zakres MVP (v0 demo)

**W scope:**
1. Import / edycja **zleceń cięcia** na jeden **profil** (ten sam kształt/stop w jednej sesji optymalizacji).
2. Parametry **wędki wejściowej** (długość dostępna na piłę, np. 6000–7500 mm) i **szerokość rzazu** piły (kerf, np. 3–5 mm).
3. **Algorytm optymalizacji** (cutting stock / bin packing): minimalizacja długości odpadu lub liczby wędek przy zadanych ograniczeniach.
4. **Łączenie wielu zleceń** na ten sam profil w jeden plan (to główny quick win).
5. Widok **dla operatora**: 2–3 **warianty planu** (np. „najmniej odpadu”, „najmniej wędek”, „najszybsze cięcie”) z wizualizacją — pasek długości z kolorami: odcinki zamówień / odpad / rzaz.
6. **Porównanie** „plan ręczny (baseline)” vs „plan zoptymalizowany” na tych samych danych — metryki: % odpadu, liczba wędek, kg odpadu (jeśli podano kg/m).
7. **Dane syntetyczne** — wbudowany zestaw przykładowy „Extral-like” (polskie UI, profile okienkowe, długości 3–7,5 m).
8. Export planu: JSON + czytelny PDF/print view (opcjonalnie).

**Poza scope v0 (nie implementuj):**
- Integracja z BPSC Impuls, PSAW, PLC
- Optymalizacja długości **wyciągania na prasie** (osobny moduł — tylko placeholder w menu)
- Wielowymiarowe ograniczenia matrycy (max długość wyciągania zależna od kształtu)
- Uwierzytelnianie, multi-tenant, produkcja

---

### Model danych

#### Zlecenie (OrderLine)
```typescript
{
  orderId: string;           // np. "ZL-2026-0412"
  profileCode: string;       // np. "E-12345" — wszystkie linie w jednej optymalizacji = ten sam profileCode
  alloy: string;             // np. "6060", "6082" — do segregacji odpadów (informacyjnie)
  lengthMm: number;          // długość docelowa jednej sztuki [mm]
  quantity: number;          // ile sztuk
  tolerancePlusMm?: number;  // domyślnie 10
  toleranceMinusMm?: number; // domyślnie 0
  priority?: number;         // 1 = najwyższy
}
```

#### Parametry piły / materiału (CutSessionConfig)
```typescript
{
  profileCode: string;
  kgPerMeter?: number;       // do przeliczenia kg odpadu
  stockLengthMm: number;     // długość jednej wędki na wejściu piły
  kerfMm: number;            // szerokość rzazu
  minOffcutReusableMm: number;  // poniżej = odpad do remeltu (np. 200)
  remeltCostPerKg?: number;  // domyślnie 0.30 PLN/kg (300 PLN/t)
  burnOffPercent?: number;   // domyślnie 3%
}
```

#### Plan cięcia (CutPlan)
```typescript
{
  variant: "min_waste" | "min_stocks" | "balanced";
  stocks: Array<{
    stockIndex: number;
    stockLengthMm: number;
    cuts: Array<{ orderId: string; lengthMm: number; pieceIndex: number }>;
    kerfLossMm: number;
    remnantMm: number;       // reszta na stole / remelt
    wasteMm: number;         // fragmenty < minOffcutReusable
  }>;
  metrics: {
    totalWasteMm: number;
    totalWasteKg?: number;
    wastePercent: number;
    stockCount: number;
    remeltCostPln?: number;
  };
}
```

---

### Reguły algorytmu

1. Każda wędka: `sum(cuts) + (n_cuts - 1) * kerf + remnant + waste = stockLengthMm` (lub remnant wraca na stół — w v0 uprość: każda wędka niezależna).
2. Długość cięcia musi mieścić się w tolerancji zamówienia (dla demo: cięcie = `lengthMm`, tolerancja tylko informacyjna).
3. **Optymalizacja:** użyj znanych heurystyk cutting stock (FFD, BFD) + opcjonalnie dokładniejszy solver (ILP) dla N ≤ 30 linii zleceń — wybierz implementację prostą, ale poprawną.
4. **Łączenie zleceń:** wszystkie `OrderLine` z tym samym `profileCode` w jednym problemie.
5. **Warianty:**
   - `min_waste` — minimalizuj sumę `wasteMm + remnantMm` (lub tylko waste jeśli remnant reużywalny > minOffcutReusable)
   - `min_stocks` — minimalizuj liczbę wędek
   - `balanced` — ważona funkcja celu (50% waste, 50% stocks)

6. **Baseline „ręczny”:** symuluj naiwną strategię: zlecenia w kolejności wejścia, każde zlecenie na świeżej wędce, bez łączenia — do porównania.

---

### UI / UX (demo dla technologa + operatora)

**Język interfejsu:** polski.

**Ekrany:**
1. **Dashboard** — krótki opis modułu + „Wczytaj przykład Extral” + upload CSV.
2. **Zlecenia** — tabela edytowalna (profil, długość, ilość, zlecenie).
3. **Parametry** — długość wędki, kerf, kg/m, koszt remeltu.
4. **Wynik** — trzy karty wariantów + **pasek wizualny** cięcia (jak timeline / strip packing).
5. **Porównanie** — tabela: ręcznie vs zoptymalizowany (% odpadu, wędki, szac. PLN/rok przy założonym wolumenie).

**Ton wizualny:** industrial, czytelny, bez „AI hype” — to narzędzie decyzyjne dla produkcji.

**Nagłówek produktu (placeholder):** „Magurit Cut Planner” / „Planer cięcia — moduł Extral”.

---

### Przykładowe dane demo (hardcode)

Profil: `E-08421` (system okienny), stop `6060`, kg/m = 1.2, wędka = 6500 mm, kerf = 4 mm.

| Zlecenie | Długość [mm] | Ilość |
|----------|--------------|-------|
| ZL-101 | 4200 | 8 |
| ZL-102 | 3800 | 6 |
| ZL-103 | 2100 | 12 |
| ZL-104 | 1500 | 20 |
| ZL-105 | 6000 | 4 |

Oczekiwany efekt demo: zoptymalizowany plan **wyraźnie** lepszy od baseline (mniej wędek lub kilka–kilkanaście % mniej odpadu).

---

### Stack techniczny (sugerowany)

- **Next.js** lub **Vite + React** (jedna aplikacja, bez backendu — logika w przeglądarce).
- TypeScript.
- Tailwind lub prosty CSS.
- Opcjonalnie: `csv-parse` do importu.
- Bez bazy danych w v0 — stan w pamięci + localStorage.

Jeśli repo ma już stack (np. v0-magurit-homepage) — **dopasuj się do istniejących konwencji**, ale moduł może być w podfolderze `tools/cut-planner-demo/`.

---

### Kryteria akceptacji demo

- [ ] Wczytanie przykładu jednym kliknięciem i wyliczenie 3 wariantów < 1 s.
- [ ] Wizualizacja paska cięcia jest zrozumiała bez instrukcji.
- [ ] Porównanie z baseline pokazuje konkretną różnicę w % i szac. koszcie remeltu.
- [ ] Kod czytelny — łatwo podmienić dane na export CSV z Impuls w v1.
- [ ] README: jak uruchomić, jak dodać CSV, co oznaczają metryki, **czego demo nie robi**.

---

### Komentarz produktowy (dla implementującego)

To demo ma **sprzedać rozmowę**, nie produkcję:
- Technolog Extral już powiedział, że brakuje warstwy „podpowiadającej” ponad Impuls.
- Nie konkuruj z PSAW (ich web) — to **moduł analityczny obok**.
- W prezentacji klientowi podkreśl: *„to ten sam typ problemu, który opisywałeś przy Impex — najpierw piły i resztki, potem długości wyciągania”*.

Zaimplementuj MVP end-to-end. Zacznij od algorytmu i testów jednostkowych na cutting stock, potem UI.

## KONIEC PROMPTU
