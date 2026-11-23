"""Tests für den Berichtsexport (Reveal.js-HTML aus Bausteinen)."""

from __future__ import annotations

import re
from datetime import date

import plotly.graph_objects as go
import pytest

from haushaltssimulator import bausteine, bericht, dataset, paths
from haushaltssimulator.bericht import BerichtKonfiguration, Eintrag

DATEN_DA = (paths.PROCESSED_DIR / dataset.ANNUAL_DEBT).exists()
ALLE = list(bausteine.SEITEN["insolvenzen"].baustein_ids())


def test_configuration_roundtrip_and_unknown_ids() -> None:
    konfiguration = BerichtKonfiguration(
        titel="Test",
        format="hoch",
        eintraege=[Eintrag("insolvenzen.langreihe", {"mittel_monate": 6})],
    )
    zurueck, unbekannt = BerichtKonfiguration.aus_json(konfiguration.als_json())
    assert zurueck == konfiguration
    assert unbekannt == []

    daten = konfiguration.als_dict()
    daten["eintraege"].append({"id": "gibt.es_nicht"})
    daten["format"] = "rund"
    daten["eintraege"][0]["parameter"]["mittel_monate"] = 999
    gelesen, unbekannt = BerichtKonfiguration.aus_dict(daten)
    assert unbekannt == ["gibt.es_nicht"]
    assert gelesen.format == "quer"
    assert gelesen.eintraege[0].parameter == {"mittel_monate": 36}


def test_markdown_subset() -> None:
    assert bericht.markdown_zu_html("a **b** <c>") == "<p>a <b>b</b> &lt;c&gt;</p>"
    assert bericht.markdown_zu_html("* x\n* y") == "<ul><li>x</li><li>y</li></ul>"


def test_slide_layout_does_not_change_original_figure() -> None:
    figur = go.Figure(go.Scatter(y=[1, 2]))
    folie = bericht.folienlayout(figur, bericht.FORMATE["hoch"])
    assert folie.layout.width == 960
    assert folie.layout.font.size >= 30
    assert figur.layout.width is None


def test_file_name_is_ascii() -> None:
    konfiguration = BerichtKonfiguration(titel="Zinsen & Schulden – Übersicht")
    assert bericht.dateiname(konfiguration, date(2026, 11, 22)) == (
        "zinsen_schulden_uebersicht_2026-11-22.html"
    )


@pytest.mark.skipif(not DATEN_DA, reason="Aufbereitete Daten fehlen")
@pytest.mark.parametrize("format_", list(bericht.FORMATE))
def test_report_has_title_content_and_source_slides(format_: str) -> None:
    konfiguration = BerichtKonfiguration(
        titel="Insolvenzen <Test>",
        format=format_,
        text="methodik",
        eintraege=[Eintrag(bid) for bid in ALLE],
    )
    text = bericht.erzeuge_bericht(konfiguration, stand=date(2026, 11, 22))
    assert text.startswith("<!doctype html>")
    assert len(re.findall(r"<section\b", text)) == len(ALLE) + 2
    assert re.findall(r'data-baustein="([^"]+)"', text) == ALLE
    assert "Insolvenzen &lt;Test&gt;" in text
    assert "<h2>Quellen</h2>" in text and "DL-DE-BY-2.0" in text
    assert f"width: {bericht.FORMATE[format_].breite}" in text
    assert text.count('class="diagramm plot"') == sum(
        bausteine.hole(bid).art == bausteine.Art.DIAGRAMM for bid in ALLE
    )
    assert "cdn.plot.ly" in text


@pytest.mark.skipif(not DATEN_DA, reason="Aufbereitete Daten fehlen")
def test_report_respects_frozen_parameters_and_options() -> None:
    konfiguration = BerichtKonfiguration(
        text="kernaussage",
        quellenfolie=False,
        eintraege=[Eintrag("insolvenzen.langreihe", {"mittel_monate": 6})],
    )
    text = bericht.erzeuge_bericht(konfiguration)
    assert "6-Monats-Mittel" in text
    assert "Einstellung: Gleitendes Mittel (Monate): 6" in text
    assert "<h2>Quellen</h2>" not in text
    assert "Methodik:" not in text


@pytest.mark.skipif(not DATEN_DA, reason="Aufbereitete Daten fehlen")
def test_static_report_falls_back_to_interactive(monkeypatch) -> None:
    def ohne_kaleido(*args, **kwargs):
        raise RuntimeError("Chrome fehlt")

    monkeypatch.setattr(go.Figure, "to_image", ohne_kaleido)
    konfiguration = BerichtKonfiguration(
        diagramme="statisch", eintraege=[Eintrag("insolvenzen.langreihe")]
    )
    text = bericht.erzeuge_bericht(konfiguration)
    assert 'class="diagramm plot"' in text
