"""Prüft, dass die Insight-Präsentationen vollständig sind."""

from __future__ import annotations

import json
import re

import pytest

from haushaltssimulator import paths

INSIGHTS = paths.PROJECT_ROOT / "insights"
PRAESENTATIONEN = sorted(path.parent for path in INSIGHTS.glob("*/index.html"))
# Alle Foliensätze, auch Varianten wie kurz.html neben der ausführlichen Fassung.
FOLIENSAETZE = sorted(INSIGHTS.glob("*/*.html"))


def test_insights_contain_presentations() -> None:
    assert PRAESENTATIONEN, "Keine Präsentation unter insights/*/index.html"


def _name(datei) -> str:
    return f"{datei.parent.name}/{datei.name}"


@pytest.mark.parametrize("datei", FOLIENSAETZE, ids=_name)
def test_presentation_references_existing_files(datei) -> None:
    html = datei.read_text(encoding="utf-8")
    bilder = re.findall(r'src="(bilder/[^"]+)"', html)
    assert bilder, "Die Präsentation bindet keine Diagramme ein"
    lokal = re.findall(r'href="([^":]+\.css)"', html)
    fehlend = [pfad for pfad in [*bilder, *lokal] if not (datei.parent / pfad).exists()]
    assert not fehlend, f"Fehlende Diagramme – diagramme.py ausführen: {fehlend}"


@pytest.mark.parametrize("ordner", PRAESENTATIONEN, ids=lambda ordner: ordner.name)
def test_presentation_has_generated_key_figures(ordner) -> None:
    assert (ordner / "diagramme.py").exists()
    kennzahlen = json.loads((ordner / "kennzahlen.json").read_text(encoding="utf-8"))
    assert kennzahlen.get("quelle")


def test_zinslast_deck_matches_key_figures() -> None:
    """Die zentralen Zahlen im Text müssen zu kennzahlen.json passen."""
    ordner = INSIGHTS / "zinslast"
    html = (ordner / "index.html").read_text(encoding="utf-8")
    k = json.loads((ordner / "kennzahlen.json").read_text(encoding="utf-8"))

    def deutsch(wert: float, stellen: int = 1) -> str:
        return f"{wert:.{stellen}f}".replace(".", ",")

    erwartet = [
        f"≈ {round(k['zinslast']['aktuell_mrd_eur'])} Mrd. €",
        f"+{k['zinslast']['anstieg_10_monate_mrd_eur']} Milliarden",
        f"+{deutsch(k['rendite']['anstieg_2022_pp'])} Prozentpunkte",
        f"+{deutsch(k['rendite']['anstieg_seit_hormus_pp'])} Prozentpunkte",
        f"{deutsch(k['haushalt']['nicht_gedeckt_mrd_eur'][1])} Mrd. € nicht gedeckt",
        f"<b>{deutsch(k['haushalt']['ausgaben_mrd_eur'][1])} Mrd. €</b> Ausgaben",
        f"<b>{deutsch(k['haushalt']['einnahmen_ohne_schulden_mrd_eur'][1])} Mrd. €</b>",
        f"Verteidigungsetat ({deutsch(k['haushalt']['verteidigung_mrd_eur'][1])} Mrd. €)",
        f"<b>{k['haushalt']['anteil_rente_zinsen_pct'][1]} %</b>",
        f"≈ {k['zerlegung']['mrd_eur']['Renditeanstieg 2022']} Mrd. €",
        f"≈ {k['zerlegung']['mrd_eur']['Renditeanstieg seit Iran-Krieg (Feb. 2026)']} Mrd. €",
        f"{deutsch(k['zinslast']['tatsaechlich_2021_mrd_eur'])} → "
        f"{deutsch(k['zinslast']['tatsaechlich_2025_mrd_eur'])} Mrd. €",
    ]
    fehlend = [text for text in erwartet if text not in html]
    assert not fehlend, f"Zahlen im Foliensatz weichen von kennzahlen.json ab: {fehlend}"


MIN_SCHRIFT_PX = 30


