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
    imf,
    laender,
    oil,
    paths,
    sources,
    weltbank,
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

LAENDER_CODES = tuple(code for code, _ in laender.EUROPA_LAENDER)

# Länder außerhalb der Europäischen Union, die der IWF-Datensatz abdeckt.
IMF_LAENDER = {"USA": "Vereinigte Staaten", "RUS": "Russland"}

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


def _laender_eurostat(raw_dir: Path, filename: str, value_column: str) -> pd.DataFrame:
    """Liest eine Eurostat-Tabelle mit Länderdimension und ergänzt deutsche Namen."""
    frame = eurostat.jsonstat_to_frame(_load_json(raw_dir, filename))
    frame = frame[frame["geo"].isin(LAENDER_CODES)].copy()
    frame["land"] = frame["geo"].map(laender.LAND_NAMEN)
    return frame.rename(columns={"value": value_column})


def _laender_gdp(raw_dir: Path) -> pd.DataFrame:
    """BIP je Land und Jahr in Mio. EUR."""
    frame = _laender_eurostat(raw_dir, "eurostat_nama_10_gdp_laender.json", "bip_mio_eur")
    frame["jahr"] = frame["time"].astype(int)
    return frame[["jahr", "geo", "bip_mio_eur"]].dropna(subset=["bip_mio_eur"])


def _laender_population(raw_dir: Path) -> pd.DataFrame:
    """Bevölkerung je Land und Jahr."""
    frame = _laender_eurostat(raw_dir, "eurostat_demo_pjan_laender.json", "bevoelkerung")
    frame["jahr"] = frame["time"].astype(int)
    return frame[["jahr", "geo", "bevoelkerung"]].dropna(subset=["bevoelkerung"])


def _imf_roh(raw_dir: Path) -> pd.DataFrame:
    return pd.read_csv(raw_dir / "imf_fiskal.csv")


def _imf_reihe(raw_dir: Path, indikator: str) -> pd.DataFrame:
    """Liest eine IWF-Reihe als Tabelle ``iso3, jahr, wert``."""
    frame = _imf_roh(raw_dir)
    frame = frame[frame["indikator"] == indikator]
    return frame.pivot_table(index=["iso3", "jahr"], values="wert", aggfunc="first").reset_index()


def _eur_usd(raw_dir: Path) -> pd.DataFrame:
    """Jahresdurchschnitt des US-Dollars je Euro (EZB)."""
    frame = ecb.parse_exr_csv((raw_dir / "ecb_eur_usd_jahr.csv").read_bytes())
    return frame.rename(columns={"wert": "usd_je_eur"})[["jahr", "usd_je_eur"]]


def _internationale_finanzen(raw_dir: Path) -> pd.DataFrame:
    """Jahreswerte für USA und Russland aus IWF-Daten, in Euro umgerechnet.

    Schuldenquote, Einnahmen und Zinsausgaben stammen aus der IWF-Datenbank
    Public Finances in Modern History, BIP und Bevölkerung aus dem WEO. Die
    Umrechnung in Euro erfolgt mit dem Jahresdurchschnitt des EZB-Referenzkurses.
    Schätzjahre des WEO werden ausgelassen.
    """
    letztes_ist_jahr = date.today().year - 1
    reihen = {
        "schuldenquote_pct": imf.FPP_SCHULDENQUOTE,
        "einnahmenquote_pct": imf.FPP_EINNAHMEN,
        "zinsquote_pct": imf.FPP_ZINSEN,
        "bip_mrd_usd": imf.WEO_BIP_USD,
        "bip_wachstum_pct": imf.WEO_BIP_WACHSTUM,
        "bevoelkerung_mio": imf.WEO_BEVOELKERUNG,
        "bip_je_einwohner_usd": imf.WEO_BIP_JE_EINWOHNER,
    }
    frame = None
    for spalte, indikator in reihen.items():
        reihe = _imf_reihe(raw_dir, indikator).rename(columns={"wert": spalte})
        frame = reihe if frame is None else frame.merge(reihe, on=["iso3", "jahr"], how="outer")
    if frame is None:
        raise ValueError("Keine IWF-Daten für die internationalen Länder gefunden")

    frame = frame[frame["iso3"].isin(IMF_LAENDER)].copy()
    frame["jahr"] = frame["jahr"].astype(int)
    frame = frame[frame["jahr"] <= letztes_ist_jahr]
    frame = frame.merge(_eur_usd(raw_dir), on="jahr", how="left")
    frame["land"] = frame["iso3"].map(IMF_LAENDER)
    frame["geo"] = frame["iso3"]

    frame["bip_mio_eur"] = frame["bip_mrd_usd"] * 1000 / frame["usd_je_eur"]
    frame["schulden_mio_eur"] = frame["schuldenquote_pct"] / 100 * frame["bip_mio_eur"]
    frame["einnahmen_mio_eur"] = frame["einnahmenquote_pct"] / 100 * frame["bip_mio_eur"]
    frame["zinsausgaben_mio_eur"] = frame["zinsquote_pct"] / 100 * frame["bip_mio_eur"]
    frame["bevoelkerung"] = frame["bevoelkerung_mio"] * 1_000_000
    frame["quelle"] = "IWF WEO/FPP"
    frame["quelle_key"] = "imf_fiskal"
    frame = frame.dropna(
        subset=["schuldenquote_pct", "einnahmenquote_pct", "zinsquote_pct"], how="all"
    )
    return frame.dropna(subset=["bip_mio_eur"]).reset_index(drop=True)


