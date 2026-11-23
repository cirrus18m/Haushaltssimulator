"""Grundtypen der Bausteine: Inhalte einmal beschreiben, beliebig zusammenstellen.

Ein :class:`Baustein` ist die kleinste darstellbare Einheit der App – ein Diagramm, eine
Reihe Kennzahlen, eine Tabelle oder ein Text – zusammen mit Titel, Kernaussage,
Erklärung, Methodik und Quellen. Seiten der App (:class:`Seite`) und exportierte
Berichte sind nur Zusammenstellungen von Baustein-IDs.

Das Modul kennt kein Streamlit. ``erzeuge`` liefert den Inhalt ohne endgültiges Layout;
das setzt erst das Ausgabeziel (App über ``ui.plot``, Folie über ``bericht``).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import pandas as pd
import plotly.graph_objects as go


class Art(StrEnum):
    DIAGRAMM = "diagramm"
    KENNZAHLEN = "kennzahlen"
    TABELLE = "tabelle"
    TEXT = "text"


class Ebene(StrEnum):
    """Ab welcher Ansicht ein Baustein erscheint."""

    EINFACH = "einfach"  # in beiden Ansichten
    EXPERTE = "experte"  # nur in der Expertenansicht


ANSICHTEN = (Ebene.EINFACH, Ebene.EXPERTE)


@dataclass(frozen=True)
class Parameter:
    """Ein Bedienelement, unabhängig von Streamlit beschrieben.

    ``art`` ist ``"ganzzahl"`` (Schieberegler ``minimum`` … ``maximum``) oder
    ``"auswahl"`` (eine Option aus ``optionen``). In der einfachen Ansicht gilt immer
    ``standard``; der Export friert den gewählten Wert ein.
    """

    name: str
    beschriftung: str
    art: str
    standard: Any
    minimum: int | None = None
    maximum: int | None = None
    schritt: int = 1
    optionen: tuple[Any, ...] = ()
    hilfe: str = ""

    def pruefe(self, wert: Any) -> Any:
        """Gibt einen gültigen Wert zurück, ungültige Werte fallen auf den Standard."""
        if self.art == "ganzzahl":
            try:
                zahl = int(wert)
            except (TypeError, ValueError):
                return self.standard
            if self.minimum is not None:
                zahl = max(zahl, self.minimum)
            if self.maximum is not None:
                zahl = min(zahl, self.maximum)
            return zahl
        if self.art == "auswahl":
            return wert if wert in self.optionen else self.standard
        return wert


@dataclass(frozen=True)
class Kennzahl:
    beschriftung: str
    wert: str
    veraenderung: str | None = None
    # wie ``st.metric``: "normal", "inverse" (Anstieg ist schlecht) oder "off"
    farbe: str = "normal"


@dataclass(frozen=True)
class Diagramm:
    """Plotly-Figur plus App-Layoutwünsche (Höhe, eigene Legenden)."""

    figur: go.Figure
    hoehe: int = 430
    legende: bool = True
    eigene_legenden: bool = False


Inhalt = Diagramm | list[Kennzahl] | pd.DataFrame | str


@dataclass(frozen=True)
class Kontext:
    """Daten und Parameterwerte, mit denen ein Baustein seinen Inhalt erzeugt.

    ``lade(name)`` liefert einen Datensatz über den Kurznamen der Ladefunktion, also
    ``"insolvencies"`` für ``dataset.load_insolvencies`` bzw. ``ui.insolvencies``. So
    nutzt die App ihre gecachten Lader und der Export die reinen Funktionen.
    """

    lade: Callable[[str], pd.DataFrame]
    parameter: Mapping[str, Any] = field(default_factory=dict)

    def daten(self, name: str) -> pd.DataFrame:
        return self.lade(name)

    def wert(self, name: str) -> Any:
        return self.parameter[name]


@dataclass(frozen=True)
class Baustein:
    id: str
    titel: str
    art: Art
    ebene: Ebene
    quellen: tuple[str, ...]
    erzeuge: Callable[[Kontext], Inhalt]
    # fester Satz oder Funktion, die den Satz mit aktuellen Zahlen füllt
    kernaussage: str | Callable[[Kontext], str] = ""
    erklaerung: str = ""
    methodik: str = ""
    parameter: tuple[Parameter, ...] = ()
    schlagworte: tuple[str, ...] = ()

    def parameterwerte(self, werte: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Standardwerte, überschrieben von gültigen ``werte``."""
        werte = werte or {}
        return {
            p.name: p.pruefe(werte[p.name]) if p.name in werte else p.standard
            for p in self.parameter
        }

    def kontext(
        self, lade: Callable[[str], pd.DataFrame], werte: Mapping[str, Any] | None = None
    ) -> Kontext:
        return Kontext(lade=lade, parameter=self.parameterwerte(werte))

    def aussage(self, kontext: Kontext) -> str:
        if callable(self.kernaussage):
            return self.kernaussage(kontext)
        return self.kernaussage

    def sichtbar(self, ansicht: Ebene) -> bool:
        return ansicht == Ebene.EXPERTE or self.ebene == Ebene.EINFACH


