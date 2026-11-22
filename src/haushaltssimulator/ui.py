"""Streamlit-Hilfen: gecachte Daten, Formatierung und einheitliches Layout."""

from __future__ import annotations

import functools
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from . import bausteine, dataset, insights, sources
from .format import (  # noqa: F401 – Formatierung wird über ui angeboten
    MONATSNAMEN,
    format_eur,
    format_month,
    format_mrd,
    format_number,
    format_signed,
)

EBENE_ORDER = [
    "Bund (Zentralstaat)",
    "Länder (Staatsebene)",
    "Gemeinden (lokale Ebene)",
    "Sozialversicherung",
]

EBENE_COLORS = {
    "Bund (Zentralstaat)": "#1f4e79",
    "Länder (Staatsebene)": "#2e86ab",
    "Gemeinden (lokale Ebene)": "#7fb2d5",
    "Sozialversicherung": "#c9a227",
    "Staat insgesamt": "#1f4e79",
    "Bund": "#1f4e79",
    "Länder": "#2e86ab",
    "Gemeinden / Gemeindeverbände": "#7fb2d5",
}

SCHULDENART_COLORS = {
    "Wertpapierschulden": "#1f4e79",
    "Kredite beim nicht-öffentlichen Bereich": "#2e86ab",
    "Kassenkredite beim nicht-öffentlichen Bereich": "#c9a227",
}

# Farbfolge für Diagramme mit vielen Linien (z. B. Ländervergleich).
CHART_COLORS = (
    "#1f4e79",
    "#b03a2e",
    "#c9a227",
    "#2e7d32",
    "#6a3d9a",
    "#e67e22",
    "#17becf",
    "#8c564b",
    "#7f7f7f",
    "#bcbd22",
    "#d62728",
    "#9467bd",
    "#e377c2",
    "#393b79",
    "#637939",
)


def chart_color(index: int) -> str:
    """Farbe für die Linie mit der angegebenen Position."""
    return CHART_COLORS[index % len(CHART_COLORS)]


@st.cache_data(show_spinner=False)
def annual_debt() -> pd.DataFrame:
    return dataset.load_annual_debt()


@st.cache_data(show_spinner=False)
def quarterly_debt() -> pd.DataFrame:
    return dataset.load_quarterly_debt()


@st.cache_data(show_spinner=False)
def destatis_annual() -> pd.DataFrame:
    return dataset.load_destatis_annual()


@st.cache_data(show_spinner=False)
def destatis_quarterly() -> pd.DataFrame:
    return dataset.load_destatis_quarterly()


@st.cache_data(show_spinner=False)
def laender_quarterly() -> pd.DataFrame:
    return dataset.load_laender_quarterly()


@st.cache_data(show_spinner=False)
def gdp_population() -> pd.DataFrame:
    return dataset.load_gdp_population()


@st.cache_data(show_spinner=False)
def household() -> pd.DataFrame:
    return dataset.load_household()


@st.cache_data(show_spinner=False)
def bund_yield() -> pd.DataFrame:
    return dataset.load_bund_yield()


@st.cache_data(show_spinner=False)
def international_yields() -> pd.DataFrame:
    return dataset.load_international_yields()


@st.cache_data(show_spinner=False)
def interest_burden() -> pd.DataFrame:
    return dataset.load_interest_burden()


@st.cache_data(show_spinner=False)
def insolvencies() -> pd.DataFrame:
    return dataset.load_insolvencies()


@st.cache_data(show_spinner=False)
def money_supply() -> pd.DataFrame:
    return dataset.load_money_supply()


@st.cache_data(show_spinner=False)
def purchasing_power() -> pd.DataFrame:
    return dataset.load_purchasing_power()


@st.cache_data(show_spinner=False)
def energy_prices() -> pd.DataFrame:
    return dataset.load_energy_prices()


@st.cache_data(show_spinner=False)
def day_ahead_prices() -> pd.DataFrame:
    return dataset.load_day_ahead_prices()


@st.cache_data(show_spinner=False)
def fuel_prices() -> pd.DataFrame:
    return dataset.load_fuel_prices()


@st.cache_data(show_spinner=False)
def big_mac() -> pd.DataFrame:
    return dataset.load_big_mac()


