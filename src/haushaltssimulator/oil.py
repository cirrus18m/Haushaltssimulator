"""Parser für das wöchentliche Ölbulletin der EU-Kommission (xlsx)."""

from __future__ import annotations

import io
from datetime import date

import pandas as pd

PRODUKTE = {
    "euro95": "Superbenzin (Euro 95)",
    "diesel": "Diesel",
}


def parse_prices(
    raw: bytes,
    *,
    since: date | None = None,
    produkte: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Liest die wöchentlichen Verbraucherpreise (mit Steuern) je Land.

    Die Preise stehen im Blatt ``Prices with taxes`` in Blöcken je Land; die
    Spaltennamen lauten ``<CODE>_price_with_tax_<produkt>``. Die Werte sind in
    EUR je 1000 Liter hinterlegt und werden hier in EUR je Liter umgerechnet.
    ``produkte`` ordnet Spaltenschlüssel den deutschen Bezeichnungen zu.
    """
    produkte = PRODUKTE if produkte is None else produkte
    frame = pd.read_excel(io.BytesIO(raw), sheet_name="Prices with taxes", header=None)
    columns: dict[str, dict[str, int]] = {}
    for index, name in enumerate(frame.iloc[0]):
        if not isinstance(name, str):
            continue
        for product in produkte:
            suffix = f"_price_with_tax_{product}"
            if name.endswith(suffix):
                columns.setdefault(name[: -len(suffix)], {})[product] = index
    if not columns:
        raise ValueError("Keine Preisblöcke im Ölbulletin gefunden")

    records = []
    for _, row in frame.iterrows():
        datum = row.iloc[0]
        if not hasattr(datum, "year"):
            continue
        tag = pd.Timestamp(datum).date()
        if since and tag < since:
            continue
        for code, products in columns.items():
            for product, index in products.items():
                value = row.iloc[index]
                if pd.isna(value):
                    continue
                records.append(
                    {
                        "datum": tag,
                        "land_code": code,
                        "produkt": produkte[product],
                        "preis_eur_l": float(value) / 1000,
                    }
                )
    return pd.DataFrame.from_records(records)
