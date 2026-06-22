#!/usr/bin/env python3
"""Generate client-facing PDF report: analiza zrzutu matryce - dane v2.json."""

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "analiza-danych-matryc-extral.pdf"

MAGURIT = ASSETS / "logo-magurit-transparent.png"
if not MAGURIT.exists():
    MAGURIT = ASSETS / "logo-magurit.png"
EXTRAL = ASSETS / "logo-extral.png"


def _prepare_magurit_logo() -> None:
    """Remove near-black background from Magurit logo PNG."""
    src = ASSETS / "logo-magurit.png"
    out = ASSETS / "logo-magurit-transparent.png"
    if not src.exists():
        return
    try:
        import cv2
        import numpy as np

        img = cv2.imread(str(src), cv2.IMREAD_COLOR)
        if img is None:
            return
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        alpha = np.clip((gray.astype(np.int16) - 30) * 5, 0, 255).astype(np.uint8)
        bgra[:, :, 3] = alpha
        ys, xs = np.where(bgra[:, :, 3] > 15)
        if len(ys) == 0:
            return
        bgra = bgra[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
        cv2.imwrite(str(out), bgra)
    except ImportError:
        pass

FONT = "ArialPL"
FONT_BOLD = "ArialPL-Bold"


def _register_fonts() -> None:
    """Register TTF with full Polish glyph coverage."""
    candidates = [
        (FONT, FONT_BOLD),
        (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ),
        ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists():
            pdfmetrics.registerFont(TTFont(FONT, regular))
            bold_path = bold if Path(bold).exists() else regular
            pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))
            return
    raise FileNotFoundError("No Arial TTF found — install Arial or Arial Unicode")


