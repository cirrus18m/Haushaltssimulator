"""Energiepreise: Haushaltspreise, Börsenstrom und Kraftstoffe im EU-Vergleich."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Energiepreise")
st.markdown(
    "Was kostet Energie? Die Seite zeigt die Haushaltspreise für Strom und Gas in "
    "Deutschland, den Börsenstrompreis, die Kraftstoffpreise im europäischen Vergleich "
    "sowie Heizöl, Gas-Großhandel und Brent-Rohöl."
)

preise = ui.energy_prices()
boerse = ui.day_ahead_prices()
kraftstoff = ui.fuel_prices()
maerkte = ui.energy_markets()
if preise.empty or kraftstoff.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

retrieved = ui.data_retrieved_at()
gesamt = preise[preise["verbrauchsklasse"] == "Insgesamt"].sort_values("jahr")
letztes_jahr = gesamt.iloc[-1]
vorjahr = gesamt.iloc[-2] if len(gesamt) > 1 else letztes_jahr

st.header("1. Strom- und Gaspreise für Haushalte")
strom_delta = (letztes_jahr["strompreis_eur_kwh"] - vorjahr["strompreis_eur_kwh"]) * 100
gas_delta = (letztes_jahr["gaspreis_eur_kwh"] - vorjahr["gaspreis_eur_kwh"]) * 100
columns = st.columns(3)
columns[0].metric(
    "Strompreis (inkl. Steuern)",
    ui.format_number(letztes_jahr["strompreis_eur_kwh"] * 100, 1, " ct/kWh"),
    f"{ui.format_number(strom_delta, 1)} ct/kWh zum Vorjahr",
    delta_color="inverse",
)
columns[1].metric(
    "Gaspreis (inkl. Steuern)",
    ui.format_number(letztes_jahr["gaspreis_eur_kwh"] * 100, 1, " ct/kWh"),
    f"{ui.format_number(gas_delta, 1)} ct/kWh zum Vorjahr",
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
        y=gesamt["strompreis_eur_kwh"] * 100,
        name="Strom",
        mode="lines+markers",
        line={"color": "#c9a227", "width": 3},
        hovertemplate="%{y:.1f} ct/kWh<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=gesamt["jahr"],
        y=gesamt["gaspreis_eur_kwh"] * 100,
        name="Erdgas",
        mode="lines+markers",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:.1f} ct/kWh<extra></extra>",
    )
)
figure.update_yaxes(title_text="ct je kWh", tickformat=".1f", rangemode="tozero")
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

st.divider()
st.header("4. Heizöl, Gas und Rohöl")
st.markdown(
    "Monatspreise für Heizöl in Deutschland, den europäischen Gas-Großhandelspreis und "
    "Brent-Rohöl. Für den Vergleich der Energieträger sind alle drei Reihen zusätzlich "
    "in Cent je kWh umgerechnet."
)

if maerkte.empty:
    st.info("Keine Marktpreise gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
else:
    letzte_heizoel = maerkte.dropna(subset=["heizoel_ct_l"]).iloc[-1]
    letzte_gas = maerkte.dropna(subset=["gas_ct_kwh"]).iloc[-1]
    letzte_brent = maerkte.dropna(subset=["brent_eur_barrel"]).iloc[-1]

    columns = st.columns(3)
    columns[0].metric(
        "Heizöl, ct/l",
        ui.format_number(letzte_heizoel["heizoel_ct_l"], 1),
        help=f"Stand {ui.format_month(letzte_heizoel['monat'])}; "
        f"{ui.format_number(letzte_heizoel['heizoel_ct_kwh'], 1)} ct/kWh",
    )
    columns[1].metric(
        "Gas Europa, ct/kWh",
        ui.format_number(letzte_gas["gas_ct_kwh"], 1),
        help=f"Stand {ui.format_month(letzte_gas['monat'])}",
    )
    columns[2].metric(
        "Brent, €/Barrel",
        ui.format_number(letzte_brent["brent_eur_barrel"], 1),
        help=f"Stand {ui.format_month(letzte_brent['monat'])}; "
        f"{ui.format_number(letzte_brent['brent_ct_kwh'], 1)} ct/kWh",
    )
    figure = go.Figure()
    for spalte, name, farbe in (
        ("heizoel_ct_kwh", "Heizöl", "#b03a2e"),
        ("gas_ct_kwh", "Gas (Europa)", "#2e86ab"),
        ("brent_ct_kwh", "Brent-Rohöl", "#1f4e79"),
    ):
        figure.add_trace(
            go.Scatter(
                x=pd.to_datetime(maerkte["monat"]),
                y=maerkte[spalte],
                name=name,
                line={"color": farbe, "width": 2},
                hovertemplate="%{x|%m.%Y}: %{y:.2f} ct/kWh<extra>" + name + "</extra>",
            )
        )
    figure.update_yaxes(title_text="ct je kWh", rangemode="tozero")
    ui.plot(figure, filename="energiepreise_ct_kwh", height=420)
    st.caption(
        "Monatsmittel in Cent je kWh. Heizöl ist ein Endverbraucherpreis inklusive "
        "Steuern, Gas und Brent sind Großhandels- bzw. Börsenpreise ohne deutsche "
        "Steuern und Abgaben."
    )

    figure = go.Figure(
        go.Scatter(
            x=pd.to_datetime(maerkte["monat"]),
            y=maerkte["brent_eur_barrel"],
            name="Brent-Rohöl",
            line={"color": "#1f4e79", "width": 2},
            hovertemplate="%{x|%m.%Y}: %{y:.2f} €/Barrel<extra></extra>",
        )
    )
    figure.update_yaxes(title_text="€ je Barrel", rangemode="tozero")
    ui.plot(figure, filename="brent_eur_barrel", height=380)
    st.caption(
        "Brent-Spotpreis (EIA über FRED), mit dem EZB-Tageskurs in Euro umgerechnet."
    )

    with st.expander("Umrechnung und Abgrenzung"):
        st.markdown(
            "Umrechnung in ct je kWh: 1 Liter Heizöl = 10 kWh, 1 Barrel Rohöl "
            "= 1.700 kWh, 1 Million British Thermal Units = 293,071 kWh. "
            "Die Gasreihe ist der europäische Benchmark-Preis des IWF "
            "(Primary Commodity Prices); die Dollar-Werte von Gas und Brent werden "
            "mit dem EZB-Referenzkurs in Euro umgerechnet.\n\n"
            "Die Reihen sind unterschiedlich abgegrenzt: Heizöl ist ein "
            "Endverbraucherpreis mit Steuern und Abgaben, Gas und Brent sind "
            "Großhandels- bzw. Börsenpreise. Der Vergleich in ct/kWh zeigt die "
            "Energiegehalte, nicht die tatsächlichen Haushaltskosten."
        )

st.divider()
st.header("5. Regionale Gas- und Öl-Benchmarks")
st.markdown(
    "Die wichtigsten regionalen Gasmärkte im Vergleich: **TTF** für Europa, **JKM** "
    "für Nordostasien und **Henry Hub** für die USA. Für Öl stehen **Brent** "
    "(Europa), **WTI** (USA) und **Dubai** (Asien). Alle Werte sind in Euro "
    "umgerechnet."
)

if not maerkte.empty:
    letzte_ttf = maerkte.dropna(subset=["gas_ttf_eur_mwh"]).iloc[-1]
    letzte_jkm = maerkte.dropna(subset=["gas_jkm_eur_mwh"]).iloc[-1]
    letzte_henry = maerkte.dropna(subset=["gas_henry_hub_eur_mwh"]).iloc[-1]
    letzte_wti = maerkte.dropna(subset=["wti_eur_barrel"]).iloc[-1]
    letzte_dubai = maerkte.dropna(subset=["dubai_eur_barrel"]).iloc[-1]
    letzte_brent_benchmark = maerkte.dropna(subset=["brent_eur_barrel"]).iloc[-1]

    columns = st.columns(3)
    columns[0].metric(
        "TTF, €/MWh",
        ui.format_number(letzte_ttf["gas_ttf_eur_mwh"], 1),
        help=f"Stand {ui.format_month(letzte_ttf['monat'])}",
    )
    columns[1].metric(
        "JKM, €/MWh",
        ui.format_number(letzte_jkm["gas_jkm_eur_mwh"], 1),
        help=f"Stand {ui.format_month(letzte_jkm['monat'])}; "
        "frei verfügbare Referenz: IWF-Preis für LNG Japan",
    )
    columns[2].metric(
        "Henry Hub, €/MWh",
        ui.format_number(letzte_henry["gas_henry_hub_eur_mwh"], 1),
        help=f"Stand {ui.format_month(letzte_henry['monat'])}",
    )

    figure = go.Figure()
    for spalte, name, farbe in (
        ("gas_ttf_eur_mwh", "TTF (Europa)", "#1f4e79"),
        ("gas_jkm_eur_mwh", "JKM (Nordostasien)", "#b03a2e"),
        ("gas_henry_hub_eur_mwh", "Henry Hub (USA)", "#2e7d32"),
    ):
        figure.add_trace(
            go.Scatter(
                x=pd.to_datetime(maerkte["monat"]),
                y=maerkte[spalte],
                name=name,
                line={"color": farbe, "width": 2},
                hovertemplate="%{x|%m.%Y}: %{y:.2f} €/MWh<extra>" + name + "</extra>",
            )
        )
    figure.update_yaxes(title_text="€ je MWh", rangemode="tozero")
    ui.plot(figure, filename="gaspreise_regionen", height=440)
    st.caption(
        "Regionale Gas-Benchmarks in Euro je MWh. TTF: IWF-Benchmark für europäisches "
        "Erdgas; JKM: frei verfügbare Referenz ist der IWF-Preis für LNG Japan "
        "(Platts JKM ist kostenpflichtig); Henry Hub: EIA-Spotpreis. Umrechnung mit "
        "dem EZB-Tages- bzw. Monatsdurchschnitt des Dollar-Euro-Kurses."
    )

    columns = st.columns(3)
    columns[0].metric(
        "Brent, €/Barrel",
        ui.format_number(letzte_brent_benchmark["brent_eur_barrel"], 1),
        help=f"Stand {ui.format_month(letzte_brent_benchmark['monat'])}",
    )
    columns[1].metric(
        "WTI, €/Barrel",
        ui.format_number(letzte_wti["wti_eur_barrel"], 1),
        help=f"Stand {ui.format_month(letzte_wti['monat'])}",
    )
    columns[2].metric(
        "Dubai, €/Barrel",
        ui.format_number(letzte_dubai["dubai_eur_barrel"], 1),
        help=f"Stand {ui.format_month(letzte_dubai['monat'])}",
    )

    figure = go.Figure()
    for spalte, name, farbe in (
        ("brent_eur_barrel", "Brent (Europa)", "#1f4e79"),
        ("wti_eur_barrel", "WTI (USA)", "#b03a2e"),
        ("dubai_eur_barrel", "Dubai (Asien)", "#c9a227"),
    ):
        figure.add_trace(
            go.Scatter(
                x=pd.to_datetime(maerkte["monat"]),
                y=maerkte[spalte],
                name=name,
                line={"color": farbe, "width": 2},
                hovertemplate="%{x|%m.%Y}: %{y:.2f} €/Barrel<extra>" + name + "</extra>",
            )
        )
    figure.update_yaxes(title_text="€ je Barrel", rangemode="tozero")
    ui.plot(figure, filename="oelpreise_regionen", height=400)
    st.caption(
        "Regionale Öl-Benchmarks in Euro je Barrel: Brent (Nordsee), WTI "
        "(Cushing, Oklahoma) und Dubai (Asien). Umrechnung mit dem EZB-Referenzkurs."
    )

    with st.expander("Abgrenzung der Benchmarks"):
        st.markdown(
            "**TTF (Title Transfer Facility, Niederlande):** maßgeblicher "
            "Referenzpreis für den europäischen Gasmarkt. Die App nutzt die frei "
            "verfügbare IWF-Benchmarkreihe für europäisches Erdgas; der lizenzierte "
            "ICE-Endex-TTF wird nicht verwendet.\n\n"
            "**JKM (Japan/Korea Marker):** Benchmark für LNG nach Nordostasien. Der "
            "Platts-JKM ist kostenpflichtig; die App nutzt den frei verfügbaren "
            "IWF-Preis für LNG Japan als Referenz.\n\n"
            "**Henry Hub (Louisiana, USA):** wichtigster Referenzpreis für den "
            "US-Erdgasmarkt.\n\n"
            "**Öl:** Brent ist der Referenzpreis für die Nordsee und Europa, WTI für "
            "Nordamerika und Dubai für Asien. Die Rohölsorten unterscheiden sich in "
            "Dichte und Schwefelgehalt; die Preise sind daher nicht vollständig "
            "deckungsgleich."
        )

st.caption(
    "Quellen: Statistisches Bundesamt (61243-0002, 61243-0011), energy-charts.info "
    "(Daten: Bundesnetzagentur | SMARD.de), EU Weekly Oil Bulletin (Kraftstoffe und "
    "Heizöl), EIA und IWF über FRED (Brent, WTI, Henry Hub, Gas Europa/Japan) sowie "
    "EZB (Wechselkurs)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
