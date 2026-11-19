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
    "theoretische Zinslast bei aktuellem Marktzins sowie Inflation und Realzins. "
    "Für die europäischen Länder stammen Schulden und Zinsausgaben von Eurostat; "
    "für USA und Russland aus der IWF-Datenbank *Public Finances in Modern History* "
    "und dem *World Economic Outlook*, umgerechnet mit dem EZB-Jahresdurchschnittskurs."
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
    "und Preisentwicklung. Schulden und Zinsausgaben der europäischen Länder stammen "
    "von Eurostat (`gov_10dd_edpt1`, `gov_10a_main`), die Inflationsraten aus "
    "`prc_hicp_manr` (HVPI). Für die USA und Russland nutzt die App die IWF-Datenbank "
    "*Public Finances in Modern History* (Schuldenquote, Einnahmen, Zinsausgaben) und "
    "den *World Economic Outlook* (BIP, Bevölkerung); die Werte sind mit dem "
    "EZB-Jahresdurchschnitt des Dollar-Euro-Kurses in Euro umgerechnet."
)

schulden = ui.laender_debt()
haushalt = ui.laender_budget()
inflation = ui.laender_inflation()
income = ui.laender_income()

EINKOMMENSARTEN = {
    "BIP je Einwohner:in": "bip_pro_kopf",
    "Verfügbares Einkommen je Einwohner:in": "verfuegbar_pro_kopf",
    "Bruttoverdienst je Beschäftigten": "bruttolohn",
}
EINKOMMENSQUELLEN = {
    "bip_pro_kopf": (
        "BIP je Einwohner:in: Eurostat `nama_10_gdp`/`demo_pjan` für die EU-Länder, "
        "IWF-WEO `NGDPDPC` für USA und Russland."
    ),
    "verfuegbar_pro_kopf": (
        "Verfügbares Einkommen je Einwohner:in: Eurostat `ilc_di03` für die EU-Länder, "
        "BEA/FRED `A229RC0A052NBEA` für die USA. Für Russland liegt keine frei "
        "abrufbare Reihe zum verfügbaren Haushaltseinkommen vor; ersatzweise wird das "
        "Bruttonationaleinkommen je Einwohner:in der Weltbank (`NY.GNP.PCAP.CD`) genutzt."
    ),
    "bruttolohn": (
        "Bruttoverdienst je Beschäftigten: Eurostat `nama_10_lp_ulc` (Arbeitnehmerentgelt "
        "je Arbeitnehmer:in) für die EU-Länder, BLS/FRED `CES0500000011` "
        "(Wochenverdienst × 52) für die USA. Für Russland liegt keine frei abrufbare "
        "Reihe vor."
    ),
}
einkommens_label = st.selectbox(
    "Einkommensgröße",
    list(EINKOMMENSARTEN),
    help=(
        "Grundlage für den Anteil der Zinslast am Durchschnittseinkommen und für den "
        "Einkommensverlauf."
    ),
)
einkommensart = EINKOMMENSARTEN[einkommens_label]

vergleich_auswahl = [land for land in selected if land in set(schulden["land"])]
if not vergleich_auswahl:
    st.info(
        "Für die ausgewählten Länder liegen keine Schulden- und Zinsdaten vor. "
        "Bitte mindestens ein Land mit verfügbaren Daten auswählen."
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
    auswahl = frame[frame["land"].isin(vergleich_auswahl)]
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
    "`nama_10_gdp`, `demo_pjan`; IWF WEO/FPP für USA und Russland, umgerechnet mit "
    "dem EZB-Jahresdurchschnittskurs."
)

einkommen_zeitraum = income[
    (income["einkommensart"] == einkommensart) & (income["jahr"] >= erstes_jahr)
]
einkommen_einheit = (
    "EUR je Beschäftigten" if einkommensart == "bruttolohn" else "EUR je Einwohner:in"
)
laender_linien(
    einkommen_zeitraum,
    "jahr",
    "einkommen_eur",
    einheit=einkommen_einheit,
    titel=f"Durchschnittseinkommen: {einkommens_label}",
    dateiname="zinsvergleich_einkommen",
)
st.caption(EINKOMMENSQUELLEN[einkommensart])

