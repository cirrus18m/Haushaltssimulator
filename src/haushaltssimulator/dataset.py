"""Zugriff auf die aufbereiteten CSV-Dateien (reines pandas, ohne Streamlit)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .paths import PROCESSED_DIR

ANNUAL_DEBT = "schulden_jahresreihe.csv"
QUARTERLY_DEBT = "schulden_quartalsreihe.csv"
DESTATIS_ANNUAL = "schulden_destatis_jahr.csv"
DESTATIS_QUARTERLY = "schulden_destatis_quartal.csv"
DESTATIS_LAENDER = "schulden_destatis_bundeslaender.csv"
GDP_POPULATION = "bip_bevoelkerung.csv"
HOUSEHOLD = "haushalt_jahr.csv"
BUND_YIELD = "zins_bund_10j.csv"
INTERNATIONAL_YIELDS = "zins_vergleich.csv"
INTEREST_BURDEN = "zinslast_jahr.csv"
INSOLVENCIES = "insolvenzen_monat.csv"
MONEY_SUPPLY = "geldmenge_monat.csv"
PURCHASING_POWER = "kaufkraft_monat.csv"
HOUSEHOLD_ENERGY = "energiepreise_jahr.csv"
DAY_AHEAD = "strom_boerse_tag.csv"
FUEL_PRICES = "kraftstoffpreise.csv"
BIG_MAC = "big_mac.csv"
HOMEOWNERSHIP = "eigentumsquote.csv"
BUND_INTEREST = "bund_zinsausgaben.csv"
BUND_INTEREST_PLAN = "bund_zinsausgaben_plan.csv"
BUND_BUDGET_AREAS = "bund_ausgaben_aufgabenbereiche.csv"
LAENDER_DEBT = "laender_schulden_jahr.csv"
LAENDER_BUDGET = "laender_haushalt_jahr.csv"
LAENDER_INFLATION = "laender_inflation_monat.csv"
LAENDER_INCOME = "laender_einkommen_jahr.csv"
GDP_GERMANY = "bip_deutschland_jahr.csv"
GDP_GROWTH = "bip_wachstum_jahr.csv"
INVESTMENTS = "investitionen_jahr.csv"
PRODUCTION_GERMANY = "produktion_deutschland_monat.csv"
PRODUCTION_GERMANY_LONG = "produktion_deutschland_lang.csv"
PRODUCTION_COMPARISON = "produktion_vergleich_monat.csv"
ENERGY_MARKETS = "energie_maerkte_monat.csv"
KEY_RATES = "leitzinsen.csv"
INFLATION_GERMANY = "inflation_de_monat.csv"
CO2_PRICE = "co2_preis_jahr.csv"
CO2_SURCHARGE = "co2_aufschlag_jahr.csv"

# Beschreibung der aufbereiteten Tabellen für die Quellenseite.
DATASET_LABELS = {
    ANNUAL_DEBT: "Maastricht-Schuldenstand je Jahr und Ebene",
    QUARTERLY_DEBT: "Maastricht-Schuldenstand je Quartal und Ebene",
    DESTATIS_ANNUAL: "Schulden beim nicht-öffentlichen Bereich, jährlich",
    DESTATIS_QUARTERLY: "Schulden beim nicht-öffentlichen Bereich, vierteljährlich",
    DESTATIS_LAENDER: "Schulden der Bundesländer, vierteljährlich",
    GDP_POPULATION: "BIP, Bevölkerung und BIP je Einwohner:in",
    HOUSEHOLD: "Einnahmen, Ausgaben und Zinsausgaben des Staates",
    BUND_YIELD: "Tagesrendite der 10-jährigen Bundesanleihe",
    INTERNATIONAL_YIELDS: "Renditen 10-jähriger Staatsanleihen im Ländervergleich",
    INTEREST_BURDEN: "Theoretische Zinslast und Zinsquoten",
    INSOLVENCIES: "Insolvenzverfahren je Monat",
    MONEY_SUPPLY: "Geldmenge M3 und Wachstumsrate",
    PURCHASING_POWER: "Inflation und Kaufkraftindex",
    HOUSEHOLD_ENERGY: "Strom- und Gaspreise für Haushalte",
    DAY_AHEAD: "Börsenstrompreis (Day-Ahead), Tagesmittel",
    FUEL_PRICES: "Kraftstoffpreise im EU-Vergleich",
    BIG_MAC: "Big-Mac-Index je Land",
    HOMEOWNERSHIP: "Eigentums- und Mietquote in Europa",
    BUND_INTEREST: "Zinsausgaben des Bundes am Kreditmarkt",
    BUND_INTEREST_PLAN: "Geplante Zinsausgaben des Bundes (Finanzplan 2026 bis 2030)",
    BUND_BUDGET_AREAS: "Ausgaben des Bundes nach Aufgabenbereichen (2025 bis 2030)",
    LAENDER_DEBT: "Schuldenstand und Schuldenquote im Ländervergleich",
    LAENDER_BUDGET: "Einnahmen und Zinsausgaben im Ländervergleich",
    LAENDER_INFLATION: "Inflationsraten im Ländervergleich",
    LAENDER_INCOME: "Durchschnittseinkommen im Ländervergleich",
    GDP_GERMANY: "BIP, realer Index und Wachstum Deutschlands",
    GDP_GROWTH: "Reales BIP-Wachstum im Ländervergleich",
    INVESTMENTS: "Private und staatliche Investitionen",
    PRODUCTION_GERMANY: "Produktionsindex des Verarbeitenden Gewerbes",
    PRODUCTION_GERMANY_LONG: "Industrieproduktion im langfristigen Trend",
    PRODUCTION_COMPARISON: "Produktionsindex im Ländervergleich",
    ENERGY_MARKETS: "Heizöl, Gas und Brent-Rohöl im Monatsvergleich",
    KEY_RATES: "Leitzinsen von EZB und Fed",
    INFLATION_GERMANY: "Inflation in Deutschland: HVPI, Kerninflation und VPI",
    CO2_PRICE: "CO₂-Preis im nationalen Emissionshandel (BEHG)",
    CO2_SURCHARGE: "CO₂-Aufschlag je Liter bzw. kWh auf Heizöl, Kraftstoffe und Erdgas",
}

_DATE_COLUMNS = ("stichtag", "quartalsende", "datum")


def _read(filename: str, processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    path = processed_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} fehlt. Bitte zuerst `uv run scripts/build_data.py` ausführen."
        )
    frame = pd.read_csv(path, dtype={"jahr": "Int64"})
    for column in _DATE_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def load_annual_debt(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Maastricht-Schuldenstand je Jahr und Ebene (Eurostat, ab 1995)."""
    return _read(ANNUAL_DEBT, processed_dir)


