"""Auswertungen: Wachstum, Schuldenquote, Schulden je Einwohner."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import analysis, dataset, ui

st.title("Analysen")
st.markdown(
    "Wie hat sich der Schuldenstand im Verhältnis zur Wirtschaftsleistung entwickelt? "
    "Die folgenden Auswertungen beziehen sich auf den Maastricht-Schuldenstand des "
    "Gesamtstaats."
)

annual = ui.annual_debt()
total = annual[annual["sector"] == "S13"].dropna(subset=["schulden_mio_eur"]).sort_values("jahr")
total = dataset.with_debt_per_capita(total, ui.gdp_population()).reset_index(drop=True)
total["schulden_wachstum_pct"] = total["schulden_mio_eur"].pct_change() * 100
total["bip_wachstum_pct"] = total["bip_mio_eur"].pct_change() * 100

first, last = total.iloc[0], total.iloc[-1]
years = int(last["jahr"] - first["jahr"])
growth = analysis.cagr(first["schulden_mio_eur"], last["schulden_mio_eur"], years)
gdp_growth = analysis.cagr(first["bip_mio_eur"], last["bip_mio_eur"], years)
declines = int((total["schulden_wachstum_pct"] < 0).sum())
peak = total.loc[total["schuldenquote_pct"].idxmax()]
trough = total.loc[total["schuldenquote_pct"].idxmin()]

columns = st.columns(4)
columns[0].metric(
    f"Anstieg {int(first['jahr'])}–{int(last['jahr'])} (Mrd. €)",
    ui.format_number((last["schulden_mio_eur"] - first["schulden_mio_eur"]) / 1000, 0),
    f"{ui.format_number((last['schulden_mio_eur'] / first['schulden_mio_eur'] - 1) * 100)} %",
    delta_color="off",
)
columns[1].metric("Ø Wachstum p. a.", ui.format_number(growth, 1, " %"))
columns[2].metric("Ø BIP-Wachstum p. a.", ui.format_number(gdp_growth, 1, " %"))
columns[3].metric("Jahre mit Rückgang", f"{declines} von {years}", delta_color="off")

left, right = st.columns(2)

with left:
    st.subheader("Schuldenquote und Maastricht-Grenze")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=total["jahr"],
            y=total["schuldenquote_pct"],
            mode="lines",
            line={"color": "#1f4e79", "width": 3},
            fill="tozeroy",
            fillcolor="rgba(31,78,121,0.10)",
            hovertemplate="%{x}: %{y:.1f} % des BIP<extra></extra>",
        )
    )
    figure.add_hline(
        y=60,
        line={"color": "#b03a2e", "dash": "dash"},
        annotation_text="Maastricht-Referenz 60 %",
    )
    figure.update_yaxes(
        title_text="% des BIP", range=[0, max(90, total["schuldenquote_pct"].max() + 10)]
    )
    ui.plot(figure, filename="analysen_schuldenquote", height=400, legend=False)
    peak_quote = ui.format_number(peak["schuldenquote_pct"], 1, " %")
    trough_quote = ui.format_number(trough["schuldenquote_pct"], 1, " %")
    st.caption(
        f"Höchstwert {int(peak['jahr'])}: {peak_quote} · "
        f"Tiefstwert {int(trough['jahr'])}: {trough_quote}"
    )

with right:
    st.subheader("Schuldenwachstum vs. BIP-Wachstum")
    scatter_data = total.dropna(subset=["schulden_wachstum_pct", "bip_wachstum_pct"])
    notable = {int(peak["jahr"]), int(trough["jahr"]), int(last["jahr"]), 2008, 2020}
    labels = [str(int(jahr)) if int(jahr) in notable else "" for jahr in scatter_data["jahr"]]
    figure = go.Figure(
        go.Scatter(
            x=scatter_data["bip_wachstum_pct"],
            y=scatter_data["schulden_wachstum_pct"],
            mode="markers+text",
            text=labels,
            customdata=scatter_data["jahr"],
            textposition="top center",
            textfont={"size": 10},
            marker={
                "size": 10,
                "color": scatter_data["schuldenquote_pct"],
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "Quote<br>(% BIP)"},
            },
            hovertemplate=("%{customdata}: BIP %{x:+.1f} %, Schulden %{y:+.1f} %<extra></extra>"),
        )
    )
    figure.add_hline(y=0, line={"color": "#999", "width": 1})
    figure.add_vline(x=0, line={"color": "#999", "width": 1})
    figure.update_xaxes(title_text="BIP-Wachstum (%)")
    figure.update_yaxes(title_text="Schuldenwachstum (%)")
    ui.plot(figure, filename="analysen_wachstum", height=400, legend=False)

st.divider()
st.subheader("Schuldenstand je Einwohner:in")
figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["schulden_je_einwohner_eur"],
        name="Schulden je Einwohner:in",
        marker_color="#2e86ab",
        hovertemplate="%{y:,.0f} €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=total["jahr"],
        y=total["schuldenquote_pct"],
        name="Schuldenquote",
        line={"color": "#c9a227", "width": 2, "dash": "dot"},
        hovertemplate="%{y:.1f} % des BIP<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_yaxes(title_text="€ je Einwohner:in", secondary_y=False)
figure.update_yaxes(title_text="% des BIP", range=[40, 90], dtick=10, secondary_y=True)
ui.plot(figure, filename="analysen_je_einwohner", height=380)
st.caption(
    "Bevölkerung jeweils zum Jahresbeginn (Eurostat demo_pjan), Schuldenstand zum Jahresende."
)

st.divider()
st.subheader("Jahreswerte")
recent = total.tail(15).copy()
st.dataframe(
    recent[
        [
            "jahr",
            "schulden_mio_eur",
            "schuldenquote_pct",
            "schulden_je_einwohner_eur",
            "schulden_wachstum_pct",
            "bip_wachstum_pct",
        ]
    ].rename(
        columns={
            "jahr": "Jahr",
            "schulden_mio_eur": "Schulden",
            "schuldenquote_pct": "Quote",
            "schulden_je_einwohner_eur": "Je Einw.",
            "schulden_wachstum_pct": "Δ Schulden",
            "bip_wachstum_pct": "Δ BIP",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Schulden": st.column_config.NumberColumn(
            "Schulden (Mio. €)", format="%,.0f", width="small"
        ),
        "Quote": st.column_config.NumberColumn("Quote (% BIP)", format="%.1f", width="small"),
        "Je Einw.": st.column_config.NumberColumn("Je Einw. (€)", format="%,.0f", width="small"),
        "Δ Schulden": st.column_config.NumberColumn("Δ Schulden (%)", format="%+.1f"),
        "Δ BIP": st.column_config.NumberColumn("Δ BIP (%)", format="%+.1f"),
    },
)
st.caption("Quelle: Eurostat gov_10dd_edpt1, nama_10_gdp und demo_pjan.")
