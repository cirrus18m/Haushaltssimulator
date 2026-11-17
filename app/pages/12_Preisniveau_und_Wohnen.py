"""Big-Mac-Index und Eigentumsquote: Preisniveau und Wohnen in Europa."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Preisniveau und Wohnen")
st.markdown(
    "Der Big-Mac-Index vergleicht Preisniveaus über Länder (der Economist weist den "
    "Euro-Raum als eigene Reihe aus), die Eigentumsquote zeigt, "
    "wie viele Haushalte in Europa im Eigentum wohnen. Beide Reihen ergänzen die "
    "Schuldenanalyse um die Vermögens- und Lebenshaltungskostenseite."
)

big_mac = ui.big_mac()
eigentum = ui.homeownership()
if big_mac.empty or eigentum.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

retrieved = ui.data_retrieved_at()

st.header("1. Big-Mac-Index")
letzter_termin = big_mac["datum"].max()
aktuell = big_mac[big_mac["datum"] == letzter_termin].sort_values("preis_usd", ascending=False)
teuerstes = aktuell.iloc[0]
billigstes = aktuell.iloc[-1]

columns = st.columns(3)
columns[0].metric(
    "Teuerster Big Mac",
    f"{ui.format_number(teuerstes['preis_usd'], 2)} $",
    str(teuerstes["land"]),
    delta_color="off",
)
columns[1].metric(
    "Günstigster Big Mac",
    f"{ui.format_number(billigstes['preis_usd'], 2)} $",
    str(billigstes["land"]),
    delta_color="off",
)
columns[2].metric(
    "Stand",
    f"{letzter_termin:%m/%Y}",
    f"{len(aktuell)} Länder",
    delta_color="off",
)

laender = sorted(big_mac["land"].unique())
standard = [
    land
    for land in ["Euro-Raum", "Vereinigte Staaten", "Schweiz", "Japan", "China"]
    if land in laender
]
selected = st.multiselect("Länder im Zeitverlauf", laender, default=standard)
if selected:
    figure = go.Figure()
    for index, land in enumerate(sorted(selected)):
        reihe = big_mac[big_mac["land"] == land].sort_values("datum")
        figure.add_trace(
            go.Scatter(
                x=reihe["datum"],
                y=reihe["preis_usd"],
                name=land,
                mode="lines+markers",
                marker={"size": 4},
                line={"color": ui.chart_color(index), "width": 2},
                hovertemplate="%{y:.2f} $<extra>" + land + "</extra>",
            )
        )
    figure.update_yaxes(title_text="Preis in US-Dollar")
    ui.plot(figure, filename="big_mac_zeitverlauf", height=420)

st.subheader("Aktuelle Abweichung vom US-Preis")
tabelle = aktuell[["land", "preis_usd", "abweichung_pct"]].rename(
    columns={
        "land": "Land",
        "preis_usd": "Preis (US-$)",
        "abweichung_pct": "Abweichung vom US-Preis (%)",
    }
)
st.dataframe(
    tabelle,
    hide_index=True,
    width="stretch",
    column_config={
        "Preis (US-$)": st.column_config.NumberColumn(format="%.2f"),
        "Abweichung vom US-Preis (%)": st.column_config.NumberColumn(format="%+.1f"),
    },
)

st.divider()
st.header("2. Eigentumsquote in Europa")
letztes_jahr = eigentum["jahr"].max()
aktuell_eigentum = eigentum[eigentum["jahr"] == letztes_jahr].sort_values(
    "eigentumsquote_pct", ascending=False
)
deutschland = eigentum[(eigentum["land"] == "Deutschland")].sort_values("jahr")
eu = eigentum[(eigentum["land"] == "EU-27")].sort_values("jahr")

columns = st.columns(3)
columns[0].metric(
    "Eigentumsquote Deutschland",
    ui.format_number(deutschland.iloc[-1]["eigentumsquote_pct"], 1, " %"),
    f"Berichtsjahr {int(deutschland.iloc[-1]['jahr'])}",
    delta_color="off",
)
columns[1].metric(
    "Eigentumsquote EU-27",
    ui.format_number(eu.iloc[-1]["eigentumsquote_pct"], 1, " %") if not eu.empty else "–",
    f"Berichtsjahr {int(eu.iloc[-1]['jahr'])}" if not eu.empty else "",
    delta_color="off",
)
columns[2].metric(
    "Höchste Quote",
    ui.format_number(aktuell_eigentum.iloc[0]["eigentumsquote_pct"], 1, " %"),
    str(aktuell_eigentum.iloc[0]["land"]),
    delta_color="off",
)

figure = go.Figure(
    go.Bar(
        x=aktuell_eigentum["land"],
        y=aktuell_eigentum["eigentumsquote_pct"],
        marker_color="#1f4e79",
        hovertemplate="%{x}: %{y:.1f} %<extra></extra>",
    )
)
figure.update_yaxes(title_text="Eigentumsquote in %", range=[0, 100])
figure.update_xaxes(title_text="")
ui.plot(figure, filename="eigentumsquote_laender", height=380, legend=False)

figure = go.Figure()
for index, land in enumerate(["Deutschland", "EU-27", "Spanien", "Niederlande"]):
    reihe = eigentum[eigentum["land"] == land].sort_values("jahr")
    if reihe.empty:
        continue
    figure.add_trace(
        go.Scatter(
            x=reihe["jahr"],
            y=reihe["eigentumsquote_pct"],
            name=land,
            mode="lines+markers",
            line={"color": ui.chart_color(index), "width": 2},
            hovertemplate="%{y:.1f} %<extra>" + land + "</extra>",
        )
    )
figure.update_yaxes(title_text="Eigentumsquote in %", range=[0, 100])
ui.plot(figure, filename="eigentumsquote_zeitverlauf", height=380)

st.caption(
    "Quellen: The Economist (Big-Mac-Index) und Eurostat ilc_lvho02 "
    "(Verteilung der Bevölkerung nach Wohnstatus)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
