"""Tests für die Parser der Wirtschafts- und Preisindikatoren."""

from __future__ import annotations

import io
from datetime import datetime

import openpyxl
import pandas as pd
import pytest

from haushaltssimulator import bigmac, bmf, destatis, ecb, oil

FIXED_TABLE = """Tabelle: 52411-0002
Deutschland, Monate, Beantragte Verfahren;;;
;;Insolvenzverfahren;Forderungen
;;Anzahl;Tsd. EUR
2026;Januar;Insgesamt;10494;3913424
2026;Januar;eröffnet;9418;3611659
2026;Februar;Insgesamt;10439;3178273
__________
© Statistisches Bundesamt (Destatis), 2026
"""

FLAGGED_TABLE = """Tabelle: 52411-0017
Insolvenzverfahren (Unternehmen): Deutschland, Monate;;;;;;
;;;Beantragte Verfahren;Beantragte Verfahren
;;;eröffnet;eröffnet
2003;Januar;Insgesamt;1892;e;1353;e;x;;3245;e
2003;Februar;Insgesamt;1790;e;1316;e;x;;3106;e
2003;Januar;1 Arbeitnehmer;197;e;193;e;x;;390;e
"""

ECB_CSV = b"""KEY,FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE
ICP.M.DE.N.000000.4.ANR,M,DE,2024-01,2.9
ICP.M.DE.N.000000.4.ANR,M,DE,2024-02,2.6
ICP.M.U2.N.000000.4.ANR,M,U2,2024-01,2.8
ICP.M.U2.N.000000.4.ANR,M,U2,2024-02,2.5
"""

BMF_CSV = "Jahr;Zinsausgaben\r\n2022 (Ist);15,34\r\n2026 (Soll);30,28\r\n2027 (RegE);41,88\r\n"

BIG_MAC_CSV = (
    "date,iso_a3,currency_code,name,local_price,dollar_ex,dollar_price,USD_raw\n"
    "2024-01-01,DEU,EUR,Germany,5.0,0.92,5.43,0.05\n"
    "2024-01-01,USA,USD,United States,5.69,1,5.69,0.0\n"
)

YEAR_TABLE = (
    "Tabelle: 81000-0025\n"
    "VGR des Bundes - Bruttoanlageinvestitionen;;;;;;;;;;;;\n"
    "Deutschland, Jahre;;;;;;;;;;;;\n"
    ";;;2023;2024\n"
    "in jeweiligen Preisen (Mrd. EUR);Bruttoanlageinvestitionen des Staates;jew. ME;"
    "122,802;139,707\n"
    "in jeweiligen Preisen (Mrd. EUR);"
    "Bruttoanlageinvestitionen der nichtstaatl.Sektoren;jew. ME;775,246;758,566\n"
    "preisbereinigt, Kettenindex (2020=100);"
    "Bruttoanlageinvestitionen des Staates;jew. ME;95,910;106,460\n"
    "__________\n"
    "© Statistisches Bundesamt (Destatis), 2026\n"
)

PRODUCTION_TABLE = (
    "Tabelle: 42153-0001\n"
    "Produktionsindex für das Verarbeitende Gewerbe:;;;;;;;\n"
    "Deutschland, Monate, Original- und bereinigte Daten,;;;;;;;\n"
    ";;;Original- und bereinigte Daten;Original- und bereinigte Daten;"
    "Original- und bereinigte Daten;Original- und bereinigte Daten;"
    "Original- und bereinigte Daten\n"
    ";;;Originalwerte;X13 JDemetra+  kalenderbereinigt;"
    "X13 JDemetra+  kalender- und saisonbereinigt;"
    "BV4.1 kalender- und saisonbereinigt;BV4.1 Trend\n"
    "Produzierendes Gewerbe;2026;Januar;80,0;81,6;91,3;-;91,5\n"
    "Verarbeitendes Gewerbe;2026;Januar;82,5;84,2;91,8;-;92,1\n"
    "Verarbeitendes Gewerbe;2026;Februar;88,4;89,3;91,9;-;92,0\n"
    "__________\n"
    "© Statistisches Bundesamt (Destatis), 2026\n"
)


