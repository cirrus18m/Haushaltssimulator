"""Parser für Indikatoren der Weltbank-API (World Development Indicators)."""

from __future__ import annotations

import json

import pandas as pd


def parse_indicator_json(payload: bytes | str, indikator: str) -> pd.DataFrame:
    """Liest eine Weltbank-Reihe mit Jahreswerten.

    Die API liefert ein Array aus Metadaten und Beobachtungen. Zurückgegeben wird
    ein Frame mit ``indikator``, ``iso3``, ``jahr`` und ``wert``.
    """
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    data = json.loads(text)
    if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
        raise ValueError("Weltbank-Antwort enthält keine Beobachtungen")

    rows = [
        {
            "indikator": indikator,
            "iso3": beobachtung["countryiso3code"],
            "jahr": int(beobachtung["date"]),
            "wert": float(beobachtung["value"]),
        }
        for beobachtung in data[1]
        if beobachtung.get("value") is not None
    ]
    frame = pd.DataFrame(rows)
    return frame.sort_values(["indikator", "iso3", "jahr"]).reset_index(drop=True)
