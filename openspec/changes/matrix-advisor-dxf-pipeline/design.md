## Context

Matrix Advisor PoC (`tools/matrix-advisor-poc/`) obsługuje dziś ~10 877 profili Extral zaimportowanych z JSON (piktogram GIF base64). Pipeline: raster → maska 256×256 → geometric + ResNet18 embedding → `geometric.npz` / `embedding.npz` → SQLite.

Upload „Nowe zamówienie” (spec 003) przyjmuje GIF/PNG/JPEG i robi ephemeral query przeciw istniejącemu indeksowi.

**Nowe dane referencyjne:** `data/die/rysunki/` — 5 profili z parą DXF+PDF. Ustalenia z analizy (czerwiec 2026):

| Obserwacja | Implikacja |
|------------|------------|
| DXF AC1018, jednostki mm (`$INSUNITS=4`) | Parser zakłada mm; skala 1:1 w geometrii |
| Dwa style: E02004 (warstwy `*_FRAME`, modelspace) vs reszta (bloki `Ramka`, `EAL_WYP_*`, `EAL_WKL_*`) | Reguły ekstrakcji profilu muszą obsługiwać oba warianty |
| Geometria profilu = `LINE` + `ARC`, rzadko jedna `LWPOLYLINE` | Kontur budowany jako graf segmentów → polygon → raster |
| Wymiary w encjach `DIMENSION` zgadzają się z Extral `wlasnosci` | Walidacja i Stage 2 scoring możliwe bez OCR |
| PDF = wektorowy eksport CAD, brak tekstu | **Poza scope** — nie parsujemy PDF |
| Brak DWG w próbkach | MVP: tylko DXF; DWG jako future z konwerterem |

**Docelowy use case:** klient wgrywa DXF profilu spoza bazy → Stage 1 zwraca top 20–30 podobnych historycznie → Stage 2 filtruje/rerankuje po wymiarach i detalach wewnętrznych.

## Goals / Non-Goals

**Goals:**

1. DXF jako **główny** format wejściowy dla nowych zapytań i (docelowo) importu profili
2. Powtarzalny pipeline: DXF → dane pochodne (JSON maska-meta, geometria, embedding) z możliwością pełnej regeneracji
3. Dwuetapowe wyszukiwanie z transparentnym breakdown score
4. Deterministyczne cechy (otwory, bbox, wymiary) **obok** embeddingów — nie zamiast
5. Walidacja wymiarów DXF vs metadane Extral tam, gdzie profil istnieje w obu źródłach
6. Modularna architektura pod przyszłe: supplier ranking, die recommendation, production history
7. MVP ograniczony do konwencji plików jak w `data/die/rysunki/`

**Non-Goals:**

- Parsowanie PDF, OCR, DWG w MVP
- Fine-tuning modeli ML na danych Extral
- Persist uploadu klienta do produkcyjnej bazy profili (ephemeral query jak dziś)
- Automatyczny wybór dostawcy / matrycy
- Migracja wszystkich 10k profili na DXF w tym change (osobny batch później)
- Auth, HA, PostgreSQL (SQLite OK na PoC; model pod migrację)

## Proposed Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  DXF file   │────▶│  DXF Parser  │────▶│ GeometryNormalizer  │
│ (source of  │     │  (ezdxf)     │     │ (layers/blocks,     │
│   truth)    │     └──────────────┘     │  units, contour)    │
└─────────────┘                          └──────────┬──────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    ▼                               ▼                               ▼
           ┌────────────────┐              ┌─────────────────┐              ┌──────────────────┐
           │ PictogramRenderer│            │ FeatureExtractor │              │ MetadataExtractor │
           │ → mask 256×256   │            │ (holes, bbox,    │              │ (DIMENSION,       │
           │ → preview PNG    │            │  cavities, etc.) │              │  title block)     │
           └────────┬─────────┘            └────────┬─────────┘              └────────┬─────────┘
                    │                               │                                  │
                    ▼                               │                                  │
           ┌────────────────┐                       │                                  │
           │ EmbeddingGen   │                       │                                  │
           │ (ResNet18)     │                       │                                  │
           └────────┬─────────┘                       │                                  │
                    │                               ▼                                  ▼
                    │                      ┌─────────────────────────────────────────────┐
                    │                      │ Derived store: geometry.json, features.json, │
                    └─────────────────────▶│ normalization_meta, SQLite rows, npz index  │
                                           └──────────────────────┬──────────────────────┘
                                                                  │
                    ┌─────────────────────────────────────────────┘
                    ▼
           ┌────────────────┐     ┌─────────────────┐     ┌──────────────┐
           │ Stage 1 Search │────▶│ Stage 2 Filter  │────▶│ Combined     │
           │ (shape top N)  │     │ + Rerank        │     │ Score + API  │
           └────────────────┘     └─────────────────┘     └──────────────┘
                                                                  │
                                                                  ▼
                                                         ┌──────────────┐
                                                         │ React UI     │
                                                         └──────────────┘
