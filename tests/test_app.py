"""Smoke-Tests für die aufbereiteten Datensätze und die Streamlit-Seiten."""

from __future__ import annotations

from pathlib import Path

import pytest

from haushaltssimulator import dataset, paths

APP_DIR = paths.PROJECT_ROOT / "app"

pytestmark = pytest.mark.skipif(
    not (paths.PROCESSED_DIR / dataset.ANNUAL_DEBT).exists(),
    reason="Aufbereitete Daten fehlen – `uv run scripts/build_data.py` ausführen",
)


def test_annual_debt_covers_gesamtstaat() -> None:
    annual = dataset.load_annual_debt()
    total = annual[annual["sector"] == "S13"].dropna(subset=["schulden_mio_eur"])
    assert total["jahr"].min() <= 1995
    assert total["jahr"].max() >= 2024
    assert total["schulden_mio_eur"].is_monotonic_increasing is False
    assert total["schuldenquote_pct"].between(0, 200).all()


def test_destatis_quarterly_has_all_levels() -> None:
    frame = dataset.load_destatis_quarterly()
    complete = frame[(frame["haushalt"] == "Insgesamt") & (frame["schuldenart"] == "Insgesamt")]
    levels = set(complete["ebene"])
    assert {"Bund", "Länder", "Gemeinden / Gemeindeverbände", "Insgesamt"} <= levels
    latest = complete[complete["stichtag"] == complete["stichtag"].max()]
    einzel = latest[latest["ebene"] != "Insgesamt"]["schulden_mio_eur"].sum()
    gesamt = latest.loc[latest["ebene"] == "Insgesamt", "schulden_mio_eur"].sum()
    assert einzel == pytest.approx(gesamt, rel=1e-6)


def test_laender_quarterly_has_sixteen_states() -> None:
    frame = dataset.load_laender_quarterly()
    assert frame["bundesland"].nunique() == 16
    assert frame["stichtag"].nunique() >= 4


def test_interest_burden_links_debt_revenue_and_yield() -> None:
    frame = dataset.load_interest_burden().dropna(subset=["rendite_pct"])
    latest = frame.iloc[-1]
    expected = latest["schulden_mio_eur"] * latest["rendite_pct"] / 100
    # Die gespeicherte Rendite ist auf zwei Nachkommastellen gerundet.
    tolerance = latest["schulden_mio_eur"] * 0.0001
    assert latest["zins_theoretisch_mio_eur"] == pytest.approx(expected, abs=tolerance)
    assert 0 < latest["zins_quote_einnahmen_pct"] < 20
    assert 0 < latest["zins_quote_bip_pct"] < 10


def test_international_yields_cover_germany_usa_and_russia() -> None:
    frame = dataset.load_international_yields()
    assert {"Deutschland", "Vereinigte Staaten", "Russland"} <= set(frame["land"])
    assert frame["monat"].max() >= "2026-01"
    assert frame["rendite_pct"].between(-5, 100).all()


@pytest.mark.parametrize(
    "script",
    [
        "main.py",
        "pages/0_Ueberblick.py",
        "pages/1_Zeitreihe.py",
        "pages/2_Ebenen_und_Schuldenarten.py",
        "pages/3_Bundeslaender.py",
        "pages/4_Analysen.py",
        "pages/5_Szenario.py",
        "pages/6_Haushalt_und_Zinsen.py",
        "pages/7_Zinsvergleich.py",
        "pages/8_Quellen.py",
    ],
)
def test_streamlit_pages_run_without_exception(script: str) -> None:
    from streamlit.testing.v1 import AppTest

    test = AppTest.from_file(str(Path(APP_DIR) / script), default_timeout=60)
    test.run()
    assert not test.exception, [str(exception.value) for exception in test.exception]
