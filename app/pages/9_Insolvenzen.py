"""Unternehmensinsolvenzen: Langreihe, Verfahrensausgang und aktuelle Forderungen."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Insolvenzen")
st.markdown(
    "Beantragte Insolvenzverfahren von Unternehmen in Deutschland ab 2003. Die "
    "Langreihe stammt aus der GENESIS-Tabelle 52411-0017 (Monate, Größenklassen), die "
    "aktuellen Forderungen und betroffenen Arbeitnehmer aus den Tabellen 52411-0002 und "
    "52411-0011."
)

insolvenzen = ui.insolvencies()
if insolvenzen.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

retrieved = ui.data_retrieved_at()
unternehmen = insolvenzen.dropna(subset=["verfahren_unternehmen"]).reset_index(drop=True)
letzte = unternehmen.iloc[-1]

vorjahres_monat = f"{int(letzte['jahr']) - 1}-{letzte['monat'][5:7]}"
vorjahr = unternehmen[unternehmen["monat"] == vorjahres_monat]
vorjahres_wert = vorjahr.iloc[0]["verfahren_unternehmen"] if not vorjahr.empty else float("nan")
veraenderung = letzte["verfahren_unternehmen"] - vorjahres_wert
veraenderung_pct = veraenderung / vorjahres_wert * 100 if vorjahres_wert else float("nan")

summe_12 = unternehmen["verfahren_unternehmen"].tail(12).sum()
summe_vorjahr_12 = unternehmen["verfahren_unternehmen"].iloc[-24:-12].sum()
summe_delta_pct = (summe_12 / summe_vorjahr_12 - 1) * 100 if summe_vorjahr_12 else float("nan")

columns = st.columns(4)
columns[0].metric(
    "Unternehmensinsolvenzen",
    ui.format_number(letzte["verfahren_unternehmen"], 0),
    f"{ui.format_number(veraenderung, 0)} zum Vorjahr",
    delta_color="inverse",
)
columns[1].metric(
    "Letzte 12 Monate",
    ui.format_number(summe_12, 0),
    f"{ui.format_number(summe_delta_pct, 1)} % zum Vorjahr",
    delta_color="inverse",
)
columns[2].metric(
    "Forderungen (Mrd. €)",
    ui.format_number(letzte["forderungen_unternehmen_mio_eur"] / 1000, 2),
    "voraussichtlich",
    delta_color="off",
)
columns[3].metric(
    "Arbeitnehmer",
    ui.format_number(letzte["betroffene_arbeitnehmer"], 0),
    "betroffen",
    delta_color="off",
)

st.divider()
st.header("1. Unternehmensinsolvenzen seit 2003")
verlauf = unternehmen.set_index("monat")["verfahren_unternehmen"]
gleitend = verlauf.rolling(12, min_periods=12).mean()

figure = go.Figure()
figure.add_trace(
    go.Bar(
        x=verlauf.index,
        y=verlauf,
        name="Verfahren je Monat",
        marker_color="#7fb2d5",
        hovertemplate="%{y:,.0f}<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=gleitend.index,
        y=gleitend,
        name="12-Monats-Mittel",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:,.0f}<extra></extra>",
    )
)
figure.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
ui.plot(figure, filename="insolvenzen_langreihe", height=440)

st.header("2. Verfahrensausgang")
letzte_36 = insolvenzen.dropna(subset=["verfahren_unternehmen"]).tail(36)
figure = go.Figure()
for spalte, name, farbe in [
    ("eroeffnet_unternehmen", "eröffnet", "#1f4e79"),
    ("abgewiesen_unternehmen", "mangels Masse abgewiesen", "#b03a2e"),
    ("schuldenbereinigungsplan_unternehmen", "Schuldenbereinigungsplan", "#c9a227"),
]:
    if letzte_36[spalte].notna().sum() == 0:
        continue
    figure.add_trace(
        go.Bar(
            x=letzte_36["monat"],
            y=letzte_36[spalte].fillna(0),
            name=name,
            marker_color=farbe,
            hovertemplate="%{y:,.0f}<extra>" + name + "</extra>",
        )
    )
figure.update_layout(barmode="stack")
figure.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
ui.plot(figure, filename="insolvenzen_ausgang", height=400)

st.header("3. Aktuelles Berichtsjahr: alle Verfahren")
aktuell = insolvenzen.dropna(subset=["verfahren_gesamt"])
if aktuell.empty:
    st.info("Für das aktuelle Berichtsjahr liegen noch keine Gesamtzahlen vor.")
else:
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=aktuell["monat"],
            y=aktuell["verfahren_gesamt"],
            name="Verfahren insgesamt",
            marker_color="#7fb2d5",
            hovertemplate="%{y:,.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            x=aktuell["monat"],
            y=aktuell["verfahren_unternehmen"],
            name="Unternehmensinsolvenzen",
            marker_color="#1f4e79",
            hovertemplate="%{y:,.0f}<extra></extra>",
        )
    )
    figure.update_layout(barmode="group")
    figure.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
    ui.plot(figure, filename="insolvenzen_berichtsjahr", height=380)

st.subheader("Monatswerte")
tabelle = (
    insolvenzen.drop(columns=["jahr"])
    .tail(24)
    .rename(
        columns={
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
    )
)
st.dataframe(tabelle, hide_index=True, width="stretch")

with st.expander("Datenlage und Abgrenzung"):
    st.markdown(
        "Die Langreihe 52411-0017 weist beantragte Insolvenzverfahren von Unternehmen "
        "nach Unternehmensgrößenklassen aus (Zeile „Insgesamt“). Die Werte sind "
        "vorläufig und werden nachgemeldet. Gesamtzahlen aller Verfahren, Forderungen "
        "und betroffene Arbeitnehmer stehen für das laufende Berichtsjahr aus den "
        "Tabellen 52411-0002 und 52411-0011 zur Verfügung.\n\n"
        "Der Schuldenbereinigungsplan ist erst ab 2021 ausgewiesen; davor ist die "
        "Position nicht anwendbar."
    )

st.caption(
    "Quellen: Statistisches Bundesamt, GENESIS-Online 52411-0017 (Langreihe), "
    "52411-0002 und 52411-0011 (aktuelles Berichtsjahr)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
