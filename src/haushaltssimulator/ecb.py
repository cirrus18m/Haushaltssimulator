"""Parser für CSV-Exporte des ECB Data Portals."""

from __future__ import annotations

import io

import pandas as pd


def parse_csv(raw: bytes) -> pd.DataFrame:
    """Liest Zeitreihen aus dem CSV-Export des ECB Data Portals.

    Enthält der Export mehrere Gebiete, wird zusätzlich die Spalte ``gebiet`` gefüllt.
    """
    frame = pd.read_csv(io.BytesIO(raw))
    if not {"TIME_PERIOD", "OBS_VALUE"}.issubset(frame.columns):
        raise ValueError("ECB-Export enthält TIME_PERIOD oder OBS_VALUE nicht")

    columns = ["TIME_PERIOD", "OBS_VALUE"]
    if "REF_AREA" in frame.columns:
        columns.insert(0, "REF_AREA")
    result = frame[columns].rename(
        columns={"REF_AREA": "gebiet", "TIME_PERIOD": "monat", "OBS_VALUE": "wert"}
    )
    result["wert"] = pd.to_numeric(result["wert"], errors="coerce")
    result["monat"] = result["monat"].astype(str)
    result = result.dropna(subset=["wert"])

    sort_columns = ["gebiet", "monat"] if "gebiet" in result.columns else ["monat"]
    return result.sort_values(sort_columns).reset_index(drop=True)
