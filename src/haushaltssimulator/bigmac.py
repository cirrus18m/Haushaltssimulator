"""Parser für den Big-Mac-Index des Economist."""

from __future__ import annotations

import io

import pandas as pd


def parse_index(raw: bytes) -> pd.DataFrame:
    """Liest den vollständigen Big-Mac-Index (Preis in US-Dollar und Abweichung)."""
    frame = pd.read_csv(io.BytesIO(raw))
    if not {"date", "iso_a3", "dollar_price"}.issubset(frame.columns):
        raise ValueError("Big-Mac-Export hat ein unerwartetes Format")

    result = frame[["date", "iso_a3", "dollar_price", "USD_raw"]].rename(
        columns={
            "date": "datum",
            "iso_a3": "iso3",
            "dollar_price": "preis_usd",
            "USD_raw": "abweichung_pct",
        }
    )
    result["datum"] = pd.to_datetime(result["datum"])
    result["preis_usd"] = pd.to_numeric(result["preis_usd"], errors="coerce")
    result["abweichung_pct"] = pd.to_numeric(result["abweichung_pct"], errors="coerce") * 100
    return result.dropna(subset=["preis_usd"]).sort_values(["datum", "iso3"]).reset_index(drop=True)
