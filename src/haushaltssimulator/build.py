"""Erzeugt aus den Rohdaten die aufbereiteten CSV-Dateien für die App."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from . import (
    analysis,
    bigmac,
    bmf,
    bundesbank,
    destatis,
    ecb,
    eurostat,
    fred,
    laender,
    oil,
    paths,
    sources,
)

SECTOR_LABELS = {
    "S13": "Staat insgesamt",
    "S1311": "Bund (Zentralstaat)",
    "S1312": "Länder (Staatsebene)",
    "S1313": "Gemeinden (lokale Ebene)",
    "S1314": "Sozialversicherung",
}
EBENE_ORDER = list(SECTOR_LABELS.values())

LEVEL_ORDER = ["Bund", "Länder", "Gemeinden / Gemeindeverbände", "Sozialversicherung", "Insgesamt"]
LAENDER_LEVEL_ORDER = ["Länder", "Gemeinden / Gemeindeverbände", "Insgesamt"]
HAUSHALT_ORDER = ["Kernhaushalt", "Extrahaushalte", "Insgesamt"]
SCHULDENART_ORDER = [
    "Wertpapierschulden",
    "Kredite beim nicht-öffentlichen Bereich",
    "Kassenkredite beim nicht-öffentlichen Bereich",
    "Insgesamt",
]

DESTATIS_COLUMNS = ["stichtag", "ebene", "haushalt", "schuldenart", "schulden_mio_eur"]

MONATSNAMEN = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}

HOUSEHOLD_ITEMS = {
    "TR": "einnahmen_mio_eur",
    "TE": "ausgaben_mio_eur",
    "D41PAY": "zinsausgaben_mio_eur",
    "B9": "finanzierungssaldo_mio_eur",
}


def _load_json(raw_dir: Path, filename: str) -> dict:
    return json.loads((raw_dir / filename).read_text(encoding="utf-8"))


def _trim_eurostat(frame: pd.DataFrame) -> pd.DataFrame:
    """Behält nur die Sektoren, die die App nutzt, und ergänzt deutsche Bezeichnungen."""
    trimmed = frame[frame["sector"].isin(SECTOR_LABELS)].copy()
    trimmed["ebene"] = trimmed["sector"].map(SECTOR_LABELS)
    return trimmed


def _unit_wide(frame: pd.DataFrame, index: list[str]) -> pd.DataFrame:
    """Klappt die Eurostat-Einheiten in eigene Spalten um."""
    wide = frame.pivot_table(index=index, columns="unit", values="value", aggfunc="first")
    wide = wide.reset_index()
    for column in ("MIO_EUR", "PC_GDP"):
        if column not in wide.columns:
            raise ValueError(f"Einheit {column} fehlt in der Datenquelle")
    return wide[[*index, "MIO_EUR", "PC_GDP"]].rename(
        columns={"MIO_EUR": "schulden_mio_eur", "PC_GDP": "schuldenquote_pct"}
    )


def _parse_destatis(raw_dir: Path, filename: str, label_columns: list[str]) -> pd.DataFrame:
    raw = destatis.decode((raw_dir / filename).read_bytes())
    frame = destatis.parse_table(raw, label_columns)
    units = set(frame["einheit"].dropna())
    if units != {"Mill. EUR"}:
        raise ValueError(f"Unerwartete Einheit in {filename}: {units}")

    frame = frame.rename(columns={"wert": "schulden_mio_eur"}).drop(columns=["einheit"])
    frame["stichtag"] = pd.to_datetime(frame["stichtag"])
    # Destatis liefert ganzzahlige Millionenbeträge.
    frame["schulden_mio_eur"] = frame["schulden_mio_eur"].round().astype("Int64")
    return frame


def build_annual_debt(raw_dir: Path) -> pd.DataFrame:
    """Jährlicher Maastricht-Schuldenstand je staatlicher Ebene (Eurostat)."""
    document = _load_json(raw_dir, "eurostat_gov_10dd_edpt1.json")
    frame = _trim_eurostat(eurostat.jsonstat_to_frame(document))
    wide = _unit_wide(frame, ["time", "sector", "ebene"])

    wide["jahr"] = wide["time"].astype(int)
    wide = wide.drop(columns=["time"])

    gdp = build_gdp_population(raw_dir)[["jahr", "bip_mio_eur"]]
    wide = wide.merge(gdp, on="jahr", how="left")
    wide["ebene"] = pd.Categorical(wide["ebene"], EBENE_ORDER, ordered=True)
    columns = ["jahr", "sector", "ebene", "schulden_mio_eur", "schuldenquote_pct", "bip_mio_eur"]
    return wide[columns].sort_values(["jahr", "ebene"]).reset_index(drop=True)


def build_quarterly_debt(raw_dir: Path) -> pd.DataFrame:
    """Vierteljährlicher Maastricht-Schuldenstand je staatlicher Ebene (Eurostat)."""
    document = _load_json(raw_dir, "eurostat_gov_10q_ggdebt.json")
    frame = _trim_eurostat(eurostat.jsonstat_to_frame(document))
    wide = _unit_wide(frame, ["time", "sector", "ebene"])

    wide["quartal"] = wide["time"]
    wide["quartalsende"] = (
        pd.PeriodIndex(wide["quartal"], freq="Q").to_timestamp(how="end").normalize()
    )
    wide["jahr"] = wide["quartalsende"].dt.year
    wide["ebene"] = pd.Categorical(wide["ebene"], EBENE_ORDER, ordered=True)
    columns = [
        "quartal",
        "quartalsende",
        "jahr",
        "sector",
        "ebene",
        "schulden_mio_eur",
        "schuldenquote_pct",
    ]
    return wide[columns].sort_values(["quartalsende", "ebene"]).reset_index(drop=True)


def build_annual_debt_destatis(raw_dir: Path) -> pd.DataFrame:
    """Jährliche Schulden beim nicht-öffentlichen Bereich (Destatis, ab 2010)."""
    frame = _parse_destatis(
        raw_dir, "destatis_71321-0005_jahr.csv", ["ebene", "haushalt", "schuldenart"]
    )
    frame["jahr"] = frame["stichtag"].dt.year
    frame["ebene"] = pd.Categorical(frame["ebene"], LEVEL_ORDER, ordered=True)
    frame["haushalt"] = pd.Categorical(frame["haushalt"], HAUSHALT_ORDER, ordered=True)
    frame["schuldenart"] = pd.Categorical(frame["schuldenart"], SCHULDENART_ORDER, ordered=True)
    frame = frame.dropna(subset=["ebene", "haushalt", "schuldenart"])
    return (
        frame[["jahr", *DESTATIS_COLUMNS]]
        .sort_values(["jahr", "ebene", "haushalt", "schuldenart"])
        .reset_index(drop=True)
    )


def build_quarterly_debt_destatis(raw_dir: Path) -> pd.DataFrame:
    """Vierteljährliche Schulden beim nicht-öffentlichen Bereich (Destatis)."""
    frame = _parse_destatis(
        raw_dir, "destatis_71311-0001_quartal.csv", ["ebene", "haushalt", "schuldenart"]
    )
    frame["ebene"] = pd.Categorical(frame["ebene"], LEVEL_ORDER, ordered=True)
    frame["haushalt"] = pd.Categorical(frame["haushalt"], HAUSHALT_ORDER, ordered=True)
    frame["schuldenart"] = pd.Categorical(frame["schuldenart"], SCHULDENART_ORDER, ordered=True)
    frame = frame.dropna(subset=["ebene", "haushalt", "schuldenart"])
    return (
        frame[DESTATIS_COLUMNS]
        .sort_values(["stichtag", "ebene", "haushalt", "schuldenart"])
        .reset_index(drop=True)
    )


def build_quarterly_debt_laender(raw_dir: Path) -> pd.DataFrame:
    """Vierteljährliche Schulden der Bundesländer (Destatis)."""
    frame = _parse_destatis(
        raw_dir,
        "destatis_71311-0003_bundeslaender.csv",
        ["bundesland", "ebene", "haushalt", "schuldenart"],
    )
    frame["ebene"] = pd.Categorical(frame["ebene"], LAENDER_LEVEL_ORDER, ordered=True)
    frame["haushalt"] = pd.Categorical(frame["haushalt"], HAUSHALT_ORDER, ordered=True)
    frame["schuldenart"] = pd.Categorical(frame["schuldenart"], SCHULDENART_ORDER, ordered=True)
    frame = frame.dropna(subset=["bundesland", "ebene", "haushalt", "schuldenart"])
    columns = ["stichtag", "bundesland", "ebene", "haushalt", "schuldenart", "schulden_mio_eur"]
    return (
        frame[columns]
        .sort_values(["stichtag", "bundesland", "ebene", "haushalt", "schuldenart"])
        .reset_index(drop=True)
    )


def build_gdp_population(raw_dir: Path) -> pd.DataFrame:
    """BIP und Bevölkerung je Jahr (Eurostat) inklusive BIP je Einwohner."""
    gdp = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_nama_10_gdp.json"))
    gdp = gdp[(gdp["na_item"] == "B1GQ") & (gdp["unit"] == "CP_MEUR")]
    gdp = gdp.rename(columns={"time": "jahr", "value": "bip_mio_eur"})[["jahr", "bip_mio_eur"]]

    population = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_demo_pjan.json"))
    population = population.rename(columns={"time": "jahr", "value": "bevoelkerung"})[
        ["jahr", "bevoelkerung"]
    ]

    frame = gdp.merge(population, on="jahr", how="outer")
    frame["jahr"] = frame["jahr"].astype(int)
    frame = frame.sort_values("jahr").reset_index(drop=True)
    frame["bip_je_einwohner_eur"] = frame["bip_mio_eur"] * 1_000_000 / frame["bevoelkerung"]
    return frame


def build_household(raw_dir: Path) -> pd.DataFrame:
    """Einnahmen, Ausgaben und Zinsausgaben des Staates je Jahr und Ebene (Eurostat)."""
    frame = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_gov_10a_main.json"))
    frame = frame[frame["sector"].isin(SECTOR_LABELS) & frame["na_item"].isin(HOUSEHOLD_ITEMS)]
    wide = frame.pivot_table(
        index=["time", "sector"], columns="na_item", values="value", aggfunc="first"
    ).reset_index()
    wide = wide.rename(columns={"time": "jahr", **HOUSEHOLD_ITEMS})

    missing = set(HOUSEHOLD_ITEMS.values()) - set(wide.columns)
    if missing:
        raise ValueError(f"Merkmale fehlen in gov_10a_main: {sorted(missing)}")

    wide["jahr"] = wide["jahr"].astype(int)
    wide["ebene"] = wide["sector"].map(SECTOR_LABELS)
    wide = wide.merge(build_gdp_population(raw_dir)[["jahr", "bip_mio_eur"]], on="jahr", how="left")
    wide["einnahmenquote_pct"] = wide["einnahmen_mio_eur"] / wide["bip_mio_eur"] * 100
    wide["ausgabenquote_pct"] = wide["ausgaben_mio_eur"] / wide["bip_mio_eur"] * 100
    wide["zins_einnahmen_pct"] = wide["zinsausgaben_mio_eur"] / wide["einnahmen_mio_eur"] * 100
    wide["ebene"] = pd.Categorical(wide["ebene"], EBENE_ORDER, ordered=True)
    columns = [
        "jahr",
        "sector",
        "ebene",
        "einnahmen_mio_eur",
        "ausgaben_mio_eur",
        "zinsausgaben_mio_eur",
        "finanzierungssaldo_mio_eur",
        "bip_mio_eur",
        "einnahmenquote_pct",
        "ausgabenquote_pct",
        "zins_einnahmen_pct",
    ]
    return wide[columns].sort_values(["jahr", "ebene"]).reset_index(drop=True)


def build_bund_yield(raw_dir: Path) -> pd.DataFrame:
    """Tagesrendite der 10-jährigen Bundesanleihe (Deutsche Bundesbank)."""
    frame = bundesbank.parse_yield_csv((raw_dir / "bundesbank_10j_rendite.csv").read_bytes())
    frame["jahr"] = frame["datum"].dt.year
    frame["monat"] = frame["datum"].dt.strftime("%Y-%m")
    return frame[["datum", "jahr", "monat", "rendite_pct"]]


def build_international_yields(raw_dir: Path) -> pd.DataFrame:
    """Monatliche Renditen 10-jähriger Staatsanleihen je Land und Quelle."""
    frames = []

    euro = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_irt_lt_mcby_m.json"))
    euro = euro[euro["geo"].isin(laender.LAND_NAMEN)][["time", "geo", "value"]]
    euro = euro.rename(columns={"time": "monat", "value": "rendite_pct"})
    euro["land"] = euro["geo"].map(laender.LAND_NAMEN)
    euro["quelle"] = "Eurostat irt_lt_mcby_m"
    euro["quelle_key"] = "eurostat_zinsvergleich"
    frames.append(euro[["monat", "land", "rendite_pct", "quelle", "quelle_key"]])

    usa = fred.parse_series_csv((raw_dir / "fred_us_10j_rendite.csv").read_bytes())
    usa["monat"] = usa["datum"].dt.strftime("%Y-%m")
    usa["land"] = laender.LAND_NAMEN["US"]
    usa["quelle"] = "FRED IRLTLT01USM156N"
    usa["quelle_key"] = "fred_us_zins"
    frames.append(
        usa.rename(columns={"wert": "rendite_pct"})[
            ["monat", "land", "rendite_pct", "quelle", "quelle_key"]
        ]
    )

    russland = pd.read_csv(raw_dir / "cbr_ru_10j_rendite.csv", parse_dates=["datum"])
    russland["monat"] = russland["datum"].dt.strftime("%Y-%m")
    russland["land"] = laender.LAND_NAMEN["RU"]
    russland["quelle"] = "Bank of Russia (OFZ-Zinskurve)"
    russland["quelle_key"] = "cbr_ru_zins"
    frames.append(russland[["monat", "land", "rendite_pct", "quelle", "quelle_key"]])

    frame = pd.concat(frames, ignore_index=True).dropna(subset=["rendite_pct"])
    return frame.sort_values(["monat", "land"]).reset_index(drop=True)


def build_interest_burden(raw_dir: Path) -> pd.DataFrame:
    """Schuldenstand, Rendite und daraus abgeleitete Zinslast je Jahr."""
    debt = build_annual_debt(raw_dir)
    debt = debt[debt["sector"] == "S13"][["jahr", "schulden_mio_eur", "bip_mio_eur"]]

    household = build_household(raw_dir)
    household = household[household["sector"] == "S13"][
        ["jahr", "einnahmen_mio_eur", "zinsausgaben_mio_eur"]
    ]

    yields = build_bund_yield(raw_dir).groupby("jahr", as_index=False)["rendite_pct"].mean()

    frame = debt.merge(household, on="jahr", how="inner").merge(yields, on="jahr", how="left")
    frame = analysis.with_interest_burden(frame)
    frame["effektivzins_pct"] = frame["zinsausgaben_mio_eur"] / frame["schulden_mio_eur"] * 100
    columns = [
        "jahr",
        "schulden_mio_eur",
        "rendite_pct",
        "zins_theoretisch_mio_eur",
        "einnahmen_mio_eur",
        "zins_quote_einnahmen_pct",
        "bip_mio_eur",
        "zins_quote_bip_pct",
        "zinsausgaben_mio_eur",
        "effektivzins_pct",
    ]
    return frame[columns].sort_values("jahr").reset_index(drop=True)


def build_insolvencies(raw_dir: Path) -> pd.DataFrame:
    """Monatliche Insolvenzverfahren insgesamt und von Unternehmen (Destatis)."""
    lang = destatis.parse_flagged_columns(
        destatis.decode(
            (raw_dir / "stat_bundesamt_insolvenzen_52411-0017_de_Nov2026.csv").read_bytes()
        ),
        ["jahr", "monat_name", "groessenklasse"],
        ["eroeffnet", "abgewiesen", "schuldenbereinigungsplan", "verfahren"],
    )
    lang = lang[lang["groessenklasse"] == "Insgesamt"].drop(columns=["groessenklasse"])
    lang = lang.rename(
        columns={
            "eroeffnet": "eroeffnet_unternehmen",
            "abgewiesen": "abgewiesen_unternehmen",
            "schuldenbereinigungsplan": "schuldenbereinigungsplan_unternehmen",
            "verfahren": "verfahren_unternehmen",
        }
    )

    total = destatis.parse_fixed_columns(
        destatis.decode((raw_dir / "destatis_52411-0002_insolvenzen.csv").read_bytes()),
        ["jahr", "monat_name", "status"],
        ["verfahren_gesamt", "forderungen_gesamt_tsd_eur"],
    )
    total = total[total["status"] == "Insgesamt"].drop(columns=["status"])

    unternehmen = destatis.parse_fixed_columns(
        destatis.decode((raw_dir / "destatis_52411-0011_insolvenzen_unternehmen.csv").read_bytes()),
        ["jahr", "monat_name", "rechtsform"],
        [
            "verfahren_unternehmen",
            "forderungen_unternehmen_tsd_eur",
            "betroffene_arbeitnehmer",
        ],
    )
    unternehmen = unternehmen[unternehmen["rechtsform"] == "Insgesamt"].drop(
        columns=["rechtsform", "verfahren_unternehmen"]
    )

    frame = lang.merge(total, on=["jahr", "monat_name"], how="outer")
    frame = frame.merge(unternehmen, on=["jahr", "monat_name"], how="outer")
    frame["monat_nummer"] = frame["monat_name"].map(MONATSNAMEN)
    frame = frame.dropna(subset=["monat_nummer"]).copy()
    frame["jahr"] = frame["jahr"].astype(int)
    frame["monat_nummer"] = frame["monat_nummer"].astype(int)
    frame["monat"] = (
        frame["jahr"].astype(str) + "-" + frame["monat_nummer"].map(lambda monat: f"{monat:02d}")
    )
    frame = frame.dropna(subset=["verfahren_gesamt", "verfahren_unternehmen"], how="all")
    frame["forderungen_gesamt_mio_eur"] = frame["forderungen_gesamt_tsd_eur"] / 1000
    frame["forderungen_unternehmen_mio_eur"] = frame["forderungen_unternehmen_tsd_eur"] / 1000
    columns = [
        "monat",
        "jahr",
        "verfahren_gesamt",
        "verfahren_unternehmen",
        "eroeffnet_unternehmen",
        "abgewiesen_unternehmen",
        "schuldenbereinigungsplan_unternehmen",
        "forderungen_gesamt_mio_eur",
        "forderungen_unternehmen_mio_eur",
        "betroffene_arbeitnehmer",
    ]
    return frame[columns].sort_values("monat").reset_index(drop=True)


def build_money_supply(raw_dir: Path) -> pd.DataFrame:
    """Geldmenge M3 des Euro-Raums mit Jahreswachstumsrate (EZB)."""
    frame = ecb.parse_csv((raw_dir / "ecb_geldmenge_m3.csv").read_bytes())
    frame = frame[["monat", "wert"]].rename(columns={"wert": "index_m3"}).sort_values("monat")
    frame["wachstum_pct"] = frame["index_m3"].pct_change(periods=12) * 100
    return frame[["monat", "index_m3", "wachstum_pct"]].reset_index(drop=True)


def build_purchasing_power(raw_dir: Path) -> pd.DataFrame:
    """Inflation und kumulierter Kaufkraftverlust (EZB-HVPI)."""
    frame = ecb.parse_csv((raw_dir / "ecb_hicp_de_ea.csv").read_bytes())
    wide = frame.pivot_table(
        index="monat", columns="gebiet", values="wert", aggfunc="first"
    ).reset_index()
    missing = {"DE", "U2"} - set(wide.columns)
    if missing:
        raise ValueError(f"Gebiete fehlen im HVPI-Export: {sorted(missing)}")
    wide = wide.rename(columns={"DE": "inflation_de_pct", "U2": "inflation_ea_pct"})
    wide = wide.sort_values("monat").reset_index(drop=True)
    # Jahresrate in eine Monatsrate umrechnen, sonst kumuliert sich der Verlust zu stark.
    faktor = (1 + wide["inflation_de_pct"].fillna(0) / 100) ** (-1 / 12)
    wide["kaufkraft_index"] = 100 * faktor.cumprod()
    return wide[["monat", "inflation_de_pct", "inflation_ea_pct", "kaufkraft_index"]]


def _parse_household_prices(raw_dir: Path, filename: str, wertspalte: str) -> pd.DataFrame:
    """Summiert die Preisbestandteile zu einem Gesamtpreis je Verbrauchsklasse."""
    frame = destatis.parse_fixed_columns(
        destatis.decode((raw_dir / filename).read_bytes()),
        ["jahr", "verbrauchsklasse"],
        ["energie_und_vertrieb", "netzkosten", "steuern_abgaben"],
    )
    frame["jahr"] = frame["jahr"].astype(int)
    frame[wertspalte] = frame[["energie_und_vertrieb", "netzkosten", "steuern_abgaben"]].sum(
        axis=1, min_count=1
    )
    return frame[["jahr", "verbrauchsklasse", wertspalte]]


def build_energy_prices(raw_dir: Path) -> pd.DataFrame:
    """Strom- und Gaspreise für Haushalte je Jahr (Destatis)."""
    strom = _parse_household_prices(
        raw_dir, "destatis_61243-0002_strompreise.csv", "strompreis_eur_kwh"
    )
    gas = _parse_household_prices(raw_dir, "destatis_61243-0011_gaspreise.csv", "gaspreis_eur_kwh")
    frame = strom.merge(gas, on=["jahr", "verbrauchsklasse"], how="outer")
    return frame.sort_values(["jahr", "verbrauchsklasse"]).reset_index(drop=True)


def build_day_ahead_prices(raw_dir: Path) -> pd.DataFrame:
    """Tagesmittel der Day-Ahead-Strompreise für die Gebotszone DE-LU."""
    document = _load_json(raw_dir, "energy_charts_day_ahead.json")
    frame = pd.DataFrame(
        {
            "zeit": pd.to_datetime(document["unix_seconds"], unit="s", utc=True),
            "preis_eur_mwh": pd.to_numeric(pd.Series(document["price"]), errors="coerce"),
        }
    )
    frame["zeit"] = frame["zeit"].dt.tz_convert("Europe/Berlin")
    frame["datum"] = frame["zeit"].dt.normalize().dt.tz_localize(None)
    daily = frame.groupby("datum", as_index=False)["preis_eur_mwh"].mean()
    return daily.sort_values("datum").reset_index(drop=True)


def build_fuel_prices(raw_dir: Path) -> pd.DataFrame:
    """Monatliche Kraftstoffpreise je Land aus dem EU-Ölbulletin."""
    aktuelles_jahr = datetime.now(UTC).year
    frame = oil.parse_prices(
        (raw_dir / "oil_bulletin_preise.xlsx").read_bytes(),
        since=date(aktuelles_jahr - 10, 1, 1),
    )
    frame = frame[frame["land_code"].isin(laender.OIL_LAND_NAMEN)].copy()
    if frame.empty:
        raise ValueError("Keine Kraftstoffpreise für die bekannten Länder gefunden")
    frame["land"] = frame["land_code"].map(laender.OIL_LAND_NAMEN)
    frame["monat"] = pd.to_datetime(frame["datum"]).dt.strftime("%Y-%m")
    monthly = frame.groupby(["monat", "land", "produkt"], as_index=False)["preis_eur_l"].mean()
    return monthly.sort_values(["monat", "land", "produkt"]).reset_index(drop=True)


def build_big_mac(raw_dir: Path) -> pd.DataFrame:
    """Big-Mac-Index für die ausgewählten Länder (The Economist)."""
    frame = bigmac.parse_index((raw_dir / "big_mac_index.csv").read_bytes())
    frame = frame[frame["iso3"].isin(laender.BIG_MAC_LAENDER)].copy()
    frame["land"] = frame["iso3"].map(laender.BIG_MAC_LAENDER)
    columns = ["datum", "land", "preis_usd", "abweichung_pct"]
    return frame[columns].sort_values(["datum", "land"]).reset_index(drop=True)


def build_homeownership(raw_dir: Path) -> pd.DataFrame:
    """Eigentums- und Mietquote der Haushalte je Land und Jahr (Eurostat)."""
    frame = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_ilc_lvho02.json"))
    frame = frame[frame["tenure"].isin(["OWN", "RENT"])]
    wide = frame.pivot_table(
        index=["time", "geo"], columns="tenure", values="value", aggfunc="first"
    ).reset_index()
    wide = wide.rename(
        columns={"time": "jahr", "OWN": "eigentumsquote_pct", "RENT": "mietquote_pct"}
    )
    wide["jahr"] = wide["jahr"].astype(int)
    wide["land"] = wide["geo"].map(laender.LAND_NAMEN)
    wide.loc[wide["geo"] == "EU27_2020", "land"] = "EU-27"
    columns = ["jahr", "geo", "land", "eigentumsquote_pct", "mietquote_pct"]
    return wide[columns].sort_values(["jahr", "land"]).reset_index(drop=True)


def build_bmf_interest(raw_dir: Path) -> pd.DataFrame:
    """Zinsausgaben des Bundes am Kreditmarkt (BMF)."""
    frame = bmf.parse_interest_csv((raw_dir / "bmf_zinsausgaben_kreditmarkt.csv").read_bytes())
    frame = frame.dropna(subset=["zinsausgaben_mrd_eur"])
    columns = ["jahr", "art", "zinsausgaben_mrd_eur"]
    return frame[columns].sort_values("jahr").reset_index(drop=True)


BUILDERS = {
    "schulden_jahresreihe.csv": build_annual_debt,
    "schulden_quartalsreihe.csv": build_quarterly_debt,
    "schulden_destatis_jahr.csv": build_annual_debt_destatis,
    "schulden_destatis_quartal.csv": build_quarterly_debt_destatis,
    "schulden_destatis_bundeslaender.csv": build_quarterly_debt_laender,
    "bip_bevoelkerung.csv": build_gdp_population,
    "haushalt_jahr.csv": build_household,
    "zins_bund_10j.csv": build_bund_yield,
    "zins_vergleich.csv": build_international_yields,
    "zinslast_jahr.csv": build_interest_burden,
    "insolvenzen_monat.csv": build_insolvencies,
    "geldmenge_monat.csv": build_money_supply,
    "kaufkraft_monat.csv": build_purchasing_power,
    "energiepreise_jahr.csv": build_energy_prices,
    "strom_boerse_tag.csv": build_day_ahead_prices,
    "kraftstoffpreise.csv": build_fuel_prices,
    "big_mac.csv": build_big_mac,
    "eigentumsquote.csv": build_homeownership,
    "bund_zinsausgaben.csv": build_bmf_interest,
}

# Zinsreihen brauchen zwei Nachkommastellen, Mengen genügt eine.
FLOAT_FORMATS = {
    "zins_bund_10j.csv": "%.2f",
    "zins_vergleich.csv": "%.2f",
    "zinslast_jahr.csv": "%.2f",
    "geldmenge_monat.csv": "%.2f",
    "kaufkraft_monat.csv": "%.2f",
    "energiepreise_jahr.csv": "%.4f",
    "strom_boerse_tag.csv": "%.2f",
    "kraftstoffpreise.csv": "%.3f",
    "big_mac.csv": "%.2f",
    "eigentumsquote.csv": "%.1f",
    "bund_zinsausgaben.csv": "%.2f",
}


def build_all(
    raw_dir: Path = paths.RAW_DIR, processed_dir: Path = paths.PROCESSED_DIR
) -> dict[str, Path]:
    """Schreibt alle aufbereiteten Tabellen und gibt die erzeugten Pfade zurück."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for filename, builder in BUILDERS.items():
        frame = builder(raw_dir)
        target = processed_dir / filename
        frame.to_csv(
            target,
            index=False,
            float_format=FLOAT_FORMATS.get(filename, "%.1f"),
            date_format="%Y-%m-%d",
        )
        written[filename] = target
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true", help="Rohdaten trotz vorhandener Dateien neu laden"
    )
    args = parser.parse_args(argv)

    sources.download_all(paths.RAW_DIR, refresh=args.refresh)
    for filename, target in build_all().items():
        print(f"{filename}: {target.relative_to(paths.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
