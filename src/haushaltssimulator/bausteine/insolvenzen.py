"""Bausteine der Seite Insolvenzen (Pilotseite der Baustein-Struktur)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..format import format_month, format_number, format_signed
from .kern import (
    Abschnitt,
    Art,
    Diagramm,
    Ebene,
    Kennzahl,
    Kontext,
    Parameter,
    Seite,
    baustein,
    registriere_seite,
)

QUELLE_LANGREIHE = "destatis_insolvenzen_zeitreihe"
QUELLE_GESAMT = "destatis_insolvenzen"
QUELLE_UNTERNEHMEN = "destatis_insolvenzen_unternehmen"

HELLBLAU = "#7fb2d5"
BLAU = "#1f4e79"
ROT = "#b03a2e"
GOLD = "#c9a227"


def _unternehmen(k: Kontext) -> pd.DataFrame:
    frame = k.daten("insolvencies")
    return frame.dropna(subset=["verfahren_unternehmen"]).reset_index(drop=True)


def _vergleich(k: Kontext) -> dict[str, float]:
    """Letzter Monat, Vorjahresmonat und gleitende 12-Monats-Summen."""
    unternehmen = _unternehmen(k)
    letzte = unternehmen.iloc[-1]
    vorjahres_monat = f"{int(letzte['jahr']) - 1}-{letzte['monat'][5:7]}"
    vorjahr = unternehmen.loc[unternehmen["monat"] == vorjahres_monat, "verfahren_unternehmen"]
    vorjahres_wert = float(vorjahr.iloc[0]) if not vorjahr.empty else float("nan")
    summe_12 = float(unternehmen["verfahren_unternehmen"].tail(12).sum())
    summe_vorjahr_12 = float(unternehmen["verfahren_unternehmen"].iloc[-24:-12].sum())
    return {
        "monat": letzte["monat"],
        "wert": float(letzte["verfahren_unternehmen"]),
        "vorjahr": vorjahres_wert,
        "summe_12": summe_12,
        "summe_12_delta_pct": (summe_12 / summe_vorjahr_12 - 1) * 100
        if summe_vorjahr_12
        else float("nan"),
        "forderungen_mio_eur": float(letzte["forderungen_unternehmen_mio_eur"]),
        "arbeitnehmer": float(letzte["betroffene_arbeitnehmer"]),
    }


def _aussage_kennzahlen(k: Kontext) -> str:
    v = _vergleich(k)
    richtung = "mehr" if v["summe_12_delta_pct"] >= 0 else "weniger"
    return (
        f"In den letzten zwölf Monaten bis {format_month(v['monat'])} meldeten "
        f"{format_number(v['summe_12'], 0)} Unternehmen Insolvenz an – "
        f"{format_number(abs(v['summe_12_delta_pct']), 1)} % {richtung} als im Jahr davor."
    )


@baustein(
    id="insolvenzen.kennzahlen",
    titel="Insolvenzen auf einen Blick",
    art=Art.KENNZAHLEN,
    ebene=Ebene.EINFACH,
    quellen=(QUELLE_LANGREIHE, QUELLE_UNTERNEHMEN),
    kernaussage=_aussage_kennzahlen,
    erklaerung=(
        "Gezählt werden beantragte Insolvenzverfahren von Unternehmen. Die Summe der "
        "letzten zwölf Monate gleicht Schwankungen zwischen einzelnen Monaten aus."
    ),
    methodik=(
        "Veränderung zum Vorjahr: letzter verfügbarer Monat gegen denselben Monat des "
        "Vorjahres sowie gleitende 12-Monats-Summe gegen die 12 Monate davor. Forderungen "
        "und betroffene Arbeitnehmer sind voraussichtliche Werte aus 52411-0011."
    ),
    schlagworte=("Insolvenzen", "Unternehmen"),
)
def kennzahlen(k: Kontext) -> list[Kennzahl]:
    v = _vergleich(k)
    return [
        Kennzahl(
            "Unternehmensinsolvenzen",
            format_number(v["wert"], 0),
            f"{format_signed(v['wert'] - v['vorjahr'], 0)} zum Vorjahr",
            "inverse",
        ),
        Kennzahl(
            "Letzte 12 Monate",
            format_number(v["summe_12"], 0),
            f"{format_signed(v['summe_12_delta_pct'], 1)} % zum Vorjahr",
            "inverse",
        ),
        Kennzahl(
            "Forderungen (Mrd. €)",
            format_number(v["forderungen_mio_eur"] / 1000, 2),
            "voraussichtlich",
            "off",
        ),
        Kennzahl("Arbeitnehmer", format_number(v["arbeitnehmer"], 0), "betroffen", "off"),
    ]


@baustein(
    id="insolvenzen.langreihe",
    titel="Unternehmensinsolvenzen seit 2003",
    art=Art.DIAGRAMM,
    ebene=Ebene.EINFACH,
    quellen=(QUELLE_LANGREIHE,),
    kernaussage=(
        "Nach dem Tiefstand der Corona-Jahre steigen die Unternehmensinsolvenzen wieder "
        "deutlich an."
    ),
    erklaerung=(
        "Die Säulen zeigen die Verfahren je Monat, die Linie das Mittel der jeweils "
        "letzten zwölf Monate."
    ),
    methodik=(
        "GENESIS 52411-0017, Zeile „Insgesamt“ über alle Unternehmensgrößenklassen. Die "
        "jüngsten Monate sind vorläufig und werden nachgemeldet."
    ),
    parameter=(
        Parameter(
            "mittel_monate",
            "Gleitendes Mittel (Monate)",
            "ganzzahl",
            12,
            minimum=3,
            maximum=36,
            schritt=3,
        ),
    ),
    schlagworte=("Insolvenzen", "Zeitreihe"),
)
def langreihe(k: Kontext) -> Diagramm:
    fenster = k.wert("mittel_monate")
    verlauf = _unternehmen(k).set_index("monat")["verfahren_unternehmen"]
    gleitend = verlauf.rolling(fenster, min_periods=fenster).mean()
    figur = go.Figure()
    figur.add_trace(
        go.Bar(
            x=verlauf.index,
            y=verlauf,
            name="Verfahren je Monat",
            marker_color=HELLBLAU,
            hovertemplate="%{y:,.0f}<extra></extra>",
        )
    )
    figur.add_trace(
        go.Scatter(
            x=gleitend.index,
            y=gleitend,
            name=f"{fenster}-Monats-Mittel",
            line={"color": BLAU, "width": 3},
            hovertemplate="%{y:,.0f}<extra></extra>",
        )
    )
    figur.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
    return Diagramm(figur, hoehe=440)


@baustein(
    id="insolvenzen.ausgang",
    titel="Verfahrensausgang",
    art=Art.DIAGRAMM,
    ebene=Ebene.EXPERTE,
    quellen=(QUELLE_LANGREIHE,),
    kernaussage=(
        "Ein großer Teil der Anträge wird mangels Masse abgewiesen – dann reicht das "
        "Vermögen nicht einmal für die Verfahrenskosten."
    ),
    erklaerung=(
        "Eröffnete Verfahren, mangels Masse abgewiesene Anträge und angenommene "
        "Schuldenbereinigungspläne je Monat."
    ),
    methodik="Der Schuldenbereinigungsplan ist erst ab 2021 ausgewiesen.",
    parameter=(
        Parameter(
            "monate", "Zeitraum (Monate)", "ganzzahl", 36, minimum=12, maximum=120, schritt=12
        ),
    ),
    schlagworte=("Insolvenzen",),
)
def ausgang(k: Kontext) -> Diagramm:
    frame = k.daten("insolvencies").dropna(subset=["verfahren_unternehmen"])
    letzte = frame.tail(k.wert("monate"))
    figur = go.Figure()
    for spalte, name, farbe in [
        ("eroeffnet_unternehmen", "eröffnet", BLAU),
        ("abgewiesen_unternehmen", "mangels Masse abgewiesen", ROT),
        ("schuldenbereinigungsplan_unternehmen", "Schuldenbereinigungsplan", GOLD),
    ]:
        if letzte[spalte].notna().sum() == 0:
            continue
        figur.add_trace(
            go.Bar(
                x=letzte["monat"],
                y=letzte[spalte].fillna(0),
                name=name,
                marker_color=farbe,
                hovertemplate="%{y:,.0f}<extra>" + name + "</extra>",
            )
        )
    figur.update_layout(barmode="stack")
    figur.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
    return Diagramm(figur, hoehe=400)


@baustein(
    id="insolvenzen.berichtsjahr",
    titel="Aktuelles Berichtsjahr: alle Verfahren",
    art=Art.DIAGRAMM,
    ebene=Ebene.EXPERTE,
    quellen=(QUELLE_GESAMT, QUELLE_UNTERNEHMEN),
    kernaussage=(
        "Neben Unternehmen stellen auch Verbraucher, ehemals Selbständige und Nachlässe "
        "Insolvenzanträge."
    ),
    erklaerung="Alle beantragten Insolvenzverfahren und darunter die von Unternehmen.",
    methodik=(
        "Gesamtzahlen aller Verfahren liegen nur für das laufende Berichtsjahr vor (52411-0002)."
    ),
    schlagworte=("Insolvenzen",),
)
def berichtsjahr(k: Kontext) -> Diagramm | str:
    aktuell = k.daten("insolvencies").dropna(subset=["verfahren_gesamt"])
    if aktuell.empty:
        return "Für das aktuelle Berichtsjahr liegen noch keine Gesamtzahlen vor."
    figur = go.Figure()
    for spalte, name, farbe in [
        ("verfahren_gesamt", "Verfahren insgesamt", HELLBLAU),
        ("verfahren_unternehmen", "Unternehmensinsolvenzen", BLAU),
    ]:
        figur.add_trace(
            go.Bar(
                x=aktuell["monat"],
                y=aktuell[spalte],
                name=name,
                marker_color=farbe,
                hovertemplate="%{y:,.0f}<extra></extra>",
            )
        )
    figur.update_layout(barmode="group")
    figur.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
    return Diagramm(figur, hoehe=380)


SPALTEN_MONATSWERTE = {
    "monat": "Monat",
    "verfahren_gesamt": "Verfahren insgesamt",
    "verfahren_unternehmen": "Unternehmen",
    "eroeffnet_unternehmen": "davon eröffnet",
    "abgewiesen_unternehmen": "mangels Masse abgewiesen",
    "schuldenbereinigungsplan_unternehmen": "Schuldenbereinigungsplan",
    "forderungen_gesamt_mio_eur": "Forderungen gesamt (Mio. €)",
    "forderungen_unternehmen_mio_eur": "Forderungen Unternehmen (Mio. €)",
    "betroffene_arbeitnehmer": "betroffene Arbeitnehmer",
}


@baustein(
    id="insolvenzen.monatswerte",
    titel="Monatswerte",
    art=Art.TABELLE,
    ebene=Ebene.EXPERTE,
    quellen=(QUELLE_LANGREIHE, QUELLE_GESAMT, QUELLE_UNTERNEHMEN),
    erklaerung="Die letzten Monate aller Insolvenzreihen.",
    parameter=(
        Parameter("zeilen", "Anzahl Monate", "ganzzahl", 24, minimum=6, maximum=120, schritt=6),
    ),
    schlagworte=("Insolvenzen", "Tabelle"),
)
def monatswerte(k: Kontext) -> pd.DataFrame:
    frame = k.daten("insolvencies").drop(columns=["jahr"]).tail(k.wert("zeilen"))
    return frame.rename(columns=SPALTEN_MONATSWERTE)


@baustein(
    id="insolvenzen.abgrenzung",
    titel="Datenlage und Abgrenzung",
    art=Art.TEXT,
    ebene=Ebene.EXPERTE,
    quellen=(QUELLE_LANGREIHE, QUELLE_GESAMT, QUELLE_UNTERNEHMEN),
)
def abgrenzung(k: Kontext) -> str:
    return (
        "Die Langreihe 52411-0017 weist beantragte Insolvenzverfahren von Unternehmen "
        "nach Unternehmensgrößenklassen aus (Zeile „Insgesamt“). Die Werte sind "
        "vorläufig und werden nachgemeldet. Gesamtzahlen aller Verfahren, Forderungen "
        "und betroffene Arbeitnehmer stehen für das laufende Berichtsjahr aus den "
        "Tabellen 52411-0002 und 52411-0011 zur Verfügung.\n\n"
        "Der Schuldenbereinigungsplan ist erst ab 2021 ausgewiesen; davor ist die "
        "Position nicht anwendbar."
    )


SEITE = registriere_seite(
    Seite(
        id="insolvenzen",
        titel="Insolvenzen",
        einleitung=(
            "Beantragte Insolvenzverfahren von Unternehmen in Deutschland ab 2003. Die "
            "Langreihe stammt aus der GENESIS-Tabelle 52411-0017 (Monate, Größenklassen), "
            "die aktuellen Forderungen und betroffenen Arbeitnehmer aus den Tabellen "
            "52411-0002 und 52411-0011."
        ),
        abschnitte=(
            Abschnitt("Überblick", ("insolvenzen.kennzahlen", "insolvenzen.langreihe")),
            Abschnitt("Verfahrensausgang", ("insolvenzen.ausgang",)),
            Abschnitt(
                "Aktuelles Berichtsjahr",
                ("insolvenzen.berichtsjahr", "insolvenzen.monatswerte"),
            ),
            Abschnitt("Datenlage", ("insolvenzen.abgrenzung",)),
        ),
    )
)