```

### Module boundaries

| Moduł | Odpowiedzialność |
|-------|------------------|
| `ingestion/dxf_import.py` | Zapis DXF, checksum, `profile_id` / nazwa pliku |
| `dxf/parser.py` | ezdxf read, explode INSERT, entity inventory |
| `dxf/profile_selector.py` | Reguły wyboru geometrii profilu (warstwa/blok) |
| `dxf/contour_builder.py` | LINE/ARC → zamknięty kontur (lub maska bez pełnego polygonu) |
| `dxf/dimensions.py` | Ekstrakcja `DIMENSION` + mapowanie na pola techniczne |
| `normalization/pipeline.py` | Wspólna maska 256×256 (z DXF render lub GIF) |
| `dxf/renderer.py` | Kontur → raster (OpenCV), styl Extral (ciemne tło / jasny kontur) |
| `features/geometric.py` | Rozszerzenie: outer vs inner, channel count |
| `features/dimensional.py` | **Nowy** — bbox mm, wall thickness estimate, area |
| `embeddings/encoder.py` | Bez zmian koncepcji; wejście = maska |
| `index/builder.py` | Indeksy shape + opcjonalnie dimensional features |
| `query/stage1.py` | Top N embedding/geometric |
| `query/stage2.py` | Filtry + weighted rerank |
| `query/scoring.py` | Agregacja wymiarów score |
| `query/upload_service.py` | `by-dxf` ephemeral path |
| `api/server.py` | Endpointy |
| `web/` | Upload DXF, filtry, breakdown |

## Decisions

### D1: DXF jako source of truth; JSON/SQLite pochodne

**Decision:** Oryginalny DXF w `data/raw/dxf/{profile_id}.dxf`. Pochodne: `data/processed/geometry/{profile_id}.json`, maska PNG, wpisy SQLite, wektory w npz.

**Rationale:** Regeneracja po poprawce parsera; zgodność z wymaganiem „nie traktuj JSON Extral jako prawdy”.

**Alternative:** DXF tylko przy uploadzie, bez archiwizacji — odrzucone (brak audytu i reprocess).

### D2: Parser — `ezdxf` + reguły dla próbek `rysunki/`

**Decision:** Biblioteka `ezdxf`; selekcja profilu według priorytetu:

1. Warstwa `01.Profil` (encje w modelspace)
2. Warstwa `5. RYSUNEK_GLOWNY*` / `*_GLOWNY*`
3. Blok `EAL_WYP_*` / `EAL_WKL_*` (explode)
4. Największy zamknięty kontur na warstwie `07.Widok rzeczywisty` (fallback, z flagą `quality`)

**Rationale:** Pokrywa 5 próbek; jawne `quality_flags` gdy heurystyka niepewna.

**Alternative:** Jeden uniwersalny „największy kontur w pliku” — odrzucone (łapie ramkę A4).

### D3: Kontur → maska zamiast natywnego vector search w MVP

**Decision:** DXF → raster 256×256 → istniejący embedding + geometric index.

**Rationale:** Reuse 10k indeksu GIF; szybszy MVP; vector-native jako Phase 2.

**Alternative:** Osobny indeks polilinii — lepsza precyzja, duży koszt.

### D4: Dwuetapowe wyszukiwanie

**Decision:**

- **Stage 1:** `top_n=30`, method `embedding` (default), cosine + 4 rotacje — jak dziś
- **Stage 2:** Na kandydatach Stage 1: filtry opcjonalne (min/max width, height, wall, holes) + rerank:

```
total = w_shape * shape_score
      + w_outer * outer_contour_score
      + w_inner * inner_detail_score
      + w_dim   * dimension_score
      + w_meta  * metadata_score
