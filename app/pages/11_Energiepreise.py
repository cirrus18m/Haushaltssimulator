"""Energiepreise: Haushaltspreise, Börsenstrom und Kraftstoffe im EU-Vergleich."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Energiepreise")
st.markdown(
    "Was kostet Energie? Die Seite zeigt die Haushaltspreise für Strom und Gas in "
    "Deutschland, den Börsenstrompreis und die Kraftstoffpreise im europäischen Vergleich."
)

preise = ui.energy_prices()
boerse = ui.day_ahead_prices()
kraftstoff = ui.fuel_prices()
if preise.empty or kraftstoff.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

retrieved = ui.data_retrieved_at()
gesamt = preise[preise["verbrauchsklasse"] == "Insgesamt"].sort_values("jahr")
letztes_jahr = gesamt.iloc[-1]
vorjahr = gesamt.iloc[-2] if len(gesamt) > 1 else letztes_jahr

st.header("1. Strom- und Gaspreise für Haushalte")
columns = st.columns(3)
columns[0].metric(
    "Strompreis (inkl. Steuern)",
    ui.format_number(letztes_jahr["strompreis_eur_kwh"], 3, " €/kWh"),
    f"{ui.format_number(letztes_jahr['strompreis_eur_kwh'] - vorjahr['strompreis_eur_kwh'], 3)} "
    "€/kWh zum Vorjahr",
    delta_color="inverse",
)
columns[1].metric(
    "Gaspreis (inkl. Steuern)",
    ui.format_number(letztes_jahr["gaspreis_eur_kwh"], 3, " €/kWh"),
    f"{ui.format_number(letztes_jahr['gaspreis_eur_kwh'] - vorjahr['gaspreis_eur_kwh'], 3)} "
    "€/kWh zum Vorjahr",
    delta_color="inverse",
)
columns[2].metric(
    "Berichtsjahr",
    str(int(letztes_jahr["jahr"])),
    "Jahresdurchschnitt",
    delta_color="off",
)

figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=gesamt["jahr"],
        y=gesamt["strompreis_eur_kwh"],
        name="Strom",
        mode="lines+markers",
        line={"color": "#c9a227", "width": 3},
        hovertemplate="%{y:.3f} €/kWh<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=gesamt["jahr"],
        y=gesamt["gaspreis_eur_kwh"],
        name="Erdgas",
        mode="lines+markers",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:.3f} €/kWh<extra></extra>",
    )
)
figure.update_yaxes(title_text="€ je kWh", tickformat=".2f", rangemode="tozero")
ui.plot(figure, filename="energiepreise_haushalte", height=400)
st.caption(
    "Jahresdurchschnittspreise inklusive Steuern, Abgaben und Umlagen für Haushalte "
    "insgesamt (alle Verbrauchsklassen)."
)

st.divider()
st.header("2. Börsenstrompreis (Day-Ahead)")
if not boerse.empty:
    tagesmittel = boerse.set_index("datum")["preis_eur_mwh"]
    gleitend = tagesmittel.rolling(90, min_periods=30).mean()
    letzter = boerse.iloc[-1]
    negative = int((boerse["preis_eur_mwh"] < 0).sum())
    jahresmittel = boerse["preis_eur_mwh"].mean()

    columns = st.columns(3)
    columns[0].metric(
        "Letzter Tagespreis",
        ui.format_number(letzter["preis_eur_mwh"], 2, " €/MWh"),
        f"{letzter['datum']:%d.%m.%Y}",
        delta_color="off",
    )
    columns[1].metric(
        "Mittel seit 2019",
        ui.format_number(jahresmittel, 2, " €/MWh"),
        "Tagesmittel",
        delta_color="off",
    )
    columns[2].metric(
        "Tage mit negativem Preis",
        ui.format_number(negative, 0),
        f"von {len(boerse):,} Tagen".replace(",", "."),
        delta_color="off",
    )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=boerse["datum"],
            y=boerse["preis_eur_mwh"],
            name="Tagesmittel",
            line={"color": "#7fb2d5", "width": 1},
            hovertemplate="%{y:.2f} €/MWh<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=boerse["datum"],
            y=gleitend,
            name="90-Tage-Mittel",
            line={"color": "#1f4e79", "width": 3},
            hovertemplate="%{y:.2f} €/MWh<extra></extra>",
        )
    )
    figure.add_hline(y=0, line={"color": "#b03a2e", "width": 1, "dash": "dot"})
    figure.update_yaxes(title_text="€ je MWh")
    ui.plot(figure, filename="strompreis_boerse", height=420)

st.divider()
st.header("3. Kraftstoffe im EU-Vergleich")
produkt = st.selectbox(
    "Kraftstoff",
    sorted(kraftstoff["produkt"].unique()),
    index=0,
)
auswahl = kraftstoff[kraftstoff["produkt"] == produkt]
letzter_monat = auswahl["monat"].max()
aktuell = (
    auswahl[auswahl["monat"] == letzter_monat].sort_values("preis_eur_l").reset_index(drop=True)
)

figure = go.Figure(
    go.Bar(
        x=aktuell["preis_eur_l"],
        y=aktuell["land"],
        orientation="h",
        marker_color="#2e86ab",
        text=aktuell["preis_eur_l"].map(lambda wert: f"{wert:.3f}".replace(".", ",")),
        textposition="outside",
        hovertemplate="%{y}: %{x:.3f} €/l<extra></extra>",
    )
)
figure.update_xaxes(title_text="€ je Liter")
figure.update_yaxes(title_text="", autorange="reversed")
ui.plot(figure, filename="kraftstoffpreise_eu", height=560, legend=False)
st.caption(f"Monatsmittel {letzter_monat}, Preise mit Steuern.")

laender = sorted(auswahl["land"].unique())
wunsch = ["Deutschland", "Frankreich", "Italien", "Spanien", "Polen"]
standard = [land for land in wunsch if land in laender]
selected = st.multiselect("Länder im Zeitverlauf", laender, default=standard)
if selected:
    verlauf = auswahl[auswahl["land"].isin(selected)].pivot_table(
        index="monat", columns="land", values="preis_eur_l", aggfunc="mean"
    )
    figure = go.Figure()
    for index, land in enumerate(sorted(selected)):
        if land not in verlauf:
            continue
        figure.add_trace(
            go.Scatter(
                x=verlauf.index,
                y=verlauf[land],
                name=land,
                line={"color": ui.chart_color(index), "width": 2},
                hovertemplate="%{y:.3f} €/l<extra>" + land + "</extra>",
            )
        )
    figure.update_yaxes(title_text="€ je Liter")
    ui.plot(figure, filename="kraftstoffpreise_verlauf", height=400)

st.caption(
    "Quellen: Statistisches Bundesamt (61243-0002, 61243-0011), energy-charts.info "
    "(Daten: Bundesnetzagentur | SMARD.de) und EU Weekly Oil Bulletin."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
