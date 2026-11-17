"""Länderkürzel und deutsche Bezeichnungen für den Zinsvergleich."""

from __future__ import annotations

EUROPA_LAENDER: tuple[tuple[str, str], ...] = (
    ("BE", "Belgien"),
    ("BG", "Bulgarien"),
    ("DK", "Dänemark"),
    ("DE", "Deutschland"),
    ("EE", "Estland"),
    ("FI", "Finnland"),
    ("FR", "Frankreich"),
    ("EL", "Griechenland"),
    ("IE", "Irland"),
    ("IT", "Italien"),
    ("HR", "Kroatien"),
    ("LV", "Lettland"),
    ("LT", "Litauen"),
    ("LU", "Luxemburg"),
    ("MT", "Malta"),
    ("NL", "Niederlande"),
    ("AT", "Österreich"),
    ("PL", "Polen"),
    ("PT", "Portugal"),
    ("RO", "Rumänien"),
    ("SE", "Schweden"),
    ("SK", "Slowakei"),
    ("SI", "Slowenien"),
    ("ES", "Spanien"),
    ("CZ", "Tschechien"),
    ("HU", "Ungarn"),
    ("UK", "Vereinigtes Königreich"),
    ("CY", "Zypern"),
)

LAND_NAMEN: dict[str, str] = {
    **dict(EUROPA_LAENDER),
    "US": "Vereinigte Staaten",
    "RU": "Russland",
}