st.divider()
st.header("Theoretische Zinslast bei aktuellem Marktzins")
st.markdown(
    "Wie für Deutschland rechnet die App auch für die anderen Länder: "
    "**Schuldenstand des letzten Jahres × aktuelle 10-jährige Rendite**. Das Ergebnis "
    "zeigt, was der Schuldenstand kosten würde, wenn er komplett zum heutigen "
    "Marktzins finanziert wäre. Es ist eine Modellrechnung und liegt fast immer über "
    "den tatsächlichen Zinsausgaben, weil Altschulden niedriger verzinst sind."
)

theorie = analysis.theoretical_interest_by_country(
    schulden, haushalt, yields, income, einkommensart
)
theorie = theorie[theorie["land"].isin(vergleich_auswahl)].copy()
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
                "einkommen_eur",
                "zins_quote_einkommen_pct",
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
                "einkommen_eur": "Durchschnittseinkommen (€)",
                "zins_quote_einkommen_pct": "in % des Durchschnittseinkommens",
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
            "Durchschnittseinkommen (€)": st.column_config.NumberColumn(format="%.0f"),
            "in % des Durchschnittseinkommens": st.column_config.NumberColumn(format="%.2f"),
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
        "`demo_pjan` und `irt_lt_mcby_m`; IWF WEO/FPP für USA und Russland."
    )

    anteil = anzeige.dropna(subset=["zins_quote_einkommen_pct"]).sort_values(
        "zins_quote_einkommen_pct"
    )
    st.subheader("Zinslast je Einwohner:in in Prozent des Durchschnittseinkommens")
    if anteil.empty:
        st.info(f"Für die Auswahl liegt die Einkommensgröße „{einkommens_label}“ nicht vor.")
    else:
        figur = go.Figure(
            go.Bar(
                x=anteil["zins_quote_einkommen_pct"],
                y=anteil["land"],
                orientation="h",
                marker_color=[ui.chart_color(index) for index in range(len(anteil))],
                hovertemplate="%{x:.2f} % des Einkommens<extra>%{y}</extra>",
            )
        )
        figur.update_xaxes(
            title_text="Zinslast je Einwohner:in in % des Durchschnittseinkommens"
        )
        ui.plot(
            figur,
            filename="zinsvergleich_zinslast_einkommen",
            height=max(320, 40 * len(anteil)),
        )
        fehlend = sorted(set(anzeige["land"]) - set(anteil["land"]))
        if fehlend:
            st.info(
                "Ohne die gewählte Einkommensgröße bleiben: " + ", ".join(fehlend) + "."
            )
        st.caption(
            "Zinslast je Einwohner:in geteilt durch das Durchschnittseinkommen "
            f"({einkommens_label}). Für das Einkommen wird jeweils das jüngste "
            "verfügbare Jahr verwendet. Bei „BIP je Einwohner:in“ entspricht der "
            "Anteil rechnerisch der Zinsquote in Prozent des BIP."
        )

st.divider()
st.header("Inflation und Realzins")
st.markdown(
    "Die Inflationsrate zeigt, wie schnell das Preisniveau steigt. Der **Realzins** "
    "ist die Rendite minus Inflationsrate: Er sagt, wie viel ein Gläubiger nach "
    "Kaufkraftverlust tatsächlich verdient – und wie stark die Inflation die reale "
    "Schuldenlast des Staates senkt."
)

inflation_auswahl = inflation[inflation["land"].isin(vergleich_auswahl)]
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
    st.subheader("Inflationsrate")
    ui.plot(figur, filename="zinsvergleich_inflation", height=460)
    st.caption(
        "Veränderung der Verbraucherpreise gegenüber dem Vorjahr, monatlich. "
        "Europäische Länder: HVPI (Eurostat `prc_hicp_manr`); USA: CPI (FRED "
        "`CPIAUCSL`); Russland: Rosstat über EMISS, ersatzweise die aus "
        "saisonbereinigten Monatsraten verkettete 12-Monats-Rate der Bank of Russia. "
        f"Jüngster Monat: {letzter_inflationsmonat}; die Reihen enden je nach Quelle "
        "früher."
    )

    realzins = analysis.real_interest_rate(yields, inflation)
    realzins = realzins[
        (realzins["land"].isin(vergleich_auswahl)) & (realzins["monat"] >= erster_inflationsmonat)
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
            "Realzins = Rendite 10-jähriger Staatsanleihen minus Inflationsrate, "
            "monatlich. Positive Werte bedeuten einen Kaufkraftgewinn für Gläubiger. "
            "Quellen: Eurostat `irt_lt_mcby_m` und `prc_hicp_manr`, FRED "
            "`IRLTLT01USM156N` und `CPIAUCSL`, Bank of Russia (OFZ-Zinskurve und "
            "Preisdynamik)."
        )

