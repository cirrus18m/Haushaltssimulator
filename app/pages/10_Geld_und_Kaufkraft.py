"""Geldmenge und Kaufkraft: M3-Wachstum und Inflationswirkung."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import ui

st.title("Geld und Kaufkraft")
st.markdown(
    "Die Geldmenge M3 im Euro-Raum und die daraus folgende Preisentwicklung. Der "
    "Kaufkraftindex zeigt, wie viel ein Euro nach Abzug der Inflation noch wert ist. "
    "Grundlage sind die Zeitreihen der Europäischen Zentralbank."
)

geld = ui.money_supply()
kaufkraft = ui.purchasing_power()
if geld.empty or kaufkraft.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

letzte_geld = geld.dropna(subset=["wachstum_pct"]).iloc[-1]
letzte_kaufkraft = kaufkraft.dropna(subset=["inflation_de_pct"]).iloc[-1]
erste_kaufkraft = kaufkraft.dropna(subset=["inflation_de_pct"]).iloc[0]
verlust = 100 - letzte_kaufkraft["kaufkraft_index"]
retrieved = ui.data_retrieved_at()

columns = st.columns(4)
columns[0].metric(
    "M3-Wachstum (Jahresrate)",
    ui.format_number(letzte_geld["wachstum_pct"], 1, " %"),
    f"Stand {letzte_geld['monat']}",
    delta_color="off",
)
columns[1].metric(
    "M3-Index",
    ui.format_number(letzte_geld["index_m3"], 1),
    "Dezember 2010 = 100",
    delta_color="off",
)
columns[2].metric(
    "Inflation Deutschland",
    ui.format_number(letzte_kaufkraft["inflation_de_pct"], 1, " %"),
    f"Stand {letzte_kaufkraft['monat']}",
    delta_color="inverse",
)
columns[3].metric(
    "Kaufkraftverlust seit 1997",
    ui.format_number(verlust, 1, " %"),
    "kumuliert nach HVPI",
    delta_color="off",
)

st.divider()
st.header("1. Geldmenge M3")
figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Scatter(
        x=geld["monat"],
        y=geld["index_m3"],
        name="M3-Index (Dez. 2010 = 100)",
        line={"color": "#1f4e79", "width": 2.5},
        hovertemplate="%{y:.1f}<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=geld["monat"],
        y=geld["wachstum_pct"],
        name="Wachstum gegenüber Vorjahr (%)",
        line={"color": "#c9a227", "width": 1.8, "dash": "dot"},
        hovertemplate="%{y:.1f} %<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_yaxes(title_text="Index", secondary_y=False)
figure.update_yaxes(title_text="% gegenüber Vorjahr", secondary_y=True)
figure.add_hline(y=0, line={"color": "#999", "width": 1}, secondary_y=True)
ui.plot(figure, filename="geldmenge_m3", height=420)

st.header("2. Inflation und Kaufkraft")
figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=kaufkraft["monat"],
        y=kaufkraft["inflation_de_pct"],
        name="Deutschland",
        line={"color": "#1f4e79", "width": 1.8},
        hovertemplate="%{y:.1f} %<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=kaufkraft["monat"],
        y=kaufkraft["inflation_ea_pct"],
        name="Euro-Raum",
        line={"color": "#b03a2e", "width": 1.8},
        hovertemplate="%{y:.1f} %<extra></extra>",
    )
)
figure.add_hline(y=2, line={"color": "#c9a227", "dash": "dash"})
figure.update_yaxes(title_text="Veränderung gegenüber Vorjahr in %")
ui.plot(figure, filename="kaufkraft_inflation", height=380)

figure = go.Figure(
    go.Scatter(
        x=kaufkraft["monat"],
        y=kaufkraft["kaufkraft_index"],
        name="Kaufkraft eines Euro",
        line={"color": "#2e7d32", "width": 2.5},
        fill="tozeroy",
        fillcolor="rgba(46,125,50,0.08)",
        hovertemplate="%{y:.1f}<extra></extra>",
    )
)
figure.update_yaxes(title_text="Index (Start = 100)")
ui.plot(figure, filename="kaufkraft_index", height=380)

with st.expander("Berechnung"):
    st.markdown(
        "Der Kaufkraftindex beginnt im ersten verfügbaren Monat bei 100 und wird mit der "
        "monatlichen Inflationsrate fortgeschrieben: "
        "`Index(t) = Index(t-1) × (1 + Jahresrate/100)^(-1/12)`. Die Jahresrate stammt "
        "aus dem harmonisierten Verbraucherpreisindex (HVPI).\n\n"
        f"Vom {erste_kaufkraft['monat']} bis {letzte_kaufkraft['monat']} ist der Index "
        f"von 100 auf {ui.format_number(letzte_kaufkraft['kaufkraft_index'], 1)} gefallen. "
        "Das entspricht dem kumulierten Kaufkraftverlust."
    )

st.caption(
    "Quellen: Europäische Zentralbank, Data Portal, BSI (Geldmenge M3) und ICP "
    "(HVPI Deutschland und Euro-Raum)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
