"""Haushalt, Schulden und Zinslast: von den Einnahmen zur theoretischen Zinslast."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import ui

# Zeitmarken für die Diagramme: Beschriftung, Datum, Höhe im oberen Teilbild, Anker.
ZEITMARKEN = (
    ("Start Agenda 2010", "2003-03-14", 0.02, "left"),
    ("Lehman-Pleite", "2008-09-15", 0.02, "left"),
    ("Corona", "2020-03-16", 0.02, "left"),
    ("Russland Sanktionen", "2022-03-02", 0.14, "left"),
    ("Hormus", "2026-02-28", 0.02, "right"),
)

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
bund_plan = ui.bund_interest_plan()
daily_yield = ui.bund_yield()
inflation = ui.purchasing_power()

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
inflation = inflation[inflation["monat"] >= daily_yield["monat"].min()]

st.subheader("Rendite der 10-jährigen Bundesanleihe (Monatsmittel)")
st.markdown(
    "Das obere Teilbild zeigt das Monatsmittel der Tagesrendite und – zuschaltbar – die "
    "Inflationsrate. Das untere Teilbild stellt die daraus folgende **theoretische "
    "Zinslast** den **tatsächlich gebuchten Zinsausgaben** gegenüber, ergänzt um den "
    "**Effektivzins** auf den Schuldenstand und um die im Finanzplan veranschlagten "
    "Zinsausgaben des Bundes."
)
zeige_inflation = st.toggle(
    "Inflation (HVPI) auf zweiter Achse anzeigen",
    value=not inflation.empty,
    disabled=inflation.empty,
    key="zins_bund_inflation",
)

plan = bund_plan.dropna(subset=["zinsausgaben_mrd_eur"]).sort_values("jahr")

figure = make_subplots(
    rows=2,
    cols=1,
    row_heights=[0.5, 0.5],
    vertical_spacing=0.16,
    specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
)
figure.add_trace(
    go.Scatter(
        x=monatsrendite["datum"],
        y=monatsrendite["rendite_pct"],
        name="Monatsmittel der Tagesrendite",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{x|%m.%Y}: %{y:.2f} %<extra></extra>",
    ),
    row=1,
    col=1,
    secondary_y=False,
)
if zeige_inflation:
    figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(inflation["monat"]),
            y=inflation["inflation_de_pct"],
            name="Inflation (HVPI)",
            line={"color": "#c9a227", "width": 2},
            hovertemplate="%{x|%m.%Y}: %{y:.1f} %<extra>Inflation</extra>",
        ),
        row=1,
        col=1,
        secondary_y=True,
    )

jahresmitte = pd.to_datetime(zinslast["jahr"].astype(str) + "-07-01")
figure.add_trace(
    go.Scatter(
        x=jahresmitte,
        y=zinslast["zins_theoretisch_mio_eur"] / 1000,
        name="theoretische Zinslast (Modell)",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{x|%Y}: %{y:,.1f} Mrd. €<extra></extra>",
    ),
    row=2,
    col=1,
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=jahresmitte,
        y=zinslast["zinsausgaben_mio_eur"] / 1000,
        name="tatsächliche Zinsausgaben",
        line={"color": "#b03a2e", "width": 2, "dash": "dash"},
        hovertemplate="%{x|%Y}: %{y:,.1f} Mrd. €<extra></extra>",
    ),
    row=2,
    col=1,
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=pd.to_datetime(plan["jahr"].astype(str) + "-07-01"),
        y=plan["zinsausgaben_mrd_eur"],
        name="geplante Zinsausgaben (Finanzplan)",
        mode="lines+markers",
        line={"color": "#6a3d9a", "width": 2, "dash": "dot"},
        marker={"size": 7},
        customdata=plan["art"],
        hovertemplate="%{x|%Y}: %{y:,.1f} Mrd. € (%{customdata})<extra></extra>",
    ),
    row=2,
    col=1,
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=jahresmitte,
        y=zinslast["effektivzins_pct"],
        name="Effektivzins auf den Schuldenstand",
        line={"color": "#8c564b", "width": 2, "dash": "dashdot"},
        hovertemplate="%{x|%Y}: %{y:.2f} %<extra></extra>",
    ),
    row=2,
    col=1,
    secondary_y=True,
)

for label, datum, hoehe, anker in ZEITMARKEN:
    for zeile in (1, 2):
        figure.add_vline(
            x=pd.Timestamp(datum),
            line={"color": "#b03a2e", "width": 1, "dash": "dot"},
            row=zeile,
            col=1,
        )
    figure.add_annotation(
        x=pd.Timestamp(datum),
        y=hoehe,
        xref="x",
        yref="y domain",
        text=label,
        showarrow=False,
        textangle=-90,
        xanchor=anker,
        yanchor="bottom",
        font={"size": 9, "color": "#b03a2e"},
        bgcolor="rgba(255,255,255,0.85)",
        borderpad=1,
    )

figure.update_yaxes(title_text="Rendite in %", row=1, col=1, secondary_y=False)
figure.update_yaxes(
    title_text="Inflation in %" if zeige_inflation else None,
    visible=zeige_inflation,
    showgrid=False,
    dtick=2,
    tickformat=".0f",
    row=1,
    col=1,
    secondary_y=True,
)
figure.update_yaxes(title_text="Mrd. €", row=2, col=1, secondary_y=False)
figure.update_yaxes(
    title_text="Effektivzins in %",
    showgrid=False,
    dtick=1,
    tickformat=".1f",
    row=2,
    col=1,
    secondary_y=True,
)
figure.add_hline(y=0, line={"color": "#999", "width": 1}, row=1, col=1)
figure.add_hline(y=0, line={"color": "#999", "width": 1}, row=2, col=1)
ui.plot(figure, filename="zins_bund_10j_und_zinslast", height=760, top_margin=130)
st.caption(
    "Oben: Monatsmittel der Tagesrenditen (Deutsche Bundesbank) und Inflation als "
    "Vorjahresrate des HVPI für Deutschland (EZB ICP, bis Dezember 2025). Unten: "
    "theoretische Zinslast (Schuldenstand × Jahresrendite, Modellrechnung), "
    "Zinsausgaben des Gesamtstaats (Eurostat, VGR), Effektivzins (Zinsausgaben / "
    "Schuldenstand) sowie die im Finanzplan des Bundes 2026 bis 2030 veranschlagten "
    "Zinsausgaben des Bundes im Kernhaushalt (Drucksache 21/7301, Tabelle 9) – eine "
    "engere Abgrenzung als die VGR. Die gestrichelten Marken gelten in beiden "
    "Teilbildern: Start der Agenda 2010 (14.03.2003), Lehman-Pleite (15.09.2008), "
    "Beginn der Corona-Shutdowns (16.03.2020), Beginn der Russland-Sanktionen "
    "(02.03.2022) und die Schließung der Straße von Hormus nach dem Angriff der USA "
    "und Israels auf den Iran (28.02.2026)."
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

with st.expander("Berechnung und Abgrenzung"):
    st.markdown(
        "**Theoretische Zinslast** = Schuldenstand × Jahresdurchschnitt der Tagesrendite "
        "der aktuellen 10-jährigen Bundesanleihe / 100.\n\n"
        "**Effektivzins** = tatsächliche Zinsausgaben / Schuldenstand × 100. Er liegt "
        "unter der Marktrendite, weil Altbestände noch zu niedrigeren Zinsen laufen.\n\n"
        "**Zinsquote der Einnahmen** = theoretische Zinslast / Gesamteinnahmen × 100. "
        "Die Gesamteinnahmen der Volkswirtschaftlichen Gesamtrechnung enthalten keine "
        "Kreditaufnahme.\n\n"
        "**Geplante Zinsausgaben** = Ansätze des Bundes im Kernhaushalt (Finanzplan "
        "2026 bis 2030, Drucksache 21/7301, Tabelle 9) für Ist 2025, Soll 2026, "
        "Entwurf 2027 und Finanzplan 2028 bis 2030. Sie enthalten auch die Zinsausgaben "
        "des SVIK und sind enger abgegrenzt als die Zinsausgaben des Gesamtstaats in "
        "der VGR.\n\n"
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
    "Eurostat gov_10dd_edpt1 (Schuldenstand), Eurostat nama_10_gdp (BIP), "
    "Deutsche Bundesbank BBSSY.D.REN.EUR.A630.000000WT1010.A (10-jährige Bundesanleihe) "
    "und Deutscher Bundestag, Drucksache 21/7301 (Finanzplan des Bundes 2026 bis 2030)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