@st.cache_data(show_spinner=False)
def homeownership() -> pd.DataFrame:
    return dataset.load_homeownership()


@st.cache_data(show_spinner=False)
def bund_interest() -> pd.DataFrame:
    return dataset.load_bund_interest()


@st.cache_data(show_spinner=False)
def bund_interest_plan() -> pd.DataFrame:
    return dataset.load_bund_interest_plan()


@st.cache_data(show_spinner=False)
def bund_budget_areas() -> pd.DataFrame:
    return dataset.load_bund_budget_areas()


@st.cache_data(show_spinner=False)
def federal_core_budget_svr() -> pd.DataFrame:
    return dataset.load_federal_core_budget_svr()


@st.cache_data(show_spinner=False)
def laender_debt() -> pd.DataFrame:
    return dataset.load_laender_debt()


@st.cache_data(show_spinner=False)
def laender_budget() -> pd.DataFrame:
    return dataset.load_laender_budget()


@st.cache_data(show_spinner=False)
def laender_inflation() -> pd.DataFrame:
    return dataset.load_laender_inflation()


@st.cache_data(show_spinner=False)
def laender_income() -> pd.DataFrame:
    return dataset.load_laender_income()


@st.cache_data(show_spinner=False)
def gdp_germany() -> pd.DataFrame:
    return dataset.load_gdp_germany()


@st.cache_data(show_spinner=False)
def gdp_growth() -> pd.DataFrame:
    return dataset.load_gdp_growth()


@st.cache_data(show_spinner=False)
def investments() -> pd.DataFrame:
    return dataset.load_investments()


@st.cache_data(show_spinner=False)
def production_germany() -> pd.DataFrame:
    return dataset.load_production_germany()


@st.cache_data(show_spinner=False)
def production_germany_long() -> pd.DataFrame:
    return dataset.load_production_germany_long()


@st.cache_data(show_spinner=False)
def production_comparison() -> pd.DataFrame:
    return dataset.load_production_comparison()


@st.cache_data(show_spinner=False)
def energy_markets() -> pd.DataFrame:
    return dataset.load_energy_markets()


@st.cache_data(show_spinner=False)
def key_rates() -> pd.DataFrame:
    return dataset.load_key_rates()


@st.cache_data(show_spinner=False)
def inflation_germany() -> pd.DataFrame:
    return dataset.load_inflation_germany()


@st.cache_data(show_spinner=False)
def co2_price() -> pd.DataFrame:
    return dataset.load_co2_price()


@st.cache_data(show_spinner=False)
def co2_surcharge() -> pd.DataFrame:
    return dataset.load_co2_surcharge()


@st.cache_data(show_spinner=False)
def insight_decks() -> list[insights.Foliensatz]:
    """Foliensätze aus insights/ (Datengeschichten)."""
    return insights.foliensaetze()


@st.cache_data(show_spinner=False)
def insight_html(pfad: str) -> str:
    """Foliensatz als eigenständiges HTML zum Einbetten."""
    return insights.eigenstaendiges_html(Path(pfad))


@st.cache_data(show_spinner=False)
def sources_library() -> dict:
    """Quellenbibliothek mit URLs, Lizenzen, Prüfsummen und Abrufzeitpunkten."""
    return sources.read_library()


@st.cache_data(show_spinner=False)
def data_retrieved_at() -> datetime | None:
    """Jüngster Abrufzeitpunkt über alle Quellen hinweg."""
    entries = sources_library().get("quellen", [])
    stamps = [entry["abgerufen_am"] for entry in entries if entry.get("abgerufen_am")]
    return max(datetime.fromisoformat(value) for value in stamps) if stamps else None


def format_timestamp(value: str | None) -> str:
    """Formatiert einen ISO-Zeitstempel in deutscher Schreibweise."""
    if not value:
        return "unbekannt"
    return datetime.fromisoformat(value).astimezone().strftime("%d.%m.%Y, %H:%M Uhr")


