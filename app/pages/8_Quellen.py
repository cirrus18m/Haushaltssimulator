"""Quellen und Datenabruf: welche Quelle liefert welche Daten."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from haushaltssimulator import dataset, ui

st.title("Quellen und Datenabruf")
st.markdown(
    "Alle Kennzahlen der App stammen aus frei verfügbaren, öffentlichen Quellen. "
    "Die **Quellenbibliothek** (`data/sources.json`) ist Teil des Repositories und hält "
    "je Quelle URL, Lizenz, verwendete Datensätze, Prüfsumme und den Zeitpunkt des "
    "Downloads fest. Automatisch geladene Rohdaten liegen unter `data/raw/`, von Hand "
    "geladene unter `data/raw/manual/` (versioniert), aufbereitete Tabellen unter "
    "`data/processed/`."
)

library = ui.sources_library()
entries = library.get("quellen", [])
retrieved = ui.data_retrieved_at()

if not entries:
    st.warning(
        "Keine Quellenbibliothek gefunden. Bitte `uv run scripts/build_data.py` ausführen."
    )
    st.stop()

st.metric(
    "Jüngster Datenabruf",
    f"{retrieved:%d.%m.%Y, %H:%M Uhr}" if retrieved else "unbekannt",
    f"{len(entries)} Quellen dokumentiert",
    delta_color="off",
)

st.header("Welche Quelle liefert welche Daten?")
rows = []
for datei, label in dataset.DATASET_LABELS.items():
    anbieter = [entry for entry in entries if datei in entry.get("datensaetze", [])]
    abrufe = [entry["abgerufen_am"] for entry in anbieter if entry.get("abgerufen_am")]
    rows.append(
        {
            "Datensatz": label,
            "Quellen": " · ".join(entry["key"] for entry in anbieter) or "–",
            "Abruf": ui.format_timestamp(max(abrufe)).split(",")[0] if abrufe else "–",
        }
    )
st.dataframe(
    pd.DataFrame(rows),
    hide_index=True,
    width="stretch",
    column_config={
        "Datensatz": st.column_config.TextColumn(width="large"),
        "Quellen": st.column_config.TextColumn(width="medium"),
        "Abruf": st.column_config.TextColumn(width="small"),
    },
)
st.caption(
    "Die Schlüssel entsprechen den Einträgen der Quellenbibliothek; Titel und URLs "
    "stehen in der Tabelle darunter und in den Details je Quelle."
)

st.header("Quellenbibliothek")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Schlüssel": entry["key"],
                "Herausgeber": entry["herausgeber"],
                "Lizenz": entry["lizenz"],
                "Abgerufen am": ui.format_timestamp(entry.get("abgerufen_am")),
                "Datei": entry["datei"],
                "URL": entry["url"],
            }
            for entry in entries
        ]
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Herausgeber": st.column_config.TextColumn(width="medium"),
        "Lizenz": st.column_config.TextColumn(width="medium"),
        "Datei": st.column_config.TextColumn(width="medium"),
        "URL": st.column_config.LinkColumn("URL", display_text="Quelle öffnen"),
    },
)

st.caption(
    "Abrufdatum und Prüfsumme werden beim Download gesetzt. Bereits vorhandene Rohdaten "
    "behalten ihren ursprünglichen Zeitstempel; ein erneuter Abruf erfolgt mit "
    "`uv run scripts/build_data.py --refresh`."
)

st.header("Details je Quelle")
for entry in entries:
    with st.expander(entry["titel"]):
        st.markdown(f"**Herausgeber:** {entry['herausgeber']}")
        st.markdown(f"**Lizenz:** {entry['lizenz']}")
        st.markdown(f"**Beschreibung:** {entry['beschreibung']}")
        verwendung = ", ".join(
            dataset.DATASET_LABELS.get(name, name) for name in entry.get("datensaetze", [])
        )
        st.markdown(f"**Verwendet für:** {verwendung}")
        st.markdown(f"**Abgerufen am:** {ui.format_timestamp(entry.get('abgerufen_am'))}")
        groesse = f"{entry['bytes']:,}".replace(",", ".")
        st.markdown(f"**Rohdatei:** `data/raw/{entry['datei']}` ({groesse} Bytes)")
        st.markdown(f"**SHA-256:** `{entry['sha256']}`")
        st.link_button("Quelle öffnen", entry["url"])

st.header("Quellen & Links")
anbieter = library.get("anbieter", [])
if anbieter:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Anbieter": eintrag["anbieter"],
                    "Daten in dieser App": eintrag["daten"],
                    "Portal": eintrag["portal"],
                    "API / Doku": eintrag["api"] or None,
                    "Zugang": eintrag["zugang"],
                }
                for eintrag in anbieter
            ]
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Anbieter": st.column_config.TextColumn(width="medium"),
            "Daten in dieser App": st.column_config.TextColumn(width="large"),
            "Portal": st.column_config.LinkColumn("Portal", display_text="Portal öffnen"),
            "API / Doku": st.column_config.LinkColumn("API / Doku", display_text="API-Doku"),
            "Zugang": st.column_config.TextColumn(width="medium"),
        },
    )
    st.caption(
        "Direkt nutzbare Schnittstellen sind Destatis GENESIS, FRED, das EZB-Data-Portal, "
        "Eurostat und die Bundesbank. Die App selbst ruft keine APIs auf: Abrufe laufen "
        "vorgelagert über Skripte, Zugangsdaten stehen in `.env` (nicht versioniert)."
    )
else:
    st.info("Anbieter-Links fehlen in der Quellenbibliothek – bitte Datenaufbau erneut ausführen.")

st.divider()
st.subheader("Datenfluss")
st.code(
    "data/raw/         (automatisch geladene Rohdaten, nicht versioniert)\n"
    "data/raw/manual/  (manuell geladene Rohdaten, versioniert)\n"
    "    │  sources.py: Download, Prüfsumme, Zeitstempel → data/sources.json\n"
    "    ▼\n"
    "build.py: Parser und Aufbereitung\n"
    "    ▼\n"
    "data/processed/  (aufbereitete CSVs, versioniert)\n"
    "    ▼\n"
    "app/pages/  (Darstellung)",
    language="text",
)
