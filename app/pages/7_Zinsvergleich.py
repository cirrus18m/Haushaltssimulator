"""Renditen 10-jähriger Staatsanleihen in Europa, den USA und Russland."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Zinsvergleich: Staatsanleihen in Europa, USA und Russland")
st.markdown(
    "Renditen 10-jähriger Staatsanleihen im Vergleich. Für die europäischen Länder nutzt "
    "die App die Konvergenzrenditen von Eurostat (Maastricht-Methode), für die USA die "
    "OECD-Reihe über FRED und für Russland die OFZ-Zinskurve der Bank of Russia. "
    "Die Reihen sind monatlich; die russischen Werte sind Monatsendwerte des letzten "
    "Handelstags."
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
    "Quellen: Eurostat irt_lt_mcby_m, FRED IRLTLT01USM156N und Bank of Russia "
    "(OFZ-Zinskurve)."
    + (f" Jüngster Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
