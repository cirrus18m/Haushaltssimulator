"""Foliensätze aus ``insights/`` für die App: auflisten und als eigenständiges HTML.

Die Präsentationen verweisen auf ein lokales Stylesheet und auf Diagramme in
``bilder/``. In der App laufen sie in einem eingebetteten Frame ohne Zugriff auf diese
Dateien; ``eigenstaendiges_html`` bettet sie deshalb direkt ein. Reveal.js kommt
weiterhin vom CDN.
"""

from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path

from . import paths

INSIGHTS_DIR = paths.PROJECT_ROOT / "insights"
# GitHub Pages veröffentlicht den Ordner insights/ (Workflow insights-pages.yml).
PAGES_URL = "https://cirrus18m.github.io/Haushaltssimulator/"

_STYLESHEET = re.compile(r'<link rel="stylesheet" href="([^":]+\.css)">')
_SVG_BILD = re.compile(r'src="((?![a-z]+:)[^"]+\.svg)"')
_TITEL = re.compile(r"<title>(.*?)</title>", re.S)
_BESCHREIBUNG = re.compile(r'<meta name="description" content="([^"]*)">')


@dataclass(frozen=True)
class Foliensatz:
    """Eine Präsentation unter ``insights/<thema>/``."""

    pfad: Path
    titel: str
    beschreibung: str
    folien: int

    @property
    def relativer_pfad(self) -> str:
        """Pfad unter ``insights/``; ``index.html`` als Ordneradresse."""
        relativ = self.pfad.relative_to(self.pfad.parents[1]).as_posix()
        return relativ.removesuffix("index.html")

    @property
    def pages_url(self) -> str:
        return PAGES_URL + self.relativer_pfad


def _lies(pfad: Path) -> Foliensatz:
    text = pfad.read_text(encoding="utf-8")
    titel = _TITEL.search(text)
    beschreibung = _BESCHREIBUNG.search(text)
    return Foliensatz(
        pfad=pfad,
        titel=html.unescape(titel.group(1).strip()) if titel else pfad.stem,
        beschreibung=html.unescape(beschreibung.group(1)) if beschreibung else "",
        folien=len(re.findall(r"<section\b", text)),
    )


def foliensaetze(ordner: Path = INSIGHTS_DIR) -> list[Foliensatz]:
    """Alle Foliensätze, je Thema die kürzeste Fassung zuerst."""
    saetze = [_lies(pfad) for pfad in ordner.glob("*/*.html")]
    return sorted(saetze, key=lambda satz: (satz.pfad.parent.name, satz.folien))


def eigenstaendiges_html(pfad: Path) -> str:
    """HTML der Präsentation mit eingebettetem Stylesheet und eingebetteten Diagrammen."""
    text = pfad.read_text(encoding="utf-8")

    def stylesheet(treffer: re.Match[str]) -> str:
        css = (pfad.parent / treffer.group(1)).read_text(encoding="utf-8")
        return f"<style>\n{css}\n</style>"

    def bild(treffer: re.Match[str]) -> str:
        daten = base64.b64encode((pfad.parent / treffer.group(1)).read_bytes()).decode("ascii")
        return f'src="data:image/svg+xml;base64,{daten}"'

    text = _STYLESHEET.sub(stylesheet, text)
    return _SVG_BILD.sub(bild, text)
