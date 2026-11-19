"""Parser für die CSV-Exporte aus dem Bundeshaushalt (BMF)."""

from __future__ import annotations

import csv
import io
import re

import pandas as pd

from .destatis import parse_number

_YEAR = re.compile(r"(\d{4})\s*(?:\(([^)]*)\))?")


def parse_interest_csv(raw: bytes) -> pd.DataFrame:
    """Liest Zinsausgaben je Haushaltsjahr (Ist, Soll, Entwurf oder Finanzplan)."""
    text = raw.decode("utf-8-sig")
    records = []
    for row in csv.reader(io.StringIO(text), delimiter=";"):
        if len(row) < 2:
            continue
        match = _YEAR.search(row[0])
        if match is None:
            continue
        records.append(
            {
                "jahr": int(match.group(1)),
                "art": match.group(2) or "",
                "zinsausgaben_mrd_eur": parse_number(row[1]),
            }
        )
    return pd.DataFrame.from_records(records)