def test_parse_fixed_columns_reads_label_and_value_columns() -> None:
    frame = destatis.parse_fixed_columns(
        FIXED_TABLE,
        ["jahr", "monat", "status"],
        ["verfahren", "forderungen_tsd_eur"],
    )
    assert len(frame) == 3
    gesamt = frame[frame["status"] == "Insgesamt"].iloc[0]
    assert gesamt["jahr"] == "2026"
    assert gesamt["verfahren"] == 10494
    assert gesamt["forderungen_tsd_eur"] == 3913424


def test_parse_flagged_columns_skips_status_columns() -> None:
    frame = destatis.parse_flagged_columns(
        FLAGGED_TABLE,
        ["jahr", "monat", "klasse"],
        ["eroeffnet", "abgewiesen", "plan", "insgesamt"],
    )
    assert len(frame) == 3
    erste = frame.iloc[0]
    assert erste["eroeffnet"] == 1892
    assert erste["abgewiesen"] == 1353
    assert erste["insgesamt"] == 3245
    assert pd.isna(erste["plan"])


def test_parse_year_columns_reads_years_from_header() -> None:
    frame = destatis.parse_year_columns(
        YEAR_TABLE, ["preisbasis", "aggregat", "einheit"]
    )
    assert set(frame["jahr"]) == {2023, 2024}
    staat = frame[
        (frame["preisbasis"] == "in jeweiligen Preisen (Mrd. EUR)")
        & (frame["aggregat"] == "Bruttoanlageinvestitionen des Staates")
    ].set_index("jahr")
    assert staat.loc[2023, "wert"] == pytest.approx(122.802)
    assert staat.loc[2024, "wert"] == pytest.approx(139.707)
    assert len(frame) == 6


