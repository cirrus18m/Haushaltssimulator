"""Einfacher Szenario-Rechner für Schuldenstand und Schuldenquote."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import analysis, ui

st.title("Szenario-Rechner")
st.markdown(
    "Was passiert mit der Schuldenquote, wenn Schulden und Wirtschaftsleistung unterschiedlich "
    "wachsen? Das Modell ist bewusst einfach: konstanter Zuwachs pro Jahr, keine Zinsen, keine "
    "Konjunktureffekte. Es zeigt die Richtung, nicht eine Prognose."
)

annual = ui.annual_debt()
total = annual[annual["sector"] == "S13"].dropna(subset=["schulden_mio_eur"]).sort_values("jahr")
start = total.iloc[-1]
start_year = int(start["jahr"])
recent_growth = total["schulden_mio_eur"].pct_change().tail(5).mean() * 100
recent_gdp_growth = total["bip_mio_eur"].pct_change().tail(5).mean() * 100

with st.sidebar:
    st.header("Annahmen")
    schuldenwachstum = st.slider(
        "Schuldenwachstum pro Jahr (%)",
        min_value=-5.0,
        max_value=15.0,
        value=round(float(recent_growth), 1),
        step=0.1,
        help="Durchschnitt der letzten fünf Jahre als Startwert.",
    )
    bip_wachstum = st.slider(
        "BIP-Wachstum pro Jahr (%)",
        min_value=-3.0,
        max_value=8.0,
        value=round(float(recent_gdp_growth), 1),
        step=0.1,
        help="Nominales Wachstum. Durchschnitt der letzten fünf Jahre als Startwert.",
    )
    horizont = st.slider("Zeithorizont (Jahre)", min_value=1, max_value=20, value=10)

projection = analysis.simulate_debt_ratio(
    schulden_mio_eur=float(start["schulden_mio_eur"]),
    bip_mio_eur=float(start["bip_mio_eur"]),
    schuldenwachstum_pct=schuldenwachstum,
    bip_wachstum_pct=bip_wachstum,
    jahre=horizont,
    startjahr=start_year,
)
end = projection.iloc[-1]
change_points = end["schuldenquote_pct"] - start["schuldenquote_pct"]

columns = st.columns(4)
columns[0].metric(
    f"Schuldenquote {start_year}", ui.format_number(start["schuldenquote_pct"], 1, " %")
)
columns[1].metric(
    f"Schuldenquote {int(end['jahr'])}",
    ui.format_number(end["schuldenquote_pct"], 1, " %"),
    f"{ui.format_number(change_points, 1)} %-Pkt.",
    delta_color="inverse",
)
columns[2].metric(
    f"Schuldenstand {int(end['jahr'])} (Mrd. €)",
    ui.format_number(end["schulden_mio_eur"] / 1000, 0),
)
columns[3].metric(
    "Abstand zu 60 % (%-Pkt.)",
    ui.format_number(end["schuldenquote_pct"] - 60, 1),
    delta_color="off",
)

figure = go.Figure()
historical = total.tail(10)
figure.add_trace(
    go.Scatter(
        x=historical["jahr"],
        y=historical["schuldenquote_pct"],
        name="bisherige Entwicklung",
        mode="lines+markers",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{x}: %{y:.1f} %<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=projection["jahr"],
        y=projection["schuldenquote_pct"],
        name="Szenario",
        mode="lines+markers",
        line={"color": "#c9a227", "width": 3, "dash": "dash"},
        hovertemplate="%{x}: %{y:.1f} %<extra></extra>",
    )
)
figure.add_hline(
    y=60,
    line={"color": "#b03a2e", "dash": "dot"},
    annotation_text="Maastricht-Referenz 60 %",
)
figure.update_yaxes(title_text="% des BIP")
st.plotly_chart(ui.style(figure), width="stretch")

st.divider()
st.subheader("Szenariopfad")
table = projection.copy()
table["schulden_mio_eur"] = table["schulden_mio_eur"] / 1000
table["bip_mio_eur"] = table["bip_mio_eur"] / 1000
st.dataframe(
    table.rename(
        columns={
            "jahr": "Jahr",
            "schulden_mio_eur": "Schulden (Mrd. €)",
            "bip_mio_eur": "BIP (Mrd. €)",
            "schuldenquote_pct": "Schuldenquote (%)",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Schulden (Mrd. €)": st.column_config.NumberColumn(format="%,.1f"),
        "BIP (Mrd. €)": st.column_config.NumberColumn(format="%,.1f"),
        "Schuldenquote (%)": st.column_config.NumberColumn(format="%.1f"),
    },
)

with st.expander("Berechnung"):
    st.markdown(
        "Schuldenquote = Schuldenstand / BIP × 100\n\n"
        f"Startwerte {start_year}: {ui.format_mrd(start['schulden_mio_eur'])} Schulden, "
        f"{ui.format_mrd(start['bip_mio_eur'])} BIP. "
        "Beide Größen wachsen anschließend mit den eingestellten Raten."
    )
st.caption("Quelle der Startwerte: Eurostat gov_10dd_edpt1 und nama_10_gdp.")