def style(
    fig: go.Figure,
    *,
    height: int = 430,
    legend: bool = True,
    legend_y: float = 1.02,
    top_margin: int = 40,
    own_legends: bool = False,
) -> go.Figure:
    """Einheitliches Layout für alle Diagramme.

    Mit ``own_legends=True`` bleibt das Legenden-Layout der Figur erhalten, etwa eine
    eigene Legende je Teilbild (``legend``, ``legend2``, …).
    """
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 10, "r": 10, "t": top_margin, "b": 10},
        hovermode="x unified" if legend else "closest",
        showlegend=legend,
        font={"family": "Inter, Segoe UI, sans-serif", "size": 13},
    )
    if not own_legends:
        fig.update_layout(
            legend={"orientation": "h", "yanchor": "bottom", "y": legend_y, "x": 0}
        )
    return fig


# Ersatzgrafik, falls Kaleido bzw. Chrome in der Umgebung fehlt.
SVG_NICHT_VERFUEGBAR = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="60">'
    b'<text x="10" y="35" font-family="sans-serif" font-size="14">'
    b"SVG-Export hier nicht verf\xc3\xbcgbar \xe2\x80\x93 bitte das Kamera-Symbol des "
    b"Diagramms nutzen.</text></svg>"
)


@functools.lru_cache(maxsize=64)
def _svg_bytes(figure_json: str) -> bytes:
    """Rendert ein Diagramm als SVG (Kaleido); ohne Kaleido eine Ersatzgrafik.

    Läuft erst beim Klick auf den Download-Button in einem eigenen Thread, daher
    ``functools.lru_cache`` statt ``st.cache_data``.
    """
    try:
        return pio.from_json(figure_json).to_image(format="svg")
    except Exception:  # Kaleido bzw. Chrome kann in manchen Umgebungen fehlen
        return SVG_NICHT_VERFUEGBAR


def plot(
    figure: go.Figure,
    *,
    filename: str,
    height: int = 430,
    legend: bool = True,
    legend_y: float = 1.02,
    top_margin: int = 40,
    own_legends: bool = False,
    zusatz: Callable[[DeltaGenerator], None] | None = None,
) -> None:
    """Zeigt ein Diagramm und bietet es als SVG und als HTML zum Download an.

    ``zusatz`` zeichnet ein weiteres Bedienelement neben die Download-Buttons, etwa
    den Knopf „Bericht“ der Bausteine.

    Beide Dateien entstehen erst beim Klick auf den jeweiligen Button. Das SVG-Rendern
    mit Kaleido dauert pro Diagramm etwa eine Sekunde und würde sonst jeden Seitenaufruf
    (und jeden Seitentest) ausbremsen.
    """
    styled = style(
        figure,
        height=height,
        legend=legend,
        legend_y=legend_y,
        top_margin=top_margin,
        own_legends=own_legends,
    )
    config = {
        "displaylogo": False,
        "toImageButtonOptions": {"format": "svg", "filename": filename, "scale": 1},
    }
    st.plotly_chart(styled, width="stretch", config=config)

    if zusatz is None:
        svg_column, html_column, _ = st.columns([1, 1, 5])
    else:
        svg_column, html_column, zusatz_column, _ = st.columns([1, 1, 2, 3])
        zusatz(zusatz_column)
    svg_column.download_button(
        "SVG",
        lambda: _svg_bytes(styled.to_json()),
        file_name=f"{filename}.svg",
        mime="image/svg+xml",
        key=f"{filename}-svg",
        type="tertiary",
        help="Vektorgrafik zum Weiterverarbeiten oder Drucken",
    )
    html_column.download_button(
        "HTML",
        lambda: styled.to_html(full_html=True, include_plotlyjs="cdn", config=config),
        file_name=f"{filename}.html",
        mime="text/html",
        key=f"{filename}-html",
        type="tertiary",
        help="Interaktives Diagramm als eigenständige Datei",
    )


# --------------------------------------------------------------------------- Bausteine
# Ansicht (einfach/Experte) und Berichtskorb liegen in st.session_state. Der Umschalter
# steht in app/main.py; Seiten, die allein laufen (Tests), nutzen die einfache Ansicht.

ANSICHT_KEY = "experte"
BERICHT_KEY = "bericht"
# Widgets der Seite „Bericht“; main.py hält ihren Zustand beim Seitenwechsel fest.
BERICHT_OPTIONEN = (
    "bericht_titel",
    "bericht_untertitel",
    "bericht_autor",
    "bericht_format",
    "bericht_diagramme",
    "bericht_text",
    "bericht_quellenfolie",
)