def build_laender_debt(raw_dir: Path) -> pd.DataFrame:
    """Maastricht-Schuldenstand je Land, jährlich (Eurostat, USA und Russland: IWF)."""
    frame = _laender_eurostat(raw_dir, "eurostat_gov_10dd_edpt1_laender.json", "value")
    wide = frame.pivot_table(
        index=["time", "geo", "land"], columns="unit", values="value", aggfunc="first"
    ).reset_index()
    for column in ("MIO_EUR", "PC_GDP"):
        if column not in wide.columns:
            raise ValueError(f"Einheit {column} fehlt in gov_10dd_edpt1 (Länder)")
    wide = wide.rename(
        columns={
            "time": "jahr",
            "MIO_EUR": "schulden_mio_eur",
            "PC_GDP": "schuldenquote_pct",
        }
    )
    wide["jahr"] = wide["jahr"].astype(int)
    wide["quelle"] = "Eurostat gov_10dd_edpt1"
    wide["quelle_key"] = "eurostat_schulden_laender"
    columns = [
        "jahr",
        "geo",
        "land",
        "schulden_mio_eur",
        "schuldenquote_pct",
        "quelle",
        "quelle_key",
    ]
    international = _internationale_finanzen(raw_dir)
    result = pd.concat([wide[columns], international[columns]], ignore_index=True)
    return result.sort_values(["jahr", "land"]).reset_index(drop=True)


def build_laender_budget(raw_dir: Path) -> pd.DataFrame:
    """Einnahmen, Zinsausgaben und abgeleitete Quoten je Land.

    Europäische Länder aus Eurostat, USA und Russland aus dem IWF-Datensatz.
    """
    frame = _laender_eurostat(raw_dir, "eurostat_gov_10a_main_laender.json", "value")
    wide = frame.pivot_table(
        index=["time", "geo", "land"], columns="na_item", values="value", aggfunc="first"
    ).reset_index()
    wide = wide.rename(
        columns={
            "time": "jahr",
            "D41PAY": "zinsausgaben_mio_eur",
            "TR": "einnahmen_mio_eur",
        }
    )
    wide["jahr"] = wide["jahr"].astype(int)
    wide = wide.merge(_laender_gdp(raw_dir), on=["jahr", "geo"], how="left")
    wide = wide.merge(_laender_population(raw_dir), on=["jahr", "geo"], how="left")

    wide["zins_quote_bip_pct"] = wide["zinsausgaben_mio_eur"] / wide["bip_mio_eur"] * 100
    wide["zins_quote_einnahmen_pct"] = (
        wide["zinsausgaben_mio_eur"] / wide["einnahmen_mio_eur"] * 100
    )
    wide["zins_je_einwohner_eur"] = wide["zinsausgaben_mio_eur"] * 1_000_000 / wide["bevoelkerung"]
    wide["quelle"] = "Eurostat gov_10a_main"
    wide["quelle_key"] = "eurostat_haushalt_laender"

    columns = [
        "jahr",
        "geo",
        "land",
        "einnahmen_mio_eur",
        "zinsausgaben_mio_eur",
        "bip_mio_eur",
        "bevoelkerung",
        "zins_quote_bip_pct",
        "zins_quote_einnahmen_pct",
        "zins_je_einwohner_eur",
        "quelle",
        "quelle_key",
    ]
    international = _internationale_finanzen(raw_dir).copy()
    international["zins_quote_bip_pct"] = (
        international["zinsausgaben_mio_eur"] / international["bip_mio_eur"] * 100
    )
    international["zins_quote_einnahmen_pct"] = (
        international["zinsausgaben_mio_eur"] / international["einnahmen_mio_eur"] * 100
    )
    international["zins_je_einwohner_eur"] = (
        international["zinsausgaben_mio_eur"] * 1_000_000 / international["bevoelkerung"]
    )
    result = pd.concat([wide[columns], international[columns]], ignore_index=True)
    return result.sort_values(["jahr", "land"]).reset_index(drop=True)


