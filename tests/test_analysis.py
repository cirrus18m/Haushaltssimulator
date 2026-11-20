"""Tests für die Analysefunktionen."""

from __future__ import annotations

import pandas as pd
import pytest

from haushaltssimulator import analysis


def test_cagr() -> None:
    assert analysis.cagr(100, 121, 2) == pytest.approx(10.0)
    assert analysis.cagr(100, 100, 5) == pytest.approx(0.0)
    assert pd.isna(analysis.cagr(0, 100, 5))
    assert pd.isna(analysis.cagr(100, 100, 0))


def test_year_over_year_uses_groups() -> None:
    frame = pd.DataFrame(
        {
            "sector": ["S13", "S13", "S13", "S1311", "S1311"],
            "jahr": [2020, 2021, 2022, 2020, 2021],
            "schulden_mio_eur": [100.0, 110.0, 121.0, 50.0, 40.0],
        }
    )
    result = analysis.year_over_year(frame, "schulden_mio_eur", "sector").set_index(
        ["sector", "jahr"]
    )
    assert pd.isna(result.loc[("S13", 2020), "veraenderung_mio_eur"])
    assert result.loc[("S13", 2021), "veraenderung_mio_eur"] == pytest.approx(10.0)
    assert result.loc[("S13", 2022), "veraenderung_pct"] == pytest.approx(10.0)
    assert result.loc[("S1311", 2021), "veraenderung_pct"] == pytest.approx(-20.0)


def test_with_interest_burden_links_debt_and_yield() -> None:
    frame = pd.DataFrame(
        {
            "schulden_mio_eur": [2_000_000.0],
            "rendite_pct": [2.5],
            "einnahmen_mio_eur": [1_000_000.0],
            "bip_mio_eur": [4_000_000.0],
        }
    )
    result = analysis.with_interest_burden(frame)
    assert result.loc[0, "zins_theoretisch_mio_eur"] == pytest.approx(50_000.0)
    assert result.loc[0, "zins_quote_einnahmen_pct"] == pytest.approx(5.0)
    assert result.loc[0, "zins_quote_bip_pct"] == pytest.approx(1.25)


def test_monthly_interest_burden_interpolates_and_extrapolates_debt() -> None:
    debt = pd.DataFrame({"jahr": [2020, 2021], "schulden_mio_eur": [1_000_000.0, 1_200_000.0]})
    yields = pd.DataFrame({"monat": ["2021-06", "2022-03"], "rendite_pct": [2.0, 3.0]})

    result = analysis.monthly_interest_burden(debt, yields).set_index("monat")

    # Zwischen dem 31.12.2020 und dem 31.12.2021 liegt der 01.06.2021 bei 152 von 365 Tagen.
    erwartet = 1_000_000.0 + 200_000.0 * 152 / 365
    assert result.loc["2021-06", "schulden_mio_eur"] == pytest.approx(erwartet)
    assert result.loc["2021-06", "zins_theoretisch_mio_eur"] == pytest.approx(erwartet * 0.02)
    # Nach dem letzten Jahresende wird der Bestand mit dem Trend der letzten beiden
    # Jahresenden fortgeschrieben: 1.3.2022 liegt 60 Tage nach dem 31.12.2021.
    assert result.loc["2022-03", "schulden_mio_eur"] == pytest.approx(
        1_200_000.0 + 200_000.0 * 60 / 365
    )


def test_monthly_interest_burden_keeps_value_without_second_stichtag() -> None:
    debt = pd.DataFrame({"jahr": [2021], "schulden_mio_eur": [1_000_000.0]})
    yields = pd.DataFrame({"monat": ["2021-06", "2022-03"], "rendite_pct": [2.0, 3.0]})

    result = analysis.monthly_interest_burden(debt, yields).set_index("monat")

    # Ohne zwei Stichtage gibt es keinen Trend; der Bestand bleibt stehen.
    assert result.loc["2022-03", "schulden_mio_eur"] == pytest.approx(1_000_000.0)


def test_monthly_interest_burden_uses_monthly_mean_yield() -> None:
    debt = pd.DataFrame({"jahr": [2021], "schulden_mio_eur": [1_000_000.0]})
    yields = pd.DataFrame(
        {"monat": ["2021-03", "2021-03", "2021-04"], "rendite_pct": [1.0, 3.0, 2.0]}
    )

    result = analysis.monthly_interest_burden(debt, yields).set_index("monat")

    assert list(result.index) == ["2021-03", "2021-04"]
    assert result.loc["2021-03", "rendite_pct"] == pytest.approx(2.0)
    assert result.loc["2021-03", "zins_theoretisch_mio_eur"] == pytest.approx(20_000.0)


