"""Zugriff auf die aufbereiteten CSV-Dateien (reines pandas, ohne Streamlit)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .paths import PROCESSED_DIR

ANNUAL_DEBT = "schulden_jahresreihe.csv"
QUARTERLY_DEBT = "schulden_quartalsreihe.csv"
DESTATIS_ANNUAL = "schulden_destatis_jahr.csv"
DESTATIS_QUARTERLY = "schulden_destatis_quartal.csv"
DESTATIS_LAENDER = "schulden_destatis_bundeslaender.csv"
GDP_POPULATION = "bip_bevoelkerung.csv"

_DATE_COLUMNS = ("stichtag", "quartalsende")


def _read(filename: str, processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    path = processed_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} fehlt. Bitte zuerst `uv run scripts/build_data.py` ausführen."
        )
    frame = pd.read_csv(path, dtype={"jahr": "Int64"})
    for column in _DATE_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def load_annual_debt(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Maastricht-Schuldenstand je Jahr und Ebene (Eurostat, ab 1995)."""
    return _read(ANNUAL_DEBT, processed_dir)


def load_quarterly_debt(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Maastricht-Schuldenstand je Quartal und Ebene (Eurostat, ab 2000)."""
    return _read(QUARTERLY_DEBT, processed_dir)


def load_destatis_annual(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Jährliche Schulden beim nicht-öffentlichen Bereich (Destatis, ab 2010)."""
    return _read(DESTATIS_ANNUAL, processed_dir)


def load_destatis_quarterly(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Vierteljährliche Schulden beim nicht-öffentlichen Bereich (Destatis)."""
    return _read(DESTATIS_QUARTERLY, processed_dir)


def load_laender_quarterly(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Vierteljährliche Schulden der Bundesländer (Destatis)."""
    return _read(DESTATIS_LAENDER, processed_dir)


def load_gdp_population(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """BIP, Bevölkerung und BIP je Einwohner je Jahr (Eurostat)."""
    return _read(GDP_POPULATION, processed_dir)


def with_debt_per_capita(annual_debt: pd.DataFrame, gdp_population: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt den Schuldenstand des Gesamtstaats um Schulden je Einwohner."""
    frame = annual_debt.merge(gdp_population[["jahr", "bevoelkerung"]], on="jahr", how="left")
    frame["schulden_je_einwohner_eur"] = (
        frame["schulden_mio_eur"] * 1_000_000 / frame["bevoelkerung"]
    )
    return frame
