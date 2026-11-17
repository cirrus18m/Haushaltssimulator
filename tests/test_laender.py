"""Tests für die Länderdaten des Zinsvergleichs (Schulden, Zinsausgaben, Inflation)."""

from __future__ import annotations

import pandas as pd
import pytest

from haushaltssimulator import analysis, dataset, sources


@pytest.fixture(scope="module")
def laender_debt() -> pd.DataFrame:
    return dataset.load_laender_debt()


@pytest.fixture(scope="module")
def laender_budget() -> pd.DataFrame:
    return dataset.load_laender_budget()


@pytest.fixture(scope="module")
def laender_inflation() -> pd.DataFrame:
    return dataset.load_laender_inflation()


def test_debt_covers_major_european_countries(laender_debt: pd.DataFrame) -> None:
    laender = set(laender_debt["land"])
    for name in ("Deutschland", "Frankreich", "Italien", "Spanien"):
        assert name in laender
    assert laender_debt["jahr"].min() <= 1995
    assert laender_debt["jahr"].max() >= 2024


def test_german_debt_ratio_matches_eurostat(laender_debt: pd.DataFrame) -> None:
    deutschland = laender_debt[
        (laender_debt["land"] == "Deutschland") & (laender_debt["jahr"] == 2025)
    ]
    assert not deutschland.empty
    quote = float(deutschland["schuldenquote_pct"].iloc[0])
    assert 55 < quote < 70
    schulden = float(deutschland["schulden_mio_eur"].iloc[0])
    assert 2_500_000 < schulden < 3_200_000


def test_budget_has_interest_quotas(laender_budget: pd.DataFrame) -> None:
    deutschland = laender_budget[
        (laender_budget["land"] == "Deutschland") & (laender_budget["jahr"] == 2025)
    ]
    zeile = deutschland.iloc[0]
    assert 0.5 < float(zeile["zins_quote_bip_pct"]) < 2.5
    assert 300 < float(zeile["zins_je_einwohner_eur"]) < 900
    assert laender_budget["zinsausgaben_mio_eur"].notna().all()


def test_inflation_is_monthly_and_complete(laender_inflation: pd.DataFrame) -> None:
    assert laender_inflation["monat"].str.match(r"^\d{4}-\d{2}$").all()
    assert {"Deutschland", "Frankreich", "Italien"} <= set(laender_inflation["land"])
    assert laender_inflation["inflation_pct"].notna().all()


def test_theoretical_interest_by_country(laender_debt, laender_budget) -> None:
    yields = pd.DataFrame(
        {
            "monat": ["2026-10", "2026-10"],
            "land": ["Deutschland", "Italien"],
            "rendite_pct": [3.0, 4.0],
        }
    )
    ergebnis = analysis.theoretical_interest_by_country(laender_debt, laender_budget, yields)

    assert set(ergebnis["land"]) == {"Deutschland", "Italien"}
    deutschland = ergebnis[ergebnis["land"] == "Deutschland"].iloc[0]
    erwartet = float(deutschland["schulden_mio_eur"]) * 3.0 / 100
    assert deutschland["zins_theoretisch_mio_eur"] == pytest.approx(erwartet)

    bip = laender_budget[
        (laender_budget["land"] == "Deutschland")
        & (laender_budget["jahr"] == deutschland["jahr"])
    ]["bip_mio_eur"].iloc[0]
    assert deutschland["zins_quote_bip_pct"] == pytest.approx(float(erwartet) / float(bip) * 100)
    # Italien hat Schuldenquote und Rendite höher, also auch die höhere Zinsquote.
    assert ergebnis.iloc[0]["land"] == "Italien"


def test_real_interest_rate_subtracts_inflation(laender_inflation) -> None:
    yields = pd.DataFrame(
        {
            "monat": ["2025-12", "2025-12"],
            "land": ["Deutschland", "Italien"],
            "rendite_pct": [3.0, 4.0],
        }
    )
    inflation = laender_inflation[laender_inflation["monat"] == "2025-12"]

    ergebnis = analysis.real_interest_rate(yields, inflation)

    assert set(ergebnis["land"]) == {"Deutschland", "Italien"}
    for _, zeile in ergebnis.iterrows():
        assert zeile["realzins_pct"] == pytest.approx(zeile["rendite_pct"] - zeile["inflation_pct"])


def test_real_interest_rate_needs_matching_months(laender_inflation) -> None:
    yields = pd.DataFrame({"monat": ["1990-01"], "land": ["Deutschland"], "rendite_pct": [3.0]})

    assert analysis.real_interest_rate(yields, laender_inflation).empty


def test_country_sources_are_library_entries() -> None:
    keys = {entry["key"] for entry in sources.read_library()["quellen"]}
    for key in (
        "eurostat_schulden_laender",
        "eurostat_haushalt_laender",
        "eurostat_bip_laender",
        "eurostat_bevoelkerung_laender",
        "eurostat_inflation_laender",
    ):
        assert key in keys
