"""Insights: Datengeschichten als Foliensätze (Reveal.js, Hochformat)."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from haushaltssimulator import ui

st.title("Insights")
st.markdown(
    "Datengeschichten aus den Daten dieser App – als Foliensätze im Hochformat, gemacht "
    "für das Smartphone und zum Teilen. Alle Zahlen und Diagramme werden aus denselben "
    "Daten erzeugt wie die übrigen Seiten; die Quellen stehen auf jeder Folie."
)

saetze = ui.insight_decks()
if not saetze:
    st.info("Noch keine Foliensätze vorhanden (Ordner `insights/`).")
    st.stop()

beschriftungen = {f"{satz.titel} · {satz.folien} Folien": satz for satz in saetze}
wahl = st.radio("Foliensatz", list(beschriftungen), key="insight_auswahl")
satz = beschriftungen[wahl]

folien, info = st.columns([3, 2], gap="large")
with folien:
    # Hochformat 9:16: Reveal.js skaliert die Folie auf die Breite der Spalte.
    components.html(ui.insight_html(str(satz.pfad)), height=900, scrolling=False)
with info:
    st.subheader("Bedienung")
    st.markdown(
        "* **Blättern:** Pfeile unten rechts, Pfeiltasten oder Wischen\n"
        "* **Übersicht:** Taste `O`\n"
        "* **Vollbild und Teilen:** über den Link unten"
    )
    st.link_button("Im Vollbild öffnen", satz.pages_url, icon=":material/open_in_new:")
    st.caption(
        f"Adresse zum Teilen: {satz.pages_url} – erreichbar, sobald GitHub Pages für "
        "das Repository eingerichtet ist (siehe insights/README.md)."
    )
    if satz.beschreibung:
        st.subheader("Worum es geht")
        st.markdown(satz.beschreibung)

st.caption(
    "Die Foliensätze liegen im Repository unter `insights/`; Diagramme und Kennzahlen "
    "erzeugt `insights/<thema>/diagramme.py` aus `data/processed/`."
)