def load_quarterly_debt(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Maastricht-Schuldenstand je Quartal und Ebene (Eurostat, ab 2000)."""
    return _read(QUARTERLY_DEBT, processed_dir)


def load_destatis_annual(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Jährliche Schulden beim nicht-öffentlichen Bereich (Destatis, ab 2010)."""
    return _read(DESTATIS_ANNUAL, processed_dir)


def load_destatis_quarterly(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Vierteljährliche Schulden beim nicht-öffentlichen Bereich (Destatis)."""
    return _read(DESTATIS_QUARTERLY, processed_dir)


def load_laender_quarterly(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Vierteljährliche Schulden der Bundesländer (Destatis)."""
    return _read(DESTATIS_LAENDER, processed_dir)


def load_gdp_population(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """BIP, Bevölkerung und BIP je Einwohner je Jahr (Eurostat)."""
    return _read(GDP_POPULATION, processed_dir)


def with_debt_per_capita(annual_debt: pd.DataFrame, gdp_population: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt den Schuldenstand des Gesamtstaats um Schulden je Einwohner."""
    frame = annual_debt.merge(gdp_population[["jahr", "bevoelkerung"]], on="jahr", how="left")
    frame["schulden_je_einwohner_eur"] = (
        frame["schulden_mio_eur"] * 1_000_000 / frame["bevoelkerung"]
    )
    return frame


def load_household(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Einnahmen, Ausgaben, Zinsausgaben und Finanzierungssaldo je Jahr und Ebene."""
    return _read(HOUSEHOLD, processed_dir)


def load_bund_yield(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Tagesrenditen der aktuellen 10-jährigen Bundesanleihe (Bundesbank)."""
    return _read(BUND_YIELD, processed_dir)


def load_international_yields(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatliche Renditen 10-jähriger Staatsanleihen je Land und Quelle."""
    return _read(INTERNATIONAL_YIELDS, processed_dir)


def load_interest_burden(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Schuldenstand, Rendite, theoretische und tatsächliche Zinslast je Jahr."""
    return _read(INTEREST_BURDEN, processed_dir)


def load_insolvencies(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatliche Insolvenzverfahren insgesamt und von Unternehmen."""
    return _read(INSOLVENCIES, processed_dir)


def load_money_supply(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Geldmenge M3 des Euro-Raums mit Jahreswachstumsrate."""
    return _read(MONEY_SUPPLY, processed_dir)


def load_purchasing_power(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Inflation in Deutschland und im Euro-Raum sowie Kaufkraftindex."""
    return _read(PURCHASING_POWER, processed_dir)


def load_energy_prices(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Strom- und Gaspreise für Haushalte je Jahr und Verbrauchsklasse."""
    return _read(HOUSEHOLD_ENERGY, processed_dir)


def load_day_ahead_prices(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Tagesmittel der Day-Ahead-Strompreise für Deutschland/Luxemburg."""
    return _read(DAY_AHEAD, processed_dir)


def load_fuel_prices(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatliche Kraftstoffpreise je Land und Produkt."""
    return _read(FUEL_PRICES, processed_dir)


def load_big_mac(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Big-Mac-Preis in US-Dollar und Abweichung vom US-Preis."""
    return _read(BIG_MAC, processed_dir)


def load_homeownership(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Eigentums- und Mietquote der Haushalte je Land und Jahr."""
    return _read(HOMEOWNERSHIP, processed_dir)


def load_laender_debt(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Maastricht-Schuldenstand und Schuldenquote je europäischem Land."""
    return _read(LAENDER_DEBT, processed_dir)


def load_laender_budget(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Einnahmen, Zinsausgaben und Quoten je europäischem Land."""
    return _read(LAENDER_BUDGET, processed_dir)


def load_laender_inflation(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatliche Inflationsrate je Land."""
    return _read(LAENDER_INFLATION, processed_dir)


def load_laender_income(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Durchschnittseinkommen je Land, Jahr und Abgrenzung."""
    return _read(LAENDER_INCOME, processed_dir)


def load_bund_interest(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Zinsausgaben des Bundes am Kreditmarkt je Haushaltsjahr."""
    return _read(BUND_INTEREST, processed_dir)


def load_bund_interest_plan(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Geplante Zinsausgaben des Bundes im Kernhaushalt je Haushaltsjahr."""
    return _read(BUND_INTEREST_PLAN, processed_dir)


def load_bund_budget_areas(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Ausgaben des Bundes nach Aufgabenbereichen im Kernhaushalt je Haushaltsjahr."""
    return _read(BUND_BUDGET_AREAS, processed_dir)


def load_gdp_germany(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """BIP, realer Kettenindex und Wachstumsraten Deutschlands je Jahr (Destatis)."""
    return _read(GDP_GERMANY, processed_dir)


def load_gdp_growth(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Reales BIP-Wachstum je Land und Jahr (Eurostat, USA und Russland: IWF)."""
    return _read(GDP_GROWTH, processed_dir)


def load_investments(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Bruttoanlageinvestitionen von Staat und nichtstaatlichen Sektoren (Destatis)."""
    return _read(INVESTMENTS, processed_dir)


def load_production_germany(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatlicher Produktionsindex des Verarbeitenden Gewerbes (Destatis)."""
    return _read(PRODUCTION_GERMANY, processed_dir)


def load_production_germany_long(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Industrieproduktion Deutschlands ab 1993 mit Langfristtrend (Eurostat)."""
    return _read(PRODUCTION_GERMANY_LONG, processed_dir)


def load_production_comparison(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatlicher Produktionsindex des Verarbeitenden Gewerbes je Land (Eurostat)."""
    return _read(PRODUCTION_COMPARISON, processed_dir)


def load_energy_markets(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Monatspreise für Heizöl, Gas und Brent-Rohöl, jeweils auch in ct/kWh."""
    return _read(ENERGY_MARKETS, processed_dir)


def load_key_rates(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    return _read(KEY_RATES, processed_dir)


def load_inflation_germany(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    return _read(INFLATION_GERMANY, processed_dir)


def load_co2_price(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    return _read(CO2_PRICE, processed_dir)


def load_co2_surcharge(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    return _read(CO2_SURCHARGE, processed_dir)
