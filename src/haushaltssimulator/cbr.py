"""Parser für die Zero-Coupon-Yield-Curve der Bank of Russia."""

from __future__ import annotations

import calendar
import re
from datetime import date

_TABLE_PATTERN = re.compile(r"Remaining maturity.*?</table>", re.DOTALL)
_CELL_PATTERN = re.compile(r"<td>\s*([^<]*?)\s*</td>")
# Die erste Zelle enthält die Beschriftung, danach folgen die Laufzeiten
# 0,25 / 0,5 / 0,75 / 1 / 2 / 3 / 5 / 7 / 10 / 15 / 20 / 30 Jahre.
_TEN_YEAR_POSITION = 9


def parse_ten_year_yield(html: str) -> float | None:
    """Liest die 10-Jahres-Rendite aus der Tabellenansicht der Zinskurve."""
    table = _TABLE_PATTERN.search(html)
    if table is None:
        return None
    cells = _CELL_PATTERN.findall(table.group(0))
    if len(cells) <= _TEN_YEAR_POSITION:
        return None
    text = cells[_TEN_YEAR_POSITION].replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def month_ends(start: date, end: date) -> list[date]:
    """Kalendermonatsenden von ``start`` bis ``end`` (einschließlich)."""
    result = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        result.append(date(year, month, calendar.monthrange(year, month)[1]))
        month += 1
        if month > 12:
            year += 1
            month = 1
    return result
