"""Renditen 10-jähriger Staatsanleihen in Europa, den USA und Russland."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import analysis, ui

st.title("Zinsvergleich: Staatsanleihen in Europa, USA und Russland")
st.markdown(
    "Renditen 10-jähriger Staatsanleihen im Vergleich. Für die europäischen Länder nutzt "
    "die App die Konvergenzrenditen von Eurostat (Maastricht-Methode), für die USA die "
    "OECD-Reihe über FRED und für Russland die OFZ-Zinskurve der Bank of Russia. "
    "Die Reihen sind monatlich; die russischen Werte sind Monatsendwerte des letzten "
    "Handelstags.\n\n"
    "Unter den Renditen folgen Schuldenstand, Schuldenquote, Zinsausgaben je Land, die "
    "theoretische Zinslast bei aktuellem Marktzins sowie Inflation und Realzins."
)

yields = ui.international_yields()
if yields.empty:
    st.warning("Keine Zinsdaten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

laender = sorted(yields["land"].unique())
standard = [
    "Deutschland",
    "Frankreich",
    "Italien",
    "Spanien",
    "Vereinigte Staaten",
    "Russland",
]
selected = st.multiselect(
    "Länder",
    laender,
    default=[land for land in standard if land in laender],
    help="Mehrere Länder gleichzeitig auswählbar.",
)

jahre = st.select_slider(
    "Zeitraum",
    options=[5, 10, 20, 30],
    value=10,
    format_func=lambda wert: f"letzte {wert} Jahre",
)

letzter_monat = yields["monat"].max()
start_monat = (pd.Period(letzter_monat, freq="M") - jahre * 12).strftime("%Y-%m")
filtered = yields[(yields["monat"] >= start_monat) & (yields["land"].isin(selected))]

if filtered.empty:
    st.info("Für die Auswahl liegen keine Daten vor.")
    st.stop()

figure = go.Figure()
for index, land in enumerate(sorted(filtered["land"].unique())):
    reihe = filtered[filtered["land"] == land].sort_values("monat")
    figure.add_trace(
        go.Scatter(
            x=reihe["monat"],
            y=reihe["rendite_pct"],
            name=land,
            mode="lines",
            line={
                "width": 2.6 if land == "Deutschland" else 1.8,
                "color": ui.chart_color(index),
            },
            hovertemplate="%{y:.2f} %<extra>" + land + "</extra>",
        )
    )
figure.update_yaxes(title_text="Rendite in %", rangemode="tozero")
ui.plot(figure, filename="zinsvergleich_laender", height=520)

st.subheader("Letzte verfügbare Werte")
letzte = filtered.sort_values(["land", "monat"]).groupby("land", as_index=False).tail(1)
library = {entry["key"]: entry for entry in ui.sources_library().get("quellen", [])}
letzte["Abruf"] = letzte["quelle_key"].map(
    lambda key: ui.format_timestamp(library.get(key, {}).get("abgerufen_am"))
)
st.dataframe(
    letzte[["land", "monat", "rendite_pct", "quelle", "Abruf"]].rename(
        columns={
            "land": "Land",
            "monat": "Monat",
            "rendite_pct": "Rendite (%)",
            "quelle": "Quelle",
            "Abruf": "Datenabruf",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={"Rendite (%)": st.column_config.NumberColumn(format="%.2f")},
)

st.divider()
st.header("Schulden und Zinsausgaben im Vergleich")
st.markdown(
    "Die folgenden Abschnitte verknüpfen die Renditen mit Schuldenstand, Zinsausgaben "
    "und Preisentwicklung. Schulden und Zinsausgaben stammen von Eurostat "
    "(`gov_10dd_edpt1`, `gov_10a_main`), die Inflationsraten aus `prc_hicp_manr` "
    "(HVPI). Für die USA und Russland führt die Quellenbibliothek keine vergleichbaren "
    "Schulden- und Zinsreihen; sie fehlen in diesen Abschnitten deshalb."
)

schulden = ui.laender_debt()
haushalt = ui.laender_budget()
inflation = ui.laender_inflation()

europa_auswahl = [land for land in selected if land in set(schulden["land"])]
if not europa_auswahl:
    st.info(
        "Für die ausgewählten Länder liegen keine Schulden- und Zinsdaten vor. "
        "Bitte mindestens ein europäisches Land auswählen."
    )
    st.stop()

letztes_jahr = int(schulden["jahr"].max())
erstes_jahr = letztes_jahr - jahre


def laender_linien(
    frame: pd.DataFrame,
    x: str,
    y: str,
    *,
    einheit: str,
    titel: str,
    dateiname: str,
    hoehe: int = 440,
) -> None:
    """Zeichnet je Land eine Linie und blendet die Einheit in die Achse ein."""
    auswahl = frame[frame["land"].isin(europa_auswahl)]
    if auswahl.empty:
        st.info(f"Keine Daten für {titel}.")
        return
    figur = go.Figure()
    for index, land in enumerate(sorted(auswahl["land"].unique())):
        reihe = auswahl[auswahl["land"] == land].sort_values(x)
        figur.add_trace(
            go.Scatter(
                x=reihe[x],
                y=reihe[y],
                name=land,
                mode="lines",
                line={
                    "width": 2.6 if land == "Deutschland" else 1.8,
                    "color": ui.chart_color(index),
                },
                hovertemplate="%{y:.1f} " + einheit + "<extra>" + land + "</extra>",
            )
        )
    figur.update_yaxes(title_text=f"{einheit}")
    st.subheader(titel)
    ui.plot(figur, filename=dateiname, height=hoehe)


schulden_zeitraum = schulden[schulden["jahr"] >= erstes_jahr].copy()
schulden_zeitraum["schulden_mrd_eur"] = schulden_zeitraum["schulden_mio_eur"] / 1000

laender_linien(
    schulden_zeitraum,
    "jahr",
    "schulden_mrd_eur",
    einheit="Mrd. EUR",
    titel="Schuldenstand",
    dateiname="zinsvergleich_schulden",
)
st.caption(
    "Maastricht-Schuldenstand des Gesamtstaats (Sektor S13) zu Marktwerten, "
    f"{erstes_jahr} bis {letztes_jahr}. Quelle: Eurostat `gov_10dd_edpt1`."
)

laender_linien(
    schulden_zeitraum,
    "jahr",
    "schuldenquote_pct",
    einheit="% des BIP",
    titel="Schuldenquote",
    dateiname="zinsvergleich_schuldenquote",
)
st.caption(
    "Schuldenstand in Prozent des BIP. Die 60-%-Referenz des Maastricht-Vertrags gilt "
    "für alle EU-Mitgliedstaaten. Quelle: Eurostat `gov_10dd_edpt1`."
)

haushalt_zeitraum = haushalt[haushalt["jahr"] >= erstes_jahr]

laender_linien(
    haushalt_zeitraum,
    "jahr",
    "zins_quote_bip_pct",
    einheit="% des BIP",
    titel="Zinsausgaben in Prozent des BIP",
    dateiname="zinsvergleich_zinsquote_bip",
)
st.caption(
    "Tatsächlich gebuchte Zinsausgaben des Gesamtstaats (D41PAY) in Prozent des BIP. "
    "Quelle: Eurostat `gov_10a_main` und `nama_10_gdp`."
)

laender_linien(
    haushalt_zeitraum,
    "jahr",
    "zins_je_einwohner_eur",
    einheit="EUR je Einwohner:in",
    titel="Zinsausgaben je Einwohner:in",
    dateiname="zinsvergleich_zins_pro_kopf",
)
st.caption(
    "Zinsausgaben je Einwohner:in in Euro – eine Größe, die Länder unterschiedlicher "
    "Größe direkt vergleichbar macht. Sie skaliert wie die Zinsquote mit "
    "Schuldenstand, Zinsniveau und Preisniveau. Quellen: Eurostat `gov_10a_main`, "
    "`nama_10_gdp`, `demo_pjan`."
)

st.divider()
st.header("Theoretische Zinslast bei aktuellem Marktzins")
st.markdown(
    "Wie für Deutschland rechnet die App auch für die anderen Länder: "
    "**Schuldenstand des letzten Jahres × aktuelle 10-jährige Rendite**. Das Ergebnis "
    "zeigt, was der Schuldenstand kosten würde, wenn er komplett zum heutigen "
    "Marktzins finanziert wäre. Es ist eine Modellrechnung und liegt fast immer über "
    "den tatsächlichen Zinsausgaben, weil Altschulden niedriger verzinst sind."
)

theorie = analysis.theoretical_interest_by_country(schulden, haushalt, yields)
theorie = theorie[theorie["land"].isin(europa_auswahl)].copy()
theorie["zins_theoretisch_mrd_eur"] = theorie["zins_theoretisch_mio_eur"] / 1000

if theorie.empty:
    st.info("Für die Auswahl lässt sich keine theoretische Zinslast berechnen.")
else:
    anzeige = theorie.sort_values("zins_theoretisch_mrd_eur", ascending=False)
    st.dataframe(
        anzeige[
            [
                "land",
                "jahr",
                "schuldenquote_pct",
                "rendite_pct",
                "zins_theoretisch_mrd_eur",
                "zins_quote_bip_pct",
                "zins_quote_einnahmen_pct",
                "zins_je_einwohner_eur",
            ]
        ].rename(
            columns={
                "land": "Land",
                "jahr": "Schuldenstand",
                "schuldenquote_pct": "Schuldenquote (%)",
                "rendite_pct": "Rendite 10 J. (%)",
                "zins_theoretisch_mrd_eur": "Zinslast (Mrd. €)",
                "zins_quote_bip_pct": "in % des BIP",
                "zins_quote_einnahmen_pct": "in % der Einnahmen",
                "zins_je_einwohner_eur": "je Einwohner:in (€)",
            }
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Schuldenquote (%)": st.column_config.NumberColumn(format="%.1f"),
            "Rendite 10 J. (%)": st.column_config.NumberColumn(format="%.2f"),
            "Zinslast (Mrd. €)": st.column_config.NumberColumn(format="%.1f"),
            "in % des BIP": st.column_config.NumberColumn(format="%.2f"),
            "in % der Einnahmen": st.column_config.NumberColumn(format="%.2f"),
            "je Einwohner:in (€)": st.column_config.NumberColumn(format="%.0f"),
        },
    )

    figur = go.Figure(
        go.Bar(
            x=anzeige["zins_theoretisch_mrd_eur"],
            y=anzeige["land"],
            orientation="h",
            marker_color=[ui.chart_color(index) for index in range(len(anzeige))],
            hovertemplate="%{x:.1f} Mrd. EUR<extra>%{y}</extra>",
        )
    )
    figur.update_xaxes(title_text="Theoretische Zinslast in Mrd. EUR")
    figur.update_yaxes(autorange="reversed")
    ui.plot(figur, filename="zinsvergleich_zinslast", height=max(360, 40 * len(anzeige)))
    st.caption(
        "Theoretische Zinslast = Schuldenstand × aktuelle Rendite. Der Zins ist der "
        "letzte verfügbare Monatswert, der Schuldenstand das letzte verfügbare Jahr. "
        "Quellen: Eurostat `gov_10dd_edpt1`, `gov_10a_main`, `nama_10_gdp`, "
        "`demo_pjan` und `irt_lt_mcby_m`."
    )

st.divider()
st.header("Inflation und Realzins")
st.markdown(
    "Die Inflationsrate (HVPI, Veränderung gegenüber dem Vorjahr) zeigt, wie schnell "
    "das Preisniveau steigt. Der **Realzins** ist die Rendite minus Inflationsrate: "
    "Er sagt, wie viel ein Gläubiger nach Kaufkraftverlust tatsächlich verdient – und "
    "wie stark die Inflation die reale Schuldenlast des Staates senkt."
)

inflation_auswahl = inflation[inflation["land"].isin(europa_auswahl)]
if inflation_auswahl.empty:
    st.info("Für die Auswahl liegen keine Inflationsdaten vor.")
else:
    letzter_inflationsmonat = inflation_auswahl["monat"].max()
    erster_inflationsmonat = (pd.Period(letzter_inflationsmonat, freq="M") - jahre * 12).strftime(
        "%Y-%m"
    )
    inflation_zeitraum = inflation_auswahl[inflation_auswahl["monat"] >= erster_inflationsmonat]

    figur = go.Figure()
    for index, land in enumerate(sorted(inflation_zeitraum["land"].unique())):
        reihe = inflation_zeitraum[inflation_zeitraum["land"] == land].sort_values("monat")
        figur.add_trace(
            go.Scatter(
                x=reihe["monat"],
                y=reihe["inflation_pct"],
                name=land,
                mode="lines",
                line={
                    "width": 2.6 if land == "Deutschland" else 1.8,
                    "color": ui.chart_color(index),
                },
                hovertemplate="%{y:.2f} %<extra>" + land + "</extra>",
            )
        )
    figur.update_yaxes(title_text="Inflationsrate in %")
    figur.add_hline(y=2.0, line_dash="dot", line_color="#888", annotation_text="EZB-Ziel 2 %")
    st.subheader("Inflationsrate (HVPI)")
    ui.plot(figur, filename="zinsvergleich_inflation", height=460)
    st.caption(
        "HVPI-Inflationsrate gegenüber dem Vorjahr, monatlich. "
        f"Letzter Datenstand: {letzter_inflationsmonat}. Quelle: Eurostat `prc_hicp_manr`."
    )

    realzins = analysis.real_interest_rate(yields, inflation)
    realzins = realzins[
        (realzins["land"].isin(europa_auswahl)) & (realzins["monat"] >= erster_inflationsmonat)
    ]
    if realzins.empty:
        st.info("Für die Auswahl lässt sich kein Realzins berechnen.")
    else:
        figur = go.Figure()
        for index, land in enumerate(sorted(realzins["land"].unique())):
            reihe = realzins[realzins["land"] == land].sort_values("monat")
            figur.add_trace(
                go.Scatter(
                    x=reihe["monat"],
                    y=reihe["realzins_pct"],
                    name=land,
                    mode="lines",
                    line={
                        "width": 2.6 if land == "Deutschland" else 1.8,
                        "color": ui.chart_color(index),
                    },
                    hovertemplate="%{y:.2f} %<extra>" + land + "</extra>",
                )
            )
        figur.update_yaxes(title_text="Realzins in %")
        figur.add_hline(y=0.0, line_dash="dot", line_color="#888")
        st.subheader("Realzins: Rendite minus Inflation")
        ui.plot(figur, filename="zinsvergleich_realzins", height=460)
        st.caption(
            "Realzins = Rendite 10-jähriger Staatsanleihen minus HVPI-Inflationsrate, "
            "monatlich. Positive Werte bedeuten einen Kaufkraftgewinn für Gläubiger. "
            "Quellen: Eurostat `irt_lt_mcby_m` und `prc_hicp_manr`."
        )

st.divider()
st.subheader("Quellen & Links")
st.markdown(
    "* [Eurostat Data Browser](https://ec.europa.eu/eurostat/databrowser/) – "
    "Schulden, Einnahmen, BIP, Bevölkerung und Inflationsraten\n"
    "* [EZB Data Portal](https://data.ecb.europa.eu/) – Geldmenge, Preise und "
    "Zinsstatistiken der Europäischen Zentralbank\n"
    "* [FRED](https://fred.stlouisfed.org/docs/api/fred/) – US-Renditen\n"
    "* [Deutsche Bundesbank](https://www.bundesbank.de/de/statistiken) – Rendite der "
    "Bundesanleihe\n"
    "* [Bank of Russia](https://www.cbr.ru/eng/hd_base/zcyc_params/) – OFZ-Zinskurve"
)

st.divider()
st.subheader("Hinweise zur Vergleichbarkeit")

st.markdown(
    "* **Europäische Länder:** Eurostat `irt_lt_mcby_m`, monatliche Renditen "
    "10-jähriger Staatsanleihen nach der Konvergenzmethode.\n"
    "* **Vereinigte Staaten:** OECD-Reihe `IRLTLT01USM156N` über FRED, monatlicher "
    "Durchschnitt 10-jähriger Staatsanleihen.\n"
    "* **Russland:** Bank of Russia, Zero-Coupon-Yield-Curve, 10-jährige OFZ-Rendite "
    "am Monatsende. Die Reihe beginnt 2016.\n"
    "* Die Reihen stammen aus unterschiedlichen Erhebungssystemen. Niveauunterschiede "
    "von wenigen Zehntelprozentpunkten sind methodisch bedingt."
)

retrieved = ui.data_retrieved_at()
st.caption(
    "Quellen: Eurostat `irt_lt_mcby_m`, `gov_10dd_edpt1`, `gov_10a_main`, `nama_10_gdp`, "
    "`demo_pjan` und `prc_hicp_manr`, FRED `IRLTLT01USM156N` sowie Bank of Russia "
    "(OFZ-Zinskurve)." + (f" Jüngster Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