@dataclass(frozen=True)
class Abschnitt:
    titel: str
    bausteine: tuple[str, ...]
    einleitung: str = ""


@dataclass(frozen=True)
class Seite:
    id: str
    titel: str
    abschnitte: tuple[Abschnitt, ...]
    einleitung: str = ""

    def baustein_ids(self) -> list[str]:
        return [bid for abschnitt in self.abschnitte for bid in abschnitt.bausteine]


REGISTRY: dict[str, Baustein] = {}
SEITEN: dict[str, Seite] = {}


def baustein(**angaben: Any) -> Callable[[Callable[[Kontext], Inhalt]], Baustein]:
    """Dekorator: registriert die Funktion als ``erzeuge`` eines neuen Bausteins."""

    def registriere(funktion: Callable[[Kontext], Inhalt]) -> Baustein:
        neu = Baustein(erzeuge=funktion, **angaben)
        if neu.id in REGISTRY:
            raise ValueError(f"Baustein-ID doppelt vergeben: {neu.id}")
        REGISTRY[neu.id] = neu
        return neu

    return registriere


def registriere_seite(seite: Seite) -> Seite:
    if seite.id in SEITEN:
        raise ValueError(f"Seiten-ID doppelt vergeben: {seite.id}")
    unbekannt = [bid for bid in seite.baustein_ids() if bid not in REGISTRY]
    if unbekannt:
        raise ValueError(f"Seite {seite.id} nennt unbekannte Bausteine: {unbekannt}")
    SEITEN[seite.id] = seite
    return seite


def hole(baustein_id: str) -> Baustein:
    try:
        return REGISTRY[baustein_id]
    except KeyError:
        raise KeyError(f"Unbekannter Baustein: {baustein_id}") from None


def seite_von(baustein_id: str) -> Seite | None:
    """Erste Seite, die den Baustein enthält (für Kicker und Gruppierung)."""
    for seite in SEITEN.values():
        if baustein_id in seite.baustein_ids():
            return seite
    return None


def quellenangaben(schluessel: tuple[str, ...], bibliothek: Mapping[str, Any]) -> list[dict]:
    """Einträge der Quellenbibliothek zu den Schlüsseln, in der angegebenen Reihenfolge.

    Unbekannte Schlüssel erscheinen mit ihrem Schlüssel als Titel, damit nichts
    stillschweigend verschwindet (ein Test stellt sicher, dass es keine gibt).
    """
    nach_schluessel = {eintrag["key"]: eintrag for eintrag in bibliothek.get("quellen", [])}
    return [nach_schluessel.get(key, {"key": key, "titel": key}) for key in schluessel]


def lade_aus_dataset(name: str) -> pd.DataFrame:
    """Reiner Lader ohne Streamlit: ``name`` → ``dataset.load_<name>()``."""
    from .. import dataset

    return getattr(dataset, f"load_{name}")()
