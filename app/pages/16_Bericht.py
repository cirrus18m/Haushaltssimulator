"""Eigener Bericht: gesammelte Bausteine ordnen und als Reveal.js-Präsentation exportieren."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from haushaltssimulator import bausteine, bericht, ui

st.title("Eigener Bericht")
st.markdown(
    "Diagramme, Kennzahlen und Tabellen lassen sich auf den Seiten der App mit "
    "**Zum Bericht** vormerken (bisher auf der Seite Insolvenzen). Hier werden sie "
    "geordnet und als eine HTML-Datei mit Folien (Reveal.js) exportiert – im Querformat "
    "für Rechner und Beamer oder im Hochformat für das Smartphone. Jede Folie nennt ihre "
    "Quelle; am Ende steht eine Quellenfolie mit Lizenzen und Abrufzeitpunkten."
)


# Standardwerte vorab setzen statt value=…, damit „Zusammenstellung laden“ sie ersetzen kann.
_STANDARD = bericht.BerichtKonfiguration()
for _key, _wert in {
    "bericht_titel": _STANDARD.titel,
    "bericht_untertitel": _STANDARD.untertitel,
    "bericht_autor": _STANDARD.autor,
    "bericht_format": _STANDARD.format,
    "bericht_diagramme": _STANDARD.diagramme,
    "bericht_text": _STANDARD.text,
    "bericht_quellenfolie": _STANDARD.quellenfolie,
}.items():
    st.session_state.setdefault(_key, _wert)


def _beschriftung(baustein_id: str) -> str:
    baustein = bausteine.hole(baustein_id)
    seite = bausteine.seite_von(baustein_id)
    return f"{seite.titel} · {baustein.titel}" if seite else baustein.titel


def _hinzufuegen() -> None:
    for baustein_id in st.session_state.get("bericht_auswahl", []):
        ui.bericht_hinzufuegen(baustein_id, parameter={})
    st.session_state["bericht_auswahl"] = []


def _laden() -> None:
    datei = st.session_state.get("bericht_upload")
    if datei is None:
        return
    try:
        konfiguration, unbekannt = bericht.BerichtKonfiguration.aus_json(
            datei.getvalue().decode("utf-8")
        )
    except (ValueError, UnicodeDecodeError) as fehler:
        st.session_state["bericht_meldung"] = f"Datei nicht lesbar: {fehler}"
        return
    st.session_state[ui.BERICHT_KEY] = [
        {"id": e.id, "parameter": e.parameter} for e in konfiguration.eintraege
    ]
    st.session_state["bericht_titel"] = konfiguration.titel
    st.session_state["bericht_untertitel"] = konfiguration.untertitel
    st.session_state["bericht_autor"] = konfiguration.autor
    st.session_state["bericht_format"] = konfiguration.format
    st.session_state["bericht_diagramme"] = konfiguration.diagramme
    st.session_state["bericht_text"] = konfiguration.text
    st.session_state["bericht_quellenfolie"] = konfiguration.quellenfolie
    meldung = f"{len(konfiguration.eintraege)} Bausteine geladen."
    if unbekannt:
        meldung += f" Übersprungen (unbekannt): {', '.join(unbekannt)}."
    st.session_state["bericht_meldung"] = meldung


with st.expander("Bausteine direkt auswählen oder gespeicherte Zusammenstellung laden"):
    vorhanden = {e["id"] for e in ui.bericht_eintraege()}
    st.multiselect(
        "Bausteine",
        [bid for bid in bausteine.REGISTRY if bid not in vorhanden],
        format_func=_beschriftung,
        key="bericht_auswahl",
        placeholder="Bausteine wählen (mit Standardeinstellungen)",
    )
    st.button("Hinzufügen", on_click=_hinzufuegen, icon=":material/playlist_add:")
    st.file_uploader(
        "Gespeicherte Zusammenstellung (JSON)",
        type=["json"],
        key="bericht_upload",
        on_change=_laden,
    )
if meldung := st.session_state.pop("bericht_meldung", None):
    st.info(meldung)

eintraege = ui.bericht_eintraege()
if not eintraege:
    st.info(
        "Noch keine Bausteine vorgemerkt. Auf einer Seite **Zum Bericht** anklicken oder "
        "oben Bausteine direkt auswählen."
    )
    st.stop()

st.subheader(f"Inhalt ({len(eintraege)} Folien plus Titel- und Quellenfolie)")
for index, eintrag in enumerate(eintraege):
    baustein = bausteine.hole(eintrag["id"])
    text, hoch, runter, weg = st.columns([12, 1, 1, 1], vertical_alignment="center")
    einstellungen = ", ".join(
        f"{p.beschriftung}: {eintrag['parameter'].get(p.name, p.standard)}"
        for p in baustein.parameter
    )
    text.markdown(
        f"**{index + 1}. {_beschriftung(baustein.id)}**"
        + (f"  \n:gray[{einstellungen}]" if einstellungen else "")
    )
    hoch.button(
        "",
        key=f"hoch.{baustein.id}",
        icon=":material/arrow_upward:",
        disabled=index == 0,
        on_click=ui.bericht_verschieben,
        args=(index, -1),
        help="nach oben",
    )
    runter.button(
        "",
        key=f"runter.{baustein.id}",
        icon=":material/arrow_downward:",
        disabled=index == len(eintraege) - 1,
        on_click=ui.bericht_verschieben,
        args=(index, 1),
        help="nach unten",
    )
    weg.button(
        "",
        key=f"weg.{baustein.id}",
        icon=":material/delete:",
        on_click=ui.bericht_entfernen,
        args=(baustein.id,),
        help="entfernen",
    )

st.subheader("Gestaltung")
links, rechts = st.columns(2)
with links:
    st.text_input("Titel", key="bericht_titel")
    st.text_input("Untertitel", key="bericht_untertitel")
    st.text_input("Autor (optional)", key="bericht_autor")
with rechts:
    st.radio(
        "Format",
        list(bericht.FORMATE),
        format_func=lambda key: bericht.FORMATE[key].name,
        key="bericht_format",
        horizontal=True,
    )
    st.radio(
        "Diagramme",
        list(bericht.DIAGRAMM_ARTEN),
        format_func=bericht.DIAGRAMM_ARTEN.get,
        key="bericht_diagramme",
        horizontal=True,
        help="Interaktiv: Plotly im Browser (Internet nötig). Statisch: eingebettete "
        "SVG-Grafiken; braucht Kaleido auf dem Server, sonst bleibt es interaktiv.",
    )
    st.radio(
        "Text je Folie",
        list(bericht.TEXT_UMFANG),
        format_func=bericht.TEXT_UMFANG.get,
        key="bericht_text",
        horizontal=True,
    )
    st.checkbox("Quellenfolie am Ende", key="bericht_quellenfolie")

konfiguration = bericht.BerichtKonfiguration(
    titel=st.session_state["bericht_titel"] or "Mein Bericht",
    untertitel=st.session_state["bericht_untertitel"],
    autor=st.session_state["bericht_autor"],
    format=st.session_state["bericht_format"],
    diagramme=st.session_state["bericht_diagramme"],
    text=st.session_state["bericht_text"],
    quellenfolie=st.session_state["bericht_quellenfolie"],
    eintraege=[bericht.Eintrag(e["id"], dict(e["parameter"])) for e in eintraege],
)


def _html() -> str:
    return bericht.erzeuge_bericht(
        konfiguration, lade=ui._app_lader, bibliothek=ui.sources_library()
    )


st.subheader("Export")
export, speichern, _ = st.columns([2, 2, 3])
export.download_button(
    "Bericht als HTML exportieren",
    _html,
    file_name=bericht.dateiname(konfiguration),
    mime="text/html",
    type="primary",
    icon=":material/download:",
    help="Eine Datei; im Browser öffnen. Blättern mit Pfeiltasten, PDF über "
    "„?print-pdf“ an der Adresse und Drucken im Chrome.",
)
speichern.download_button(
    "Zusammenstellung speichern (JSON)",
    json.dumps(konfiguration.als_dict(), ensure_ascii=False, indent=2),
    file_name=bericht.dateiname(konfiguration).removesuffix(".html") + ".json",
    mime="application/json",
    icon=":material/save:",
    help="Später oben wieder laden – auch nach einem Datenupdate mit neuen Zahlen.",
)

if st.toggle("Vorschau anzeigen", key="bericht_vorschau"):
    fmt = bericht.FORMATE[konfiguration.format]
    hoehe = 560 if konfiguration.format == "quer" else 900
    components.html(_html(), height=hoehe, scrolling=False)
    st.caption(f"{fmt.name}, {fmt.breite} × {fmt.hoehe} Pixel, verkleinert dargestellt.")