def ansicht() -> bausteine.Ebene:
    """Aktuelle Ansicht; ohne Umschalter die einfache."""
    if st.session_state.get(ANSICHT_KEY):
        return bausteine.Ebene.EXPERTE
    return bausteine.Ebene.EINFACH


def optionen_erhalten() -> None:
    """Verhindert, dass Streamlit Widget-Zustände anderer Seiten verwirft."""
    for key in BERICHT_OPTIONEN:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def bericht_eintraege() -> list[dict]:
    """Berichtskorb: Liste von ``{"id": …, "parameter": {…}}``."""
    return st.session_state.setdefault(BERICHT_KEY, [])


def im_bericht(baustein_id: str) -> bool:
    return any(eintrag["id"] == baustein_id for eintrag in bericht_eintraege())


def _param_key(baustein: bausteine.Baustein, name: str) -> str:
    return f"param.{baustein.id}.{name}"


def _aktuelle_parameter(baustein: bausteine.Baustein) -> dict:
    """Gewählte Parameter; in der einfachen Ansicht immer die Standardwerte."""
    if ansicht() != bausteine.Ebene.EXPERTE:
        return baustein.parameterwerte()
    werte = {
        p.name: st.session_state[_param_key(baustein, p.name)]
        for p in baustein.parameter
        if _param_key(baustein, p.name) in st.session_state
    }
    return baustein.parameterwerte(werte)


def bericht_hinzufuegen(baustein_id: str, parameter: dict | None = None) -> None:
    if im_bericht(baustein_id):
        return
    baustein = bausteine.hole(baustein_id)
    werte = parameter if parameter is not None else _aktuelle_parameter(baustein)
    bericht_eintraege().append({"id": baustein_id, "parameter": baustein.parameterwerte(werte)})


def bericht_entfernen(baustein_id: str) -> None:
    st.session_state[BERICHT_KEY] = [
        eintrag for eintrag in bericht_eintraege() if eintrag["id"] != baustein_id
    ]


def bericht_verschieben(index: int, schritt: int) -> None:
    eintraege = bericht_eintraege()
    ziel = index + schritt
    if 0 <= index < len(eintraege) and 0 <= ziel < len(eintraege):
        eintraege[index], eintraege[ziel] = eintraege[ziel], eintraege[index]


def _bericht_umschalten(baustein_id: str) -> None:
    if im_bericht(baustein_id):
        bericht_entfernen(baustein_id)
    else:
        bericht_hinzufuegen(baustein_id)


def _bericht_knopf(baustein: bausteine.Baustein, ziel: DeltaGenerator) -> None:
    drin = im_bericht(baustein.id)
    ziel.button(
        "Im Bericht" if drin else "Zum Bericht",
        key=f"bericht.{baustein.id}",
        icon=":material/playlist_add_check:" if drin else ":material/playlist_add:",
        type="tertiary",
        on_click=_bericht_umschalten,
        args=(baustein.id,),
        help="Für den eigenen Bericht (Seite „Bericht“) vormerken bzw. wieder entfernen. "
        "Die aktuellen Einstellungen werden mitgenommen.",
    )


def _app_lader(name: str) -> pd.DataFrame:
    """Gecachter Lader aus diesem Modul, sonst die reine Ladefunktion."""
    lader = globals().get(name)
    return lader() if callable(lader) else bausteine.lade_aus_dataset(name)


def quellen_caption(schluessel: tuple[str, ...]) -> str:
    teile = []
    for eintrag in bausteine.quellenangaben(schluessel, sources_library()):
        text = eintrag.get("herausgeber") or ""
        text = f"{text}: {eintrag['titel']}" if text else eintrag["titel"]
        if eintrag.get("lizenz"):
            text += f" ({eintrag['lizenz']})"
        if eintrag.get("abgerufen_am"):
            text += f", abgerufen am {datetime.fromisoformat(eintrag['abgerufen_am']):%d.%m.%Y}"
        teile.append(text)
    return "Quelle: " + "; ".join(teile)