def _us_inflation(raw_dir: Path) -> pd.DataFrame:
    """Vorjahresrate des US-Verbraucherpreisindex (FRED)."""
    frame = fred.parse_series_csv((raw_dir / "fred_us_cpi.csv").read_bytes())
    frame = frame.sort_values("datum").reset_index(drop=True)
    frame["inflation_pct"] = frame["wert"].pct_change(12) * 100
    frame["monat"] = frame["datum"].dt.strftime("%Y-%m")
    frame["geo"] = "US"
    frame["land"] = laender.LAND_NAMEN["US"]
    frame["quelle"] = "FRED CPIAUCSL"
    frame["quelle_key"] = "fred_us_cpi"
    return frame.dropna(subset=["inflation_pct"])[
        ["monat", "geo", "land", "inflation_pct", "quelle", "quelle_key"]
    ]


def _russland_inflation(raw_dir: Path) -> pd.DataFrame:
    """Monatliche Inflationsrate Russlands (Rosstat/EMISS bzw. Bank of Russia)."""
    frame = pd.read_csv(raw_dir / "rosstat_cpi_monatlich.csv", dtype={"monat": str})
    frame["geo"] = "RU"
    frame["land"] = laender.LAND_NAMEN["RU"]
    frame["quelle_key"] = "rosstat_cpi"
    if "quelle" not in frame.columns:
        frame["quelle"] = "Rosstat (EMISS)"
    return frame[["monat", "geo", "land", "inflation_pct", "quelle", "quelle_key"]]


def build_laender_inflation(raw_dir: Path) -> pd.DataFrame:
    """Monatliche Inflationsraten je Land.

    Europäische Länder: HVPI (Eurostat); USA: CPI (FRED); Russland: Rosstat
    beziehungsweise die verkettete Rate der Bank of Russia.
    """
    frame = _laender_eurostat(raw_dir, "eurostat_prc_hicp_manr.json", "inflation_pct")
    frame = frame.rename(columns={"time": "monat"})
    frame["quelle"] = "Eurostat prc_hicp_manr"
    frame["quelle_key"] = "eurostat_inflation_laender"
    columns = ["monat", "geo", "land", "inflation_pct", "quelle", "quelle_key"]
    europe = frame[columns].dropna(subset=["inflation_pct"])
    result = pd.concat([europe, _us_inflation(raw_dir), _russland_inflation(raw_dir)])
    return result.sort_values(["monat", "land"]).reset_index(drop=True)


def _jahreswerte(raw_dir: Path, filename: str, faktor: float) -> pd.DataFrame:
    """Aggregiert eine FRED-Reihe zu Jahreswerten (Mittelwert × Faktor)."""
    frame = fred.parse_series_csv((raw_dir / filename).read_bytes())
    frame["jahr"] = frame["datum"].dt.year
    yearly = frame.groupby("jahr", as_index=False)["wert"].mean()
    yearly["wert"] = yearly["wert"] * faktor
    return yearly


def _einkommen_aus_usd(
    frame: pd.DataFrame,
    spalte: str,
    wechselkurse: pd.Series,
    *,
    land: str,
    geo: str,
    art: str,
    quelle: str,
    quelle_key: str,
) -> pd.DataFrame:
    """Rechnet eine US-Dollar-Reihe je Einwohner:in in Euro um."""
    result = frame[["jahr", spalte]].rename(columns={spalte: "einkommen_usd"}).copy()
    result["einkommen_eur"] = result["einkommen_usd"] / result["jahr"].map(wechselkurse)
    result["land"] = land
    result["geo"] = geo
    result["einkommensart"] = art
    result["quelle"] = quelle
    result["quelle_key"] = quelle_key
    return result.dropna(subset=["einkommen_eur"])[
        ["jahr", "geo", "land", "einkommensart", "einkommen_eur", "quelle", "quelle_key"]
    ]


