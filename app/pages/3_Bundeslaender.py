"""Schulden der Bundesländer im Vergleich (Destatis)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Bundesländer im Vergleich")
st.markdown(
    "Vierteljährliche Schulden beim nicht-öffentlichen Bereich je Bundesland. Die Abgrenzung "
    "**Land + Gemeinden** entspricht dem gesamtstaatlichen Anteil eines Landes, "
    "**Länder** nur der Landesebene ohne die kommunalen Haushalte."
)

frame = ui.laender_quarterly()
latest_date = frame["stichtag"].max()
first_date = frame["stichtag"].min()

scope = st.radio(
    "Abgrenzung",
    ["Insgesamt", "Länder"],
    horizontal=True,
    format_func=lambda value: "Land + Gemeinden" if value == "Insgesamt" else "Nur Länder",
)

totals = frame[
    (frame["haushalt"] == "Insgesamt")
    & (frame["schuldenart"] == "Insgesamt")
    & (frame["ebene"] == scope)
]
latest = (
    totals[totals["stichtag"] == latest_date]
    .groupby("bundesland", as_index=False)["schulden_mio_eur"]
    .sum()
    .sort_values("schulden_mio_eur")
)

figure = go.Figure(
    go.Bar(
        x=latest["schulden_mio_eur"] / 1000,
        y=latest["bundesland"],
        orientation="h",
        marker_color="#1f4e79",
        text=(latest["schulden_mio_eur"] / 1000).map(
            lambda value: f"{value:,.0f}".replace(",", ".")
        ),
        textposition="outside",
        hovertemplate="%{y}: %{x:,.0f} Mrd. €<extra></extra>",
    )
)
figure.update_xaxes(title_text="Mrd. €")
figure.update_yaxes(title_text="")
st.plotly_chart(ui.style(figure, height=520, legend=False), width="stretch")

st.divider()
st.subheader("Entwicklung ausgewählter Länder")
default = list(latest.tail(4)["bundesland"])
selected = st.multiselect("Bundesländer", sorted(frame["bundesland"].unique()), default=default)

if selected:
    series = (
        totals[totals["bundesland"].isin(selected)]
        .pivot_table(
            index="stichtag", columns="bundesland", values="schulden_mio_eur", aggfunc="sum"
        )
        .sort_index()
    )
    figure = go.Figure()
    for bundesland in selected:
        column = series.get(bundesland)
        if column is None:
            continue
        figure.add_trace(
            go.Scatter(
                x=series.index,
                y=column / 1000,
                name=bundesland,
                mode="lines+markers",
                marker={"size": 5},
                hovertemplate="%{y:,.1f} Mrd. €<extra>" + bundesland + "</extra>",
            )
        )
    figure.update_yaxes(title_text="Mrd. €")
    figure.update_xaxes(title_text="Quartalsende")
    st.plotly_chart(ui.style(figure, height=420), width="stretch")

st.divider()
st.subheader("Veränderung seit dem ersten verfügbaren Quartal")
first_values = (
    totals[totals["stichtag"] == first_date]
    .groupby("bundesland", as_index=False)["schulden_mio_eur"]
    .sum()
    .rename(columns={"schulden_mio_eur": "start"})
)
table = latest.rename(columns={"schulden_mio_eur": "aktuell"}).merge(first_values, on="bundesland")
table["veraenderung"] = table["aktuell"] - table["start"]
table["veraenderung_pct"] = table["veraenderung"] / table["start"] * 100
table["anteil_pct"] = table["aktuell"] / table["aktuell"].sum() * 100
table = table.sort_values("aktuell", ascending=False)

st.dataframe(
    table.rename(
        columns={
            "bundesland": "Bundesland",
            "aktuell": "Aktuell",
            "start": "Start",
            "veraenderung": "Δ absolut",
            "veraenderung_pct": "Δ in %",
            "anteil_pct": "Anteil",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Aktuell": st.column_config.NumberColumn("Aktuell (Mio. €)", format="%,.0f", width="small"),
        "Start": st.column_config.NumberColumn("Start (Mio. €)", format="%,.0f", width="small"),
        "Δ absolut": st.column_config.NumberColumn("Δ (Mio. €)", format="%+,.0f", width="small"),
        "Δ in %": st.column_config.NumberColumn(format="%+.1f", width="small"),
        "Anteil": st.column_config.NumberColumn("Anteil (%)", format="%.1f", width="small"),
    },
)

st.caption(
    f"Quelle: Statistisches Bundesamt, GENESIS-Online 71311-0003. "
    f"Zeitraum: {first_date:%d.%m.%Y} bis {latest_date:%d.%m.%Y}. "
    "Stadtstaaten weisen keine eigenständigen Gemeindehaushalte aus."
)
