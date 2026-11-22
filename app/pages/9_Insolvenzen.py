"""Unternehmensinsolvenzen: Langreihe, Verfahrensausgang und aktuelle Forderungen.

Pilotseite der Baustein-Struktur: Inhalte, Texte und Quellen stehen in
``haushaltssimulator.bausteine.insolvenzen``; diese Datei stellt sie nur zusammen.
"""

from __future__ import annotations

import streamlit as st

from haushaltssimulator import ui
from haushaltssimulator.bausteine import insolvenzen

if ui.insolvencies().empty:
    st.title(insolvenzen.SEITE.titel)
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

ui.zeige_seite(insolvenzen.SEITE)