def build_laender_einkommen(raw_dir: Path) -> pd.DataFrame:
    """Durchschnittseinkommen je Land und Jahr in drei Abgrenzungen.

    * ``bip_pro_kopf``: BIP je Einwohner:in (Eurostat für die EU, IWF-WEO für USA
      und Russland).
    * ``verfuegbar_pro_kopf``: verfügbares Einkommen je Einwohner:in (Eurostat,
      BEA/FRED für die USA); für Russland die BNE-Ersatzreihe der Weltbank.
    * ``bruttolohn``: Bruttoverdienst je Beschäftigten (Eurostat, BLS/FRED für die
      USA); für Russland liegt keine frei abrufbare Reihe vor.
    """
    frames: list[pd.DataFrame] = []

    gdp = _laender_gdp(raw_dir).merge(_laender_population(raw_dir), on=["jahr", "geo"])
    gdp["einkommen_eur"] = gdp["bip_mio_eur"] * 1_000_000 / gdp["bevoelkerung"]
    gdp["einkommensart"] = "bip_pro_kopf"
    gdp["land"] = gdp["geo"].map(laender.LAND_NAMEN)
    gdp["quelle"] = "Eurostat nama_10_gdp, demo_pjan"
    gdp["quelle_key"] = "eurostat_bip_laender"
    frames.append(
        gdp[["jahr", "geo", "land", "einkommensart", "einkommen_eur", "quelle", "quelle_key"]]
    )

    verfuegbar = _laender_eurostat(raw_dir, "eurostat_ilc_di03_laender.json", "einkommen_eur")
    verfuegbar["jahr"] = verfuegbar["time"].astype(int)
    verfuegbar["einkommensart"] = "verfuegbar_pro_kopf"
    verfuegbar["quelle"] = "Eurostat ilc_di03"
    verfuegbar["quelle_key"] = "eurostat_einkommen_laender"
    frames.append(
        verfuegbar[
            ["jahr", "geo", "land", "einkommensart", "einkommen_eur", "quelle", "quelle_key"]
        ]
    )

    lohn = _laender_eurostat(raw_dir, "eurostat_nama_10_lp_ulc_laender.json", "einkommen_eur")
    lohn["jahr"] = lohn["time"].astype(int)
    lohn["einkommensart"] = "bruttolohn"
    lohn["quelle"] = "Eurostat nama_10_lp_ulc"
    lohn["quelle_key"] = "eurostat_arbeitnehmerentgelt_laender"
    frames.append(
        lohn[["jahr", "geo", "land", "einkommensart", "einkommen_eur", "quelle", "quelle_key"]]
    )

    wechselkurse = _eur_usd(raw_dir).set_index("jahr")["usd_je_eur"]

    weo = _imf_reihe(raw_dir, imf.WEO_BIP_JE_EINWOHNER).rename(columns={"wert": "bip_je_kopf_usd"})
    weo = weo[weo["iso3"].isin(IMF_LAENDER)]
    weo["jahr"] = weo["jahr"].astype(int)
    # WEO enthält Schätzungen und Projektionen; nur abgeschlossene Jahre verwenden.
    weo = weo[weo["jahr"] <= date.today().year - 1]
    for iso3, land in IMF_LAENDER.items():
        frames.append(
            _einkommen_aus_usd(
                weo[weo["iso3"] == iso3],
                "bip_je_kopf_usd",
                wechselkurse,
                land=land,
                geo=iso3,
                art="bip_pro_kopf",
                quelle="IWF WEO NGDPDPC",
                quelle_key="imf_fiskal",
            )
        )

    usa_einkommen = _jahreswerte(raw_dir, "fred_us_einkommen.csv", 1.0)
    frames.append(
        _einkommen_aus_usd(
            usa_einkommen,
            "wert",
            wechselkurse,
            land=laender.LAND_NAMEN["US"],
            geo="US",
            art="verfuegbar_pro_kopf",
            quelle="BEA/FRED A229RC0A052NBEA",
            quelle_key="fred_us_einkommen",
        )
    )

    usa_lohn = _jahreswerte(raw_dir, "fred_us_lohn.csv", 52.0)
    frames.append(
        _einkommen_aus_usd(
            usa_lohn,
            "wert",
            wechselkurse,
            land=laender.LAND_NAMEN["US"],
            geo="US",
            art="bruttolohn",
            quelle="BLS/FRED CES0500000011 (Wochenverdienst × 52)",
            quelle_key="fred_us_lohn",
        )
    )

    russland_bne = weltbank.parse_indicator_json(
        (raw_dir / "weltbank_bne_russland.json").read_bytes(), "NY.GNP.PCAP.CD"
    ).rename(columns={"wert": "bne_je_kopf_usd"})
    frames.append(
        _einkommen_aus_usd(
            russland_bne,
            "bne_je_kopf_usd",
            wechselkurse,
            land=laender.LAND_NAMEN["RU"],
            geo="RU",
            art="verfuegbar_pro_kopf",
            quelle="Weltbank NY.GNP.PCAP.CD (Ersatzreihe)",
            quelle_key="weltbank_bne_russland",
        )
    )

    result = pd.concat(frames, ignore_index=True)
    return result.dropna(subset=["einkommen_eur"]).sort_values(
        ["jahr", "land", "einkommensart"]
    ).reset_index(drop=True)


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
            (
                raw_dir / "manual" / "stat_bundesamt_insolvenzen_52411-0017_de_Nov2026.csv"
            ).read_bytes()
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


# Energiegehalt für die Umrechnung in ct je kWh.
KWH_JE_LITER_HEIZOEL = 10.0
KWH_JE_BARREL_ROHOEL = 1700.0
KWH_JE_MMBTU = 293.071


