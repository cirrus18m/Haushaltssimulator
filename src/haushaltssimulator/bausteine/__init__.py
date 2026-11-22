"""Bausteine: Diagramme, Kennzahlen, Tabellen und Texte als wiederverwendbare Einheiten.

Jedes Themenmodul registriert beim Import seine Bausteine und Seiten in
:data:`REGISTRY` bzw. :data:`SEITEN`. Neue Themenmodule hier importieren.
"""

from __future__ import annotations

from . import insolvenzen  # noqa: F401 – registriert die Bausteine
from .kern import (
    ANSICHTEN,
    REGISTRY,
    SEITEN,
    Abschnitt,
    Art,
    Baustein,
    Diagramm,
    Ebene,
    Inhalt,
    Kennzahl,
    Kontext,
    Parameter,
    Seite,
    baustein,
    hole,
    lade_aus_dataset,
    quellenangaben,
    registriere_seite,
    seite_von,
)

__all__ = [
    "ANSICHTEN",
    "REGISTRY",
    "SEITEN",
    "Abschnitt",
    "Art",
    "Baustein",
    "Diagramm",
    "Ebene",
    "Inhalt",
    "Kennzahl",
    "Kontext",
    "Parameter",
    "Seite",
    "baustein",
    "hole",
    "lade_aus_dataset",
    "quellenangaben",
    "registriere_seite",
    "seite_von",
]
