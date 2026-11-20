"""Parser für die Destatis-Tabellenexporte (CSV, Semikolon-getrennt)."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Sequence
from datetime import datetime

import pandas as pd

_DATE_FORMAT = "%d.%m.%Y"
_UNIT_PATTERN = re.compile(r"\(([^()]*)\)")
_ALLOWED_UNITS = {"Mill. EUR", "EUR", "%", "Mill. USD"}


def decode(raw: bytes) -> str:
    """Dekodiert Destatis-Exporte (meist Windows-1252, teils UTF-8)."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1252", errors="replace")


def parse_number(value: str) -> float:
    """Wandelt Destatis-Zahlen um; fehlende Werte ("-", "...") werden zu NaN."""
    text = value.strip().replace("\u00a0", "").replace(" ", "")
    if text in {"", "-", "...", "/", "."}:
        return float("nan")
    if re.fullmatch(r"-?\d+", text):
        return float(text)
    # Deutsche Schreibweise: Punkt als Tausendertrenner, Komma als Dezimaltrenner
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def _detect_unit(rows: Sequence[Sequence[str]]) -> str:
    for row in rows[:8]:
        for cell in row:
            match = _UNIT_PATTERN.search(cell)
            if match and match.group(1) in _ALLOWED_UNITS:
                return match.group(1)
    return ""


def parse_table(raw: str, label_columns: Sequence[str]) -> pd.DataFrame:
    """Wandelt eine Destatis-Tabelle in ein langes Datenformat um.

    Die Spaltennamen der Merkmale stehen im Export nicht zur Verfügung, daher
    werden sie über ``label_columns`` in der Reihenfolge der Datei vergeben.
    """
    rows = [row for row in csv.reader(io.StringIO(raw), delimiter=";")]
    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if sum(cell.strip().startswith("Stichtag") for cell in row) >= 2
        ),
        None,
    )
    if header_index is None:
        raise ValueError("Keine Stichtagsspalten in der Tabelle gefunden")

    header = rows[header_index]
    date_columns = [
        (index, datetime.strptime(rows[header_index + 1][index].strip(), _DATE_FORMAT).date())
        for index, cell in enumerate(header)
        if cell.strip().startswith("Stichtag")
    ]
    first_date_column = date_columns[0][0]
    if first_date_column != len(label_columns):
        raise ValueError(
            f"Tabelle hat {first_date_column} Merkmalsspalten, erwartet {len(label_columns)}"
        )

    records = []
    unit = _detect_unit(rows)
    for row in rows[header_index + 2 :]:
        if not row or not row[0].strip() or row[0].strip().startswith(("_", "©")):
            continue
        labels = [cell.strip() for cell in row[:first_date_column]]
        if len(labels) != len(label_columns) or not all(labels):
            continue
        for column, stichtag in date_columns:
            records.append(
                {
                    **dict(zip(label_columns, labels, strict=True)),
                    "stichtag": stichtag,
                    "wert": parse_number(row[column]) if column < len(row) else float("nan"),
                }
            )

    frame = pd.DataFrame.from_records(records)
    frame["einheit"] = unit
    return frame


def parse_fixed_columns(
    raw: str,
    label_columns: Sequence[str],
    value_columns: Sequence[str],
    *,
    year_column: int = 0,
    fill_down: Sequence[str] = (),
) -> pd.DataFrame:
    """Liest Tabellen mit festen Merkmals- und Wertspalten.

    Anders als bei den Stichtagstabellen enthalten die Merkmalsspalten das Jahr
    (z. B. ``2026;Januar;Insgesamt;9418;3611659``). Kopfzeilen werden übersprungen,
    bis in ``year_column`` eine Jahreszahl steht. Bei ``year_column=1`` beginnt die
    Tabelle mit einem Merkmal, etwa ``Verarbeitendes Gewerbe;2026;Januar;...``.

    Merkmale in ``fill_down`` werden aus der vorigen Zeile übernommen, wenn die Zelle
    leer ist – lange Monatsreihen nennen das Jahr oft nur beim Januar
    (``1991;Januar;...`` gefolgt von ``;Februar;...``).
    """
    rows = list(csv.reader(io.StringIO(raw), delimiter=";"))
    start = next(
        (
            index
            for index, row in enumerate(rows)
            if len(row) > year_column and re.fullmatch(r"\d{4}", row[year_column].strip())
        ),
        None,
    )
    if start is None:
        raise ValueError("Keine Datenzeilen in der Tabelle gefunden")

    records = []
    previous: dict[str, str] = {}
    for row in rows[start:]:
        if len(row) < len(label_columns) + len(value_columns):
            continue
        labels = [cell.strip() for cell in row[: len(label_columns)]]
        for index, column in enumerate(label_columns):
            if column in fill_down:
                labels[index] = labels[index] or previous.get(column, "")
                previous[column] = labels[index]
        if not all(labels):
            continue
        record: dict[str, object] = dict(zip(label_columns, labels, strict=True))
        for offset, column in enumerate(value_columns):
            record[column] = parse_number(row[len(label_columns) + offset])
        records.append(record)

    return pd.DataFrame.from_records(records)


