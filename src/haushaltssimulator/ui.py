"""Streamlit-Hilfen: gecachte Daten, Formatierung und einheitliches Layout."""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import dataset
from .paths import RAW_DIR

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
def data_retrieved_at() -> datetime | None:
    path = RAW_DIR / "_quellen.json"
    if not path.exists():
        return None
    metadata = json.loads(path.read_text(encoding="utf-8"))
    return datetime.fromisoformat(metadata["abgerufen_am"])


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


def style(fig: go.Figure, *, height: int = 430, legend: bool = True) -> go.Figure:
    """Einheitliches Layout für alle Diagramme."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        hovermode="x unified" if legend else "closest",
        showlegend=legend,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        font={"family": "Inter, Segoe UI, sans-serif", "size": 13},
    )
    return fig
