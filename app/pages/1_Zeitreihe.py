"""Langfristige Zeitreihe der deutschen Staatsschulden (Eurostat)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import analysis, ui

st.title("Zeitreihe 1995 bis heute")

annual = ui.annual_debt()
quarterly = ui.quarterly_debt()

st.markdown(
    "Der Maastricht-Schuldenstand wird von Eurostat jährlich ab 1995 und vierteljährlich "
    "ab 2000 veröffentlicht. Die Aufteilung nach staatlichen Ebenen ist ab 2022 verfügbar."
)

controls, chart_area = st.columns([1, 3])
with controls:
    unit = st.radio("Einheit", ["Mrd. €", "% des BIP"], index=0)
    years = st.slider(
        "Zeitraum",
        int(annual["jahr"].min()),
        int(annual["jahr"].max()),
        (1995, int(annual["jahr"].max())),
    )
    available = [
        "Staat insgesamt",
        *[ebene for ebene in ui.EBENE_ORDER if ebene in set(annual["ebene"])],
    ]
    selected = st.multiselect("Ebenen", available, default=["Staat insgesamt"])
    if not selected:
        selected = ["Staat insgesamt"]

with chart_area:
    data = annual[(annual["jahr"].between(*years)) & (annual["ebene"].isin(selected))].dropna(
        subset=["schulden_mio_eur"]
    )
    figure = go.Figure()
    for ebene in [*selected]:
        subset = data[data["ebene"] == ebene].sort_values("jahr")
        if unit == "Mrd. €":
            values = subset["schulden_mio_eur"] / 1000
            hover = "%{y:,.0f} Mrd. €"
        else:
            values = subset["schuldenquote_pct"]
            hover = "%{y:.1f} % des BIP"
        figure.add_trace(
            go.Scatter(
                x=subset["jahr"],
                y=values,
                name=ebene,
                mode="lines+markers",
                line={"width": 3 if ebene == "Staat insgesamt" else 2},
                marker={"size": 4},
                hovertemplate=hover + "<extra>" + ebene + "</extra>",
            )
        )
    if unit == "% des BIP":
        figure.add_hline(
            y=60,
            line={"color": "#b03a2e", "dash": "dash"},
            annotation_text="Maastricht-Referenz 60 %",
        )
    figure.update_yaxes(title_text="Mrd. €" if unit == "Mrd. €" else "% des BIP")
    st.plotly_chart(ui.style(figure), width="stretch")

st.divider()
st.subheader("Kennzahlen des Gesamtstaats")
total = annual[annual["sector"] == "S13"].dropna(subset=["schulden_mio_eur"]).sort_values("jahr")
with_changes = analysis.year_over_year(total, "schulden_mio_eur", "sector")
table = with_changes[
    ["jahr", "schulden_mio_eur", "veraenderung_mio_eur", "veraenderung_pct", "schuldenquote_pct"]
].copy()
table["schulden_mio_eur"] = table["schulden_mio_eur"] / 1000
table["veraenderung_mio_eur"] = table["veraenderung_mio_eur"].astype("Float64") / 1000
table["veraenderung_pct"] = table["veraenderung_pct"].astype("Float64")
st.dataframe(
    table.rename(
        columns={
            "jahr": "Jahr",
            "schulden_mio_eur": "Schulden (Mrd. €)",
            "veraenderung_mio_eur": "Veränderung (Mrd. €)",
            "veraenderung_pct": "Veränderung (%)",
            "schuldenquote_pct": "Schuldenquote (%)",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Schulden (Mrd. €)": st.column_config.NumberColumn(format="%.1f"),
        "Veränderung (Mrd. €)": st.column_config.NumberColumn(format="%+.1f"),
        "Veränderung (%)": st.column_config.NumberColumn(format="%+.1f"),
        "Schuldenquote (%)": st.column_config.NumberColumn(format="%.1f"),
    },
)

st.divider()
st.subheader("Vierteljährliche Entwicklung")
quarterly_total = quarterly[quarterly["sector"] == "S13"].dropna(subset=["schulden_mio_eur"])
quarterly_total = quarterly_total.sort_values("quartalsende")
figure = go.Figure(
    go.Scatter(
        x=quarterly_total["quartalsende"],
        y=quarterly_total["schulden_mio_eur"] / 1000,
        mode="lines",
        line={"color": "#1f4e79", "width": 3},
        fill="tozeroy",
        fillcolor="rgba(31,78,121,0.08)",
        hovertemplate="%{x|%m/%Y}: %{y:,.0f} Mrd. €<extra></extra>",
    )
)
figure.update_yaxes(title_text="Mrd. €", rangemode="tozero")
st.plotly_chart(ui.style(figure, height=360, legend=False), width="stretch")
st.caption(
    f"Quelle: Eurostat gov_10q_ggdebt, letztes Quartal: {quarterly_total['quartal'].iloc[-1]}."
)