def test_parse_fixed_columns_reads_year_after_label() -> None:
    frame = destatis.parse_fixed_columns(
        PRODUCTION_TABLE,
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
    assert len(frame) == 3
    erste = frame.iloc[0]
    assert erste["wirtschaftszweig"] == "Produzierendes Gewerbe"
    assert erste["jahr"] == "2026"
    assert erste["index_2021_original"] == 80.0
    assert erste["index_2021_saisonbereinigt"] == 91.3
    assert pd.isna(erste["index_2021_bv4_saisonbereinigt"])


def test_ecb_parser_keeps_area_and_month() -> None:
    frame = ecb.parse_csv(ECB_CSV)
    assert list(frame.columns) == ["gebiet", "monat", "wert"]
    assert frame[frame["gebiet"] == "DE"]["wert"].tolist() == [2.9, 2.6]
    assert frame["monat"].max() == "2024-02"


def test_bmf_parser_extracts_year_and_type() -> None:
    frame = bmf.parse_interest_csv(BMF_CSV.encode("utf-8"))
    assert frame["jahr"].tolist() == [2022, 2026, 2027]
    assert frame["art"].tolist() == ["Ist", "Soll", "RegE"]
    assert frame.loc[0, "zinsausgaben_mrd_eur"] == pytest.approx(15.34)


def test_big_mac_parser_scales_deviation() -> None:
    frame = bigmac.parse_index(BIG_MAC_CSV.encode("utf-8"))
    assert set(frame.columns) == {"datum", "iso3", "preis_usd", "abweichung_pct"}
    deutschland = frame[frame["iso3"] == "DEU"].iloc[0]
    assert deutschland["preis_usd"] == pytest.approx(5.43)
    assert deutschland["abweichung_pct"] == pytest.approx(5.0)


def _oil_fixture() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Prices with taxes"
    sheet.append(
        [
            "Consumer prices of petroleum products inclusive of duties and taxes",
            "CTR",
            "DE_price_with_tax_euro95",
            "DE_price_with_tax_diesel",
        ]
    )
    sheet.append([None, None, "Euro-super 95 (I)", "Diesel"])
    sheet.append([None, None, "1000 l", "1000 l"])
    sheet.append(["Date", None, "1000 l", "1000 l"])
    sheet.append([datetime(2026, 1, 5), "DE_", 1800.0, 1700.0])
    sheet.append([datetime(2026, 1, 12), "DE_", 1850.0, 1750.0])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_oil_parser_converts_to_euro_per_litre() -> None:
    frame = oil.parse_prices(_oil_fixture())
    assert len(frame) == 4
    assert set(frame["produkt"]) == {"Superbenzin (Euro 95)", "Diesel"}
    erster_tag = pd.Timestamp("2026-01-05").date()
    diesel = frame[(frame["produkt"] == "Diesel") & (frame["datum"] == erster_tag)]
    assert diesel.iloc[0]["preis_eur_l"] == pytest.approx(1.7)


def test_oil_parser_filters_dates() -> None:
    frame = oil.parse_prices(_oil_fixture(), since=datetime(2026, 1, 10).date())
    assert frame["datum"].min() == pd.Timestamp("2026-01-12").date()


def _heating_oil_fixture() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Prices with taxes"
    sheet.append(
        [
            "Consumer prices of petroleum products inclusive of duties and taxes",
            "CTR",
            "DE_price_with_tax_heating_oil",
            "EU_price_with_tax_heating_oil",
        ]
    )
    sheet.append([None, None, "Heizöl (II)", "Heizöl (II)"])
    sheet.append([None, None, "1000 l", "1000 l"])
    sheet.append(["Date", None, "1000 l", "1000 l"])
    sheet.append([datetime(2026, 1, 5), "DE_", 1800.0, 1900.0])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_oil_parser_supports_heating_oil() -> None:
    frame = oil.parse_prices(_heating_oil_fixture(), produkte={"heating_oil": "Heizöl"})
    assert set(frame["produkt"]) == {"Heizöl"}
    assert set(frame["land_code"]) == {"DE", "EU"}
    deutschland = frame[frame["land_code"] == "DE"].iloc[0]
    assert deutschland["preis_eur_l"] == pytest.approx(1.8)


ECB_DAILY_CSV = b"""KEY,TIME_PERIOD,OBS_VALUE
EXR.D.USD.EUR.SP00.A,2024-01-02,1.0950
EXR.D.USD.EUR.SP00.A,2024-01-03,1.0921
"""


def test_ecb_daily_parser_keeps_dates() -> None:
    frame = ecb.parse_exr_daily_csv(ECB_DAILY_CSV)
    assert list(frame.columns) == ["datum", "usd_je_eur"]
    assert frame.iloc[0]["datum"] == pd.Timestamp("2024-01-02")
    assert frame["usd_je_eur"].tolist() == [1.095, 1.0921]


def test_parse_fixed_columns_fills_year_down() -> None:
    raw = (
        ";;Verbraucherpreisindex;Veränderung zum Vorjahresmonat;Veränderung zum Vormonat\n"
        "1992;Januar;63,8;+5,6;+0,9\n"
        ";Februar;64,2;+5,8;+0,6\n"
        "1993;Januar;66,6;+4,4;+1,1\n"
    )
    frame = destatis.parse_fixed_columns(
        raw, ["jahr", "monat_name"], ["index", "vj_pct", "vm_pct"], fill_down=("jahr",)
    )
    assert frame["jahr"].tolist() == ["1992", "1992", "1993"]
    assert frame["vj_pct"].tolist() == [5.6, 5.8, 4.4]
    ohne = destatis.parse_fixed_columns(raw, ["jahr", "monat_name"], ["index", "vj", "vm"])
    assert len(ohne) == 2
