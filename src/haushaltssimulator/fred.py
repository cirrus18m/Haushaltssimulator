"""Parser für FRED-CSV-Exporte (Federal Reserve Bank of St. Louis)."""

from __future__ import annotations

import io

import pandas as pd


def parse_series_csv(raw: bytes) -> pd.DataFrame:
    """Liest eine FRED-Zeitreihe mit Datum in der ersten und Wert in der zweiten Spalte."""
    frame = pd.read_csv(io.BytesIO(raw))
    if frame.shape[1] < 2:
        raise ValueError("FRED-Export enthält keine Wertspalte")
    frame = frame.iloc[:, :2].copy()
    frame.columns = ["datum", "wert"]
    frame["datum"] = pd.to_datetime(frame["datum"], errors="coerce")
    frame["wert"] = pd.to_numeric(frame["wert"], errors="coerce")
    return frame.dropna(subset=["datum", "wert"]).reset_index(drop=True)
