"""Haushalt, Schulden und Zinslast: von den Einnahmen zur theoretischen Zinslast."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import ui

st.title("Haushalt, Schulden und Zinslast")
st.markdown(
    "Die Seite führt von der Einnahmenseite des Staates über den Schuldenstand zur "
    "Zinslast. Die **theoretische Zinslast** ist der gesamte Schuldenstand multipliziert "
    "mit der Rendite der aktuellen 10-jährigen Bundesanleihe. Sie zeigt, was der "
    "Schuldenstand kosten würde, wenn er vollständig zum aktuellen Marktzins verzinst "
    "würde – die tatsächlich gebuchten Zinsausgaben liegen wegen der niedrigeren Zinsen "
    "älterer Anleihen meist darunter."
)

household = ui.household()
total = household[household["sector"] == "S13"].dropna(subset=["einnahmen_mio_eur"])
total = total.sort_values("jahr").reset_index(drop=True)
zinslast = ui.interest_burden()
daily_yield = ui.bund_yield()

if total.empty or zinslast.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

latest = total.iloc[-1]
previous = total.iloc[-2] if len(total) > 1 else latest
retrieved = ui.data_retrieved_at()

st.subheader(f"Haushalt {int(latest['jahr'])}")
columns = st.columns(4)
columns[0].metric(
    "Einnahmen (Mrd. €)",
    ui.format_number(latest["einnahmen_mio_eur"] / 1000, 0),
    f"{ui.format_number((latest['einnahmen_mio_eur'] - previous['einnahmen_mio_eur']) / 1000, 1)}"
    " zum Vorjahr",
    delta_color="off",
)
columns[1].metric(
    "Ausgaben (Mrd. €)",
    ui.format_number(latest["ausgaben_mio_eur"] / 1000, 0),
    f"{ui.format_number((latest['ausgaben_mio_eur'] - previous['ausgaben_mio_eur']) / 1000, 1)}"
    " zum Vorjahr",
    delta_color="inverse",
)
columns[2].metric(
    "Zinsausgaben (Mrd. €)",
    ui.format_number(latest["zinsausgaben_mio_eur"] / 1000, 1),
    f"{ui.format_number(latest['zins_einnahmen_pct'], 1)} % der Einnahmen",
    delta_color="inverse",
)
columns[3].metric(
    "Finanzierungssaldo (Mrd. €)",
    ui.format_number(latest["finanzierungssaldo_mio_eur"] / 1000, 1),
    "Defizit" if latest["finanzierungssaldo_mio_eur"] < 0 else "Überschuss",
    delta_color="off",
)

st.divider()
st.header("1. Haushalt")
st.markdown(
    "Einnahmen und Ausgaben des Gesamtstaats in der Abgrenzung der Volkswirtschaftlichen "
    "Gesamtrechnung. Die Einnahmen enthalten **keine Kreditaufnahme** – sie sind damit das "
    "Haushaltseinkommen ohne neue Schulden."
)

figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["einnahmen_mio_eur"] / 1000,
        name="Einnahmen",
        marker_color="#2e7d32",
        hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["ausgaben_mio_eur"] / 1000,
        name="Ausgaben",
        marker_color="#b03a2e",
        hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=total["jahr"],
        y=total["finanzierungssaldo_mio_eur"] / 1000,
        name="Finanzierungssaldo",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{y:+,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_layout(barmode="group")
figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
figure.update_yaxes(title_text="Saldo in Mrd. €", secondary_y=True)
ui.plot(figure, filename="haushalt_einnahmen_ausgaben", height=420)

figure = go.Figure()
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["zinsausgaben_mio_eur"] / 1000,
        name="Zinsausgaben (Mrd. €)",
        marker_color="#c9a227",
        hovertemplate="%{y:,.1f} Mrd. €<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=total["jahr"],
        y=total["zins_einnahmen_pct"],
        name="in % der Einnahmen",
        yaxis="y2",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{y:.1f} %<extra></extra>",
    )
)
figure.update_layout(
    yaxis={"title": "Mrd. €"},
    yaxis2={"title": "% der Einnahmen", "overlaying": "y", "side": "right", "showgrid": False},
)
ui.plot(figure, filename="haushalt_zinsausgaben", height=380)

st.divider()
st.header("2. Schulden")
st.markdown(
    "Maastricht-Schuldenstand des Gesamtstaats. Er ist die Bezugsgröße für die "
    "Zinslast im nächsten Abschnitt."
)

debt = zinslast.dropna(subset=["schulden_mio_eur"]).sort_values("jahr")
figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Scatter(
        x=debt["jahr"],
        y=debt["schulden_mio_eur"] / 1000,
        name="Schuldenstand",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=debt["jahr"],
        y=debt["schulden_mio_eur"] / debt["bip_mio_eur"] * 100,
        name="Schuldenquote",
        line={"color": "#c9a227", "width": 2, "dash": "dot"},
        hovertemplate="%{y:.1f} % des BIP<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
figure.update_yaxes(title_text="% des BIP", secondary_y=True)
ui.plot(figure, filename="zinslast_schuldenstand", height=400)

st.divider()
st.header("3. Zinslast")
st.markdown(
    "Die 10-jährige Bundesanleihe ist der Referenzzins für die Refinanzierung des Bundes. "
    "Multipliziert mit dem gesamten Schuldenstand ergibt sie die theoretische Zinslast."
)

monatsrendite = daily_yield.groupby("monat", as_index=False)["rendite_pct"].mean()
monatsrendite["datum"] = pd.to_datetime(monatsrendite["monat"])

st.subheader("Rendite der 10-jährigen Bundesanleihe (Monatsmittel)")
figure = go.Figure(
    go.Scatter(
        x=monatsrendite["datum"],
        y=monatsrendite["rendite_pct"],
        name="Monatsmittel der Tagesrendite",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{x|%m.%Y}: %{y:.2f} %<extra></extra>",
    )
)
for label, datum, hoehe, anker in (
    ("Lehman-Pleite", "2008-09-15", 0.02, "left"),
    ("Corona", "2020-03-16", 0.02, "left"),
    ("Russland", "2022-03-02", 0.02, "left"),
    ("Hormus", "2026-02-28", 0.02, "right"),
):
    figure.add_vline(
        x=pd.Timestamp(datum),
        line={"color": "#b03a2e", "width": 1, "dash": "dot"},
    )
    figure.add_annotation(
        x=pd.Timestamp(datum),
        y=hoehe,
        yref="paper",
        text=label,
        showarrow=False,
        textangle=-90,
        xanchor=anker,
        yanchor="bottom",
        font={"size": 10, "color": "#b03a2e"},
    )
figure.add_hline(y=0, line={"color": "#999", "width": 1})
figure.update_yaxes(title_text="Rendite in %")
ui.plot(figure, filename="zins_bund_10j_monatlich", height=480)
st.caption(
    "Monatsmittel der Tagesrenditen (Deutsche Bundesbank). Die gestrichelten Linien "
    "markieren: Lehman-Pleite (15.09.2008), Beginn der Corona-Shutdowns (16.03.2020), "
    "Beginn der Russland-Sanktionen (02.03.2022) und die Schließung der Straße von "
    "Hormus nach dem Angriff der USA und Israels auf den Iran (28.02.2026)."
)

latest_yield = daily_yield.iloc[-1]
latest_debt = debt.iloc[-1]
theoretical_mio = latest_debt["schulden_mio_eur"] * latest_yield["rendite_pct"] / 100
quote_einnahmen = theoretical_mio / latest_debt["einnahmen_mio_eur"] * 100
quote_bip = theoretical_mio / latest_debt["bip_mio_eur"] * 100
actual_mio = latest_debt["zinsausgaben_mio_eur"]

st.markdown(
    f"**Aktuelle Rechnung:** {ui.format_mrd(latest_debt['schulden_mio_eur'], 0)} Schuldenstand "
    f"({int(latest_debt['jahr'])}) × {ui.format_number(latest_yield['rendite_pct'], 2)} % "
    f"Rendite ({latest_yield['datum']:%d.%m.%Y}) = "
    f"**{ui.format_mrd(theoretical_mio, 1)}** theoretische Zinslast pro Jahr."
)

columns = st.columns(3)
columns[0].metric(
    "Theoretische Zinslast (Mrd. €)",
    ui.format_number(theoretical_mio / 1000, 1),
    f"tatsächlich {ui.format_number(actual_mio / 1000, 1)}",
    delta_color="off",
)
columns[1].metric(
    "in % der Einnahmen",
    ui.format_number(quote_einnahmen, 1, " %"),
    "ohne neue Schulden",
    delta_color="off",
)
columns[2].metric(
    "in % des BIP",
    ui.format_number(quote_bip, 1, " %"),
    f"BIP {int(latest_debt['jahr'])}",
    delta_color="off",
)

figure = make_subplots(specs=[[{"secondary_y": True}]])
yield_rows = zinslast.dropna(subset=["rendite_pct"])
figure.add_trace(
    go.Scatter(
        x=yield_rows["jahr"],
        y=yield_rows["rendite_pct"],
        name="10-jährige Bundesanleihe (Jahresmittel)",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:.2f} %<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=yield_rows["jahr"],
        y=yield_rows["effektivzins_pct"],
        name="Effektivzins auf den Schuldenstand",
        line={"color": "#c9a227", "width": 2, "dash": "dot"},
        hovertemplate="%{y:.2f} %<extra></extra>",
    ),
    secondary_y=False,
)
figure.update_yaxes(title_text="Rendite in %", secondary_y=False)
figure.add_hline(y=0, line={"color": "#999", "width": 1})
ui.plot(figure, filename="zinslast_rendite", height=380)

figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=zinslast["jahr"],
        y=zinslast["zins_theoretisch_mio_eur"] / 1000,
        name="theoretische Zinslast",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:,.1f} Mrd. €<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=zinslast["jahr"],
        y=zinslast["zinsausgaben_mio_eur"] / 1000,
        name="tatsächliche Zinsausgaben",
        line={"color": "#b03a2e", "width": 2, "dash": "dash"},
        hovertemplate="%{y:,.1f} Mrd. €<extra></extra>",
    )
)
figure.update_yaxes(title_text="Mrd. €")
ui.plot(figure, filename="zinslast_theoretisch_tatsaechlich", height=380)

with st.expander("Berechnung und Abgrenzung"):
    st.markdown(
        "**Theoretische Zinslast** = Schuldenstand × Jahresdurchschnitt der Tagesrendite "
        "der aktuellen 10-jährigen Bundesanleihe / 100.\n\n"
        "**Effektivzins** = tatsächliche Zinsausgaben / Schuldenstand × 100. Er liegt "
        "unter der Marktrendite, weil Altbestände noch zu niedrigeren Zinsen laufen.\n\n"
        "**Zinsquote der Einnahmen** = theoretische Zinslast / Gesamteinnahmen × 100. "
        "Die Gesamteinnahmen der Volkswirtschaftlichen Gesamtrechnung enthalten keine "
        "Kreditaufnahme.\n\n"
        "Negative Werte in den Jahren 2019 bis 2021 spiegeln die damals negativen "
        "Renditen am Kapitalmarkt wider. Die Rechnung ist ein Modell und keine Prognose "
        "der tatsächlichen Haushaltsbelastung."
    )

st.divider()
st.subheader("Jahreswerte")
recent = zinslast.tail(15).copy()
st.dataframe(
    recent.rename(
        columns={
            "jahr": "Jahr",
            "schulden_mio_eur": "Schulden (Mio. €)",
            "rendite_pct": "Rendite (%)",
            "zins_theoretisch_mio_eur": "Theoretische Zinslast (Mio. €)",
            "einnahmen_mio_eur": "Einnahmen (Mio. €)",
            "zins_quote_einnahmen_pct": "in % der Einnahmen",
            "zins_quote_bip_pct": "in % des BIP",
            "zinsausgaben_mio_eur": "Zinsausgaben (Mio. €)",
            "effektivzins_pct": "Effektivzins (%)",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Schulden (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "Rendite (%)": st.column_config.NumberColumn(format="%.2f"),
        "Theoretische Zinslast (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "Einnahmen (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "in % der Einnahmen": st.column_config.NumberColumn(format="%.1f"),
        "in % des BIP": st.column_config.NumberColumn(format="%.1f"),
        "Zinsausgaben (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "Effektivzins (%)": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.caption(
    "Quellen: Eurostat gov_10a_main (Einnahmen, Ausgaben, Zinsausgaben), "
    "Eurostat gov_10dd_edpt1 (Schuldenstand), Eurostat nama_10_gdp (BIP) und "
    "Deutsche Bundesbank BBSSY.D.REN.EUR.A630.000000WT1010.A (10-jährige Bundesanleihe)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
