"""Tests für die Parser der IWF-, Weltbank-, Rosstat- und EZB-Reihen."""

from __future__ import annotations

import io
import json
from datetime import datetime

import openpyxl
import pytest

from haushaltssimulator import ecb, imf, rosstat, weltbank

DATAMAPPER = {
    "values": {
        "GGXWDG_NGDP": {
            "DEU": {"2022": 66.1, "2023": 62.9, "2024": 62.5},
            "RUS": {"2022": 18.5, "2023": 19.5},
            "USA": {"2022": 119.1, "2023": None},
        }
    }
}


def test_datamapper_liefert_lange_reihe() -> None:
    frame = imf.parse_datamapper(json.dumps(DATAMAPPER), "GGXWDG_NGDP")
    assert list(frame.columns) == ["indikator", "iso3", "jahr", "wert"]
    assert len(frame) == 6
    assert frame["jahr"].max() == 2024
    assert "USA" in set(frame["iso3"])


def test_datamapper_meldet_fehlenden_indikator() -> None:
    try:
        imf.parse_datamapper(json.dumps(DATAMAPPER), "unbekannt")
    except ValueError as fehler:
        assert "unbekannt" in str(fehler)
    else:  # pragma: no cover - Sicherheitsnetz
        raise AssertionError("Fehlender Indikator wurde nicht erkannt")


def test_weltbank_liest_jahreswerte() -> None:
    antwort = [
        {"page": 1},
        [
            {
                "countryiso3code": "RUS",
                "date": "2024",
                "value": 14250.0,
            },
            {
                "countryiso3code": "RUS",
                "date": "2023",
                "value": None,
            },
        ],
    ]
    frame = weltbank.parse_indicator_json(json.dumps(antwort), "NY.GNP.PCAP.CD")
    assert frame["jahr"].tolist() == [2024]
    assert frame["wert"].tolist() == [14250.0]


def test_emiss_liest_perioden_und_dezimalkomma() -> None:
    roh = "Период;Значение\n01.2024;7,4\n02.2024;7,6\n".encode("cp1251")
    frame = rosstat.parse_emiss_csv(roh)
    assert frame["monat"].tolist() == ["2024-01", "2024-02"]
    assert frame["inflation_pct"].tolist() == [7.4, 7.6]


def test_cbr_verkettet_monatsraten_zu_zwoelfmonatsrate() -> None:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    monate = [datetime(2024 + (index // 12), index % 12 + 1, 1) for index in range(13)]
    worksheet.append(["Titel", *monate])
    worksheet.append(["Consumer goods and services", *([1.0] * len(monate))])
    puffer = io.BytesIO()
    workbook.save(puffer)

    frame = rosstat.parse_cbr_cpi(puffer.getvalue())
    letzte = frame.iloc[-1]
    assert letzte["monat"] == "2025-01"
    assert letzte["inflation_pct"] == pytest.approx((1.01**12 - 1) * 100, rel=1e-6)


def test_ezb_liest_jahreswechselkurs() -> None:
    roh = (
        b"KEY,FREQ,TIME_PERIOD,OBS_VALUE\n"
        b"EXR,A,2023,1.0813\n"
        b"EXR,A,2024,1.0824\n"
    )
    frame = ecb.parse_exr_csv(roh)
    assert frame["jahr"].tolist() == [2023, 2024]
    assert frame["wert"].tolist() == [1.0813, 1.0824]
