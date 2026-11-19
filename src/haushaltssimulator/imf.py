"""Parser für die DataMapper-API des Internationalen Währungsfonds."""

from __future__ import annotations

import json

import pandas as pd

# Indikatoren, die der Datenaufbau aus der DataMapper-API bezieht.
WEO_SCHULDENQUOTE = "GGXWDG_NGDP"
WEO_BIP_USD = "NGDPD"
WEO_BIP_JE_EINWOHNER = "NGDPDPC"
WEO_BIP_WACHSTUM = "NGDP_RPCH"
WEO_BEVOELKERUNG = "LP"
FPP_SCHULDENQUOTE = "d"
FPP_EINNAHMEN = "rev"
FPP_ZINSEN = "ie"


def parse_datamapper(payload: bytes | str, indikator: str) -> pd.DataFrame:
    """Liest eine IWF-Reihe aus einer DataMapper-Antwort.

    Die API liefert je Aufruf die Werte aller Länder. Zurückgegeben wird ein langes
    Frame mit ``indikator``, ``iso3``, ``jahr`` und ``wert``.
    """
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    data = json.loads(text)
    values = data.get("values", {}).get(indikator)
    if not values:
        raise ValueError(f"IWF-Antwort enthält den Indikator {indikator} nicht")

    rows = [
        {"indikator": indikator, "iso3": iso3, "jahr": int(jahr), "wert": float(wert)}
        for iso3, serie in values.items()
        for jahr, wert in serie.items()
        if wert is not None
    ]
    frame = pd.DataFrame(rows)
    return frame.sort_values(["indikator", "iso3", "jahr"]).reset_index(drop=True)