def parse_year_columns(raw: str, label_columns: Sequence[str]) -> pd.DataFrame:
    """Liest Tabellen, die Jahre als Spalten führen (z. B. VGR-Jahrestabellen).

    Beispiel::

        ;;;2016;2017;2018
        in jeweiligen Preisen (Mrd. EUR);Bruttoinlandsprodukt;jew. ME;3204,870;3345,860;3450,580

    Zurückgegeben wird je Merkmalszeile und Jahr ein Datensatz mit den
    ``label_columns``, ``jahr`` und ``wert``.
    """
    rows = list(csv.reader(io.StringIO(raw), delimiter=";"))
    header_index = None
    year_columns: list[tuple[int, int]] = []
    for index, row in enumerate(rows):
        columns = [
            (position, int(cell.strip()))
            for position, cell in enumerate(row)
            if re.fullmatch(r"\d{4}", cell.strip())
        ]
        # Die Jahreszahlen stehen nach den Merkmalsspalten und steigen auf.
        if (
            len(columns) >= 2
            and columns[0][0] >= len(label_columns)
            and all(
                links[1] < rechts[1]
                for links, rechts in zip(columns, columns[1:], strict=False)
            )
        ):
            header_index = index
            year_columns = columns
            break
    if header_index is None:
        raise ValueError("Keine Jahres-Kopfzeile in der Tabelle gefunden")

    records = []
    for row in rows[header_index + 1 :]:
        labels = [cell.strip() for cell in row[: len(label_columns)]]
        if len(labels) != len(label_columns) or not all(labels):
            continue
        for position, jahr in year_columns:
            records.append(
                {
                    **dict(zip(label_columns, labels, strict=True)),
                    "jahr": jahr,
                    "wert": parse_number(row[position]) if position < len(row) else float("nan"),
                }
            )

    return pd.DataFrame.from_records(records)


def parse_flagged_columns(
    raw: str, label_columns: Sequence[str], value_columns: Sequence[str]
) -> pd.DataFrame:
    """Liest Tabellen, in denen auf jeden Wert eine Statusspalte folgt.

    Beispiel: ``2003;Januar;Insgesamt;1892;e;1353;e;x;;3245;e``. Ausgelesen werden
    nur die Wertspalten; Statusspalten (``e``, ``x``, leer) werden verworfen.
    """
    rows = list(csv.reader(io.StringIO(raw), delimiter=";"))
    start = next(
        (index for index, row in enumerate(rows) if row and re.fullmatch(r"\d{4}", row[0].strip())),
        None,
    )
    if start is None:
        raise ValueError("Keine Datenzeilen in der Tabelle gefunden")

    records = []
    for row in rows[start:]:
        if len(row) <= len(label_columns):
            continue
        labels = [cell.strip() for cell in row[: len(label_columns)]]
        if not all(labels):
            continue
        record: dict[str, object] = dict(zip(label_columns, labels, strict=True))
        for index, column in enumerate(value_columns):
            position = len(label_columns) + 2 * index
            record[column] = parse_number(row[position]) if position < len(row) else float("nan")
        records.append(record)

    return pd.DataFrame.from_records(records)