def test_simulate_debt_ratio_constant_growth() -> None:
    projection = analysis.simulate_debt_ratio(
        schulden_mio_eur=1000,
        bip_mio_eur=2000,
        schuldenwachstum_pct=0,
        bip_wachstum_pct=0,
        jahre=2,
        startjahr=2025,
    )
    assert projection["jahr"].tolist() == [2025, 2026, 2027]
    assert projection["schuldenquote_pct"].tolist() == pytest.approx([50.0, 50.0, 50.0])


def test_simulate_debt_ratio_growing_debt_reduces_ratio() -> None:
    projection = analysis.simulate_debt_ratio(
        schulden_mio_eur=1000,
        bip_mio_eur=2000,
        schuldenwachstum_pct=0,
        bip_wachstum_pct=10,
        jahre=1,
        startjahr=2025,
    )
    assert projection.loc[1, "schuldenquote_pct"] == pytest.approx(1000 / 2200 * 100)


def test_linear_trend_extrapolates_fit_period() -> None:
    frame = pd.DataFrame(
        {
            "monat": pd.date_range("2000-01-01", periods=25, freq="MS").strftime("%Y-%m"),
            "wert": [10 + 0.5 * index for index in range(25)],
        }
    )
    trend = analysis.linear_trend(frame, "wert", fit_end="2001-12")
    assert trend.iloc[0] == pytest.approx(10.0, abs=0.05)
    assert trend.iloc[-1] == pytest.approx(22.0, abs=0.05)
    assert trend.is_monotonic_increasing


def test_budget_shares_normalise_per_year() -> None:
    frame = pd.DataFrame(
        {
            "jahr": [2025, 2025, 2025, 2026, 2026],
            "aufgabenbereich": ["A", "B", "C", "A", "B"],
            "ausgaben_mrd_eur": [50.0, 30.0, 20.0, 60.0, 40.0],
        }
    )

    anteile = analysis.budget_shares(frame)

    assert anteile.groupby("jahr")["anteil_pct"].sum().round(6).tolist() == [100.0, 100.0]
    assert anteile.loc[0, "anteil_pct"] == pytest.approx(50.0)


def test_budget_shares_skip_missing_values() -> None:
    frame = pd.DataFrame(
        {
            "jahr": [2025, 2025],
            "aufgabenbereich": ["A", "B"],
            "ausgaben_mrd_eur": [80.0, float("nan")],
        }
    )

    anteile = analysis.budget_shares(frame)

    assert anteile.loc[0, "anteil_pct"] == pytest.approx(100.0)
    assert pd.isna(anteile.loc[1, "anteil_pct"])


def test_largest_areas_groups_small_budgets_per_year() -> None:
    frame = pd.DataFrame(
        {
            "jahr": [2025, 2025, 2025, 2026, 2026, 2026],
            "aufgabenbereich": ["Groß", "Mittel", "Klein", "Groß", "Mittel", "Klein"],
            "ausgaben_mrd_eur": [60.0, 20.0, 20.0, 70.0, 20.0, 10.0],
            "anteil_pct": [60.0, 20.0, 20.0, 70.0, 20.0, 10.0],
        }
    )

    gruppen = analysis.largest_areas(frame, threshold_pct=25.0)

    assert set(gruppen["aufgabenbereich"]) == {"Groß", "Übrige Aufgabenbereiche"}
    rest = gruppen[gruppen["aufgabenbereich"] == "Übrige Aufgabenbereiche"].set_index("jahr")
    assert rest.loc[2025, "anteil_pct"] == pytest.approx(40.0)
    assert rest.loc[2026, "ausgaben_mrd_eur"] == pytest.approx(30.0)


def test_share_change_reports_percentage_points() -> None:
    frame = pd.DataFrame(
        {
            "jahr": [2025, 2025, 2030, 2030],
            "aufgabenbereich": ["A", "B", "A", "B"],
            "ausgaben_mrd_eur": [50.0, 50.0, 30.0, 70.0],
            "anteil_pct": [50.0, 50.0, 30.0, 70.0],
        }
    )

    wechsel = analysis.share_change(frame, start_year=2025, end_year=2030).set_index(
        "aufgabenbereich"
    )

    assert wechsel.loc["A", "anteil_veraenderung_pp"] == pytest.approx(-20.0)
    assert wechsel.loc["B", "anteil_veraenderung_pp"] == pytest.approx(20.0)
    assert wechsel.loc["B", "ausgaben_2030_mrd_eur"] == pytest.approx(70.0)
    assert wechsel.index[0] == "B", "größter Anteil im Endjahr steht oben"