st.divider()
st.subheader("Quellen & Links")
st.markdown(
    "* [Eurostat Data Browser](https://ec.europa.eu/eurostat/databrowser/) – "
    "Schulden, Einnahmen, BIP, Bevölkerung, Einkommen und Inflationsraten\n"
    "* [EZB Data Portal](https://data.ecb.europa.eu/) – Geldmenge, Preise, "
    "Zinsstatistiken und Wechselkurse\n"
    "* [FRED](https://fred.stlouisfed.org/docs/api/fred/) – US-Renditen, "
    "Verbraucherpreise, Einkommen und Wochenverdienst\n"
    "* [Internationaler Währungsfonds](https://www.imf.org/en/Data) – Schuldenquote, "
    "Einnahmen, Zinsausgaben, BIP und Bevölkerung außerhalb der EU\n"
    "* [Rosstat](https://rosstat.gov.ru/statistics/price) und "
    "[EMISS](https://fedstat.ru/) – Verbraucherpreise Russlands\n"
    "* [Weltbank](https://data.worldbank.org/) – Bruttonationaleinkommen je "
    "Einwohner:in\n"
    "* [Deutsche Bundesbank](https://www.bundesbank.de/de/statistiken) – Rendite der "
    "Bundesanleihe\n"
    "* [Bank of Russia](https://www.cbr.ru/eng/hd_base/zcyc_params/) – OFZ-Zinskurve "
    "und Preisdynamik"
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
    "* **Schulden und Zinsausgaben:** Für die EU-Länder Maastricht-Schulden und "
    "gebuchte Zinsausgaben (Eurostat). Für USA und Russland Bruttoschulden, "
    "Einnahmen und gezahlte Zinsen aus der IWF-Datenbank *Public Finances in Modern "
    "History*; die Abgrenzung weicht von der Maastricht-Definition ab. Die "
    "Euro-Beträge sind mit Jahresdurchschnittskursen umgerechnet.\n"
    "* **Inflation:** HVPI für die EU-Länder, CPI für die USA, Rosstat-CPI "
    "beziehungsweise eine verkettete 12-Monats-Rate der Bank of Russia. Die "
    "Erhebungssysteme unterscheiden sich.\n"
    "* **Einkommen:** Die drei wählbaren Größen sind unterschiedlich abgegrenzt. "
    "Für Russland steht beim verfügbaren Einkommen nur die BNE-Ersatzreihe der "
    "Weltbank zur Verfügung, beim Bruttoverdienst keine Reihe.\n"
    "* Die Renditen stammen aus unterschiedlichen Erhebungssystemen. "
    "Niveauunterschiede von wenigen Zehntelprozentpunkten sind methodisch bedingt."
)

retrieved = ui.data_retrieved_at()
st.caption(
    "Quellen: Eurostat `irt_lt_mcby_m`, `gov_10dd_edpt1`, `gov_10a_main`, `nama_10_gdp`, "
    "`demo_pjan`, `ilc_di03`, `nama_10_lp_ulc` und `prc_hicp_manr`; IWF WEO/FPP; "
    "EZB EXR; FRED `IRLTLT01USM156N`, `CPIAUCSL`, `A229RC0A052NBEA` und "
    "`CES0500000011`; Weltbank `NY.GNP.PCAP.CD`; Rosstat/EMISS und Bank of Russia "
    "(OFZ-Zinskurve, Preisdynamik)."
    + (f" Jüngster Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
