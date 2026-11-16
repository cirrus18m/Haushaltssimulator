"""Schulden nach staatlichen Ebenen und Schuldenarten (Destatis)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Ebenen und Schuldenarten")
st.markdown(
    "Das Statistische Bundesamt weist die **Schulden beim nicht-öffentlichen Bereich** "
    "vierteljährlich zum Quartalsende aus – getrennt nach Bund, Ländern, Gemeinden und "
    "Sozialversicherung sowie nach Kernhaushalten und Extrahaushalten."
)

frame = ui.destatis_quarterly()
ebenen = ["Bund", "Länder", "Gemeinden / Gemeindeverbände", "Sozialversicherung"]
KURZ = {"Gemeinden / Gemeindeverbände": "Gemeinden", "Sozialversicherung": "Sozialvers."}

haushalt = (
    st.segmented_control(
        "Haushaltsabgrenzung",
        ["Insgesamt", "Kernhaushalt", "Extrahaushalte"],
        default="Insgesamt",
    )
    or "Insgesamt"
)
selected = st.pills("Ebenen", ebenen, selection_mode="multi", default=ebenen)

if not selected:
    st.info("Bitte mindestens eine Ebene auswählen.")
    st.stop()

totals = frame[
    (frame["haushalt"] == haushalt)
    & (frame["schuldenart"] == "Insgesamt")
    & (frame["ebene"].isin(selected))
]
latest_date = totals["stichtag"].max()

pivot = (
    totals.pivot_table(index="stichtag", columns="ebene", values="schulden_mio_eur", aggfunc="sum")
    .reindex(columns=selected)
    .sort_index()
)
figure = go.Figure()
for ebene in selected:
    figure.add_trace(
        go.Scatter(
            x=pivot.index,
            y=pivot[ebene] / 1000,
            name=ebene,
            mode="lines",
            stackgroup="schulden",
            line={"width": 1, "color": ui.EBENE_COLORS.get(ebene)},
            hovertemplate="%{y:,.0f} Mrd. €<extra>" + ebene + "</extra>",
        )
    )
figure.update_yaxes(title_text="Mrd. €")
figure.update_xaxes(title_text="Quartalsende")
st.plotly_chart(ui.style(figure), width="stretch")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader(f"Zusammensetzung am {latest_date:%d.%m.%Y}")
    composition = frame[
        (frame["stichtag"] == latest_date)
        & (frame["haushalt"] == haushalt)
        & (frame["schuldenart"] != "Insgesamt")
        & (frame["ebene"].isin(selected))
    ]
    figure = go.Figure()
    for schuldenart, group in composition.groupby("schuldenart", observed=True):
        figure.add_trace(
            go.Bar(
                y=group["ebene"].map(lambda ebene: KURZ.get(ebene, ebene)),
                x=group["schulden_mio_eur"] / 1000,
                orientation="h",
                name=schuldenart,
                marker_color=ui.SCHULDENART_COLORS.get(schuldenart),
                hovertemplate="%{y}: %{x:,.0f} Mrd. €<extra>" + schuldenart + "</extra>",
            )
        )
    figure.update_xaxes(title_text="Mrd. €", dtick=500)
    figure.update_layout(barmode="stack")
    styled = ui.style(figure, height=400)
    styled.update_layout(legend={"y": 1.12})
    st.plotly_chart(styled, width="stretch")

with right:
    st.subheader("Veränderung zum Vorquartal")
    changes = totals.sort_values("stichtag").copy()
    changes["delta"] = changes.groupby("ebene", observed=True)["schulden_mio_eur"].diff()
    latest_changes = changes[changes["stichtag"] == latest_date]
    figure = go.Figure(
        go.Bar(
            y=latest_changes["ebene"].map(lambda ebene: KURZ.get(ebene, ebene)),
            x=latest_changes["delta"] / 1000,
            orientation="h",
            marker_color=[
                "#b03a2e" if value > 0 else "#2e7d32" for value in latest_changes["delta"].fillna(0)
            ],
            hovertemplate="%{y}: %{x:+,.1f} Mrd. €<extra></extra>",
        )
    )
    figure.update_xaxes(title_text="Veränderung in Mrd. €")
    st.plotly_chart(ui.style(figure, height=400, legend=False), width="stretch")

st.divider()
st.subheader("Werte im Überblick (Mio. €)")
table = pivot.copy()
table.index = table.index.strftime("%d.%m.%Y")
st.dataframe(
    table.iloc[::-1].rename_axis("Stichtag").reset_index(),
    hide_index=True,
    width="stretch",
    column_config={
        ebene: st.column_config.NumberColumn(ebene, format="%,.0f") for ebene in table.columns
    },
)

st.info(
    "**Abgrenzung:** Destatis zählt hier nur Schulden beim nicht-öffentlichen Bereich "
    "(Wertpapierschulden, Kredite und Kassenkredite). Der Maastricht-Schuldenstand auf der "
    "Startseite ist breiter definiert und daher höher; die Zeitreihen sind nicht direkt "
    "miteinander vergleichbar."
)
st.caption("Quelle: Statistisches Bundesamt, GENESIS-Online 71311-0001 (letzte 10 Quartale).")
