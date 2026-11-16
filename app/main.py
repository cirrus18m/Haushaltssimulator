"""Einstiegspunkt der Streamlit-App mit der Seitennavigation."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Haushaltssimulator – Deutsche Staatsschulden",
    page_icon="🇩🇪",
    layout="wide",
)

pages = [
    st.Page("pages/0_Ueberblick.py", title="Überblick", icon=":material/dashboard:", default=True),
    st.Page("pages/1_Zeitreihe.py", title="Zeitreihe", icon=":material/timeline:"),
    st.Page(
        "pages/2_Ebenen_und_Schuldenarten.py",
        title="Ebenen & Schuldenarten",
        icon=":material/account_balance:",
    ),
    st.Page("pages/3_Bundeslaender.py", title="Bundesländer", icon=":material/map:"),
    st.Page("pages/4_Analysen.py", title="Analysen", icon=":material/analytics:"),
    st.Page("pages/5_Szenario.py", title="Szenario-Rechner", icon=":material/tune:"),
]

st.navigation(pages).run()
