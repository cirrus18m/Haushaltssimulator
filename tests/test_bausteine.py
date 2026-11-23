"""Tests für die Bausteine: Registry, Quellen, Parameter und Erzeugung."""

from __future__ import annotations

import pandas as pd
import pytest

from haushaltssimulator import bausteine, dataset, paths, sources
from haushaltssimulator.bausteine import Art, Diagramm, Ebene, Kennzahl, Parameter
from haushaltssimulator.format import format_number, format_signed

DATEN_DA = (paths.PROCESSED_DIR / dataset.ANNUAL_DEBT).exists()


def test_registry_has_pilot_page() -> None:
    seite = bausteine.SEITEN["insolvenzen"]
    assert seite.baustein_ids()
    assert all(bid in bausteine.REGISTRY for bid in seite.baustein_ids())


@pytest.mark.parametrize("baustein", bausteine.REGISTRY.values(), ids=lambda b: b.id)
def test_baustein_is_complete(baustein: bausteine.Baustein) -> None:
    assert baustein.id.count(".") == 1, "IDs haben die Form <thema>.<name>"
    assert baustein.titel
    assert baustein.quellen, "Jeder Baustein nennt mindestens eine Quelle"
    bekannte = {quelle.key for quelle in sources.SOURCES}
    assert set(baustein.quellen) <= bekannte, set(baustein.quellen) - bekannte
    if baustein.ebene == Ebene.EINFACH and baustein.art != Art.TEXT:
        assert baustein.kernaussage, "Bausteine der einfachen Ansicht brauchen eine Kernaussage"


def test_every_baustein_belongs_to_a_page() -> None:
    auf_seiten = {bid for seite in bausteine.SEITEN.values() for bid in seite.baustein_ids()}
    assert set(bausteine.REGISTRY) == auf_seiten


def test_duplicate_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="doppelt"):
        bausteine.baustein(
            id="insolvenzen.langreihe",
            titel="x",
            art=Art.TEXT,
            ebene=Ebene.EXPERTE,
            quellen=("destatis_insolvenzen",),
        )(lambda k: "")


def test_parameter_values_are_validated() -> None:
    parameter = Parameter("n", "N", "ganzzahl", 12, minimum=3, maximum=36)
    assert parameter.pruefe(100) == 36
    assert parameter.pruefe("x") == 12
    auswahl = Parameter("land", "Land", "auswahl", "DE", optionen=("DE", "FR"))
    assert auswahl.pruefe("IT") == "DE"
    baustein = bausteine.hole("insolvenzen.langreihe")
    assert baustein.parameterwerte() == {"mittel_monate": 12}
    assert baustein.parameterwerte({"mittel_monate": 6, "fremd": 1}) == {"mittel_monate": 6}


def test_visibility_follows_view() -> None:
    einfach = bausteine.hole("insolvenzen.langreihe")
    experte = bausteine.hole("insolvenzen.ausgang")
    assert einfach.sichtbar(Ebene.EINFACH) and einfach.sichtbar(Ebene.EXPERTE)
    assert not experte.sichtbar(Ebene.EINFACH) and experte.sichtbar(Ebene.EXPERTE)


def test_sources_lookup_keeps_unknown_keys() -> None:
    bibliothek = {"quellen": [{"key": "a", "titel": "A"}]}
    assert bausteine.quellenangaben(("a", "b"), bibliothek) == [
        {"key": "a", "titel": "A"},
        {"key": "b", "titel": "b"},
    ]


def test_signed_format() -> None:
    assert format_signed(88, 0) == "+88"
    assert format_signed(-3.25, 1) == "-3,2" or format_signed(-3.25, 1) == "-3,3"
    assert format_signed(0, 0) == "0"
    assert format_number(1234.5) == "1.234,5"


@pytest.mark.skipif(not DATEN_DA, reason="Aufbereitete Daten fehlen")
@pytest.mark.parametrize("baustein", bausteine.REGISTRY.values(), ids=lambda b: b.id)
def test_baustein_renders_with_processed_data(baustein: bausteine.Baustein) -> None:
    kontext = baustein.kontext(bausteine.lade_aus_dataset)
    inhalt = baustein.erzeuge(kontext)
    if isinstance(inhalt, Diagramm):
        assert inhalt.figur.data, "Diagramm ohne Daten"
        assert inhalt.figur.layout.yaxis.title.text, "Diagramm ohne Achsentitel"
    elif isinstance(inhalt, list):
        assert inhalt and all(isinstance(k, Kennzahl) for k in inhalt)
    elif isinstance(inhalt, pd.DataFrame):
        assert not inhalt.empty
    else:
        assert isinstance(inhalt, str) and inhalt
    assert isinstance(baustein.aussage(kontext), str)
