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


def test_rate_changes_keeps_change_days_and_last_day() -> None:
    frame = pd.DataFrame(
        {
            "datum": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            ),
            "zins_pct": [5.5, 5.5, 5.25, 5.25, 5.25],
        }
    )
    result = analysis.rate_changes(frame)
    assert result["datum"].dt.day.tolist() == [1, 3, 5]
    assert result["zins_pct"].tolist() == [5.5, 5.25, 5.25]


def test_extend_steps_carries_last_value_per_group() -> None:
    frame = pd.DataFrame(
        {
            "datum": pd.to_datetime(["2024-01-01", "2024-06-01", "2024-03-01"]),
            "leitzins": ["A", "A", "B"],
            "zins_pct": [4.0, 3.5, 2.0],
        }
    )
    ende = pd.Timestamp("2024-12-31")
    result = analysis.extend_steps(frame, ende, "leitzins")
    letzte = result.sort_values("datum").groupby("leitzins").last()
    assert (letzte["datum"] == ende).all()
    assert letzte.loc["A", "zins_pct"] == 3.5
    assert letzte.loc["B", "zins_pct"] == 2.0
    assert len(result) == 5
    assert result["zins_pct"].dtype == float


EBEV_STANDARDWERTE = pd.DataFrame(
    {
        "brennstoff": ["Heizöl EL", "Benzin", "Erdgas"],
        "einheit": ["1000 l", "1000 l", "MWh"],
        "dichte_t_je_1000l": [0.845, 0.755, None],
        "heizwert_gj_je_t": [42.8, 43.5, 1.0],
        "umrechnung_gj_je_mwh": [None, None, 3.2508],
        "emissionsfaktor_t_co2_je_gj": [0.074, 0.0729, 0.0558],
    }
)


def test_co2_emissions_follow_ebev_standard_values() -> None:
    frame = analysis.co2_emissions_per_unit(EBEV_STANDARDWERTE).set_index("brennstoff")
    # 0,845 t/1000 l × 42,8 GJ/t × 0,074 t CO₂/GJ
    assert frame.loc["Heizöl EL", "kg_co2_je_einheit"] == pytest.approx(2.6763, abs=1e-4)
    assert frame.loc["Benzin", "kg_co2_je_einheit"] == pytest.approx(2.3942, abs=1e-4)
    assert frame.loc["Erdgas", "kg_co2_je_einheit"] == pytest.approx(0.1814, abs=1e-4)
    assert frame.loc["Erdgas", "einheit_verbrauch"] == "kWh"


def test_co2_surcharge_in_cent_with_corridor_and_vat() -> None:
    preise = pd.DataFrame(
        {
            "jahr": [2021, 2026],
            "preis_min_eur_t": [25, 55],
            "preis_max_eur_t": [25, 65],
            "art": ["Festpreis", "Preiskorridor"],
        }
    )
    frame = analysis.co2_surcharge(preise, EBEV_STANDARDWERTE)
    heizoel = frame[frame["brennstoff"] == "Heizöl EL"].set_index("jahr")
    # 25 €/t × 2,6763 kg/l = 6,69 ct/l netto, mit 19 % Umsatzsteuer 7,96 ct/l
    assert heizoel.loc[2021, "aufschlag_min_netto_ct"] == pytest.approx(6.691, abs=1e-3)
    assert heizoel.loc[2021, "aufschlag_min_brutto_ct"] == pytest.approx(7.962, abs=1e-3)
    assert heizoel.loc[2026, "aufschlag_max_brutto_ct"] == pytest.approx(20.701, abs=1e-3)
    korridor = heizoel.loc[2026]
    assert korridor["aufschlag_min_brutto_ct"] < korridor["aufschlag_max_brutto_ct"]


def test_co2_share_of_consumer_price_uses_yearly_means() -> None:
    preise = pd.DataFrame(
        {"jahr": [2021], "preis_min_eur_t": [25], "preis_max_eur_t": [25], "art": ["Festpreis"]}
    )
    faktoren = pd.concat(
        [EBEV_STANDARDWERTE, EBEV_STANDARDWERTE.iloc[[0]].assign(brennstoff="Diesel")]
    )
    aufschlag = analysis.co2_surcharge(preise, faktoren)
    heizoel = pd.DataFrame(
        {"monat": ["2021-01", "2021-02", "2022-01"], "heizoel_ct_l": [70, 90, 150]}
    )
    kraftstoffe = pd.DataFrame(
        {
            "monat": ["2021-01", "2021-01", "2021-01"],
            "land": ["Deutschland", "Deutschland", "Frankreich"],
            "produkt": ["Diesel", "Superbenzin (Euro 95)", "Diesel"],
            "preis_eur_l": [1.40, 1.60, 9.99],
        }
    )
    frame = analysis.co2_share_of_consumer_price(aufschlag, heizoel, kraftstoffe, 2021)
    frame = frame.set_index("brennstoff")
    assert frame.loc["Heizöl EL", "preis_ct_l"] == 80
    assert frame.loc["Diesel", "preis_ct_l"] == pytest.approx(140)
    assert frame.loc["Heizöl EL", "anteil_pct"] == pytest.approx(7.962 / 80 * 100, abs=0.01)


def test_interest_per_working_age_uses_latest_population() -> None:
    zinslast = pd.DataFrame({"land": ["A", "B"], "zins_theoretisch_mio_eur": [100_000, 50]})
    bevoelkerung = pd.DataFrame(
        {
            "land": ["A", "A", "B"],
            "jahr": [2024, 2025, 2025],
            "bevoelkerung_20_59": [50_000_000, 40_000_000, 1_000_000],
        }
    )
    frame = analysis.interest_per_working_age(zinslast, bevoelkerung).set_index("land")
    assert frame.loc["A", "bevoelkerung_jahr"] == 2025
    assert frame.loc["A", "zins_je_person_20_59_eur"] == pytest.approx(2500)
    assert frame.loc["B", "zins_je_person_20_59_eur"] == pytest.approx(50)
