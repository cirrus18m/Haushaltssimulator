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


def parse_areas_csv(raw: bytes) -> pd.DataFrame:
    """Liest die Ausgaben nach Aufgabenbereichen je Haushaltsjahr.

    Der manuelle Export hat eine Kopfzeile mit den Haushaltsjahren, danach je Zeile
    Einzelplan, Aufgabenbereich und die Ausgaben in Mrd. EUR; "-" steht für einen
    nicht veranschlagten Betrag.
    """
    text = raw.decode("utf-8-sig")
    rows = [row for row in csv.reader(io.StringIO(text), delimiter=";") if row]
    if not rows:
        raise ValueError("Leerer Export der Ausgaben nach Aufgabenbereichen")
    jahre = [int(spalte) for spalte in rows[0][2:] if spalte.strip()]
    records = []
    for row in rows[1:]:
        if len(row) < 2 or not row[0].strip():
            continue
        bereich = " ".join(row[1].split())
        for jahr, wert in zip(jahre, row[2:], strict=False):
            records.append(
                {
                    "einzelplan": row[0].strip(),
                    "aufgabenbereich": bereich,
                    "jahr": jahr,
                    "ausgaben_mrd_eur": parse_number(wert),
                }
            )
    return pd.DataFrame.from_records(records)
