"""Tests für die Parser der neuen Zinsquellen."""

from __future__ import annotations

from datetime import date

import pytest

from haushaltssimulator import bundesbank, cbr, fred, sources

BUNDESBANK_CSV = (
    b'''\xef\xbb\xbf"",BBSSY.D.REN.EUR.A630.000000WT1010.A,'''
    b"""BBSSY.D.REN.EUR.A630.000000WT1010.A_FLAGS
"",Daily yield of the current 10 year federal bond,
Decimals,2,
unit,PROZENT,
2001-10-01,4.78,
2001-10-02,4.75,
2001-10-06,.,No value available
2001-10-08,4.63,
"""
)

CBR_HTML = """
<div class="data">
  <table class="data">
    <tr>
      <th>Remaining maturity</th>
      <th>0.25</th><th>0.50</th><th>0.75</th><th>1.00</th><th>2.00</th><th>3.00</th>
      <th>5.00</th><th>7.00</th><th>10.00</th><th>15.00</th><th>20.00</th><th>30.00</th>
    </tr>
    <tr>
      <td>Yield, % per annum</td>
      <td>13.36</td><td>13.59</td><td>13.80</td><td>14.03</td><td>14.85</td><td>15.48</td>
      <td>16.25</td><td>16.64</td><td>16.87</td><td>17.01</td><td>17.09</td><td>17.22</td>
    </tr>
  </table>
</div>
"""


def test_bundesbank_parses_daily_values_and_skips_missing() -> None:
    frame = bundesbank.parse_yield_csv(BUNDESBANK_CSV)
    assert list(frame.columns) == ["datum", "rendite_pct"]
    assert frame["datum"].dt.date.tolist() == [
        date(2001, 10, 1),
        date(2001, 10, 2),
        date(2001, 10, 8),
    ]
    assert frame["rendite_pct"].tolist() == [4.78, 4.75, 4.63]


def test_cbr_reads_ten_year_maturity() -> None:
    assert cbr.parse_ten_year_yield(CBR_HTML) == pytest.approx(16.87)


def test_cbr_returns_none_for_holiday_table() -> None:
    holiday = CBR_HTML.replace("<td>16.87</td>", "<td>—</td>")
    assert cbr.parse_ten_year_yield(holiday) is None
    assert cbr.parse_ten_year_yield("<html></html>") is None


def test_cbr_month_ends() -> None:
    assert cbr.month_ends(date(2024, 1, 15), date(2024, 3, 2)) == [
        date(2024, 1, 31),
        date(2024, 2, 29),
        date(2024, 3, 31),
    ]


def test_fred_parses_observation_and_value_columns() -> None:
    raw = b"observation_date,IRLTLT01USM156N\n2024-01-01,4.10\n2024-02-01,.\n2024-03-01,4.30\n"
    frame = fred.parse_series_csv(raw)
    assert list(frame.columns) == ["datum", "wert"]
    assert frame["wert"].tolist() == [4.10, 4.30]


def test_eurostat_url_repeats_list_parameters() -> None:
    url = sources._eurostat("gov_10a_main", geo="DE", na_item=["TR", "TE"])
    assert "geo=DE" in url
    assert url.count("na_item=") == 2
    assert "na_item=TR" in url and "na_item=TE" in url


@pytest.mark.parametrize("source", sources.SOURCES, ids=lambda source: source.key)
def test_source_metadata_is_complete(source: sources.Source) -> None:
    assert source.title
    assert source.publisher
    assert source.license
    assert source.url.startswith("https://")
    assert source.datasets