```

MVP wagi w `config.py` (hardcoded). Breakdown w JSON response.

**Rationale:** Użytkownik widzi „dlaczego”; można odfiltrować podobny kształt ze złymi wymiarami.

### D5: Cechy wewnętrzne (kanały, kieszenie)

**Decision:** Rozszerzyć `hole_count` + dodać `cavity_count`, `inner_channel_count` (connected components wewnątrz obrysu na masce). Osobny `inner_mask` (wypełnienie zewnętrzne minus obrys) do porównania IoU lub feature vector.

**Rationale:** Odpowiada na case „1 kanał vs 3 kanały” bez nowego modelu ML.

### D6: Wymiary z DXF

**Decision:** Ekstrakcja z `DIMENSION.actual_measurement`; mapowanie heurystyczne na `width_mm`, `height_mm`, `wall_thickness_mm`, `ocd_mm` przez ranking wartości + porównanie z Extral gdy dostępne. Walidacja: tolerancja ±5% lub ±0.5 mm (config).

**Rationale:** W próbkach wymiary są w DXF i zgadzają się z `wlasnosci`.

### D7: Upload API

**Decision:** `POST /api/v1/query/by-dxf` (multipart, max 10 MB). Ephemeral — bez zapisu profilu. Opcjonalnie `stage=1|2`, `top_n`, `filters` JSON.

Zachować `POST /api/v1/query/by-image` dla kompatybilności.

### D8: PDF — explicit out

**Decision:** Brak endpointu, brak modułu PDF.

### D9: Przetwarzanie profili historycznych

**Decision:** Faza implementacji 1: upload query z DXF. Faza 2: `matrix-advisor import-dxf` dla folderu (batch na `rysunki/` + przyszły katalog). GIF-y z Extral nadal źródłem dla profili bez DXF.

### D10: Baza danych — rozszerzenie schematu

**Decision:** Nowe tabele/kolumny (SQLite, migracja w `db.py`):

- `dxf_assets` (profile_id, path, checksum, parsed_at, status, parser_version)
- `profile_dimensions` (width_mm, height_mm, wall_mm, ocd_mm, area_mm2, source: dxf|extral|estimated)
- `dimension_validation` (field, dxf_value, extral_value, delta, ok)
- `processing_status` na profilu: `pending|gif_only|dxf_ready|indexed`

Projekt pod późniejszy PostgreSQL: bez SQLite-specific logic w parserze.

## Data Model (derived)

### `geometry.json` (per profile)

```json
{
  "profile_id": "E08594",
  "source_dxf": "E08594.dxf",
  "parser_version": "0.1.0",
  "units": "mm",
  "selection": { "strategy": "block", "layer": "01.Profil", "block": "EAL_WKL_GÓRA" },
  "bbox_mm": { "width": 21.2, "height": 14.5 },
  "dimensions_extracted": [25.0, 1.4, 19.0],
  "dimensions_mapped": { "ocd_mm": 25.0, "wall_thickness_mm": 1.4 },
  "contour": { "type": "polygon", "vertex_count": 22 },
  "quality_flags": []
}
```

### Query response (Stage 2)

```json
{
  "query_profile_id": "__upload__",
  "stage": 2,
  "similar": [{
    "profile_id": "E08594",
    "rank": 1,
    "total_score": 0.91,
    "score_breakdown": {
      "shape_embedding": 0.95,
      "outer_contour": 0.92,
      "inner_detail": 0.88,
      "dimension": 0.85,
      "metadata": 0.70
    },
    "dimensions": { "ocd_mm": 25, "wall_mm": 1.4 },
    "features": { "hole_count": 1, "cavity_count": 1 },
    "metadata_match": { "wall_thickness": "ok", "ocd": "ok" }
  }]
}
```

## API Endpoints (MVP)

| Method | Path | Opis |
|--------|------|------|
| POST | `/api/v1/query/by-dxf` | Ephemeral DXF upload → Stage 1/2 |
| POST | `/api/v1/query/by-image` | Bez zmian (legacy) |
| GET | `/api/v1/profiles/{id}/dimensions` | Wymiary + walidacja |
| GET | `/api/v1/profiles/{id}/geometry` | geometry.json summary |
| POST | `/api/v1/search/similar` | Unified: profile_id lub mask + stage + filters |
| GET | `/api/v1/profiles/{id}/advisory` | Rozszerzone o breakdown gdy Stage 2 |

## Frontend (Stage 1 + 2)

### Ekrany / elementy

1. **Nowe zamówienie** — upload DXF (primary), opcjonalnie GIF; podgląd wyrenderowanego piktogramu; wymiary wyciągnięte z pliku
2. **Wyniki Stage 1** — lista top N: piktogram, shape score, kluczowe wymiary
3. **Panel Stage 2** — suwaki/filtry: szerokość, wysokość, ścianka, liczba otworów; przycisk „Zastosuj filtry”
4. **Wynik końcowy** — total score + breakdown (wykres paskowy lub tabela); badge „shape match” vs „dimension match”
5. **Szczegóły profilu** — zakładka wymiary: DXF vs Extral, flagi walidacji

## Similarity Scoring Approach

| Wymiar | Źródło | Metryka MVP |
|--------|--------|-------------|
| Shape embedding | Maska 256, ResNet18 | Cosine similarity |
| Outer contour | Maska, zewnętrzny kontur | Hu moments / IoU obrysu |
| Inner detail | Komponenty wewnętrzne maski | Porównanie `hole_count`, `cavity_count`, inner IoU |
| Dimension | `profile_dimensions` | Normalized L1 na width/height/wall/ocd |
| Metadata | Extral `wlasnosci` | Binary match per pole (gdy dostępne) |

**Wagi MVP (propozycja):** shape 0.40, outer 0.15, inner 0.20, dimension 0.20, metadata 0.05.

## Feature Extraction Approach

**Z DXF (deterministyczne):**

- Bbox konturu profilu [mm]
- Lista wartości DIMENSION
- Szacowana grubość ścianki (najmniejsza odległość równoległych segmentów lub min dimension &lt; threshold)
- Powierzchnia poligonu [mm²] gdy kontur zamknięty

**Z maski (deterministyczne, istniejące + nowe):**

- `hole_count`, `cavity_count`, `aspect_ratio`, `solidity`, Hu moments
- Osobny wektor „outer only” (wypełnienie bez dziur)

**Z embedding (ML):**

- ResNet18 — „ które profile wyglądają podobnie”

## MVP Limitations

- Parser tylko dla konwencji jak `data/die/rysunki/` (AC1018, mm, znane warstwy/bloki)
- Brak DWG; brak PDF
- Wagi scoringu hardcoded
- Wall thickness — heurystyka, nie FEM
- Profile historyczne bez DXF: tylko shape search (brak dimension score vs query DXF — partial null)
- E12223-like złożone rysunki (pasy termiczne): mogą wymagać ręcznej flagi jakości
- Brak user-adjustable weights w UI

## Implementation Plan

### Stage 1 (shape-first MVP)

1. Moduł `dxf/` + `import-dxf` dla 5 próbek
2. Renderer → maska kompatybilna z indeksem
3. `POST /query/by-dxf` Stage 1 only
4. UI upload DXF + preview
5. Testy na 5 profilach: DXF mask vs GIF mask similarity

### Stage 2 (filtering + scoring)

1. `profile_dimensions` + ekstrakcja DIMENSION
2. Walidacja vs Extral dla 5 próbek
3. `query/stage2.py` + scoring breakdown
4. UI filtry + breakdown
5. Testy regresji: profil 1-kanałowy vs wielokanałowy (synthetic lub próbki)

## Risks / Trade-offs

| Ryzyko | Mitygacja |
|--------|-----------|
| Heterogeniczne DXF poza 5 próbkami | `quality_flags`, parser_version, iteracyjne rozszerzanie reguł |
| Geometria w blokach nie rozwinięta | `explode` INSERT w ezdxf; test na E04900 |
| Query DXF vs baza GIF-only — brak wymiarów u kandydatów | Stage 2 dimension score tylko gdy kandydat ma dane; UI pokazuje „brak wymiarów” |
| Błędna selekcja warstwy (ramka A4) | Whitelist warstw/bloków; testy na 5 plikach |
| ezdxf + zależność ciężka | Optional extra `[cad]`; lazy import |
| Złożone profile (E12223) | Fallback `07.Widok rzeczywisty` + flaga `complex_drawing` |
| Overfitting wag na 5 profilach | Udokumentować; kolekcja walidacyjna przed tuningiem |

## Migration Plan

1. Deploy API/UI z DXF upload obok GIF — bez breaking changes
2. Batch `import-dxf` na `data/die/rysunki/` → geometry.json + walidacja
3. Później: masowy import DXF z Extral/EXD gdy dostępny eksport
4. Rollback: wyłączenie endpointu `by-dxf`; GIF path nietknięty

## Open Questions — resolution status (2026-06, n=5 samples `data/die/rysunki/`)

| Question | Status |
|----------|--------|
| Which DXF entities are present? | **Resolved (partial):** LINE, ARC, CIRCLE, LWPOLYLINE, DIMENSION, INSERT, blocks `EAL_*`, `Ramka`, `TABELA` |
| Where are dimensions stored? | **Resolved:** `DIMENSION.actual_measurement` in DXF; not in PDF text |
| DWG needed? | **Open:** not in samples; DXF sufficient for MVP |
| Pictogram from DXF? | **Resolved:** rasterize → mask 256×256 → preview PNG |
| Profile numbers consistent? | **Resolved:** filename stem = Extral `indeks` (E02004…) |
| Validation package | **In progress:** 5 files OK; need 10+ hard cases |
| Rotation/scale normalization | **Partial:** 4 rotations at query; mm from DXF units |
| Business-critical details | **Open:** confirm with technologists (channels, wall, OCD priority) |
| User-adjustable weights? | **Deferred:** hardcoded `SCORING_WEIGHTS` in config |
