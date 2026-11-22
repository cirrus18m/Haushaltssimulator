"""Deutsche Zahlen- und Datumsformatierung ohne Streamlit (von ``ui`` re-exportiert)."""

from __future__ import annotations

import pandas as pd

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
    text = text.replace(",", " ").replace(".", ",").replace(" ", ".")
    return f"{text}{unit}"


def format_signed(value: float, decimals: int = 1, unit: str = "") -> str:
    """Wie :func:`format_number`, aber mit „+“ vor positiven Werten (Veränderungen)."""
    text = format_number(value, decimals, unit)
    return f"+{text}" if value is not None and not pd.isna(value) and value > 0 else text


def format_mrd(value_mio_eur: float, decimals: int = 1) -> str:
    """Millionen Euro als Milliarden Euro."""
    return format_number(value_mio_eur / 1000, decimals, " Mrd. €")


def format_eur(value_eur: float) -> str:
    return format_number(value_eur, 0, " €")
