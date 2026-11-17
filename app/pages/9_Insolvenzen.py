"""Unternehmensinsolvenzen: Verfahren, Forderungen und betroffene Arbeitnehmer."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import ui

st.title("Insolvenzen")
st.markdown(
    "Beantragte Insolvenzverfahren in Deutschland nach der amtlichen "
    "Insolvenzstatistik. Die Tabelle des Statistischen Bundesamts liefert das laufende "
    "Berichtsjahr; die Werte werden monatlich nachgemeldet."
)

insolvenzen = ui.insolvencies()
if insolvenzen.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

letzte = insolvenzen.iloc[-1]
vorher = insolvenzen.iloc[-2] if len(insolvenzen) > 1 else letzte
retrieved = ui.data_retrieved_at()

st.subheader(f"Stand {letzte['monat']}")
columns = st.columns(4)
columns[0].metric(
    "Verfahren insgesamt",
    ui.format_number(letzte["verfahren_gesamt"], 0),
    f"{ui.format_number(letzte['verfahren_gesamt'] - vorher['verfahren_gesamt'], 0)} zum Vormonat",
    delta_color="inverse",
)
columns[1].metric(
    "davon Unternehmen",
    ui.format_number(letzte["verfahren_unternehmen"], 0),
    f"{ui.format_number(letzte['verfahren_unternehmen'] - vorher['verfahren_unternehmen'], 0)} "
    "zum Vormonat",
    delta_color="inverse",
)
columns[2].metric(
    "Forderungen (Mrd. €)",
    ui.format_number(letzte["forderungen_unternehmen_mio_eur"] / 1000, 2),
    "Unternehmen, voraussichtlich",
    delta_color="off",
)
columns[3].metric(
    "Arbeitnehmer",
    ui.format_number(letzte["betroffene_arbeitnehmer"], 0),
    "in Unternehmensverfahren",
    delta_color="off",
)

figure = go.Figure()
figure.add_trace(
    go.Bar(
        x=insolvenzen["monat"],
        y=insolvenzen["verfahren_gesamt"],
        name="Verfahren insgesamt",
        marker_color="#7fb2d5",
        hovertemplate="%{y:,.0f}<extra></extra>",
    )
)
figure.add_trace(
    go.Bar(
        x=insolvenzen["monat"],
        y=insolvenzen["verfahren_unternehmen"],
        name="Unternehmensinsolvenzen",
        marker_color="#1f4e79",
        hovertemplate="%{y:,.0f}<extra></extra>",
    )
)
figure.update_layout(barmode="group")
figure.update_yaxes(title_text="Verfahren je Monat", rangemode="tozero")
ui.plot(figure, filename="insolvenzen_verfahren", height=420)

figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Bar(
        x=insolvenzen["monat"],
        y=insolvenzen["forderungen_unternehmen_mio_eur"],
        name="Forderungen Unternehmen (Mio. €)",
        marker_color="#b03a2e",
        hovertemplate="%{y:,.0f} Mio. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=insolvenzen["monat"],
        y=insolvenzen["betroffene_arbeitnehmer"],
        name="betroffene Arbeitnehmer",
        line={"color": "#c9a227", "width": 2},
        hovertemplate="%{y:,.0f}<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_yaxes(title_text="Mio. €", secondary_y=False)
figure.update_yaxes(title_text="Arbeitnehmer", secondary_y=True)
ui.plot(figure, filename="insolvenzen_forderungen", height=400)

with st.expander("Datenlage und Abgrenzung"):
    st.markdown(
        "Die GENESIS-Tabelle 52411-0002 enthält das laufende Berichtsjahr; ältere "
        "Monatswerte sind über den GENESIS-Webservice nur mit Zeitraumfilter und "
        "Zugangskennung abrufbar. Deshalb zeigt die Seite die verfügbaren Monate des "
        "aktuellen Jahres. Die Werte sind vorläufig und werden nachgemeldet.\n\n"
        "Die Tabelle 52411-0011 weist die Unternehmensinsolvenzen nach Rechtsformen aus; "
        "dargestellt ist die Zeile „Insgesamt“."
    )

st.subheader("Monatswerte")
tabelle = insolvenzen.drop(columns=["jahr"]).rename(
    columns={
        "monat": "Monat",
        "verfahren_gesamt": "Verfahren insgesamt",
        "verfahren_unternehmen": "Unternehmen",
        "forderungen_gesamt_mio_eur": "Forderungen gesamt (Mio. €)",
        "forderungen_unternehmen_mio_eur": "Forderungen Unternehmen (Mio. €)",
        "betroffene_arbeitnehmer": "betroffene Arbeitnehmer",
    }
)
st.dataframe(tabelle, hide_index=True, width="stretch")

st.caption(
    "Quelle: Statistisches Bundesamt, GENESIS-Online 52411-0002 und 52411-0011. "
    + (f"Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
