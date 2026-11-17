"""Parser für die CSV-Exporte der Deutschen Bundesbank."""

from __future__ import annotations

import csv
import io
from datetime import datetime

import pandas as pd

_DATE_FORMAT = "%Y-%m-%d"


def parse_yield_csv(raw: bytes) -> pd.DataFrame:
    """Wandelt einen Bundesbank-Zeitreihenexport in Tageswerte um.

    Der Export enthält mehrere Kopfzeilen mit Metadaten; Datenzeilen beginnen mit
    einem ISO-Datum (``JJJJ-MM-TT``). Fehlende Werte sind mit ``.`` markiert.
    """
    text = raw.decode("utf-8-sig")
    records = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2:
            continue
        try:
            datum = datetime.strptime(row[0].strip(), _DATE_FORMAT).date()
        except ValueError:
            continue
        value = row[1].strip().replace(",", ".")
        if value in {"", ".", "-"}:
            continue
        try:
            rendite = float(value)
        except ValueError:
            continue
        records.append({"datum": datum, "rendite_pct": rendite})

    frame = pd.DataFrame.from_records(records, columns=["datum", "rendite_pct"])
    frame["datum"] = pd.to_datetime(frame["datum"])
    return frame.sort_values("datum").reset_index(drop=True)
