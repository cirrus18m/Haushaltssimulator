"""Eigene Berichte: ausgewählte Bausteine als eigenständige Reveal.js-Präsentation.

Reine Funktionen ohne Streamlit. Die App sammelt Baustein-IDs samt eingefrorener
Parameter in einer :class:`BerichtKonfiguration`; :func:`erzeuge_bericht` macht daraus
eine einzelne HTML-Datei mit Titelfolie, je Baustein einer Folie und einer
Quellenfolie (Herausgeber, Lizenz, Abrufzeitpunkt aus ``data/sources.json``).

Diagramme sind standardmäßig **interaktiv**: Die Plotly-Figur steht als JSON in der
Datei und wird im Browser gezeichnet. Das braucht kein Kaleido/Chrome auf dem Server.
Die Variante **statisch** bettet SVG ein (Kaleido); fehlt es, bleibt die Folie
interaktiv.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import plotly.offline

from . import bausteine, sources
from .bausteine import Baustein, Diagramm, Kennzahl
from .format import format_number

VORLAGEN = Path(__file__).resolve().parent / "vorlagen"
REVEAL_VERSION = "5.2.1"
REVEAL_CDN = f"https://cdn.jsdelivr.net/npm/reveal.js@{REVEAL_VERSION}/dist"
PLOTLY_CDN = f"https://cdn.plot.ly/plotly-{plotly.offline.get_plotlyjs_version()}.min.js"


@dataclass(frozen=True)
class Format:
    name: str
    breite: int
    hoehe: int
    diagramm_breite: int
    diagramm_hoehe: int
    schrift: int
    tabellenzeilen: int


FORMATE: dict[str, Format] = {
    "quer": Format("Querformat 16:9 (Rechner, Beamer)", 1920, 1080, 1780, 560, 22, 8),
    # Wie die Insights: 1080 × 1920, Mindestschrift 30 px in Diagrammen.
    "hoch": Format("Hochformat 9:16 (Smartphone)", 1080, 1920, 960, 960, 30, 14),
}
DIAGRAMM_ARTEN = {"interaktiv": "interaktiv (Plotly)", "statisch": "statisch (SVG)"}
TEXT_UMFANG = {
    "kernaussage": "nur Kernaussage",
    "erklaerung": "Kernaussage und Erklärung",
    "methodik": "zusätzlich Methodik",
}


@dataclass
class Eintrag:
    id: str
    parameter: dict[str, Any] = field(default_factory=dict)


@dataclass
class BerichtKonfiguration:
    titel: str = "Mein Bericht"
    untertitel: str = ""
    autor: str = ""
    format: str = "quer"
    diagramme: str = "interaktiv"
    text: str = "erklaerung"
    quellenfolie: bool = True
    eintraege: list[Eintrag] = field(default_factory=list)

    def als_dict(self) -> dict[str, Any]:
        return {"schema_version": 1, **asdict(self)}

    def als_json(self) -> str:
        return json.dumps(self.als_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def aus_dict(cls, daten: Mapping[str, Any]) -> tuple[BerichtKonfiguration, list[str]]:
        """Liest eine gespeicherte Zusammenstellung.

        Gibt zusätzlich die IDs zurück, die es (nicht mehr) gibt; sie werden übersprungen.
        """
        unbekannt: list[str] = []
        eintraege = []
        for roh in daten.get("eintraege", []):
            if roh.get("id") not in bausteine.REGISTRY:
                unbekannt.append(str(roh.get("id")))
                continue
            werte = bausteine.hole(roh["id"]).parameterwerte(roh.get("parameter") or {})
            eintraege.append(Eintrag(roh["id"], werte))
        standard = cls()
        konfiguration = cls(
            titel=str(daten.get("titel", standard.titel)),
            untertitel=str(daten.get("untertitel", "")),
            autor=str(daten.get("autor", "")),
            format=daten.get("format") if daten.get("format") in FORMATE else standard.format,
            diagramme=daten.get("diagramme")
            if daten.get("diagramme") in DIAGRAMM_ARTEN
            else standard.diagramme,
            text=daten.get("text") if daten.get("text") in TEXT_UMFANG else standard.text,
            quellenfolie=bool(daten.get("quellenfolie", True)),
            eintraege=eintraege,
        )
        return konfiguration, unbekannt

    @classmethod
    def aus_json(cls, text: str) -> tuple[BerichtKonfiguration, list[str]]:
        return cls.aus_dict(json.loads(text))


# --------------------------------------------------------------------------- Layout


def folienlayout(figur: go.Figure, fmt: Format, hoehe: int | None = None) -> go.Figure:
    """Kopie der Figur im Layout der Folie (feste Größe, große Schrift)."""
    folie = go.Figure(figur)
    folie.update_layout(
        template="plotly_white",
        width=fmt.diagramm_breite,
        height=hoehe or fmt.diagramm_hoehe,
        autosize=False,
        margin={"l": 10, "r": 20, "t": 20 + fmt.schrift * 3, "b": 10},
        font={"family": "Inter, Segoe UI, Helvetica, Arial, sans-serif", "size": fmt.schrift},
        hovermode="x unified",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        title=None,
    )
    return folie


# --------------------------------------------------------------------------- HTML-Teile


def _e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def markdown_zu_html(text: str) -> str:
    """Kleines Markdown: Absätze, ``* ``-Listen, ``**fett**`` und ``\\`Code\\```."""

    def inline(zeile: str) -> str:
        zeile = _e(zeile)
        zeile = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", zeile)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", zeile)

    teile = []
    for block in re.split(r"\n\s*\n", text.strip()):
        zeilen = [z.strip() for z in block.splitlines() if z.strip()]
        if zeilen and all(z.startswith(("* ", "- ")) for z in zeilen):
            punkte = "".join(f"<li>{inline(z[2:])}</li>" for z in zeilen)
            teile.append(f"<ul>{punkte}</ul>")
        elif zeilen:
            teile.append(f"<p>{inline(' '.join(zeilen))}</p>")
    return "\n".join(teile)


def _svg(figur: go.Figure) -> str | None:
    try:
        svg = figur.to_image(format="svg").decode("utf-8")
    except Exception:  # Kaleido bzw. Chrome fehlt
        return None
    return re.sub(r"^<\?xml[^>]*>\s*", "", svg)


def _diagramm_html(diagramm: Diagramm, fmt: Format, art: str, nummer: int, hoehe: int) -> str:
    folie = folienlayout(diagramm.figur, fmt, hoehe)
    if not diagramm.legende:
        folie.update_layout(showlegend=False)
    if art == "statisch" and (svg := _svg(folie)) is not None:
        return f'<div class="diagramm statisch">{svg}</div>'
    daten = folie.to_json().replace("</", "<\\/")
    return (
        f'<div class="diagramm plot" id="plot-{nummer}" '
        f'style="width:{fmt.diagramm_breite}px;height:{hoehe}px"></div>'
        f'<script type="application/json" id="plot-{nummer}-daten">{daten}</script>'
    )


def _kennzahlen_html(kennzahlen: list[Kennzahl]) -> str:
    kacheln = []
    for kennzahl in kennzahlen:
        veraenderung = ""
        if kennzahl.veraenderung:
            # Färbung wie st.metric: „inverse“ heißt, ein Anstieg ist schlecht.
            fallend = kennzahl.veraenderung.lstrip().startswith(("-", "−"))
            klasse = {
                "normal": "schlecht" if fallend else "gut",
                "inverse": "gut" if fallend else "schlecht",
            }.get(kennzahl.farbe, "")
            veraenderung = f'<div class="veraenderung {klasse}">{_e(kennzahl.veraenderung)}</div>'
        kacheln.append(
            '<div class="kennzahl">'
            f'<div class="beschriftung">{_e(kennzahl.beschriftung)}</div>'
            f'<div class="wert">{_e(kennzahl.wert)}</div>{veraenderung}</div>'
        )
    return f'<div class="kennzahlen">{"".join(kacheln)}</div>'


def _zelle(wert: Any) -> str:
    if wert is None or (isinstance(wert, float) and pd.isna(wert)):
        return "–"
    if isinstance(wert, int | float):
        return format_number(float(wert), 0 if float(wert).is_integer() else 1)
    return str(wert)


def _tabelle_html(frame: pd.DataFrame, fmt: Format) -> str:
    gekuerzt = frame.tail(fmt.tabellenzeilen)
    kopf = "".join(f"<th>{_e(spalte)}</th>" for spalte in gekuerzt.columns)
    zeilen = "".join(
        "<tr>" + "".join(f"<td>{_e(_zelle(wert))}</td>" for wert in zeile) + "</tr>"
        for zeile in gekuerzt.itertuples(index=False)
    )
    hinweis = ""
    if len(frame) > len(gekuerzt):
        hinweis = f'<p class="klein">Letzte {len(gekuerzt)} von {len(frame)} Zeilen.</p>'
    return (
        f'<div class="tabelle"><table><thead><tr>{kopf}</tr></thead>'
        f"<tbody>{zeilen}</tbody></table></div>{hinweis}"
    )


def _quellzeile(eintraege: list[dict]) -> str:
    teile = []
    for eintrag in eintraege:
        text = eintrag.get("herausgeber") or ""
        text = f"{text}: {eintrag['titel']}" if text else eintrag["titel"]
        if eintrag.get("lizenz"):
            text += f" ({eintrag['lizenz']})"
        teile.append(text)
    return "Quelle: " + "; ".join(teile)


def _parameter_text(baustein: Baustein, werte: Mapping[str, Any]) -> str:
    abweichend = [
        f"{p.beschriftung}: {werte[p.name]}"
        for p in baustein.parameter
        if p.name in werte and werte[p.name] != p.standard
    ]
    return " · ".join(abweichend)


def _folie(
    baustein: Baustein,
    eintrag: Eintrag,
    konfiguration: BerichtKonfiguration,
    lade: Callable[[str], pd.DataFrame],
    bibliothek: Mapping[str, Any],
    nummer: int,
) -> str:
    fmt = FORMATE[konfiguration.format]
    kontext = baustein.kontext(lade, eintrag.parameter)
    inhalt = baustein.erzeuge(kontext)
    seite = bausteine.seite_von(baustein.id)

    if isinstance(inhalt, Diagramm):
        # Mit Methodik steht mehr Text auf der Folie; das Diagramm wird entsprechend flacher.
        hoehe = fmt.diagramm_hoehe - (fmt.schrift * 6 if konfiguration.text == "methodik" else 0)
        koerper = _diagramm_html(inhalt, fmt, konfiguration.diagramme, nummer, hoehe)
    elif isinstance(inhalt, pd.DataFrame):
        koerper = _tabelle_html(inhalt, fmt)
    elif isinstance(inhalt, list):
        koerper = _kennzahlen_html(inhalt)
    else:
        koerper = f'<div class="text">{markdown_zu_html(str(inhalt))}</div>'

    texte = []
    if aussage := baustein.aussage(kontext):
        texte.append(f'<div class="kern">{_e(aussage)}</div>')
    if konfiguration.text in ("erklaerung", "methodik") and baustein.erklaerung:
        texte.append(f'<div class="klein">{markdown_zu_html(baustein.erklaerung)}</div>')
    if konfiguration.text == "methodik" and baustein.methodik:
        texte.append(
            f'<div class="klein methodik"><b>Methodik:</b> '
            f"{markdown_zu_html(baustein.methodik)}</div>"
        )
    if parameter := _parameter_text(baustein, eintrag.parameter):
        texte.append(f'<div class="klein">Einstellung: {_e(parameter)}</div>')

    kicker = f'<span class="kicker">{_e(seite.titel)}</span>' if seite else ""
    quelle = _quellzeile(bausteine.quellenangaben(baustein.quellen, bibliothek))
    return (
        f'<section data-baustein="{_e(baustein.id)}">{kicker}'
        f"<h2>{_e(baustein.titel)}</h2>{koerper}{''.join(texte)}"
        f'<div class="quelle">{_e(quelle)}</div></section>'
    )


def _titelfolie(konfiguration: BerichtKonfiguration, stand: date, datenstand: str) -> str:
    zeilen = [f"<h1>{_e(konfiguration.titel)}</h1>"]
    if konfiguration.untertitel:
        zeilen.append(f'<p class="untertitel">{_e(konfiguration.untertitel)}</p>')
    meta = [konfiguration.autor, stand.strftime("%d.%m.%Y")]
    zeilen.append(f'<p class="klein">{_e(" · ".join(m for m in meta if m))}</p>')
    zeilen.append(
        '<p class="klein">Zusammengestellt mit dem Haushaltssimulator aus frei verfügbaren '
        f"amtlichen Daten. Datenstand: {_e(datenstand)}.</p>"
    )
    return f'<section class="titel">{"".join(zeilen)}</section>'


def _quellenfolie(schluessel: list[str], bibliothek: Mapping[str, Any]) -> str:
    punkte = []
    for eintrag in bausteine.quellenangaben(tuple(schluessel), bibliothek):
        teile = [f"<b>{_e(eintrag['titel'])}</b>"]
        if eintrag.get("herausgeber"):
            teile.append(_e(eintrag["herausgeber"]))
        if eintrag.get("lizenz"):
            teile.append(f"Lizenz: {_e(eintrag['lizenz'])}")
        if eintrag.get("abgerufen_am"):
            abruf = datetime.fromisoformat(eintrag["abgerufen_am"]).strftime("%d.%m.%Y")
            teile.append(f"abgerufen am {abruf}")
        if eintrag.get("url"):
            url = _e(eintrag["url"])
            teile.append(f'<a href="{url}">{url}</a>')
        punkte.append(f"<li>{' · '.join(teile)}</li>")
    return f'<section class="quellen"><h2>Quellen</h2><ul>{"".join(punkte)}</ul></section>'


def _datenstand(bibliothek: Mapping[str, Any], schluessel: list[str]) -> str:
    stempel = [
        eintrag["abgerufen_am"]
        for eintrag in bausteine.quellenangaben(tuple(schluessel), bibliothek)
        if eintrag.get("abgerufen_am")
    ]
    if not stempel:
        return "unbekannt"
    return max(datetime.fromisoformat(s) for s in stempel).strftime("%d.%m.%Y")


SKRIPT = """
<script>
(function () {
  function zeichne(bereich) {
    bereich.querySelectorAll('.plot:not([data-gezeichnet])').forEach(function (el) {
      var fig = JSON.parse(document.getElementById(el.id + '-daten').textContent);
      Plotly.newPlot(el, fig.data, fig.layout, {displaylogo: false, responsive: false});
      el.setAttribute('data-gezeichnet', '1');
    });
  }
  Reveal.initialize({
    width: %(breite)d, height: %(hoehe)d, margin: 0.03, hash: true, center: false,
    transition: 'slide'
  }).then(function () {
    if (/print-pdf/.test(window.location.search)) { zeichne(document); }
    else { zeichne(Reveal.getCurrentSlide()); }
  });
  Reveal.on('slidechanged', function (e) { zeichne(e.currentSlide); });
})();
</script>
"""


def erzeuge_bericht(
    konfiguration: BerichtKonfiguration,
    *,
    lade: Callable[[str], pd.DataFrame] = bausteine.lade_aus_dataset,
    bibliothek: Mapping[str, Any] | None = None,
    stand: date | None = None,
) -> str:
    """Erzeugt die Präsentation als eigenständige HTML-Datei (Reveal.js per CDN)."""
    fmt = FORMATE[konfiguration.format]
    bibliothek = sources.read_library() if bibliothek is None else bibliothek
    stand = stand or date.today()

    folien = []
    quellen: list[str] = []
    for nummer, eintrag in enumerate(konfiguration.eintraege, start=1):
        baustein = bausteine.hole(eintrag.id)
        folien.append(_folie(baustein, eintrag, konfiguration, lade, bibliothek, nummer))
        quellen.extend(key for key in baustein.quellen if key not in quellen)

    titel = _titelfolie(konfiguration, stand, _datenstand(bibliothek, quellen))
    alle = [titel, *folien]
    if konfiguration.quellenfolie and quellen:
        alle.append(_quellenfolie(quellen, bibliothek))

    stil = (VORLAGEN / "bericht.css").read_text(encoding="utf-8")
    plotly_js = ""
    if any('class="diagramm plot"' in folie for folie in folien):
        plotly_js = f'<script src="{PLOTLY_CDN}" charset="utf-8"></script>'
    return (
        '<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_e(konfiguration.titel)}</title>\n"
        '<meta name="generator" content="Haushaltssimulator">\n'
        f'<link rel="stylesheet" href="{REVEAL_CDN}/reveal.css">\n'
        f'<link rel="stylesheet" href="{REVEAL_CDN}/theme/white.css">\n'
        f"<style>\n{stil}</style>\n</head>\n"
        f'<body class="format-{konfiguration.format}">\n'
        '<div class="reveal"><div class="slides">\n' + "\n".join(alle) + "\n</div></div>\n"
        f'<script src="{REVEAL_CDN}/reveal.js"></script>\n{plotly_js}\n'
        + SKRIPT % {"breite": fmt.breite, "hoehe": fmt.hoehe}
        + "</body>\n</html>\n"
    )


def dateiname(konfiguration: BerichtKonfiguration, stand: date | None = None) -> str:
    """``bericht_<titel>_<datum>.html`` mit ASCII-Zeichen."""
    stand = stand or date.today()
    ersatz = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
    titel = "".join(ersatz.get(z, z) for z in konfiguration.titel)
    titel = re.sub(r"[^A-Za-z0-9]+", "_", titel).strip("_").lower() or "bericht"
    return f"{titel}_{stand:%Y-%m-%d}.html"