def build_energy_markets(raw_dir: Path) -> pd.DataFrame:
    """Monatspreise für Heizöl, Gas und Rohöl, regional vergleichbar.

    Heizöl stammt aus dem EU-Ölbulletin. Gas- und Öl-Benchmarks kommen von EIA
    bzw. IWF über FRED. Die US-Dollar-Preise werden mit dem EZB-Referenzkurs in
    Euro umgerechnet; Gas zusätzlich in Euro je MWh.
    """
    heizoel = oil.parse_prices(
        (raw_dir / "oil_bulletin_preise.xlsx").read_bytes(),
        produkte={"heating_oil": "Heizöl"},
    )
    heizoel = heizoel[heizoel["land_code"] == "DE"].copy()
    if heizoel.empty:
        raise ValueError("Keine Heizölpreise für Deutschland im Ölbulletin gefunden")
    heizoel["monat"] = pd.to_datetime(heizoel["datum"]).dt.strftime("%Y-%m")
    heizoel_monat = heizoel.groupby("monat", as_index=False)["preis_eur_l"].mean()
    heizoel_monat["heizoel_ct_l"] = heizoel_monat["preis_eur_l"] * 100
    heizoel_monat["heizoel_ct_kwh"] = heizoel_monat["heizoel_ct_l"] / KWH_JE_LITER_HEIZOEL

    wechselkurs = ecb.parse_exr_daily_csv((raw_dir / "ecb_eur_usd_tag.csv").read_bytes())
    wechselkurs_monat = (
        wechselkurs.assign(monat=wechselkurs["datum"].dt.strftime("%Y-%m"))
        .groupby("monat", as_index=False)["usd_je_eur"]
        .mean()
    )

    def monatsmittel(frame: pd.DataFrame, wertspalte: str) -> pd.DataFrame:
        return frame.groupby("monat", as_index=False)[wertspalte].mean()

    # Europa: IWF-Benchmark für europäisches Erdgas (TTF-orientiert).
    gas = fred.parse_series_csv((raw_dir / "fred_erdgas_europa.csv").read_bytes())
    gas["monat"] = gas["datum"].dt.strftime("%Y-%m")
    gas = gas.merge(wechselkurs_monat, on="monat", how="left")
    gas["gas_ct_kwh"] = 100 * gas["wert"] / (KWH_JE_MMBTU * gas["usd_je_eur"])
    gas["gas_ttf_eur_mwh"] = gas["gas_ct_kwh"] * 10

    # Nordostasien: IWF-Preis für LNG Japan als frei verfügbare JKM-Referenz.
    japan = fred.parse_series_csv((raw_dir / "fred_lng_japan.csv").read_bytes())
    japan["monat"] = japan["datum"].dt.strftime("%Y-%m")
    japan = japan.merge(wechselkurs_monat, on="monat", how="left")
    japan["gas_jkm_eur_mwh"] = (
        japan["wert"] / (KWH_JE_MMBTU / 1000) / japan["usd_je_eur"]
    )

    # USA: Henry-Hub-Spotpreis, täglich in Euro je MWh umgerechnet.
    henry = fred.parse_series_csv((raw_dir / "fred_henry_hub.csv").read_bytes())
    henry = henry.merge(wechselkurs, on="datum", how="inner")
    henry["monat"] = henry["datum"].dt.strftime("%Y-%m")
    henry["preis_eur_mwh"] = henry["wert"] / (KWH_JE_MMBTU / 1000) / henry["usd_je_eur"]
    henry_monat = monatsmittel(henry, "preis_eur_mwh").rename(
        columns={"preis_eur_mwh": "gas_henry_hub_eur_mwh"}
    )

    # Öl: Brent und WTI täglich, Dubai monatlich, jeweils in Euro je Barrel.
    brent = fred.parse_series_csv((raw_dir / "fred_brent_rohoel.csv").read_bytes())
    brent["monat"] = brent["datum"].dt.strftime("%Y-%m")
    brent = brent.merge(wechselkurs, on="datum", how="inner")
    brent["brent_eur_barrel"] = brent["wert"] / brent["usd_je_eur"]
    brent_monat = monatsmittel(brent, "brent_eur_barrel")
    brent_monat["brent_ct_kwh"] = brent_monat["brent_eur_barrel"] * 100 / KWH_JE_BARREL_ROHOEL

    wti = fred.parse_series_csv((raw_dir / "fred_wti_rohoel.csv").read_bytes())
    wti = wti.merge(wechselkurs, on="datum", how="inner")
    wti["monat"] = wti["datum"].dt.strftime("%Y-%m")
    wti["wti_eur_barrel"] = wti["wert"] / wti["usd_je_eur"]
    wti_monat = monatsmittel(wti, "wti_eur_barrel")

    dubai = fred.parse_series_csv((raw_dir / "fred_dubai_rohoel.csv").read_bytes())
    dubai["monat"] = dubai["datum"].dt.strftime("%Y-%m")
    dubai = dubai.merge(wechselkurs_monat, on="monat", how="left")
    dubai["dubai_eur_barrel"] = dubai["wert"] / dubai["usd_je_eur"]

    frame = heizoel_monat[["monat", "heizoel_ct_l", "heizoel_ct_kwh"]]
    for teil in (
        gas[["monat", "gas_ct_kwh", "gas_ttf_eur_mwh"]],
        japan[["monat", "gas_jkm_eur_mwh"]],
        henry_monat,
        brent_monat[["monat", "brent_eur_barrel", "brent_ct_kwh"]],
        wti_monat,
        dubai[["monat", "dubai_eur_barrel"]],
    ):
        frame = frame.merge(teil, on="monat", how="outer")

    preisspalten = [
        "heizoel_ct_l",
        "gas_ttf_eur_mwh",
        "gas_jkm_eur_mwh",
        "gas_henry_hub_eur_mwh",
        "brent_eur_barrel",
        "wti_eur_barrel",
        "dubai_eur_barrel",
    ]
    frame = frame.dropna(subset=preisspalten, how="all")
    columns = [
        "monat",
        "heizoel_ct_l",
        "heizoel_ct_kwh",
        "gas_ct_kwh",
        "gas_ttf_eur_mwh",
        "gas_jkm_eur_mwh",
        "gas_henry_hub_eur_mwh",
        "brent_eur_barrel",
        "brent_ct_kwh",
        "wti_eur_barrel",
        "dubai_eur_barrel",
    ]
    return frame[columns].sort_values("monat").reset_index(drop=True)

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


