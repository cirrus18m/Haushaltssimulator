"""Definition, Download und Dokumentation der frei verfügbaren Datenquellen.

Quellen:
* Destatis (GENESIS-Online): Tabellen als CSV, Lizenz DL-DE-BY-2.0
* Eurostat (Data Browser API): JSON-stat, Lizenz CC BY 4.0
* Deutsche Bundesbank: Zeitreihenexport als CSV, Quellenangabe erforderlich
* Federal Reserve Bank of St. Louis (FRED): CSV-Export, Quellenangabe erforderlich
* Bank of Russia: Zero-Coupon-Yield-Curve und Preisdynamik, Quellenangabe erforderlich
* Internationaler Währungsfonds (IWF): DataMapper-API, Quellenangabe erforderlich
* Rosstat über EMISS: Verbraucherpreise, Quellenangabe erforderlich
* Weltbank: World Development Indicators, CC BY 4.0

Jeder Abruf wird in der versionierten Quellenbibliothek ``data/sources.json``
festgehalten: URL, Lizenz, verwendete Datensätze, Prüfsumme und Zeitpunkt des
Downloads. Bereits vorhandene Rohdaten behalten ihren ursprünglichen Zeitstempel.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal

import pandas as pd

from . import cbr, config, fred_api, imf, laender, paths, rosstat

DESTATIS_TABLE_URL = "https://genesis.destatis.de/genesisWS/downloads/00/tables/{code}_00.csv"
EUROSTAT_DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}"
BUNDESBANK_SERIES_URL = (
    "https://api.statistiken.bundesbank.de/rest/download/BBSSY/"
    "D.REN.EUR.A630.000000WT1010.A?format=csv&lang=en"
)
FRED_SERIES_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
CBR_ZCYC_URL = "https://www.cbr.ru/eng/hd_base/zcyc_params/zcyc/?DateTo={datum}"
ECB_SERIES_URL = (
    "https://data-api.ecb.europa.eu/service/data/{dataset}/{key}?format=csvdata&startPeriod={start}"
)
ENERGY_CHARTS_URL = "https://api.energy-charts.info/price?bzn=DE-LU&start={start}&end={end}"
OIL_BULLETIN_URL = (
    "https://energy.ec.europa.eu/document/download/906e60ca-8b6a-44e7-8589-652854d2fd3f_en"
    "?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx"
)
BIG_MAC_URL = (
    "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/"
    "big-mac-full-index.csv"
)
BMF_INTEREST_URL = (
    "https://www.bundeshaushalt.de/Content/DE/Diagramme/Dashboard-Startseite/"
    "zinsausgaben-kreditmarkt-csv.csv?__blob=publicationFile&v=10"
)
IMF_DATAMAPPER_URL = "https://www.imf.org/external/datamapper/api/v1/{indicator}"
EMISS_URL = "https://fedstat.ru/indicator/data.do?id={indicator}&format=csv"
CBR_CPI_XLSX_URL = "https://www.cbr.ru/Content/Document/File/112040/indicators_cpd_eng.xlsx"
WELTBANK_INDICATOR_URL = (
    "https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}?format=json&per_page=100"
)

# Indikatoren des IWF, die der Datenaufbau in einer Datei sammelt.
IMF_INDICATORS = (
    imf.WEO_SCHULDENQUOTE,
    imf.WEO_BIP_USD,
    imf.WEO_BIP_JE_EINWOHNER,
    imf.WEO_BEVOELKERUNG,
    imf.FPP_SCHULDENQUOTE,
    imf.FPP_EINNAHMEN,
    imf.FPP_ZINSEN,
)

# EMISS-Indikator "Индекс потребительских цен" (monatlich, Russland).
ROSSTAT_CPI_INDICATOR = 31074

# Ab diesem Jahr liefert die Bank of Russia die Zinskurve in der genutzten Form.
CBR_START_YEAR = 2015
CBR_MAX_FALLBACK_DAYS = 8

USER_AGENT = "Haushaltssimulator/0.1 (+https://github.com/cirrus18m/Haushaltssimulator)"

FetchMode = Literal[
    "http", "cbr_zcyc", "energy_charts", "manual", "fred_api", "imf_datamapper", "emiss_api"
]


@dataclass(frozen=True)
class Source:
    """Eine herunterladbare Datenquelle samt Metadaten für die Quellenbibliothek."""

    key: str
    filename: str
    url: str
    description: str
    title: str
    publisher: str
    license: str
    datasets: tuple[str, ...]
    fetch_mode: FetchMode = "http"
    api_series: str | None = None


def _eurostat(dataset: str, **params: object) -> str:
    """Baut eine Eurostat-URL; Listen werden als wiederholte Parameter übergeben."""
    parts = []
    for key, value in params.items():
        values = value if isinstance(value, (list, tuple)) else (value,)
        parts.extend(f"{key}={item}" for item in values)
    return f"{EUROSTAT_DATA_URL.format(dataset=dataset)}?{'&'.join(parts)}"


SOURCES: tuple[Source, ...] = (
    Source(
        key="destatis_schulden_quartal",
        filename="destatis_71311-0001_quartal.csv",
        url=DESTATIS_TABLE_URL.format(code="71311-0001"),
        title="Schulden beim nicht-öffentlichen Bereich: Deutschland, Quartale",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 71311-0001",
        license="DL-DE-BY-2.0",
        datasets=("schulden_destatis_quartal.csv",),
        description=(
            "Destatis 71311-0001: Schulden beim nicht-öffentlichen Bereich, Deutschland, "
            "Stichtag zum Quartalsende, Ebenen/Haushalte/Schuldenarten (letzte 10 Quartale)"
        ),
    ),
    Source(
        key="destatis_schulden_bundeslaender",
        filename="destatis_71311-0003_bundeslaender.csv",
        url=DESTATIS_TABLE_URL.format(code="71311-0003"),
        title="Schulden beim nicht-öffentlichen Bereich: Bundesländer, Quartale",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 71311-0003",
        license="DL-DE-BY-2.0",
        datasets=("schulden_destatis_bundeslaender.csv",),
        description=(
            "Destatis 71311-0003: Schulden beim nicht-öffentlichen Bereich, Bundesländer, "
            "Stichtag zum Quartalsende, Ebenen/Haushalte/Schuldenarten (letzte 10 Quartale)"
        ),
    ),
    Source(
        key="destatis_schulden_jahr",
        filename="destatis_71321-0005_jahr.csv",
        url=DESTATIS_TABLE_URL.format(code="71321-0005"),
        title="Schulden beim nicht-öffentlichen Bereich: Deutschland, Jahresreihe",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 71321-0005",
        license="DL-DE-BY-2.0",
        datasets=("schulden_destatis_jahr.csv",),
        description=(
            "Destatis 71321-0005: Schulden beim nicht-öffentlichen Bereich, Deutschland, "
            "jährlich ab 31.12.2010, Ebenen/Haushalte/Schuldenarten"
        ),
    ),
    Source(
        key="eurostat_schulden_jahr",
        filename="eurostat_gov_10dd_edpt1.json",
        url=_eurostat(
            "gov_10dd_edpt1",
            format="JSON",
            lang="EN",
            geo="DE",
            na_item="GD",
            sinceTimePeriod="1995",
        ),
        title="Maastricht-Schuldenstand: Deutschland, jährlich",
        publisher="Eurostat, Datensatz gov_10dd_edpt1",
        license="CC BY 4.0",
        datasets=("schulden_jahresreihe.csv",),
        description=(
            "Eurostat gov_10dd_edpt1: Maastricht-Schuldenstand, Deutschland, jährlich, "
            "Sektoren S13/S1311/S1312/S1313/S1314, Mio. EUR und % des BIP"
        ),
    ),
    Source(
        key="eurostat_schulden_quartal",
        filename="eurostat_gov_10q_ggdebt.json",
        url=_eurostat(
            "gov_10q_ggdebt",
            format="JSON",
            lang="EN",
            geo="DE",
            na_item="GD",
            sinceTimePeriod="1999",
        ),
        title="Maastricht-Schuldenstand: Deutschland, vierteljährlich",
        publisher="Eurostat, Datensatz gov_10q_ggdebt",
        license="CC BY 4.0",
        datasets=("schulden_quartalsreihe.csv",),
        description=(
            "Eurostat gov_10q_ggdebt: Maastricht-Schuldenstand, Deutschland, vierteljährlich, "
            "Sektoren S13/S1311/S1312/S1313/S1314, Mio. EUR und % des BIP"
        ),
    ),
    Source(
        key="eurostat_bip",
        filename="eurostat_nama_10_gdp.json",
        url=_eurostat(
            "nama_10_gdp",
            format="JSON",
            lang="EN",
            geo="DE",
            na_item="B1GQ",
            unit="CP_MEUR",
            sinceTimePeriod="1995",
        ),
        title="Bruttoinlandsprodukt: Deutschland, jährlich",
        publisher="Eurostat, Datensatz nama_10_gdp",
        license="CC BY 4.0",
        datasets=("bip_bevoelkerung.csv",),
        description="Eurostat nama_10_gdp: Bruttoinlandsprodukt, Deutschland, jährlich, Mio. EUR",
    ),
    Source(
        key="eurostat_bevoelkerung",
        filename="eurostat_demo_pjan.json",
        url=_eurostat(
            "demo_pjan",
            format="JSON",
            lang="EN",
            geo="DE",
            sex="T",
            age="TOTAL",
            sinceTimePeriod="1995",
        ),
        title="Bevölkerung: Deutschland, jährlich",
        publisher="Eurostat, Datensatz demo_pjan",
        license="CC BY 4.0",
        datasets=("bip_bevoelkerung.csv",),
        description="Eurostat demo_pjan: Bevölkerung, Deutschland, jährlich, Stichtag 1. Januar",
    ),
    Source(
        key="eurostat_haushalt",
        filename="eurostat_gov_10a_main.json",
        url=_eurostat(
            "gov_10a_main",
            format="JSON",
            lang="EN",
            geo="DE",
            unit="MIO_EUR",
            sector=("S13", "S1311", "S1312", "S1313", "S1314"),
            na_item=("TR", "TE", "D41PAY", "B9"),
            sinceTimePeriod="1995",
        ),
        title="Einnahmen, Ausgaben und Zinsausgaben des Staates: Deutschland, jährlich",
        publisher="Eurostat, Datensatz gov_10a_main",
        license="CC BY 4.0",
        datasets=("haushalt_jahr.csv", "zinslast_jahr.csv"),
        description=(
            "Eurostat gov_10a_main: Gesamteinnahmen (TR), Gesamtausgaben (TE), "
            "Zinsausgaben (D41PAY) und Finanzierungssaldo (B9), Deutschland, jährlich ab 1995, "
            "Gesamtstaat und Ebenen, Mio. EUR"
        ),
    ),
    Source(
        key="eurostat_zinsvergleich",
        filename="eurostat_irt_lt_mcby_m.json",
        url=_eurostat(
            "irt_lt_mcby_m",
            format="JSON",
            lang="EN",
            int_rt="MCBY",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            sinceTimePeriod="1993",
        ),
        title="Konvergenzrenditen 10-jähriger Staatsanleihen: Europa, monatlich",
        publisher="Eurostat, Datensatz irt_lt_mcby_m",
        license="CC BY 4.0",
        datasets=("zins_vergleich.csv",),
        description=(
            "Eurostat irt_lt_mcby_m: Renditen 10-jähriger Staatsanleihen nach der "
            "Maastricht-Konvergenzmethode, monatlich, EU-Mitgliedstaaten und Vereinigtes "
            "Königreich, in Prozent"
        ),
    ),
    Source(
        key="eurostat_schulden_laender",
        filename="eurostat_gov_10dd_edpt1_laender.json",
        url=_eurostat(
            "gov_10dd_edpt1",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            na_item="GD",
            sector="S13",
            sinceTimePeriod="1995",
        ),
        title="Maastricht-Schuldenstand: europäische Länder, jährlich",
        publisher="Eurostat, Datensatz gov_10dd_edpt1",
        license="CC BY 4.0",
        datasets=("laender_schulden_jahr.csv",),
        description=(
            "Eurostat gov_10dd_edpt1: Maastricht-Schuldenstand (GD) des Gesamtstaats "
            "(S13), jährlich ab 1995, je Land in Mio. EUR und in % des BIP"
        ),
    ),
    Source(
        key="eurostat_haushalt_laender",
        filename="eurostat_gov_10a_main_laender.json",
        url=_eurostat(
            "gov_10a_main",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            unit="MIO_EUR",
            sector="S13",
            na_item=("D41PAY", "TR"),
            sinceTimePeriod="1995",
        ),
        title="Einnahmen und Zinsausgaben: europäische Länder, jährlich",
        publisher="Eurostat, Datensatz gov_10a_main",
        license="CC BY 4.0",
        datasets=("laender_haushalt_jahr.csv",),
        description=(
            "Eurostat gov_10a_main: Gesamteinnahmen (TR) und Zinsausgaben (D41PAY) des "
            "Gesamtstaats (S13), jährlich ab 1995, je Land in Mio. EUR"
        ),
    ),
    Source(
        key="eurostat_bip_laender",
        filename="eurostat_nama_10_gdp_laender.json",
        url=_eurostat(
            "nama_10_gdp",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            na_item="B1GQ",
            unit="CP_MEUR",
            sinceTimePeriod="1995",
        ),
        title="Bruttoinlandsprodukt: europäische Länder, jährlich",
        publisher="Eurostat, Datensatz nama_10_gdp",
        license="CC BY 4.0",
        datasets=("laender_haushalt_jahr.csv",),
        description=(
            "Eurostat nama_10_gdp: Bruttoinlandsprodukt (B1GQ) zu jeweiligen Preisen, "
            "jährlich ab 1995, je Land in Mio. EUR"
        ),
    ),
    Source(
        key="eurostat_bevoelkerung_laender",
        filename="eurostat_demo_pjan_laender.json",
        url=_eurostat(
            "demo_pjan",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            sex="T",
            age="TOTAL",
            sinceTimePeriod="1995",
        ),
        title="Bevölkerung: europäische Länder, jährlich",
        publisher="Eurostat, Datensatz demo_pjan",
        license="CC BY 4.0",
        datasets=("laender_haushalt_jahr.csv",),
        description=(
            "Eurostat demo_pjan: Bevölkerung am 1. Januar, jährlich ab 1995, je Land"
        ),
    ),
    Source(
        key="eurostat_inflation_laender",
        filename="eurostat_prc_hicp_manr.json",
        url=_eurostat(
            "prc_hicp_manr",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            coicop="CP00",
            unit="RCH_A",
            sinceTimePeriod="1997",
        ),
        title="Harmonisierter Verbraucherpreisindex: europäische Länder, monatlich",
        publisher="Eurostat, Datensatz prc_hicp_manr",
        license="CC BY 4.0",
        datasets=("laender_inflation_monat.csv",),
        description=(
            "Eurostat prc_hicp_manr: Inflationsrate (HVPI, alle Waren und Dienstleistungen) "
            "als Veränderung gegenüber dem Vorjahr, monatlich ab 1997, je Land in Prozent"
        ),
    ),
    Source(
        key="bundesbank_rendite_10j",
        filename="bundesbank_10j_rendite.csv",
        url=BUNDESBANK_SERIES_URL,
        title="Tagesrendite der aktuellen 10-jährigen Bundesanleihe",
        publisher="Deutsche Bundesbank, Zeitreihe BBSSY.D.REN.EUR.A630.000000WT1010.A",
        license="Deutsche Bundesbank, Quellenangabe erforderlich",
        datasets=("zins_bund_10j.csv", "zinslast_jahr.csv"),
        description=(
            "Deutsche Bundesbank BBSSY.D.REN.EUR.A630.000000WT1010.A: Daily yield of the "
            "current 10 year federal bond, Tageswerte in Prozent, ab Oktober 2001"
        ),
    ),
    Source(
        key="fred_us_zins",
        filename="fred_us_10j_rendite.csv",
        url=FRED_SERIES_URL.format(series="IRLTLT01USM156N"),
        title="Langfristige Staatsanleiherendite: Vereinigte Staaten, monatlich",
        publisher="OECD (MEI) über Federal Reserve Bank of St. Louis, Serie IRLTLT01USM156N",
        license="OECD-Nutzungsbedingungen, Quellenangabe erforderlich",
        datasets=("zins_vergleich.csv",),
        fetch_mode="fred_api",
        api_series="IRLTLT01USM156N",
        description=(
            "FRED IRLTLT01USM156N: Long-Term Government Bond Yields, 10-year benchmark, "
            "Vereinigte Staaten, monatlich, in Prozent. Abruf über die FRED-API, ohne "
            "API-Key über den öffentlichen CSV-Export"
        ),
    ),
    Source(
        key="cbr_ru_zins",
        filename="cbr_ru_10j_rendite.csv",
        url=CBR_ZCYC_URL.format(datum="TT.MM.JJJJ"),
        title="Zero-Coupon-Yield-Curve: Russische Staatsanleihen (OFZ)",
        publisher="Bank of Russia, Russian Government Bond Zero Coupon Yield Curve",
        license="Bank of Russia, Quellenangabe erforderlich",
        datasets=("zins_vergleich.csv",),
        fetch_mode="cbr_zcyc",
        description=(
            "Bank of Russia: 10-jährige OFZ-Rendite aus der Zero-Coupon-Yield-Curve, "
            "Monatsendwert (letzter Handelstag), in Prozent, ab 2015"
        ),
    ),
    Source(
        key="imf_fiskal",
        filename="imf_fiskal.csv",
        url=IMF_DATAMAPPER_URL.format(indicator=imf.WEO_SCHULDENQUOTE),
        title="Staatsfinanzen und Schulden: internationale Länder, jährlich",
        publisher=(
            "Internationaler Währungsfonds (IWF), World Economic Outlook und "
            "Public Finances in Modern History"
        ),
        license="IWF-Nutzungsbedingungen, Quellenangabe erforderlich",
        datasets=(
            "laender_schulden_jahr.csv",
            "laender_haushalt_jahr.csv",
            "laender_einkommen_jahr.csv",
        ),
        fetch_mode="imf_datamapper",
        api_series=",".join(IMF_INDICATORS),
        description=(
            "IWF DataMapper: Bruttoschulden des Gesamtstaats und BIP in Mrd. US-Dollar "
            "(WEO GGXWDG_NGDP, NGDPD), BIP je Einwohner:in (NGDPDPC), Bevölkerung in "
            "Mio. (LP) sowie Schuldenquote, Einnahmen und Zinsausgaben in Prozent des "
            "BIP aus der Datenbank Public Finances in Modern History (d, rev, ie). "
            "Alle Länder je Indikator in einer Datei; Einschränkung auf die in der App "
            "verwendeten Länder erfolgt im Datenaufbau."
        ),
    ),
    Source(
        key="ecb_eur_usd_jahr",
        filename="ecb_eur_usd_jahr.csv",
        url=ECB_SERIES_URL.format(dataset="EXR", key="A.USD.EUR.SP00.A", start="1995"),
        title="Wechselkurs US-Dollar/Euro, Jahresdurchschnitt",
        publisher="Europäische Zentralbank, Data Portal, Datensatz EXR",
        license="EZB, Quellenangabe erforderlich",
        datasets=(
            "laender_schulden_jahr.csv",
            "laender_haushalt_jahr.csv",
            "laender_einkommen_jahr.csv",
        ),
        description=(
            "EZB EXR A.USD.EUR.SP00.A: Referenzkurs des US-Dollars gegenüber dem Euro, "
            "Jahresdurchschnitt, für die Umrechnung der IWF- und Weltbank-Werte in Euro"
        ),
    ),
    Source(
        key="rosstat_cpi",
        filename="rosstat_cpi_monatlich.csv",
        url=EMISS_URL.format(indicator=ROSSTAT_CPI_INDICATOR),
        title="Verbraucherpreise: Russland, monatlich",
        publisher="Rosstat über EMISS; Rückgriff auf die Bank of Russia",
        license="Rosstat bzw. Bank of Russia, Quellenangabe erforderlich",
        datasets=("laender_inflation_monat.csv",),
        fetch_mode="emiss_api",
        api_series=str(ROSSTAT_CPI_INDICATOR),
        description=(
            "Rosstat/EMISS: Inflationsrate Russlands gegenüber dem Vorjahr, monatlich, "
            "in Prozent. Ohne API-Key oder bei nicht erreichbarer Schnittstelle wird "
            "die 12-Monats-Rate aus den saisonbereinigten Monatsraten der Bank of "
            "Russia verkettet (Näherung); die tatsächlich verwendete Reihe steht je "
            "Zeile in der Spalte quelle."
        ),
    ),
    Source(
        key="weltbank_bne_russland",
        filename="weltbank_bne_russland.json",
        url=WELTBANK_INDICATOR_URL.format(iso3="RUS", indicator="NY.GNP.PCAP.CD"),
        title="Bruttonationaleinkommen je Einwohner:in: Russland, jährlich",
        publisher="Weltbank, World Development Indicators, NY.GNP.PCAP.CD",
        license="CC BY 4.0",
        datasets=("laender_einkommen_jahr.csv",),
        description=(
            "Weltbank WDI NY.GNP.PCAP.CD: Bruttonationaleinkommen je Einwohner:in "
            "(Atlas-Methode, laufende US-Dollar), jährlich. Dient als Ersatzreihe für "
            "das verfügbare Einkommen Russlands, das nicht automatisch abrufbar ist."
        ),
    ),
    Source(
        key="eurostat_einkommen_laender",
        filename="eurostat_ilc_di03_laender.json",
        url=_eurostat(
            "ilc_di03",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            age="TOTAL",
            sex="T",
            statinfo="MEAN_EI",
            unit="EUR",
            sinceTimePeriod="1995",
        ),
        title="Verfügbares Einkommen je Einwohner:in: europäische Länder, jährlich",
        publisher="Eurostat, Datensatz ilc_di03",
        license="CC BY 4.0",
        datasets=("laender_einkommen_jahr.csv",),
        description=(
            "Eurostat ilc_di03: mittleres äquivalisiertes Nettoeinkommen der "
            "Bevölkerung (MEAN_EI), jährlich ab 1995, je Land in Euro"
        ),
    ),
    Source(
        key="eurostat_arbeitnehmerentgelt_laender",
        filename="eurostat_nama_10_lp_ulc_laender.json",
        url=_eurostat(
            "nama_10_lp_ulc",
            format="JSON",
            lang="EN",
            geo=[code for code, _ in laender.EUROPA_LAENDER],
            na_item="D1_SAL_PER",
            unit="EUR",
            sinceTimePeriod="1995",
        ),
        title="Arbeitnehmerentgelt je Arbeitnehmer:in: europäische Länder, jährlich",
        publisher="Eurostat, Datensatz nama_10_lp_ulc",
        license="CC BY 4.0",
        datasets=("laender_einkommen_jahr.csv",),
        description=(
            "Eurostat nama_10_lp_ulc: Arbeitnehmerentgelt je Arbeitnehmer:in "
            "(D1_SAL_PER), jährlich ab 1995, je Land in Euro"
        ),
    ),
    Source(
        key="fred_us_einkommen",
        filename="fred_us_einkommen.csv",
        url=FRED_SERIES_URL.format(series="A229RC0A052NBEA"),
        title="Verfügbares Einkommen je Einwohner:in: Vereinigte Staaten, jährlich",
        publisher="BEA über Federal Reserve Bank of St. Louis, Serie A229RC0A052NBEA",
        license="BEA-Nutzungsbedingungen, Quellenangabe erforderlich",
        datasets=("laender_einkommen_jahr.csv",),
        fetch_mode="fred_api",
        api_series="A229RC0A052NBEA",
        description=(
            "FRED A229RC0A052NBEA: Disposable Personal Income per Capita, laufende "
            "US-Dollar, jährlich"
        ),
    ),
    Source(
        key="fred_us_lohn",
        filename="fred_us_lohn.csv",
        url=FRED_SERIES_URL.format(series="CES0500000011"),
        title="Wochenverdienst: Vereinigte Staaten, monatlich",
        publisher="BLS über Federal Reserve Bank of St. Louis, Serie CES0500000011",
        license="BLS-Nutzungsbedingungen, Quellenangabe erforderlich",
        datasets=("laender_einkommen_jahr.csv",),
        fetch_mode="fred_api",
        api_series="CES0500000011",
        description=(
            "FRED CES0500000011: Average Weekly Earnings of All Employees, Total "
            "Private, laufende US-Dollar, monatlich; Jahreswert als Durchschnitt × 52"
        ),
    ),
    Source(
        key="fred_us_cpi",
        filename="fred_us_cpi.csv",
        url=FRED_SERIES_URL.format(series="CPIAUCSL"),
        title="Verbraucherpreisindex: Vereinigte Staaten, monatlich",
        publisher="BLS über Federal Reserve Bank of St. Louis, Serie CPIAUCSL",
        license="BLS-Nutzungsbedingungen, Quellenangabe erforderlich",
        datasets=("laender_inflation_monat.csv",),
        fetch_mode="fred_api",
        api_series="CPIAUCSL",
        description=(
            "FRED CPIAUCSL: Consumer Price Index for All Urban Consumers, alle Güter, "
            "saisonbereinigt, monatlich; Vorjahresrate in Prozent"
        ),
    ),
    Source(
        key="destatis_insolvenzen",
        filename="destatis_52411-0002_insolvenzen.csv",
        url=DESTATIS_TABLE_URL.format(code="52411-0002"),
        title="Insolvenzverfahren: Deutschland, Monate",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 52411-0002",
        license="DL-DE-BY-2.0",
        datasets=("insolvenzen_monat.csv",),
        description=(
            "Destatis 52411-0002: Beantragte Insolvenzverfahren und voraussichtliche "
            "Forderungen, Deutschland, Monate, Verfahrensstatus"
        ),
    ),
    Source(
        key="destatis_insolvenzen_unternehmen",
        filename="destatis_52411-0011_insolvenzen_unternehmen.csv",
        url=DESTATIS_TABLE_URL.format(code="52411-0011"),
        title="Insolvenzverfahren von Unternehmen: Deutschland, Monate",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 52411-0011",
        license="DL-DE-BY-2.0",
        datasets=("insolvenzen_monat.csv",),
        description=(
            "Destatis 52411-0011: Insolvenzverfahren von Unternehmen, voraussichtliche "
            "Forderungen und betroffene Arbeitnehmer, Deutschland, Monate, Rechtsformen"
        ),
    ),
    Source(
        key="destatis_insolvenzen_zeitreihe",
        filename="manual/stat_bundesamt_insolvenzen_52411-0017_de_Nov2026.csv",
        url="https://genesis.destatis.de/datenbank/online/table/52411-0017",
        title="Unternehmensinsolvenzen: Deutschland, Monate, Größenklassen (Langreihe)",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 52411-0017",
        license="DL-DE-BY-2.0",
        datasets=("insolvenzen_monat.csv",),
        fetch_mode="manual",
        description=(
            "Manueller Export aus GENESIS-Online, Tabelle 52411-0017: Beantragte "
            "Insolvenzverfahren von Unternehmen nach Unternehmensgrößenklassen, "
            "Deutschland, Monate 2003 bis 2026"
        ),
    ),
    Source(
        key="ecb_geldmenge",
        filename="ecb_geldmenge_m3.csv",
        url=ECB_SERIES_URL.format(
            dataset="BSI", key="M.U2.Y.V.M30.X.I.U2.2300.Z01.E", start="1995"
        ),
        title="Geldmenge M3: Euro-Raum, monatlich",
        publisher="Europäische Zentralbank, Data Portal, Datensatz BSI",
        license="EZB, Quellenangabe erforderlich",
        datasets=("geldmenge_monat.csv",),
        description=(
            "EZB BSI: Geldmenge M3, Index Dec10 = 100, arbeitstäglich und saisonbereinigt, "
            "Euro-Raum (veränderte Zusammensetzung), monatlich ab 1995"
        ),
    ),
    Source(
        key="ecb_hicp",
        filename="ecb_hicp_de_ea.csv",
        url=ECB_SERIES_URL.format(dataset="ICP", key="M.DE+U2.N.000000.4.ANR", start="1997"),
        title="Harmonisierter Verbraucherpreisindex: Deutschland und Euro-Raum",
        publisher="Europäische Zentralbank, Data Portal, Datensatz ICP",
        license="EZB, Quellenangabe erforderlich",
        datasets=("kaufkraft_monat.csv",),
        description=(
            "EZB ICP: HVPI-Gesamtindex, Veränderung gegenüber dem Vorjahr in Prozent, "
            "Deutschland und Euro-Raum, monatlich ab 1997"
        ),
    ),
    Source(
        key="destatis_strompreise",
        filename="destatis_61243-0002_strompreise.csv",
        url=DESTATIS_TABLE_URL.format(code="61243-0002"),
        title="Strompreise für Haushalte: Deutschland, Jahre",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 61243-0002",
        license="DL-DE-BY-2.0",
        datasets=("energiepreise_jahr.csv",),
        description=(
            "Destatis 61243-0002: Durchschnittspreise für Strom, Haushalte, Jahre, "
            "Jahresverbrauchsklassen und Preisbestandteile, EUR/kWh"
        ),
    ),
    Source(
        key="destatis_gaspreise",
        filename="destatis_61243-0011_gaspreise.csv",
        url=DESTATIS_TABLE_URL.format(code="61243-0011"),
        title="Erdgaspreise für Haushalte: Deutschland, Jahre",
        publisher="Statistisches Bundesamt (Destatis), GENESIS-Online 61243-0011",
        license="DL-DE-BY-2.0",
        datasets=("energiepreise_jahr.csv",),
        description=(
            "Destatis 61243-0011: Durchschnittspreise für Erdgas, Haushalte, Jahre, "
            "Jahresverbrauchsklassen und Preisbestandteile, EUR/kWh"
        ),
    ),
    Source(
        key="energy_charts_strompreis",
        filename="energy_charts_day_ahead.json",
        url=ENERGY_CHARTS_URL.format(start="JJJJ-MM-TT", end="JJJJ-MM-TT"),
        title="Börsenstrompreis Day-Ahead: Gebotszone Deutschland/Luxemburg",
        publisher="energy-charts.info (Fraunhofer ISE), Daten von Bundesnetzagentur | SMARD.de",
        license="CC BY 4.0",
        datasets=("strom_boerse_tag.csv",),
        fetch_mode="energy_charts",
        description=(
            "energy-charts.info: Day-Ahead-Preise der Gebotszone DE-LU, stündlich, "
            "EUR/MWh; die App bildet Tagesmittelwerte der letzten sieben Jahre"
        ),
    ),
    Source(
        key="oil_bulletin",
        filename="oil_bulletin_preise.xlsx",
        url=OIL_BULLETIN_URL,
        title="Wöchentliche Kraftstoffpreise in der EU",
        publisher="Europäische Kommission, Weekly Oil Bulletin, Preise mit Steuern",
        license="© Europäische Union, Quellenangabe erforderlich",
        datasets=("kraftstoffpreise.csv",),
        description=(
            "EU Weekly Oil Bulletin: Verbraucherpreise für Superbenzin (Euro 95) und "
            "Diesel je Land, wöchentlich, mit Steuern, in EUR je 1000 Liter"
        ),
    ),
    Source(
        key="big_mac",
        filename="big_mac_index.csv",
        url=BIG_MAC_URL,
        title="Big-Mac-Index: Preise und Abweichungen je Land",
        publisher="The Economist, big-mac-data",
        license="The Economist, Quellenangabe erforderlich",
        datasets=("big_mac.csv",),
        description=(
            "The Economist: Big-Mac-Index, Preis eines Big Mac in US-Dollar und "
            "Abweichung vom US-Preis, halbjährlich je Land"
        ),
    ),
    Source(
        key="eurostat_eigentumsquote",
        filename="eurostat_ilc_lvho02.json",
        url=_eurostat(
            "ilc_lvho02",
            format="JSON",
            lang="EN",
            unit="PC",
            rskpovth="TOTAL",
            hhcomp="TOTAL",
            tenure=("OWN", "RENT"),
            sinceTimePeriod="2010",
            geo=(
                "DE",
                "FR",
                "IT",
                "ES",
                "NL",
                "AT",
                "PL",
                "SE",
                "DK",
                "FI",
                "EU27_2020",
            ),
        ),
        title="Eigentums- und Mietquote der Haushalte: Europa, jährlich",
        publisher="Eurostat, Datensatz ilc_lvho02",
        license="CC BY 4.0",
        datasets=("eigentumsquote.csv",),
        description=(
            "Eurostat ilc_lvho02: Verteilung der Bevölkerung nach Wohnstatus "
            "(Eigentum, Miete), Anteile in Prozent, ausgewählte EU-Länder und EU-27"
        ),
    ),
    Source(
        key="bmf_zinsausgaben",
        filename="bmf_zinsausgaben_kreditmarkt.csv",
        url=BMF_INTEREST_URL,
        title="Zinsausgaben des Bundes am Kreditmarkt",
        publisher="Bundesministerium der Finanzen, Bundeshaushalt",
        license="© Bundesministerium der Finanzen, Quellenangabe erforderlich",
        datasets=("bund_zinsausgaben.csv",),
        description=(
            "BMF: Zinsausgaben am Kreditmarkt in Mrd. EUR je Haushaltsjahr "
            "(Ist, Soll und Regierungsentwurf)"
        ),
    ),
)

# Portale und API-Dokumentation der Anbieter – erscheint als "Quellen & Links"
# auf der Quellenseite.
PROVIDER_LINKS: tuple[dict[str, str], ...] = (
    {
        "anbieter": "Statistisches Bundesamt (Destatis)",
        "daten": "Insolvenzverfahren, Preise für Strom und Gas",
        "portal": "https://www-genesis.destatis.de/datenbank/online",
        "api": "https://genesis.destatis.de/genesisWS/rest/2020",
        "zugang": "kostenlos, API-Token nach Registrierung",
    },
    {
        "anbieter": "Eurostat",
        "daten": "Haushalte, Schuldenquote, Zinsvergleich, Eigentumsquote",
        "portal": "https://ec.europa.eu/eurostat/databrowser/",
        "api": (
            "https://ec.europa.eu/eurostat/web/user-guides/data-browser/"
            "api-data-access/api-introduction"
        ),
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "Deutsche Bundesbank",
        "daten": "Rendite der 10-jährigen Bundesanleihe",
        "portal": "https://www.bundesbank.de/de/statistiken",
        "api": "https://api.statistiken.bundesbank.de/",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "FRED (Federal Reserve Bank of St. Louis)",
        "daten": "US-Staatsanleiherendite",
        "portal": "https://fred.stlouisfed.org/",
        "api": "https://fred.stlouisfed.org/docs/api/fred/",
        "zugang": "kostenlos, API-Key erforderlich",
    },
    {
        "anbieter": "EZB – Data Portal",
        "daten": "Geldmenge M3, Harmonisierter Verbraucherpreisindex",
        "portal": "https://data.ecb.europa.eu/",
        "api": "https://data.ecb.europa.eu/help/api/overview",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "Bank of Russia",
        "daten": "Rendite russischer Staatsanleihen (OFZ), Preisdynamik",
        "portal": "https://www.cbr.ru/eng/",
        "api": "https://www.cbr.ru/eng/hd_base/zcyc_params/",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "Internationaler Währungsfonds (IWF)",
        "daten": "Schuldenquote, Einnahmen, Zinsausgaben, BIP und Bevölkerung",
        "portal": "https://www.imf.org/en/Data",
        "api": "https://www.imf.org/external/datamapper/api/help",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "Rosstat über EMISS",
        "daten": "Verbraucherpreise Russlands",
        "portal": "https://rosstat.gov.ru/statistics/price",
        "api": "https://fedstat.ru/",
        "zugang": "kostenlos, API-Key nach Registrierung",
    },
    {
        "anbieter": "Weltbank – World Development Indicators",
        "daten": "Bruttonationaleinkommen je Einwohner:in",
        "portal": "https://data.worldbank.org/",
        "api": "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "energy-charts.info (Fraunhofer ISE)",
        "daten": "Day-Ahead-Strompreise",
        "portal": "https://energy-charts.info/",
        "api": "https://api.energy-charts.info/",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "Europäische Kommission – Weekly Oil Bulletin",
        "daten": "Kraftstoffpreise",
        "portal": "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en",
        "api": "",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "The Economist – Big Mac Index",
        "daten": "Kaufkraftvergleich über Burger-Preise",
        "portal": "https://github.com/TheEconomist/big-mac-data",
        "api": "",
        "zugang": "kostenlos, ohne API-Key",
    },
    {
        "anbieter": "Bundesministerium der Finanzen",
        "daten": "Zinsausgaben des Bundes am Kreditmarkt",
        "portal": "https://www.bundeshaushalt.de/",
        "api": "",
        "zugang": "kostenlos, ohne API-Key",
    },
)


def _read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise RuntimeError(f"Leere Antwort für {url}")
    return payload


def _fetch_cbr_zcyc(source: Source) -> bytes:
    """Sammelt Monatsendwerte der 10-jährigen OFZ-Rendite und schreibt sie als CSV."""
    today = datetime.now(UTC).date()
    start = date(max(CBR_START_YEAR, today.year - 10), 1, 1)
    rows: list[tuple[str, str]] = []
    for month_end in cbr.month_ends(start, today):
        for offset in range(CBR_MAX_FALLBACK_DAYS):
            day = month_end - timedelta(days=offset)
            if day < start:
                break
            html = _read_url(CBR_ZCYC_URL.format(datum=day.strftime("%d.%m.%Y")))
            value = cbr.parse_ten_year_yield(html.decode("utf-8", errors="replace"))
            if value is not None:
                rows.append((day.isoformat(), f"{value:.2f}"))
                break
    if not rows:
        raise RuntimeError(f"Keine Zinsdaten für {source.url} gefunden")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["datum", "rendite_pct"])
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _fetch_energy_charts(source: Source) -> bytes:
    today = datetime.now(UTC).date()
    start = date(max(today.year - 7, 2019), 1, 1)
    return _read_url(ENERGY_CHARTS_URL.format(start=start.isoformat(), end=today.isoformat()))


def _fetch_fred_api(source: Source) -> bytes:
    """Lädt eine FRED-Serie über die API; ohne Schlüssel den öffentlichen CSV-Export."""
    series = source.api_series or ""
    try:
        client = fred_api.FredApi.from_env()
    except fred_api.FredApiError:
        return _read_url(source.url)
    observations = client.series_observations(series)
    if not observations:
        raise RuntimeError(f"FRED liefert keine Beobachtungen für {series}")
    lines = [f"observation_date,{series}"]
    lines.extend(f"{item.get('date', '')},{item.get('value', '')}" for item in observations)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _csv_bytes(frame: pd.DataFrame, float_format: str = "%.4f") -> bytes:
    buffer = io.StringIO()
    frame.to_csv(buffer, index=False, float_format=float_format)
    return buffer.getvalue().encode("utf-8")


def _fetch_imf_datamapper(source: Source) -> bytes:
    """Sammelt mehrere IWF-Indikatoren in einer langen CSV-Datei."""
    indicators = [item.strip() for item in (source.api_series or "").split(",") if item.strip()]
    if not indicators:
        raise RuntimeError(f"Keine IWF-Indikatoren für {source.key} hinterlegt")
    frames = [
        imf.parse_datamapper(_read_url(IMF_DATAMAPPER_URL.format(indicator=indicator)), indicator)
        for indicator in indicators
    ]
    return _csv_bytes(pd.concat(frames, ignore_index=True), float_format="%.6f")


def _fetch_emiss_api(source: Source) -> bytes:
    """Lädt Rosstat-Daten über EMISS; ohne Key den Preisdynamik-Export der Notenbank."""
    key = config.get_secret("ROSSTAT_API_KEY")
    if key:
        request = urllib.request.Request(
            source.url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/csv", "X-API-KEY": key},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                frame = rosstat.parse_emiss_csv(response.read())
            frame["quelle"] = "Rosstat (EMISS)"
            return _csv_bytes(frame, float_format="%.4f")
        except (urllib.error.URLError, OSError, ValueError):
            pass

    frame = rosstat.parse_cbr_cpi(_read_url(CBR_CPI_XLSX_URL))
    frame["quelle"] = "Bank of Russia (12-Monats-Rate aus saisonbereinigten Monatsraten)"
    return _csv_bytes(frame, float_format="%.4f")


def _fetch(source: Source) -> bytes:
    if source.fetch_mode == "cbr_zcyc":
        return _fetch_cbr_zcyc(source)
    if source.fetch_mode == "energy_charts":
        return _fetch_energy_charts(source)
    if source.fetch_mode == "fred_api":
        return _fetch_fred_api(source)
    if source.fetch_mode == "imf_datamapper":
        return _fetch_imf_datamapper(source)
    if source.fetch_mode == "emiss_api":
        return _fetch_emiss_api(source)
    return _read_url(source.url)


def download(source: Source, target_dir: Path, *, refresh: bool = False) -> Path:
    """Lädt eine Quelle herunter und legt sie in ``target_dir`` ab.

    Existierende Dateien werden nur mit ``refresh=True`` erneut geladen.
    """
    target = target_dir / source.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.fetch_mode == "manual":
        if target.exists():
            return target
        raise RuntimeError(
            f"{source.filename} fehlt. Bitte die Tabelle unter {source.url} als CSV "
            "exportieren und unter diesem Dateinamen in data/raw/ ablegen."
        )
    if target.exists() and not refresh:
        return target

    target.write_bytes(_fetch(source))
    return target


def read_library(path: Path = paths.SOURCES_FILE) -> dict:
    """Liest die Quellenbibliothek; fehlt sie, wird eine leere Struktur geliefert."""
    if not path.exists():
        return {"schema_version": 1, "quellen": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _source_entry(source: Source, path: Path, digest: str, retrieved_at: str) -> dict[str, object]:
    return {
        "key": source.key,
        "titel": source.title,
        "herausgeber": source.publisher,
        "lizenz": source.license,
        "url": source.url,
        "beschreibung": source.description,
        "datei": source.filename,
        "datensaetze": list(source.datasets),
        "abgerufen_am": retrieved_at,
        "sha256": digest,
        "bytes": path.stat().st_size,
    }


def download_all(
    target_dir: Path,
    *,
    refresh: bool = False,
    sources: Sequence[Source] = SOURCES,
    library_file: Path = paths.SOURCES_FILE,
) -> list[Path]:
    """Lädt alle Quellen, schreibt die Rohdaten und aktualisiert die Quellenbibliothek."""
    previous = {entry["key"]: entry for entry in read_library(library_file)["quellen"]}
    paths_written = []
    entries = []

    for source in sources:
        target = target_dir / source.filename
        existed = target.exists()
        path = download(source, target_dir, refresh=refresh)
        paths_written.append(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        known = previous.get(source.key, {})
        if known.get("sha256") == digest and known.get("abgerufen_am"):
            retrieved_at = str(known["abgerufen_am"])
        elif source.fetch_mode == "manual" or (existed and not refresh):
            retrieved_at = datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(
                timespec="seconds"
            )
        else:
            retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")

        entries.append(_source_entry(source, path, digest, retrieved_at))

    library = {
        "schema_version": 1,
        "aktualisiert_am": datetime.now(UTC).isoformat(timespec="seconds"),
        "hinweis": (
            "Automatisch erzeugt von haushaltssimulator.sources – nicht manuell bearbeiten."
        ),
        "quellen": entries,
        "anbieter": [dict(eintrag) for eintrag in PROVIDER_LINKS],
    }
    library_file.parent.mkdir(parents=True, exist_ok=True)
    library_file.write_text(
        json.dumps(library, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return paths_written
