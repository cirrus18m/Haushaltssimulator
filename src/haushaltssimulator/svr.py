"""Parser for figure data from the German Council of Economic Experts (SVR) reports.

The SVR annual report PDF embeds one CSV file per figure (attachment ``AbbNNN.csv``,
linked as "Daten (CSV)" in the PDF). Layout: a header row with ``Jahr`` and the series,
one row per year with values in German notation, then an empty row followed by title,
footnotes, sources and the figure number.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

import pandas as pd

from .destatis import parse_number

# Superscript footnote digits after series names, e.g. "Kreditaufnahme²".
_FOOTNOTE = re.compile(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+")


@dataclass(frozen=True)
class FigureData:
    """Values and accompanying text of one SVR figure."""

    data: pd.DataFrame
    title: str
    notes: tuple[str, ...]


def series_name(column: str) -> str:
    """Column name without footnote digits and repeated whitespace."""
    return " ".join(_FOOTNOTE.sub("", column).split())


def parse_figure_csv(raw: bytes) -> FigureData:
    """Read an embedded figure CSV; years without any value are dropped.

    All columns keep the SVR names (``Jahr`` and the German series names), only the
    footnote digits are removed.
    """
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    if not rows or not rows[0] or rows[0][0].strip() != "Jahr":
        raise ValueError("Not an SVR figure CSV: header row with 'Jahr' missing")
    header = [series_name(column) for column in rows[0]]

    records = []
    end = len(rows)
    for index, row in enumerate(rows[1:], start=1):
        if not any(cell.strip() for cell in row):
            end = index
            break
        values = [parse_number(cell) for cell in row[1:]]
        if all(pd.isna(value) for value in values):
            continue
        records.append([int(row[0]), *values])
    data = pd.DataFrame.from_records(records, columns=header)

    trailer = [" ".join(row).strip() for row in rows[end + 1 :] if any(row)]
    title = next(
        (line.removeprefix("Titel:").strip() for line in trailer if line.startswith("Titel:")),
        "",
    )
    notes = tuple(line for line in trailer if not line.startswith("Titel:"))
    return FigureData(data=data, title=title, notes=notes)
