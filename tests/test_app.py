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


def test_insolvencies_cover_total_and_companies() -> None:
    frame = dataset.load_insolvencies()
    assert {"verfahren_gesamt", "verfahren_unternehmen"} <= set(frame.columns)
    assert frame["monat"].is_monotonic_increasing
    assert frame["monat"].min() <= "2003-01"
    assert frame["verfahren_unternehmen"].notna().sum() >= 250
    assert frame["verfahren_unternehmen"].max() > 0


def test_energy_prices_cover_electricity_and_gas() -> None:
    frame = dataset.load_energy_prices()
    gesamt = frame[frame["verbrauchsklasse"] == "Insgesamt"]
    assert gesamt["strompreis_eur_kwh"].between(0.1, 1.0).all()
    assert gesamt["gaspreis_eur_kwh"].between(0.01, 0.5).all()


def test_fuel_prices_have_european_countries() -> None:
    frame = dataset.load_fuel_prices()
    assert frame["land"].nunique() >= 20
    assert frame["preis_eur_l"].between(0.5, 3.5).all()


def test_big_mac_and_homeownership_cover_germany() -> None:
    big_mac = dataset.load_big_mac()
    assert "Euro-Raum" in set(big_mac["land"])
    eigentum = dataset.load_homeownership()
    assert eigentum["eigentumsquote_pct"].between(0, 100).all()


def test_bund_interest_has_plan_values() -> None:
    frame = dataset.load_bund_interest()
    assert {"Ist", "Soll"} & set(frame["art"])
    assert (frame["zinsausgaben_mrd_eur"] > 0).all()


def test_international_yields_cover_germany_usa_and_russia() -> None:
    frame = dataset.load_international_yields()
    assert {"Deutschland", "Vereinigte Staaten", "Russland"} <= set(frame["land"])
    assert frame["monat"].max() >= "2026-01"
    assert frame["rendite_pct"].between(-5, 100).all()


def test_gdp_growth_covers_germany_usa_and_russia() -> None:
    frame = dataset.load_gdp_growth().dropna(subset=["wachstum_pct"])
    assert {"Deutschland", "Vereinigte Staaten", "Russland"} <= set(frame["land"])
    assert frame["jahr"].min() <= 1995
    assert frame["jahr"].max() >= 2024
    assert frame["wachstum_pct"].between(-30, 30).all()
    # IWF-Prognosejahre sind nicht enthalten.
    assert frame["jahr"].max() <= 2025


def test_gdp_germany_has_nominal_level_and_real_growth() -> None:
    frame = dataset.load_gdp_germany()
    assert {"bip_nominal_mrd_eur", "bip_real_index", "bip_wachstum_real_pct"} <= set(
        frame.columns
    )
    assert frame["bip_nominal_mrd_eur"].between(1000, 6000).all()
    assert frame["bip_real_index"].between(50, 150).all()


def test_production_index_covers_manufacturing() -> None:
    frame = dataset.load_production_germany()
    assert {"index_2021_original", "index_2021_saisonbereinigt"} <= set(frame.columns)
    assert frame["index_2021_saisonbereinigt"].dropna().between(40, 160).all()
    vergleich = dataset.load_production_comparison()
    assert {"Deutschland", "Italien"} <= set(vergleich["land"])
    assert vergleich["index_2021"].between(5, 500).all()


def test_investments_split_state_and_private() -> None:
    frame = dataset.load_investments()
    assert set(frame["sektor"]) == {"Staat", "Nichtstaatliche Sektoren"}
    assert (frame["investitionen_mrd_eur"] > 0).all()
    assert frame["anteil_bip_pct"].between(0, 30).all()


def test_long_production_index_has_trend_and_gap() -> None:
    frame = dataset.load_production_germany_long()
    assert frame["monat"].min() <= "1993-01"
    assert frame["monat"].max() >= "2026-02"
    assert frame.loc[frame["jahr"] == 2015, "index_2015"].mean() == pytest.approx(
        100, abs=0.1
    )
    latest = frame[frame["monat"] == "2026-02"].iloc[0]
    assert 80 < latest["index_2015"] < 95
    assert latest["trend_2015"] > latest["index_2015"]
    assert -30 < latest["abweichung_pct"] < -20


def test_energy_markets_cover_heizoel_gas_and_brent() -> None:
    frame = dataset.load_energy_markets()
    assert {
        "heizoel_ct_l",
        "gas_ct_kwh",
        "gas_ttf_eur_mwh",
        "gas_jkm_eur_mwh",
        "gas_henry_hub_eur_mwh",
        "brent_eur_barrel",
        "wti_eur_barrel",
        "dubai_eur_barrel",
    } <= set(frame.columns)
    assert frame["monat"].is_monotonic_increasing
    assert frame["heizoel_ct_l"].dropna().between(20, 400).all()
    assert frame["gas_ct_kwh"].dropna().between(0.1, 100).all()
    assert frame["gas_ttf_eur_mwh"].dropna().between(1, 400).all()
    assert frame["gas_jkm_eur_mwh"].dropna().between(1, 400).all()
    assert frame["gas_henry_hub_eur_mwh"].dropna().between(0.1, 100).all()
    assert frame["brent_eur_barrel"].dropna().between(5, 500).all()
    assert frame["wti_eur_barrel"].dropna().between(5, 500).all()
    assert frame["dubai_eur_barrel"].dropna().between(5, 500).all()


def test_app_does_not_import_api_clients() -> None:
    """Die Streamlit-App liest nur aufbereitete Daten und macht keine API-Aufrufe."""
    for path in (paths.PROJECT_ROOT / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "destatis_api" not in text, path
        assert "urllib.request" not in text, path


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
        "pages/9_Insolvenzen.py",
        "pages/10_Geld_und_Kaufkraft.py",
        "pages/11_Energiepreise.py",
        "pages/12_Preisniveau_und_Wohnen.py",
        "pages/13_Bund_und_Schuldendienst.py",
        "pages/14_Wirtschaft.py",
    ],
)
def test_streamlit_pages_run_without_exception(script: str) -> None:
    from streamlit.testing.v1 import AppTest

    # Großzügiges Timeout: Die Seiten rendern Diagramme nach SVG und sind unter Last langsam.
    test = AppTest.from_file(str(Path(APP_DIR) / script), default_timeout=180)
    test.run()
    assert not test.exception, [str(exception.value) for exception in test.exception]


def test_bund_yield_chart_can_hide_inflation_axis() -> None:
    from streamlit.testing.v1 import AppTest

    test = AppTest.from_file(
        str(Path(APP_DIR) / "pages/6_Haushalt_und_Zinsen.py"), default_timeout=180
    )
    test.run()
    assert test.toggle, "Inflations-Schalter fehlt"
    test.toggle[0].set_value(False).run()
    assert not test.exception, [str(exception.value) for exception in test.exception]