def build_finanzplan_interest(raw_dir: Path) -> pd.DataFrame:
    """Geplante Zinsausgaben des Bundes im Kernhaushalt (Drucksache 21/7301)."""
    frame = bmf.parse_interest_csv(
        (raw_dir / "manual" / "bund_finanzplan_2026-2030_zinsausgaben.csv").read_bytes()
    )
    frame = frame.dropna(subset=["zinsausgaben_mrd_eur"])
    columns = ["jahr", "art", "zinsausgaben_mrd_eur"]
    return frame[columns].sort_values("jahr").reset_index(drop=True)


# Die Drucksache weist je Haushaltsjahr eine eigene Planungsstufe aus: das Ist des
# Vorjahres, den Soll-Ansatz, den Regierungsentwurf und danach die Finanzplanjahre.
PLANUNGSSTUFEN = ("Ist", "Soll", "Entwurf")


def build_finanzplan_areas(raw_dir: Path) -> pd.DataFrame:
    """Ausgaben des Bundes nach Aufgabenbereichen im Kernhaushalt (Drucksache 21/7301)."""
    frame = bmf.parse_areas_csv(
        (raw_dir / "manual" / "bund_finanzplan_2026-2030_aufgabenbereiche.csv").read_bytes()
    )
    jahre = sorted(frame["jahr"].unique())
    stufen = {
        jahr: PLANUNGSSTUFEN[index] if index < len(PLANUNGSSTUFEN) else "Finanzplan"
        for index, jahr in enumerate(jahre)
    }
    frame["art"] = frame["jahr"].map(stufen)
    columns = ["einzelplan", "aufgabenbereich", "jahr", "art", "ausgaben_mrd_eur"]
    return frame[columns].sort_values(["jahr", "einzelplan"]).reset_index(drop=True)


PREISE_NOMINAL = "in jeweiligen Preisen (Mrd. EUR)"
PREISE_REAL = "preisbereinigt, Kettenindex (2020=100)"
STAAT_INVESTITIONEN = "Bruttoanlageinvestitionen des Staates"
NICHTSTAAT_INVESTITIONEN = "Bruttoanlageinvestitionen der nichtstaatl.Sektoren"


def _destatis_jahresreihe(
    frame: pd.DataFrame, preisbasis: str, aggregat: str, spalte: str
) -> pd.DataFrame:
    """Wählt eine Zeile der VGR-Jahrestabelle aus und benennt ihren Wert um."""
    teil = frame[(frame["preisbasis"] == preisbasis) & (frame["aggregat"] == aggregat)]
    if teil.empty:
        raise ValueError(f"Zeile {preisbasis!r} / {aggregat!r} fehlt in der Tabelle")
    return teil[["jahr", "wert"]].rename(columns={"wert": spalte})


