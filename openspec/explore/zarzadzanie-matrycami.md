# Explore: Zarządzanie matrycami (EXD)

Wątek z explore ([screenshots EXD](../changes/cut-planner-exd-realism/design.md)) — moduł **zarządzania matrycami** w systemie Extral, osobno od cut plannera.

## Screenshoty

| Plik | Widok | Uwagi |
|------|-------|-------|
| `screenshots/matryce.jpg` | Kartoteka matrycy E10217-24 | Masa teo/rzecz, typ, żywotność, prasa, rysunek techniczny |
| `screenshots/historia_matrycy.jpg` | Produkcja + zakładka **Historia matrycy** | Cykl życia matrycy, zdarzenia, skuteczność, korekty |

## `historia_matrycy.jpg` — co widać (2026-06-16)

Ekran EXD z dwoma warstwami:

**Góra — tabela produkcji (PR-10.1):**
- Kontrahent: ROSA SPZOO
- Matryce: E10217-18, E10217-22, E10217-24
- Zlecenia: ZP/26/0023157 itd.
- Długości: 5590, 6000, 2585 mm
- Uwagi operatora: „2 cięcia mniej”, „cięcie mniej”

**Dół — Historia matrycy:**
- **Skuteczność matrycy:** PR-10.1 [66,67%]
- **Zdarzenia:** zmiana statusu (PROD→PRA, GOT→PRA, KOR→GOT, POL→KOR), CZW, ILD, korekta matrycy
- **Kod korekty:** Polerowanie
- **Przebieg prod. / Pozostały przeb.:** np. 233,78 / 540,35
- **Czas wygrzewania:** 20041
- **Wydajność matrycy:** 3033 kg/h
- **Wprowadzający:** QM, DGRZADZIELA, JCZERNER, MRYBACKI

**Prawy panel:** zakładki Piktogram / Matryca / Profil (piktogram przekroju)

## Relacja do cut plannera

Cut planner (`cut-planner-exd-realism`) używa tylko **Tier A** z kartoteki matrycy (`matryce.jpg`):
- kod matrycy, kg/m, typ, prasa, placeholder rysunku

Ten screen (`historia_matrycy.jpg`) to **Tier C** — osobny moduł w roadmapie:
- cykl życia matrycy (statusy PROD / PRA / GOT / KOR / POL)
- historia korekt i polerowania
- skuteczność i wydajność [kg/h]
- przebieg produkcyjny vs pozostały przebieg
- czas wygrzewania (CZW)

## Otwarte pytania (na przyszłe spotkanie)

1. Czy skuteczność 66,67% to KPI, które technolog chce **podpowiadać** (np. kiedy planować korektę)?
2. Jak status matrycy wpływa na plan produkcyjny w Impulsie?
3. Czy „uwagi operatora” przy cięciach to sygnał do modułu optymalizacji cięć?