@pytest.mark.parametrize("ordner", PRAESENTATIONEN, ids=lambda ordner: ordner.name)
def test_no_font_below_minimum(ordner) -> None:
    """Folien und Diagramme bleiben auf dem Smartphone lesbar."""
    for datei in [*ordner.glob("*.html"), *ordner.glob("*.css")]:
        text = datei.read_text(encoding="utf-8")
        groessen = [int(px) for px in re.findall(r"font-size:\s*(\d+)px", text)]
        assert all(px >= MIN_SCHRIFT_PX for px in groessen), f"{datei.name}: {groessen}"
    for svg in (ordner / "bilder").glob("*.svg"):
        groessen = [float(px) for px in re.findall(r"font-size:\s*([\d.]+)px", svg.read_text())]
        klein = sorted({px for px in groessen if px < MIN_SCHRIFT_PX})
        assert not klein, f"{svg.name}: Schrift kleiner als {MIN_SCHRIFT_PX} px: {klein}"


def test_short_deck_matches_key_figures() -> None:
    """Die Kurzfassung nutzt dieselben Zahlen wie die ausführliche Fassung."""
    ordner = INSIGHTS / "zinslast"
    html = (ordner / "kurz.html").read_text(encoding="utf-8")
    k = json.loads((ordner / "kennzahlen.json").read_text(encoding="utf-8"))

    def deutsch(wert: float, stellen: int = 1) -> str:
        return f"{wert:.{stellen}f}".replace(".", ",")

    erwartet = [
        f"{deutsch(k['haushalt']['nicht_gedeckt_mrd_eur'][1])} Mrd. € nicht gedeckt",
        f"<b>{k['haushalt']['anteil_rente_zinsen_pct'][1]} %</b>",
        f"+{deutsch(k['rendite']['anstieg_2022_pp'])} Prozentpunkte",
        f"+{deutsch(k['rendite']['anstieg_seit_hormus_pp'])} Prozentpunkte",
        f"Deutschland <b>+{deutsch(k['international']['Deutschland'], 2)}</b>",
        f"{deutsch(k['zinslast']['tatsaechlich_2021_mrd_eur'])} → "
        f"{deutsch(k['zinslast']['tatsaechlich_2025_mrd_eur'])} Mrd. €",
        f"≈ {round(k['zinslast']['aktuell_mrd_eur'])} Mrd. € pro Jahr",
        f"(<b>{deutsch(k['rendite']['letzter_pct'], 2)} %</b>)",
    ]
    def tausender(wert: float) -> str:
        return f"{wert:,.0f}".replace(",", ".")

    for land, werte in k["frankreich_vergleich"].items():
        erwartet += [
            f"<tr><th>{land}</th><td>{deutsch(werte['schulden_mrd_eur'] / 1000, 2)} Bio. €</td>"
            f"<td>{deutsch(werte['rendite_pct'], 2)} %</td>"
            f"<td>{round(werte['theoretisch_mrd_eur'])} Mrd. €</td>"
            f"<td>{deutsch(werte['bevoelkerung_20_59_mio'])} Mio.</td>"
            f"<td><b>{tausender(werte['je_person_20_59_eur'])} €</b></td></tr>",
            f"{land} <span class=\"zahl"
            if land != "Deutschland"
            else f"Deutschland <span class=\"zahl\">≈ {tausender(werte['je_person_20_59_eur'])} €",
        ]
    fehlend = [text for text in erwartet if text not in html]
    assert not fehlend, f"Zahlen in kurz.html weichen von kennzahlen.json ab: {fehlend}"


def test_pages_landing_page_links_all_decks() -> None:
    startseite = (INSIGHTS / "index.html").read_text(encoding="utf-8")
    for datei in FOLIENSAETZE:
        ziel = f"{datei.parent.name}/" if datei.name == "index.html" else (
            f"{datei.parent.name}/{datei.name}"
        )
        assert f'href="{ziel}"' in startseite, f"Startseite verlinkt {ziel} nicht"