def build_bip_deutschland(raw_dir: Path) -> pd.DataFrame:
    """BIP, realer Index und Wachstumsraten Deutschlands (Destatis, Jahre)."""
    raw = destatis.decode((raw_dir / "destatis_81000-0001_vgr_jahr.csv").read_bytes())
    frame = destatis.parse_year_columns(raw, ["preisbasis", "aggregat", "einheit"])

    result = _destatis_jahresreihe(
        frame, PREISE_NOMINAL, "Bruttoinlandsprodukt", "bip_nominal_mrd_eur"
    )
    veraenderung = "nachr.: Bruttoinlandsprodukt (Veränderung in %)"
    reihen = (
        ("bip_wachstum_nominal_pct", PREISE_NOMINAL, veraenderung),
        ("bip_real_index", PREISE_REAL, "Bruttoinlandsprodukt"),
        ("bip_wachstum_real_pct", PREISE_REAL, veraenderung),
    )
    for spalte, preisbasis, aggregat in reihen:
        result = result.merge(
            _destatis_jahresreihe(frame, preisbasis, aggregat, spalte), on="jahr", how="outer"
        )

    columns = [
        "jahr",
        "bip_nominal_mrd_eur",
        "bip_real_index",
        "bip_wachstum_nominal_pct",
        "bip_wachstum_real_pct",
    ]
    return result[columns].sort_values("jahr").reset_index(drop=True)


def build_investitionen(raw_dir: Path) -> pd.DataFrame:
    """Private und staatliche Bruttoanlageinvestitionen (Destatis, Jahre)."""
    raw = destatis.decode((raw_dir / "destatis_81000-0025_investitionen.csv").read_bytes())
    frame = destatis.parse_year_columns(raw, ["preisbasis", "aggregat", "einheit"])

    sektoren = {
        STAAT_INVESTITIONEN: "Staat",
        NICHTSTAAT_INVESTITIONEN: "Nichtstaatliche Sektoren",
    }
    nominal = frame[(frame["preisbasis"] == PREISE_NOMINAL) & frame["aggregat"].isin(sektoren)]
    nominal = nominal.assign(sektor=nominal["aggregat"].map(sektoren)).rename(
        columns={"wert": "investitionen_mrd_eur"}
    )
    real = frame[(frame["preisbasis"] == PREISE_REAL) & frame["aggregat"].isin(sektoren)]
    real = real.assign(sektor=real["aggregat"].map(sektoren)).rename(
        columns={"wert": "real_index"}
    )
    if nominal.empty or real.empty:
        raise ValueError("Investitionszeilen fehlen in der Tabelle 81000-0025")

    result = nominal[["jahr", "sektor", "investitionen_mrd_eur"]].merge(
        real[["jahr", "sektor", "real_index"]], on=["jahr", "sektor"], how="outer"
    )
    bip = build_bip_deutschland(raw_dir)[["jahr", "bip_nominal_mrd_eur"]]
    result = result.merge(bip, on="jahr", how="left")
    result["anteil_bip_pct"] = result["investitionen_mrd_eur"] / result["bip_nominal_mrd_eur"] * 100
    columns = ["jahr", "sektor", "investitionen_mrd_eur", "real_index", "anteil_bip_pct"]
    return result[columns].sort_values(["jahr", "sektor"]).reset_index(drop=True)


def build_bip_wachstum(raw_dir: Path) -> pd.DataFrame:
    """Reales BIP-Wachstum je Land und Jahr (Eurostat; USA und Russland: IWF)."""
    frame = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_nama_10_gdp_wachstum.json"))
    frame = frame[frame["geo"].isin([*LAENDER_CODES, "EU27_2020"])].copy()
    frame["land"] = frame["geo"].map(laender.LAND_NAMEN)
    frame.loc[frame["geo"] == "EU27_2020", "land"] = "EU-27"
    frame["jahr"] = frame["time"].astype(int)
    frame["quelle"] = "Eurostat nama_10_gdp"
    frame["quelle_key"] = "eurostat_bip_wachstum"
    columns = ["jahr", "geo", "land", "wachstum_pct", "quelle", "quelle_key"]
    europe = frame.rename(columns={"value": "wachstum_pct"})[columns].dropna(
        subset=["wachstum_pct"]
    )

    international = _internationale_finanzen(raw_dir).rename(
        columns={"bip_wachstum_pct": "wachstum_pct"}
    )
    international["quelle"] = "IWF WEO"
    international["quelle_key"] = "imf_fiskal"
    result = pd.concat(
        [europe, international[columns].dropna(subset=["wachstum_pct"])], ignore_index=True
    )
    return result.sort_values(["jahr", "land"]).reset_index(drop=True)


