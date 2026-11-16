"""Tests für den Destatis-Parser."""

from __future__ import annotations

import pandas as pd
import pytest

from haushaltssimulator import destatis

SAMPLE = """Tabelle: 71311-9999
Schulden beim nicht-öffentlichen Bereich (Mill. EUR);;;;
;;;Stichtag zum Quartalsende;Stichtag zum Quartalsende
;;;31.03.2024;30.06.2024
Bund;Kernhaushalt;Wertpapierschulden;1500862;1500033
Bund;Kernhaushalt;Kassenkredite beim nicht-öffentlichen Bereich;30.214;-
__________
© Statistisches Bundesamt (Destatis), 2026
"""


def test_parse_table_long_format() -> None:
    frame = destatis.parse_table(SAMPLE, ["ebene", "haushalt", "schuldenart"])
    assert list(frame.columns) == [
        "ebene",
        "haushalt",
        "schuldenart",
        "stichtag",
        "wert",
        "einheit",
    ]
    assert len(frame) == 4
    assert set(frame["einheit"]) == {"Mill. EUR"}

    first_quarter = frame[frame["stichtag"] == pd.Timestamp("2024-03-31").date()]
    assert first_quarter["wert"].tolist() == [1500862.0, 30214.0]


def test_parse_number_handles_german_separators_and_missing() -> None:
    assert destatis.parse_number("1.234,5") == 1234.5
    assert destatis.parse_number("1500862") == 1500862.0
    assert pd.isna(destatis.parse_number("-"))
    assert pd.isna(destatis.parse_number("..."))


def test_parse_table_rejects_wrong_label_count() -> None:
    with pytest.raises(ValueError, match="Merkmalsspalten"):
        destatis.parse_table(SAMPLE, ["ebene", "haushalt"])


def test_decode_falls_back_to_cp1252() -> None:
    text = destatis.decode("Schulden öffentlicher Haushalte".encode("cp1252"))
    assert text == "Schulden öffentlicher Haushalte"
    assert destatis.decode("Schulden öffentlicher".encode()) == "Schulden öffentlicher"
