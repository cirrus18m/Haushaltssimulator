"""Diagramme und Kennzahlen für das Insight „Fast 100 Milliarden Euro Zinsen“.

Liest ausschließlich die aufbereiteten Daten aus ``data/processed/`` und den
Finanzplan des Bundes 2026 bis 2030 (Drucksache 21/7301). Schreibt die Diagramme als
SVG nach ``bilder/`` und alle im Foliensatz genannten Zahlen nach ``kennzahlen.json``.

Aufruf aus dem Projektverzeichnis::

    uv run python insights/zinslast/diagramme.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from haushaltssimulator import analysis, dataset

ORDNER = Path(__file__).resolve().parent
BILDER = ORDNER / "bilder"

# Hochformat für Smartphones: Die Folie ist 1080 px breit, die Diagramme 1000 px.
BREITE = 1000
HOEHE = 1020
# Kleinste erlaubte Schrift in Diagrammen und Folien (px bei 1080 px Folienbreite).
# tests/test_insights.py prüft die SVG-Dateien und index.html darauf.
MIN_SCHRIFT = 30

BLAU = "#1f4e79"
ROT = "#b03a2e"
GRUEN = "#2e7d32"
GOLD = "#c9a227"
GRAU = "#6b7280"
TUERKIS = "#0f766e"

SANKTIONEN = pd.Timestamp("2022-03-02")
HORMUS = pd.Timestamp("2026-02-28")
CO2_START = pd.Timestamp("2021-01-01")

# Finanzplan des Bundes 2026 bis 2030, Drucksache 21/7301. Steuereinnahmen und
# Nettokreditaufnahme: Tabelle 3 (S. 8); Leistungen an die Rentenversicherung:
# Abschnitt „Rentenversicherungsleistungen“ (S. 27). Die Zinsausgaben kommen aus
# data/processed/bund_zinsausgaben_plan.csv (Tabelle 9).
FINANZPLAN = {
    "steuereinnahmen_mrd_eur": {2026: 387.2, 2027: 394.7, 2028: 406.4, 2029: 416.6, 2030: 437.3},
    "nettokreditaufnahme_mrd_eur": {2026: 98.0, 2027: 118.7, 2028: 148.8, 2029: 152.0, 2030: 167.3},
    "rentenversicherung_mrd_eur": {2027: 132.0, 2030: 164.5},
}


def _layout(figure: go.Figure, titel: str, *, y_titel: str, hoehe: int = HOEHE) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        width=BREITE,
        height=hoehe,
        title={"text": titel, "x": 0.02, "font": {"size": 36, "color": "#111827"}},
        font={"family": "Inter, Segoe UI, Helvetica, Arial, sans-serif", "size": MIN_SCHRIFT},
        margin={"l": 90, "r": 30, "t": 120, "b": 70},
        # Legende unter der Zeichenfläche, damit sie nie den Titel überdeckt.
        legend={
            "orientation": "h", "x": 0, "y": -0.08, "yanchor": "top",
            "font": {"size": MIN_SCHRIFT},
        },
        separators=",.",
    )
    figure.update_yaxes(title_text=y_titel, title_font={"size": MIN_SCHRIFT}, zeroline=False)
    figure.update_xaxes(tickfont={"size": MIN_SCHRIFT})
    figure.update_yaxes(tickfont={"size": MIN_SCHRIFT})
    return figure


def _zahl(wert: float, stellen: int = 1) -> str:
    """Deutsche Zahlenschreibweise für Beschriftungen: 1.234,5."""
    text = f"{wert:,.{stellen}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _marke(figure: go.Figure, datum: pd.Timestamp, text: str, *, y: float = 0.98) -> None:
    figure.add_vline(x=datum, line={"color": ROT, "width": 2, "dash": "dot"})
    figure.add_annotation(
        x=datum,
        y=y,
        yref="paper",
        text=text,
        showarrow=False,
        xanchor="right",
        yanchor="top",
        textangle=-90,
        font={"size": MIN_SCHRIFT, "color": ROT},
        bgcolor="rgba(255,255,255,0.85)",
    )


def _speichern(figure: go.Figure, name: str) -> None:
    BILDER.mkdir(parents=True, exist_ok=True)
    figure.write_image(BILDER / f"{name}.svg")


def _monatsdaten() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rendite = dataset.load_bund_yield()
    monat = rendite.groupby("monat", as_index=False)["rendite_pct"].mean()
    monat["datum"] = pd.to_datetime(monat["monat"])
    zinslast = dataset.load_interest_burden()
    monatszinslast = analysis.monthly_interest_burden(zinslast, monat)
    return monat, zinslast, monatszinslast


def schuldenstand(kennzahlen: dict) -> None:
    jahre = dataset.load_annual_debt()
    staat = jahre[jahre["sector"] == "S13"].dropna(subset=["schulden_mio_eur"])
    staat = staat.sort_values("jahr")
    _, _, monatszinslast = _monatsdaten()
    erstes, letztes = staat.iloc[0], staat.iloc[-1]
    aktuell = monatszinslast.iloc[-1]
    kennzahlen["schulden"] = {
        "erstes_jahr": int(erstes["jahr"]),
        "erstes_mrd_eur": round(erstes["schulden_mio_eur"] / 1000),
        "letztes_jahr": int(letztes["jahr"]),
        "letztes_mrd_eur": round(letztes["schulden_mio_eur"] / 1000),
        "faktor": round(letztes["schulden_mio_eur"] / erstes["schulden_mio_eur"], 1),
        "quote_pct": round(float(letztes["schuldenquote_pct"]), 1),
        "fortgeschrieben_monat": aktuell["monat"],
        "fortgeschrieben_mrd_eur": round(aktuell["schulden_mio_eur"] / 1000),
    }

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=staat["jahr"],
            y=staat["schulden_mio_eur"] / 1000,
            marker_color=TUERKIS,
            name="Schuldenstand am Jahresende",
        )
    )
    for zeile, anker in ((erstes, "left"), (letztes, "right")):
        figure.add_annotation(
            x=zeile["jahr"],
            y=zeile["schulden_mio_eur"] / 1000,
            text=f"<b>{_zahl(zeile['schulden_mio_eur'] / 1e6, 2)} Bio. €</b>",
            showarrow=False,
            xanchor=anker,
            yanchor="bottom",
            yshift=6,
            font={"size": 30, "color": "#111827"},
        )
    _layout(figure, "Schulden des Staates (Bund, Länder,<br>Gemeinden, Sozialversicherung)",
            y_titel="Mrd. €")
    figure.update_layout(showlegend=False)
    _speichern(figure, "schuldenstand")


def haushalt(kennzahlen: dict) -> None:
    """Gestapelte Ausgaben des Bundes gegen die Einnahmen ohne neue Schulden.

    Ausgaben insgesamt und Verteidigung (Einzelplan 14) aus Tabelle 8, Zinsen aus
    Tabelle 9, Rentenversicherung aus dem Textteil; „übrige Ausgaben“ ist der Rest.
    Einnahmen ohne neue Schulden = Ausgaben − Nettokreditaufnahme (Tabelle 3).
    """
    plan = dataset.load_bund_interest_plan().set_index("jahr")["zinsausgaben_mrd_eur"]
    bereiche = dataset.load_bund_budget_areas()
    gesamt = bereiche.groupby("jahr")["ausgaben_mrd_eur"].sum()
    verteidigung = bereiche[bereiche["einzelplan"].astype(int) == 14].set_index("jahr")[
        "ausgaben_mrd_eur"
    ]
    jahre = [2027, 2030]
    werte = {}
    for jahr in jahre:
        rente = FINANZPLAN["rentenversicherung_mrd_eur"][jahr]
        zinsen = float(plan[jahr])
        vert = float(verteidigung[jahr])
        ausgaben = float(gesamt[jahr])
        nka = FINANZPLAN["nettokreditaufnahme_mrd_eur"][jahr]
        werte[jahr] = {
            "rente": rente,
            "zinsen": zinsen,
            "uebrige": ausgaben - rente - zinsen - vert,
            "verteidigung": vert,
            "ausgaben": ausgaben,
            "einnahmen_ohne_schulden": ausgaben - nka,
            "nicht_gedeckt": nka,
        }
    steuern = [FINANZPLAN["steuereinnahmen_mrd_eur"][j] for j in jahre]
    kennzahlen["haushalt"] = {
        "jahre": jahre,
        "steuereinnahmen_mrd_eur": steuern,
        "rentenversicherung_mrd_eur": [werte[j]["rente"] for j in jahre],
        "zinsen_mrd_eur": [werte[j]["zinsen"] for j in jahre],
        "verteidigung_mrd_eur": [round(werte[j]["verteidigung"], 1) for j in jahre],
        "ausgaben_mrd_eur": [round(werte[j]["ausgaben"], 1) for j in jahre],
        "einnahmen_ohne_schulden_mrd_eur": [
            round(werte[j]["einnahmen_ohne_schulden"], 1) for j in jahre
        ],
        "nicht_gedeckt_mrd_eur": [werte[j]["nicht_gedeckt"] for j in jahre],
        "anteil_rente_zinsen_pct": [
            round((werte[j]["rente"] + werte[j]["zinsen"]) / s * 100)
            for j, s in zip(jahre, steuern, strict=True)
        ],
        "nettokreditaufnahme_mrd_eur": FINANZPLAN["nettokreditaufnahme_mrd_eur"],
    }

    x = [str(j) for j in jahre]
    figure = go.Figure()
    for schluessel, name, farbe in (
        ("rente", "Rentenversicherung", BLAU),
        ("zinsen", "Zinsen", ROT),
        ("uebrige", "übrige Ausgaben", "#c7ccd4"),
        ("verteidigung", "Verteidigung", "#4d5a2b"),
    ):
        figure.add_trace(
            go.Bar(
                x=x,
                y=[werte[j][schluessel] for j in jahre],
                name=name,
                marker_color=farbe,
                text=[_zahl(werte[j][schluessel]) for j in jahre],
                textposition="inside",
                insidetextanchor="middle",
                textfont={"size": MIN_SCHRIFT, "color": "#111827" if schluessel == "uebrige"
                          else "#ffffff"},
            )
        )
    for index, jahr in enumerate(jahre):
        einnahmen = werte[jahr]["einnahmen_ohne_schulden"]
        ausgaben = werte[jahr]["ausgaben"]
        # Linie: Einnahmen ohne neue Schulden; darüber ist nichts gedeckt.
        figure.add_shape(
            type="line", x0=index - 0.42, x1=index + 0.42, y0=einnahmen, y1=einnahmen,
            line={"color": "#111827", "width": 5, "dash": "dash"},
        )
        figure.add_shape(
            type="rect", x0=index - 0.4, x1=index + 0.4, y0=einnahmen, y1=ausgaben,
            line={"color": ROT, "width": 4}, fillcolor="rgba(0,0,0,0)",
        )
        figure.add_annotation(
            x=index, y=ausgaben, yshift=12, showarrow=False, yanchor="bottom",
            text=f"<b>nicht gedeckt:<br>{_zahl(werte[jahr]['nicht_gedeckt'])} Mrd. €</b>",
            font={"size": MIN_SCHRIFT + 4, "color": ROT},
        )
    figure.add_annotation(
        x=-0.5, xanchor="left", y=werte[jahre[0]]["einnahmen_ohne_schulden"], yshift=-4,
        yanchor="top", showarrow=False, text="Einnahmen ohne<br>neue Schulden",
        font={"size": MIN_SCHRIFT, "color": "#111827"}, bgcolor="rgba(255,255,255,0.8)",
    )
    _layout(figure, "Bundeshaushalt: Ausgaben und<br>Einnahmen ohne neue Schulden",
            y_titel="Mrd. €", hoehe=1100)
    figure.update_layout(barmode="stack", bargap=0.2, margin={"b": 190})
    # Jahreszahlen als Kategorien, sonst baut Plotly eine Zahlenachse von 0 bis 2030.
    # Linien und Beschriftungen stehen deshalb an den Positionen 0 und 1.
    figure.update_xaxes(type="category", range=[-0.55, 1.55])
    figure.update_yaxes(range=[0, 760])
    _speichern(figure, "haushalt")


def rendite(kennzahlen: dict) -> None:
    monat, _, _ = _monatsdaten()
    tage = dataset.load_bund_yield().set_index("datum")["rendite_pct"]
    dez21 = monat.set_index("monat").loc["2021-12", "rendite_pct"]
    feb22 = monat.set_index("monat").loc["2022-02", "rendite_pct"]
    dez22 = monat.set_index("monat").loc["2022-12", "rendite_pct"]
    feb26 = monat.set_index("monat").loc["2026-02", "rendite_pct"]
    letzter = monat.iloc[-1]
    kennzahlen["rendite"] = {
        "dez_2021_pct": round(dez21, 2),
        "feb_2022_pct": round(feb22, 2),
        "dez_2022_pct": round(dez22, 2),
        "anstieg_2022_pp": round(dez22 - dez21, 2),
        "vor_sanktionen_pp": round(feb22 - dez21, 2),
        "feb_2026_pct": round(feb26, 2),
        "letzter_monat": letzter["monat"],
        "letzter_pct": round(letzter["rendite_pct"], 2),
        "anstieg_seit_hormus_pp": round(letzter["rendite_pct"] - feb26, 2),
        "letzter_tag": str(tage.index.max().date()),
    }

    ab = monat[monat["datum"] >= "2015-01-01"]
    figure = go.Figure(
        go.Scatter(x=ab["datum"], y=ab["rendite_pct"], line={"color": BLAU, "width": 4},
                   name="10-jährige Bundesanleihe")
    )
    figure.add_hline(y=0, line={"color": "#9ca3af", "width": 1})
    figure.add_vrect(x0="2021-12-01", x1="2022-12-31", fillcolor=ROT, opacity=0.08, line_width=0)
    figure.add_vrect(x0=HORMUS, x1=letzter["datum"], fillcolor=GOLD, opacity=0.15, line_width=0)
    _marke(figure, SANKTIONEN, "Russland-Sanktionen")
    _marke(figure, HORMUS, "Iran-Krieg / Hormus")
    figure.add_annotation(
        x="2021-10-01", y=2.6, showarrow=False, xanchor="right",
        font={"size": MIN_SCHRIFT, "color": ROT},
        text=f"<b>2022: +{_zahl(kennzahlen['rendite']['anstieg_2022_pp'])} Prozentpunkte</b>",
    )
    figure.add_annotation(
        x="2025-09-01", y=4.15, showarrow=False, xanchor="right",
        font={"size": MIN_SCHRIFT, "color": "#8a6d00"},
        text=f"<b>seit Feb. 2026: +{_zahl(kennzahlen['rendite']['anstieg_seit_hormus_pp'])}</b>",
    )
    _layout(figure, "Rendite der 10-jährigen Bundesanleihe<br>(Monatsmittel)", y_titel="%")
    figure.update_layout(showlegend=False)
    figure.update_yaxes(range=[-1, 4.5])
    _speichern(figure, "rendite")


def rendite_international(kennzahlen: dict) -> None:
    vergleich = pd.read_csv(dataset.PROCESSED_DIR / dataset.INTERNATIONAL_YIELDS)
    laender = {
        "Deutschland": BLAU,
        "Frankreich": "#7c3aed",
        "Italien": GRUEN,
        "Vereinigte Staaten": ROT,
    }
    fenster = vergleich[vergleich["monat"].between("2021-07", "2022-06")]
    breit = fenster.pivot_table(index="monat", columns="land", values="rendite_pct")
    kennzahlen["international"] = {
        land: round(float(breit.loc["2022-02", land] - breit.loc["2021-12", land]), 2)
        for land in [*laender, "Niederlande", "Schweden"]
    }

    figure = go.Figure()
    for land, farbe in laender.items():
        figure.add_trace(
            go.Scatter(
                x=pd.to_datetime(breit.index),
                y=breit[land],
                name=land,
                line={"color": farbe, "width": 4},
            )
        )
    figure.add_vrect(x0="2021-12-01", x1="2022-02-28", fillcolor=GOLD, opacity=0.2, line_width=0)
    _marke(figure, SANKTIONEN, "Russland-Sanktionen")
    figure.add_annotation(
        x="2022-01-15", y=3.5, showarrow=False, font={"size": MIN_SCHRIFT, "color": "#8a6d00"},
        text="<b>Dez. 2021 – Feb. 2022</b>",
    )
    _layout(figure, "Rendite 10-jähriger Staatsanleihen<br>im Vergleich", y_titel="%")
    _speichern(figure, "rendite_international")


def inflation_leitzins(kennzahlen: dict) -> None:
    inflation = dataset.load_inflation_germany()
    leitzinsen = dataset.load_key_rates()
    ab = inflation[inflation["monat"] >= "2019-01"].dropna(subset=["hvpi_pct"])
    spitze = ab.loc[ab["hvpi_pct"].idxmax()]
    ezb = leitzinsen[leitzinsen["leitzins"] == "EZB Einlagesatz"].sort_values("datum")
    ezb = analysis.extend_steps(ezb, pd.Timestamp("2026-11-17"), "leitzins")
    erste_erhoehung = ezb[(ezb["datum"] >= "2022-01-01") & (ezb["zins_pct"].diff() > 0)].iloc[0]
    kennzahlen["inflation"] = {
        "dez_2020_pct": float(inflation.set_index("monat").loc["2020-12", "hvpi_pct"]),
        "jan_2021_pct": float(inflation.set_index("monat").loc["2021-01", "hvpi_pct"]),
        "spitze_monat": spitze["monat"],
        "spitze_pct": float(spitze["hvpi_pct"]),
        "erste_ezb_erhoehung": str(erste_erhoehung["datum"].date()),
        "ezb_einlagesatz_max_pct": float(ezb["zins_pct"].max()),
    }

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=pd.to_datetime(ab["monat"]), y=ab["hvpi_pct"], name="Inflation (HVPI)",
                   line={"color": GOLD, "width": 4})
    )
    ezb_ab = ezb[ezb["datum"] >= "2019-01-01"]
    figure.add_trace(
        go.Scatter(x=ezb_ab["datum"], y=ezb_ab["zins_pct"], name="EZB-Einlagesatz",
                   line={"color": BLAU, "width": 4, "shape": "hv"})
    )
    figure.add_hline(y=0, line={"color": "#9ca3af", "width": 1})
    _marke(figure, CO2_START, "CO₂-Preis 25 €/t")
    _marke(figure, SANKTIONEN, "Russland-Sanktionen")
    _layout(figure, "Inflation in Deutschland und<br>Leitzins der EZB", y_titel="%")
    figure.update_xaxes(range=["2019-01-01", "2026-12-31"])
    _speichern(figure, "inflation_leitzins")


def co2_preis(kennzahlen: dict) -> None:
    preise = dataset.load_co2_price()
    aufschlag = dataset.load_co2_surcharge()
    anteil = analysis.co2_share_of_consumer_price(
        aufschlag, dataset.load_energy_markets(), dataset.load_fuel_prices(), 2021
    ).set_index("brennstoff")
    heizoel = aufschlag[aufschlag["brennstoff"] == "Heizöl EL"].set_index("jahr")
    kennzahlen["co2"] = {
        "preise": {int(j): [int(a), int(b)] for j, a, b in preises_tupel(preise)},
        "heizoel_2021_ct_l": round(float(heizoel.loc[2021, "aufschlag_max_brutto_ct"]), 1),
        "heizoel_2026_ct_l": round(float(heizoel.loc[2026, "aufschlag_max_brutto_ct"]), 1),
        "anteil_2021_pct": {b: round(float(anteil.loc[b, "anteil_pct"])) for b in anteil.index},
    }

    stufen = preise.assign(datum=pd.to_datetime(preise["jahr"].astype(str) + "-01-01"), r="co2")
    stufen = analysis.extend_steps(stufen, pd.Timestamp("2027-12-31"), "r")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=stufen["datum"], y=stufen["preis_min_eur_t"], mode="lines",
                   line={"color": GRUEN, "width": 4, "shape": "hv"}, name="Festpreis")
    )
    figure.add_trace(
        go.Scatter(x=stufen["datum"], y=stufen["preis_max_eur_t"], mode="lines", fill="tonexty",
                   fillcolor="rgba(46,125,50,0.15)", name="Preiskorridor",
                   line={"color": GRUEN, "width": 4, "shape": "hv"})
    )
    for jahr, unten, oben in preises_tupel(preise):
        text = f"{unten}" if unten == oben else f"{unten}–{oben}"
        figure.add_annotation(
            x=pd.Timestamp(f"{jahr}-07-01"), y=oben, text=f"<b>{text}</b>", showarrow=False,
            yanchor="bottom", font={"size": MIN_SCHRIFT, "color": GRUEN},
        )
    _layout(figure, "CO₂-Preis auf Heizöl, Erdgas und<br>Kraftstoffe (€ je Tonne)", y_titel="€/t")
    figure.update_layout(showlegend=False)
    figure.update_yaxes(range=[0, 80])
    figure.update_xaxes(range=["2020-07-01", "2028-01-31"], dtick="M12", tickformat="%Y")
    _speichern(figure, "co2_preis")


def preises_tupel(preise: pd.DataFrame) -> list[tuple[int, int, int]]:
    return [
        (int(j), int(a), int(b))
        for j, a, b in preise[["jahr", "preis_min_eur_t", "preis_max_eur_t"]].itertuples(
            index=False
        )
    ]


def zinslast(kennzahlen: dict) -> None:
    _, jahre, monate = _monatsdaten()
    plan = dataset.load_bund_interest_plan()
    m = monate.set_index("monat")
    tief = m.loc["2021-12", "zins_theoretisch_mio_eur"] / 1000
    okt22 = m.loc["2022-10", "zins_theoretisch_mio_eur"] / 1000
    aktuell = monate.iloc[-1]
    tats = jahre.set_index("jahr")
    kennzahlen["zinslast"] = {
        "dez_2021_mrd_eur": round(tief, 1),
        "okt_2022_mrd_eur": round(okt22, 1),
        "anstieg_10_monate_mrd_eur": round(okt22 - tief),
        "aktuell_monat": aktuell["monat"],
        "aktuell_mrd_eur": round(aktuell["zins_theoretisch_mio_eur"] / 1000, 1),
        "tatsaechlich_2021_mrd_eur": round(tats.loc[2021, "zinsausgaben_mio_eur"] / 1000, 1),
        "tatsaechlich_2025_mrd_eur": round(tats.loc[2025, "zinsausgaben_mio_eur"] / 1000, 1),
        "effektivzins_2021_pct": float(tats.loc[2021, "effektivzins_pct"]),
        "effektivzins_2025_pct": float(tats.loc[2025, "effektivzins_pct"]),
        "einnahmen_staat_2025_mrd_eur": round(tats.loc[2025, "einnahmen_mio_eur"] / 1000),
    }

    ab = monate[monate["datum"] >= "2019-01-01"]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(x=ab["datum"], y=ab["zins_theoretisch_mio_eur"] / 1000,
                   name="theoretisch (Schulden × Rendite)", line={"color": BLAU, "width": 4})
    )
    seit = tats.loc[2019:]
    figure.add_trace(
        go.Scatter(x=pd.to_datetime(seit.index.astype(str) + "-07-01"),
                   y=seit["zinsausgaben_mio_eur"] / 1000, name="tatsächlich gezahlt (Staat)",
                   mode="lines+markers", line={"color": ROT, "width": 4}, marker={"size": 12})
    )
    figure.add_trace(
        go.Scatter(x=pd.to_datetime(plan["jahr"].astype(str) + "-07-01"),
                   y=plan["zinsausgaben_mrd_eur"], name="Plan Bund (Finanzplan)",
                   mode="lines+markers", line={"color": "#6a3d9a", "width": 4, "dash": "dash"},
                   marker={"size": 12})
    )
    figure.add_hline(y=0, line={"color": "#9ca3af", "width": 1})
    _marke(figure, SANKTIONEN, "Russland-Sanktionen")
    _marke(figure, HORMUS, "Iran-Krieg / Hormus")
    _layout(figure, "Zinslast: theoretisch, tatsächlich<br>und geplant (Mrd. € pro Jahr)",
            y_titel="Mrd. €", hoehe=1080)
    figure.update_layout(margin={"b": 170})
    figure.update_xaxes(range=["2019-01-01", "2030-12-31"])
    _speichern(figure, "zinslast")


def zerlegung(kennzahlen: dict) -> None:
    """Was steckt in der theoretischen Zinslast? Rendite- und Schuldeneffekt je Zeitraum."""
    _, _, monate = _monatsdaten()
    m = monate.set_index("monat")
    aktuell = monate.iloc[-1]
    schulden = aktuell["schulden_mio_eur"] / 1000
    r = kennzahlen["rendite"]
    teile = {
        "Renditeanstieg 2022": r["anstieg_2022_pp"] / 100 * schulden,
        "Renditeanstieg seit<br>Iran-Krieg (Feb. 2026)": (
            r["anstieg_seit_hormus_pp"] / 100 * schulden
        ),
        "Schulden-Zuwachs<br>seit Ende 2021": (
            (schulden - m.loc["2021-12", "schulden_mio_eur"] / 1000) * aktuell["rendite_pct"] / 100
        ),
    }
    kennzahlen["zerlegung"] = {
        "schulden_aktuell_mrd_eur": round(schulden),
        "schulden_zuwachs_mrd_eur": round(schulden - m.loc["2021-12", "schulden_mio_eur"] / 1000),
        "mrd_eur": {k.replace("<br>", " "): round(v) for k, v in teile.items()},
    }

    figure = go.Figure(
        go.Bar(
            y=list(teile),
            x=list(teile.values()),
            orientation="h",
            marker_color=[ROT, GOLD, TUERKIS],
            text=[f"<b>≈ {_zahl(v, 0)} Mrd. €</b>" for v in teile.values()],
            textposition="outside",
            textfont={"size": MIN_SCHRIFT},
        )
    )
    _layout(figure, "Wie viel Zinslast pro Jahr<br>geht auf welchen Anstieg zurück?",
            y_titel="", hoehe=880)
    figure.update_layout(showlegend=False, margin={"l": 330, "r": 40})
    figure.update_yaxes(autorange="reversed", tickfont={"size": MIN_SCHRIFT})
    figure.update_xaxes(range=[0, 115], title_text="Mrd. € pro Jahr (bei heutigem Schuldenstand)",
                        title_font={"size": MIN_SCHRIFT})
    _speichern(figure, "zerlegung")


def frankreich(kennzahlen: dict) -> None:
    """Theoretische Zinslast im Vergleich: Deutschland und Frankreich, gleiche Rechnung.

    Schuldenstand am Ende des letzten Jahres × jüngste 10-jährige Rendite (Eurostat)
    mit ``analysis.theoretical_interest_by_country`` – dieselbe Rechnung wie auf der
    App-Seite Zinsvergleich. Dazu die tatsächlich gezahlten Zinsen desselben Jahres.
    """
    schulden = dataset.load_laender_debt()
    haushalt = dataset.load_laender_budget()
    renditen = pd.read_csv(dataset.PROCESSED_DIR / dataset.INTERNATIONAL_YIELDS)
    laender = ["Deutschland", "Frankreich", "Italien"]
    theorie = analysis.theoretical_interest_by_country(
        schulden[schulden["land"].isin(laender)],
        haushalt[haushalt["land"].isin(laender)],
        renditen[renditen["land"].isin(laender)],
    ).set_index("land")
    je_person = analysis.interest_per_working_age(
        theorie.reset_index(), dataset.load_working_age()
    ).set_index("land")
    gezahlt = haushalt[haushalt["land"].isin(laender)].dropna(subset=["zinsausgaben_mio_eur"])
    gezahlt = gezahlt.sort_values("jahr").groupby("land").tail(1).set_index("land")

    werte = {}
    for land in laender:
        zeile = theorie.loc[land]
        werte[land] = {
            "schulden_jahr": int(zeile["jahr"]),
            "schulden_mrd_eur": round(zeile["schulden_mio_eur"] / 1000),
            "schuldenquote_pct": round(float(zeile["schuldenquote_pct"]), 1),
            "rendite_monat": zeile["monat"],
            "rendite_pct": round(float(zeile["rendite_pct"]), 2),
            "theoretisch_mrd_eur": round(zeile["zins_theoretisch_mio_eur"] / 1000, 1),
            "quote_einnahmen_pct": round(float(zeile["zins_quote_einnahmen_pct"]), 1),
            "je_einwohner_eur": round(float(zeile["zins_je_einwohner_eur"]), -1),
            "bevoelkerung_20_59_jahr": int(je_person.loc[land, "bevoelkerung_jahr"]),
            "bevoelkerung_20_59_mio": round(je_person.loc[land, "bevoelkerung_20_59"] / 1e6, 1),
            "je_person_20_59_eur": round(
                float(je_person.loc[land, "zins_je_person_20_59_eur"]), -1
            ),
            "gezahlt_jahr": int(gezahlt.loc[land, "jahr"]),
            "gezahlt_mrd_eur": round(gezahlt.loc[land, "zinsausgaben_mio_eur"] / 1000, 1),
        }
    kennzahlen["frankreich_vergleich"] = werte

    figure = go.Figure()
    for schluessel, name, farben in (
        ("gezahlt_mrd_eur", f"tatsächlich gezahlt {werte['Frankreich']['gezahlt_jahr']}",
         ["#9db4cc", "#c9b3e6", "#a5d6a7"]),
        ("theoretisch_mrd_eur", "zum aktuellen Marktzins", [BLAU, "#7c3aed", GRUEN]),
    ):
        figure.add_trace(
            go.Bar(
                y=laender,
                x=[werte[land][schluessel] for land in laender],
                name=name,
                orientation="h",
                marker_color=farben,
                text=[f"<b>{_zahl(werte[land][schluessel], 0)} Mrd. €</b>" for land in laender],
                textposition="outside",
                textfont={"size": MIN_SCHRIFT + 2},
            )
        )
    _layout(figure, "Zinsen pro Jahr: gezahlt und<br>zum aktuellen Marktzins", y_titel="",
            hoehe=840)
    figure.update_layout(barmode="group", bargap=0.12, margin={"l": 230, "r": 40, "b": 150})
    figure.update_yaxes(autorange="reversed")
    # Die Einheit steht an jedem Balken; ein Achsentitel würde die Legende überdecken.
    figure.update_xaxes(range=[0, 225])
    # Die Balken einer Gruppe unterscheiden sich nur in der Helligkeit; die Legende
    # zeigt deshalb neutrale Farben.
    figure.update_traces(showlegend=False)
    for name, farbe in ((f"tatsächlich gezahlt {werte['Frankreich']['gezahlt_jahr']}",
                         "#c7ccd4"), ("zum aktuellen Marktzins", "#4b5563")):
        figure.add_trace(go.Bar(x=[None], y=[None], name=name, marker_color=farbe,
                                orientation="h", showlegend=True))
    _speichern(figure, "vergleich_frankreich")


def main() -> None:
    kennzahlen: dict = {"quelle": "data/processed, Finanzplan des Bundes (Drucksache 21/7301)"}
    for schritt in (
        schuldenstand,
        haushalt,
        rendite,
        rendite_international,
        inflation_leitzins,
        co2_preis,
        zinslast,
        zerlegung,
        frankreich,
    ):
        schritt(kennzahlen)
    (ORDNER / "kennzahlen.json").write_text(
        json.dumps(kennzahlen, indent=2, ensure_ascii=False, default=float) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(kennzahlen, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
