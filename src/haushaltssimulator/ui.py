"""Streamlit-Hilfen: gecachte Daten, Formatierung und einheitliches Layout."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from . import dataset, sources

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


MONATSNAMEN = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)


def format_month(value: str) -> str:
    """Formatiert einen Monat ``JJJJ-MM`` in deutscher Schreibweise."""
    return f"{MONATSNAMEN[int(value[5:7]) - 1]} {value[:4]}"


def format_number(value: float, decimals: int = 1, unit: str = "") -> str:
    """Formatiert Zahlen in deutscher Schreibweise."""
    if value is None or pd.isna(value):
        return "–"
    text = f"{value:,.{decimals}f}"
    text = text.replace(",", "\u202f").replace(".", ",").replace("\u202f", ".")
    return f"{text}{unit}"


def format_mrd(value_mio_eur: float, decimals: int = 1) -> str:
    """Millionen Euro als Milliarden Euro."""
    return format_number(value_mio_eur / 1000, decimals, " Mrd. €")


def format_eur(value_eur: float) -> str:
    return format_number(value_eur, 0, " €")


def style(
    fig: go.Figure, *, height: int = 430, legend: bool = True, legend_y: float = 1.02
) -> go.Figure:
    """Einheitliches Layout für alle Diagramme."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        hovermode="x unified" if legend else "closest",
        showlegend=legend,
        legend={"orientation": "h", "yanchor": "bottom", "y": legend_y, "x": 0},
        font={"family": "Inter, Segoe UI, sans-serif", "size": 13},
    )
    return fig


@st.cache_data(show_spinner=False, max_entries=64)
def _svg_bytes(figure_json: str) -> bytes | None:
    """Rendert ein Diagramm als SVG; ohne funktionierendes Kaleido bleibt es leer."""
    try:
        return pio.from_json(figure_json).to_image(format="svg")
    except Exception:  # Kaleido bzw. Chrome kann in manchen Umgebungen fehlen
        return None


def plot(
    figure: go.Figure,
    *,
    filename: str,
    height: int = 430,
    legend: bool = True,
    legend_y: float = 1.02,
) -> None:
    """Zeigt ein Diagramm und bietet es als SVG und als HTML zum Download an."""
    styled = style(figure, height=height, legend=legend, legend_y=legend_y)
    config = {
        "displaylogo": False,
        "toImageButtonOptions": {"format": "svg", "filename": filename, "scale": 1},
    }
    st.plotly_chart(styled, width="stretch", config=config)

    svg = _svg_bytes(styled.to_json())
    html = styled.to_html(full_html=True, include_plotlyjs="cdn", config=config)
    svg_column, html_column, _ = st.columns([1, 1, 5])
    if svg is not None:
        svg_column.download_button(
            "SVG",
            svg,
            file_name=f"{filename}.svg",
            mime="image/svg+xml",
            key=f"{filename}-svg",
            type="tertiary",
            help="Vektorgrafik zum Weiterverarbeiten oder Drucken",
        )
    else:
        svg_column.caption("SVG über das Kamera-Symbol")
    html_column.download_button(
        "HTML",
        html,
        file_name=f"{filename}.html",
        mime="text/html",
        key=f"{filename}-html",
        type="tertiary",
        help="Interaktives Diagramm als eigenständige Datei",
    )