def build_produktion_deutschland(raw_dir: Path) -> pd.DataFrame:
    """Monatlicher Produktionsindex des Verarbeitenden Gewerbes (Destatis)."""
    raw = destatis.decode((raw_dir / "destatis_42153-0001_produktion.csv").read_bytes())
    frame = destatis.parse_fixed_columns(
        raw,
        ["wirtschaftszweig", "jahr", "monat_name"],
        [
            "index_2021_original",
            "index_2021_kalenderbereinigt",
            "index_2021_saisonbereinigt",
            "index_2021_bv4_saisonbereinigt",
            "index_2021_trend",
        ],
        year_column=1,
    )
    frame = frame[frame["wirtschaftszweig"] == "Verarbeitendes Gewerbe"].copy()
    index_spalten = [
        "index_2021_original",
        "index_2021_kalenderbereinigt",
        "index_2021_saisonbereinigt",
        "index_2021_bv4_saisonbereinigt",
        "index_2021_trend",
    ]
    frame = frame.dropna(subset=index_spalten, how="all")
    frame["jahr"] = frame["jahr"].astype(int)
    frame["monat_nummer"] = frame["monat_name"].map(MONATSNAMEN)
    frame = frame.dropna(subset=["monat_nummer"]).copy()
    frame["monat_nummer"] = frame["monat_nummer"].astype(int)
    frame["monat"] = (
        frame["jahr"].astype(str) + "-" + frame["monat_nummer"].map(lambda monat: f"{monat:02d}")
    )
    columns = [
        "monat",
        "jahr",
        "index_2021_original",
        "index_2021_kalenderbereinigt",
        "index_2021_saisonbereinigt",
        "index_2021_bv4_saisonbereinigt",
        "index_2021_trend",
    ]
    return frame[columns].sort_values("monat").reset_index(drop=True)


def build_produktion_deutschland_lang(raw_dir: Path) -> pd.DataFrame:
    """Langfristiger Produktionsindex der Industrie, 2015=100 (Eurostat)."""
    frame = eurostat.jsonstat_to_frame(
        _load_json(raw_dir, "eurostat_sts_inpr_m_deutschland.json")
    )
    frame = frame.rename(columns={"time": "monat", "value": "index_2021"})
    frame["jahr"] = frame["monat"].str[:4].astype(int)
    basis = frame.loc[frame["jahr"] == 2015, "index_2021"].mean()
    if pd.isna(basis) or basis <= 0:
        raise ValueError("Basisfahr 2015 fehlt im Produktionsindex")
    frame["index_2015"] = frame["index_2021"] / basis * 100
    frame = frame.sort_values("monat").reset_index(drop=True)
    frame["trend_2015"] = analysis.linear_trend(frame, "index_2015", fit_end="2017-12")
    frame["abweichung_pct"] = (frame["index_2015"] / frame["trend_2015"] - 1) * 100
    columns = ["monat", "jahr", "index_2015", "trend_2015", "abweichung_pct"]
    return frame[columns]


def build_produktion_vergleich(raw_dir: Path) -> pd.DataFrame:
    """Produktionsindex des Verarbeitenden Gewerbes im Ländervergleich (Eurostat)."""
    frame = _laender_eurostat(raw_dir, "eurostat_sts_inpr_m.json", "index_2021")
    frame = frame.rename(columns={"time": "monat"})
    frame["quelle"] = "Eurostat sts_inpr_m"
    frame["quelle_key"] = "eurostat_produktion"
    columns = ["monat", "geo", "land", "index_2021", "quelle", "quelle_key"]
    return frame[columns].dropna(subset=["index_2021"]).sort_values(
        ["monat", "land"]
    ).reset_index(drop=True)


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
    "bund_zinsausgaben_plan.csv": build_finanzplan_interest,
    "bund_ausgaben_aufgabenbereiche.csv": build_finanzplan_areas,
    "laender_schulden_jahr.csv": build_laender_debt,
    "laender_haushalt_jahr.csv": build_laender_budget,
    "laender_inflation_monat.csv": build_laender_inflation,
    "laender_einkommen_jahr.csv": build_laender_einkommen,
    "bip_deutschland_jahr.csv": build_bip_deutschland,
    "bip_wachstum_jahr.csv": build_bip_wachstum,
    "investitionen_jahr.csv": build_investitionen,
    "produktion_deutschland_monat.csv": build_produktion_deutschland,
    "produktion_deutschland_lang.csv": build_produktion_deutschland_lang,
    "produktion_vergleich_monat.csv": build_produktion_vergleich,
    "energie_maerkte_monat.csv": build_energy_markets,
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
    "bund_zinsausgaben_plan.csv": "%.2f",
    "bund_ausgaben_aufgabenbereiche.csv": "%.3f",
    "laender_schulden_jahr.csv": "%.1f",
    "laender_haushalt_jahr.csv": "%.1f",
    "laender_inflation_monat.csv": "%.2f",
    "laender_einkommen_jahr.csv": "%.2f",
    "bip_deutschland_jahr.csv": "%.2f",
    "bip_wachstum_jahr.csv": "%.2f",
    "investitionen_jahr.csv": "%.2f",
    "produktion_deutschland_monat.csv": "%.2f",
    "produktion_deutschland_lang.csv": "%.2f",
    "produktion_vergleich_monat.csv": "%.2f",
    "energie_maerkte_monat.csv": "%.2f",
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
