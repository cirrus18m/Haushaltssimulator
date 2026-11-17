"""Bund: Zinsausgaben, Schuldenstand und Schuldendienst."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import ui

st.title("Bund und Schuldendienst")
st.markdown(
    "Zinsausgaben und Schuldenstand des Bundes. Die langen Reihen stammen aus den "
    "Volkswirtschaftlichen Gesamtrechnungen (Eurostat), die Haushaltsjahre und "
    "Planwerte aus dem Bundeshaushalt des Bundesministeriums der Finanzen."
)

haushalt = ui.household()
bund = haushalt[haushalt["sector"] == "S1311"].sort_values("jahr").reset_index(drop=True)
plan = ui.bund_interest()
schulden = ui.annual_debt()
bund_schulden = schulden[
    (schulden["sector"] == "S1311") & schulden["schulden_mio_eur"].notna()
].sort_values("jahr")

if bund.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

letzte = bund.iloc[-1]
retrieved = ui.data_retrieved_at()
plan_aktuell = plan[plan["art"].isin(["Ist", "Soll"])].sort_values("jahr")
if not plan_aktuell.empty:
    letzter_plan = plan_aktuell.iloc[-1]
    plan_wert = ui.format_number(letzter_plan["zinsausgaben_mrd_eur"], 2)
    plan_hinweis = f"Mrd. € ({int(letzter_plan['jahr'])}, {letzter_plan['art']})"
else:
    plan_wert, plan_hinweis = "–", ""

columns = st.columns(4)
columns[0].metric(
    "Zinsausgaben des Bundes",
    ui.format_number(letzte["zinsausgaben_mio_eur"] / 1000, 1),
    f"Mrd. € ({int(letzte['jahr'])})",
    delta_color="off",
)
columns[1].metric(
    "Zinsquote der Einnahmen",
    ui.format_number(letzte["zins_einnahmen_pct"], 1, " %"),
    "Zinsausgaben / Einnahmen",
    delta_color="off",
)
columns[2].metric(
    "Schuldenstand des Bundes",
    ui.format_number(bund_schulden.iloc[-1]["schulden_mio_eur"] / 1000, 0)
    if not bund_schulden.empty
    else "–",
    f"Mrd. € ({int(bund_schulden.iloc[-1]['jahr'])})" if not bund_schulden.empty else "",
    delta_color="off",
)
columns[3].metric(
    "Zinsausgaben im Haushalt",
    plan_wert,
    plan_hinweis,
    delta_color="off",
)

st.divider()
st.header("1. Zinsausgaben im Zeitverlauf")
figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Bar(
        x=bund["jahr"],
        y=bund["zinsausgaben_mio_eur"] / 1000,
        name="Zinsausgaben (Mrd. €)",
        marker_color="#b03a2e",
        hovertemplate="%{y:,.1f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=bund["jahr"],
        y=bund["zins_einnahmen_pct"],
        name="in % der Einnahmen",
        line={"color": "#1f4e79", "width": 2.5},
        hovertemplate="%{y:.1f} %<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
figure.update_yaxes(title_text="% der Einnahmen", secondary_y=True)
ui.plot(figure, filename="bund_zinsausgaben_zeitreihe", height=420)

st.header("2. Schuldenstand des Bundes")
st.markdown(
    "Eurostat weist die staatlichen Ebenen erst ab 2022 getrennt aus. Für davorliegende "
    "Jahre enthält die Schuldenstatistik von Destatis die Gliederung nach Bund, Ländern "
    "und Gemeinden."
)
if bund_schulden.empty:
    st.info("Keine Schuldenreihe für den Bund verfügbar.")
else:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=bund_schulden["jahr"],
            y=bund_schulden["schulden_mio_eur"] / 1000,
            name="Schuldenstand (Mrd. €)",
            mode="lines+markers",
            line={"color": "#1f4e79", "width": 3},
            hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=bund_schulden["jahr"],
            y=bund_schulden["schuldenquote_pct"],
            name="Schuldenquote (% BIP)",
            mode="lines+markers",
            line={"color": "#c9a227", "width": 2, "dash": "dot"},
            hovertemplate="%{y:.1f} %<extra></extra>",
        ),
        secondary_y=True,
    )
    figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
    figure.update_yaxes(title_text="% des BIP", secondary_y=True)
    ui.plot(figure, filename="bund_schuldenstand", height=380)

st.header("3. Haushaltsjahre und Planwerte (BMF)")
if plan.empty:
    st.info("Keine Planwerte verfügbar.")
else:
    farben = {"Ist": "#1f4e79", "Soll": "#2e86ab", "RegE": "#c9a227"}
    figure = go.Figure()
    for art, gruppe in plan.groupby("art", sort=False):
        figure.add_trace(
            go.Bar(
                x=gruppe["jahr"],
                y=gruppe["zinsausgaben_mrd_eur"],
                name=art,
                marker_color=farben.get(art, "#7f7f7f"),
                hovertemplate="%{y:.2f} Mrd. €<extra>" + art + "</extra>",
            )
        )
    figure.update_layout(barmode="group")
    figure.update_yaxes(title_text="Mrd. €")
    ui.plot(figure, filename="bund_zinsausgaben_plan", height=360)

with st.expander("Sondervermögen und Abgrenzung"):
    st.markdown(
        "Die Zinsausgaben des Bundes folgen der Abgrenzung der Volkswirtschaftlichen "
        "Gesamtrechnungen (Eurostat `gov_10a_main`, Sektor S1311). Die BMF-Reihe zeigt "
        "die im Haushalt veranschlagten Zinsausgaben am Kreditmarkt; Ist, Soll und "
        "Regierungsentwurf stehen nebeneinander.\n\n"
        "**Sondervermögen** (z. B. Sondervermögen Bundeswehr, Klima- und "
        "Transformationsfonds) sind in den Eurostat-Reihen je nach Abgrenzung ganz oder "
        "teilweise enthalten. Eine eigene, frei maschinenlesbare Zeitreihe je "
        "Sondervermögen liegt derzeit nicht vor; die Seite weist sie deshalb noch nicht "
        "separat aus."
    )

st.caption(
    "Quellen: Eurostat gov_10a_main (S1311), Eurostat gov_10dd_edpt1 (S1311) und "
    "Bundesministerium der Finanzen (Zinsausgaben am Kreditmarkt)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