def _parameter_widgets(baustein: bausteine.Baustein) -> None:
    for parameter in baustein.parameter:
        key = _param_key(baustein, parameter.name)
        if key not in st.session_state:
            st.session_state[key] = parameter.standard
        if parameter.art == "ganzzahl":
            st.slider(
                parameter.beschriftung,
                min_value=parameter.minimum,
                max_value=parameter.maximum,
                step=parameter.schritt,
                key=key,
                help=parameter.hilfe or None,
            )
        elif parameter.art == "auswahl":
            st.selectbox(
                parameter.beschriftung,
                parameter.optionen,
                key=key,
                help=parameter.hilfe or None,
            )


def zeige_baustein(baustein: bausteine.Baustein | str) -> None:
    """Stellt einen Baustein mit Text, Inhalt, Downloads, Berichtsknopf und Quelle dar."""
    if isinstance(baustein, str):
        baustein = bausteine.hole(baustein)
    experte = ansicht() == bausteine.Ebene.EXPERTE

    st.subheader(baustein.titel)
    if experte and baustein.parameter:
        _parameter_widgets(baustein)
    kontext = baustein.kontext(_app_lader, _aktuelle_parameter(baustein))
    if aussage := baustein.aussage(kontext):
        st.markdown(f"**{aussage}**")
    if baustein.erklaerung:
        st.markdown(baustein.erklaerung)

    inhalt = baustein.erzeuge(kontext)
    knopf = functools.partial(_bericht_knopf, baustein)
    if isinstance(inhalt, bausteine.Diagramm):
        plot(
            inhalt.figur,
            filename=baustein.id.replace(".", "_"),
            height=inhalt.hoehe,
            legend=inhalt.legende,
            own_legends=inhalt.eigene_legenden,
            zusatz=knopf,
        )
    else:
        if isinstance(inhalt, pd.DataFrame):
            st.dataframe(inhalt, hide_index=True, width="stretch")
        elif isinstance(inhalt, list):
            spalten = st.columns(len(inhalt) or 1)
            for spalte, kennzahl in zip(spalten, inhalt, strict=False):
                spalte.metric(
                    kennzahl.beschriftung,
                    kennzahl.wert,
                    kennzahl.veraenderung,
                    delta_color=kennzahl.farbe,
                )
        else:
            st.markdown(str(inhalt))
        knopf(st.container())

    if experte and baustein.methodik:
        with st.expander("Methodik"):
            st.markdown(baustein.methodik)
    st.caption(quellen_caption(baustein.quellen))


def _abschnitt_zum_bericht(ids: tuple[str, ...]) -> None:
    for baustein_id in ids:
        bericht_hinzufuegen(baustein_id)


def zeige_seite(seite: bausteine.Seite) -> None:
    """Stellt eine aus Bausteinen zusammengesetzte Seite in der aktuellen Ansicht dar."""
    aktuelle = ansicht()
    st.title(seite.titel)
    if seite.einleitung:
        st.markdown(seite.einleitung)
    if aktuelle == bausteine.Ebene.EINFACH:
        versteckt = sum(not bausteine.hole(bid).sichtbar(aktuelle) for bid in seite.baustein_ids())
        if versteckt:
            st.caption(
                f"Einfache Ansicht – {versteckt} weitere Diagramme, Tabellen und "
                "Erläuterungen zeigt die **Expertenansicht** (Schalter in der Seitenleiste)."
            )

    nummer = 0
    for abschnitt in seite.abschnitte:
        sichtbar = tuple(
            bid for bid in abschnitt.bausteine if bausteine.hole(bid).sichtbar(aktuelle)
        )
        if not sichtbar:
            continue
        nummer += 1
        st.divider()
        kopf, knopf = st.columns([3, 1], vertical_alignment="bottom")
        kopf.header(f"{nummer}. {abschnitt.titel}")
        knopf.button(
            "Abschnitt zum Bericht",
            key=f"abschnitt.{seite.id}.{abschnitt.titel}",
            icon=":material/library_add:",
            type="tertiary",
            disabled=all(im_bericht(bid) for bid in sichtbar),
            on_click=_abschnitt_zum_bericht,
            args=(sichtbar,),
        )
        if abschnitt.einleitung:
            st.markdown(abschnitt.einleitung)
        for baustein_id in sichtbar:
            zeige_baustein(baustein_id)