def _table_style(extra: list | None = None) -> TableStyle:
    base = [
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def build_pdf() -> Path:
    _register_fonts()
    _prepare_magurit_logo()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
        title="Analiza danych matryc — Extral",
        author="Magurit",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitlePL",
        parent=styles["Title"],
        fontName=FONT_BOLD,
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a2332"),
    )
    subtitle_style = ParagraphStyle(
        "SubtitlePL",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )
    h2 = ParagraphStyle(
        "H2PL",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=12,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1e293b"),
    )
    body = ParagraphStyle(
        "BodyPL",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    bullet = ParagraphStyle(
        "BulletPL",
        parent=body,
        leftIndent=12,
        bulletIndent=0,
        spaceAfter=4,
    )
    small = ParagraphStyle(
        "SmallPL",
        parent=styles["Normal"],
        fontName=FONT,
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
    )
    cell = ParagraphStyle("CellPL", parent=body, fontSize=8.5, spaceAfter=0, leading=11)
    cell_bold = ParagraphStyle("CellBoldPL", parent=cell, fontName=FONT_BOLD)

    magurit_logo = ASSETS / "logo-magurit-transparent.png"
    if not magurit_logo.exists():
        magurit_logo = ASSETS / "logo-magurit.png"

    story = []

    # Header logos
    logo_row = []
    if magurit_logo.exists():
        logo_row.append(
            Image(str(magurit_logo), width=50 * mm, height=12 * mm, kind="proportional", mask="auto")
        )
    else:
        logo_row.append(Paragraph("<b>MAGURIT</b>", body))
    logo_row.append(Spacer(1, 20 * mm))
    if EXTRAL.exists():
        logo_row.append(Image(str(EXTRAL), width=48 * mm, height=16 * mm, kind="proportional"))
    else:
        logo_row.append(Paragraph("<b>EXTRAL ALUMINIUM</b>", body))

    header_table = Table([logo_row], colWidths=[70 * mm, 30 * mm, 70 * mm])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Analiza wstępna zrzutu danych matryc i profili", title_style))
    story.append(
        Paragraph(
            f"Extral Aluminium · Materiał: <i>matryce — dane v2.json</i> · {date.today().strftime('%d.%m.%Y')}",
            subtitle_style,
        )
    )
    story.append(
        Paragraph(
            "Niniejszy dokument stanowi obiektywną analizę techniczną przekazanego pliku danych. "
            "Celem jest ocena kompletności informacji oraz możliwości wykorzystania ich w dalszych "
            "pracach analitycznych — bez wniosków implementacyjnych na tym etapie.",
            body,
        )
    )

    # 1. Zakres
    story.append(Paragraph("1. Zakres i charakterystyka pliku", h2))
    overview = [
        ["Parametr", "Wartość"],
        ["Rozmiar pliku", "ok. 79,5 MB"],
        ["Format", "JSON (lista rekordów)"],
        ["Liczba profili (indeksów)", "10 877"],
        ["Liczba rekordów matryc", "18 656"],
        ["Średnia liczba matryc na profil", "ok. 1,72"],
    ]
    t = Table(overview, colWidths=[75 * mm, 95 * mm])
    t.setStyle(
        _table_style(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Każdy rekord reprezentuje profil aluminiowy (<i>indeks</i>) i zawiera powiązane: "
            "piktogram przekroju, właściwości techniczne profilu oraz listę matryc z historią produkcyjną.",
            body,
        )
    )

    # 2. Struktura
    story.append(Paragraph("2. Struktura danych — główne elementy", h2))
    structure = [
        [_p("Element", cell_bold), _p("Zawartość", cell_bold), _p("Uwagi", cell_bold)],
        [
            _p("<b>indeks / indeksCzesci</b>", cell),
            _p("Identyfikator profilu (np. E06335)", cell),
            _p("Klucz główny rekordu", cell),
        ],
        [
            _p("<b>piktogram</b>", cell),
            _p("Metadane załącznika + pole <i>base64</i>", cell),
            _p("Obraz przekroju (GIF dominujący)", cell),
        ],
        [
            _p("<b>wlasnosci</b>", cell),
            _p("19 pól parametrów technicznych", cell),
            _p("Masa, ścianki, kontrahent profilu, przekrój itd.", cell),
        ],
        [
            _p("<b>matryce[]</b>", cell),
            _p("Lista egzemplarzy matryc", cell),
            _p("Status, dostawca, parametry, skuteczność", cell),
        ],
        [
            _p("<b>matryce[].skutecznosc[]</b>", cell),
            _p("Historia per prasa", cell),
            _p("Produkcje, przerwania, wskaźnik %", cell),
        ],
    ]
    t2 = Table(structure, colWidths=[38 * mm, 52 * mm, 80 * mm])
    t2.setStyle(
        _table_style(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t2)

    # 3. Piktogramy
    story.append(Paragraph("3. Piktogramy profili", h2))
    pic_data = [
        ["Kategoria", "Liczba", "Udział"],
        ["Z piktogramem (base64)", "10 042", "ok. 92%"],
        ["Bez piktogramu", "810", "ok. 7%"],
        ["Brak obiektu piktogram", "25", "ok. 0,2%"],
    ]
    t3 = Table(pic_data, colWidths=[60 * mm, 35 * mm, 35 * mm])
    t3.setStyle(
        _table_style(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(t3)
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "Formaty graficzne: GIF (9 823), JPEG (243), PNG (1). Obrazy są zakodowane w polu "
            "<i>base64</i> i po standardowej normalizacji dają się zdekodować w całości próbki testowej. "
            "Piktogramy mają charakter konturu przekroju — bez skali wymiarowej na rysunku.",
            body,
        )
    )

    # 4. Matryce
    story.append(Paragraph("4. Matryce — pokrycie i parametry", h2))
    story.append(Paragraph("• Profile z co najmniej jedną matrycą: <b>10 823</b> (99,5%)", bullet))
    story.append(Paragraph("• Profile z wieloma matrycami (&gt;1): <b>2 632</b>", bullet))
    story.append(Paragraph("• Profile bez matryc: <b>54</b>", bullet))
    story.append(Spacer(1, 3 * mm))

    mat_data = [
        ["Parametr matrycy", "Przykładowe wartości / rozkład"],
        ["Identyfikator", "np. E06335-1 (indeks + numer egzemplarza)"],
        ["Typ", "Komorowa (11 748), Płaska (6 733), Shut-off (174)"],
        ["Liczba otworów", "1 (9 602), 2 (4 515), 4 (2 725), 6 (1 109)…"],
        ["Status (kodStatusu)", "GOT, DZLO, WYC, PRA, KOR, POL i inne"],
        ["Dostawca", "kodKontrahenta (np. PHOENIX2, EKSTEK XP)"],
        ["Masa teo./rzecz.", "g/m — pola masaTeoretyczna, masaRzeczywista"],
        ["Przebieg / żywotność", "aktualneZuzycie, zywotnosc, pozostalyPrzebieg…"],
    ]
    t4 = Table(mat_data, colWidths=[45 * mm, 125 * mm])
    t4.setStyle(
        _table_style(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t4)

    # 5. Skuteczność
    story.append(Paragraph("5. Dane o skuteczności produkcji", h2))
    story.append(
        Paragraph(
            "Pole <i>skutecznosc</i> w obrębie matrycy jest tablicą wpisów powiązanych ze "
            "stanowiskiem produkcyjnym (prasa, np. PR-7.1). Każdy wpis zawiera m.in.:",
            body,
        )
    )
    story.append(Paragraph("• <i>iloscProdukcji</i> — liczba zdarzeń produkcyjnych", bullet))
    story.append(Paragraph("• <i>iloscPrzerwanych</i> — liczba przerwań", bullet))
    story.append(Paragraph("• <i>skutecznosc</i> — wskaźnik procentowy", bullet))
    story.append(Spacer(1, 3 * mm))

    skut_data = [
        ["Kategoria", "Liczba matryc"],
        ["Z uzupełnioną historią skuteczności", "16 622"],
        ["Z pustą tablicą skuteczności", "2 034"],
    ]
    t5 = Table(skut_data, colWidths=[90 * mm, 50 * mm])
    t5.setStyle(
        _table_style(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(t5)
    story.append(
        Paragraph(
            "Wskaźnik wymaga doprecyzowania reguł agregacji (np. średnia ważona, zakres pras, "
            "okres) przed użyciem w raportach decyzyjnych — definicja biznesowa do ustalenia z Państwem.",
            body,
        )
    )

    # 6. Dostawcy
    story.append(Paragraph("6. Dostawcy matryc — najczęstsze kody", h2))
    sup_data = [
        ["Kod kontrahenta", "Liczba wystąpień"],
        ["PHOENIX2", "5 286"],
        ["PHOENIX", "3 689"],
        ["WILKE2", "3 439"],
        ["EKSTEK XP", "3 366"],
        ["KONAR DE", "761"],
        ["EXTRUSION", "575"],
        ["HALEX", "454"],
        ["Pozostali", "ok. 1 500"],
    ]
    t6 = Table(sup_data, colWidths=[70 * mm, 50 * mm])
    t6.setStyle(
        _table_style(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ]
        )
    )
    story.append(t6)

    # 7. Właściwości profilu
    story.append(Paragraph("7. Właściwości techniczne profilu (wlasnosci)", h2))
    story.append(
        Paragraph(
            "Oprócz grafiki dostępne są ustrukturyzowane parametry, m.in.: masa teoretyczna [g/m], "
            "grubość ścianki [mm], pole przekroju [mm²], długość maksymalna, norma wymiarowa, "
            "trudność wykonania oraz kontrahent — właściciel profilu. Pola są spójne we wszystkich "
            "rekordach (19 właściwości).",
            body,
        )
    )

    # 8. Potencjał
    story.append(Paragraph("8. Potencjał wykorzystania — wstępna ocena", h2))
    story.append(
        Paragraph(
            "Na podstawie analizy struktury i pokrycia danych można wskazać następujące obszary, "
            "w których materiał wydaje się odpowiedni do dalszych prac:",
            body,
        )
    )
    potentials = [
        (
            "<b>Wyszukiwanie podobnych profili</b> — piktogramy w ~92% rekordów; "
            "wystarczająca baza do metod porównania kształtu."
        ),
        (
            "<b>Łączenie profil → matryca → dostawca</b> — relacje są jawne w strukturze JSON; "
            "wiele profili ma historię wielu matryc."
        ),
        (
            "<b>Ocena historycznej efektywności</b> — dane o skuteczności i produkcji obecne "
            "u większości matryc; wymaga ustalenia reguł agregacji."
        ),
        (
            "<b>Parametry uzupełniające</b> — liczba otworów, typ matrycy, masa, grubość ścianki "
            "mogą wspierać filtrowanie i walidację wyników podobieństwa."
        ),
    ]
    for p in potentials:
        story.append(Paragraph(f"• {p}", bullet))

    # 9. Ograniczenia
    story.append(Paragraph("9. Ograniczenia i kwestie do doprecyzowania", h2))
    limits = [
        "810 profili bez piktogramu — analiza wyłącznie graficzna ich nie obejmie.",
        "Statusy DZLO / WYC — matryce historyczne; interpretacja w kontekście rekomendacji nowych zleceń.",
        "Skuteczność per prasa — potrzebna definicja KPI zbiorczego dla matrycy lub dostawcy.",
        "Kody dostawców — mapowanie na nazwy handlowe (jeśli wymagane w UI).",
        "Rozmiar pliku (~80 MB) — import jednorazowy możliwy; przy regularnej synchronizacji warto rozważyć format przyrostowy.",
    ]
    for lim in limits:
        story.append(Paragraph(f"• {lim}", bullet))

    # 10. Podsumowanie
    story.append(Paragraph("10. Podsumowanie", h2))
    story.append(
        Paragraph(
            "Przekazany zrzut danych charakteryzuje się wysokim stopniem kompletności w zakresie "
            "profili, piktogramów, matryc, dostawców oraz historii produkcyjnej. Struktura jest "
            "spójna i nadaje się do automatycznego przetwarzania. Kolejnym krokiem — po Państwa "
            "akceptacji kierunku — byłaby integracja z narzędziem analitycznym i weryfikacja "
            "jakości wyszukiwania podobieństwa na wybranych profilach referencyjnych.",
            body,
        )
    )

    story.append(Spacer(1, 12 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Dokument przygotowany przez Magurit w ramach współpracy z Extral Aluminium. "
            "Analiza oparta wyłącznie na pliku <i>matryce — dane v2.json</i>. "
            "Dane liczbowe pochodzą z automatycznej analizy struktury pliku.",
            small,
        )
    )

    doc.build(story)
    return OUT


if __name__ == "__main__":
    path = build_pdf()
    print(path)
