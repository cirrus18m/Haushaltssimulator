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
    st.Page(
        "pages/6_Haushalt_und_Zinsen.py",
        title="Haushalt & Zinsen",
        icon=":material/payments:",
    ),
    st.Page(
        "pages/7_Zinsvergleich.py",
        title="Zinsvergleich",
        icon=":material/public:",
    ),
    st.Page("pages/8_Quellen.py", title="Quellen", icon=":material/library_books:"),
    st.Page("pages/9_Insolvenzen.py", title="Insolvenzen", icon=":material/gavel:"),
    st.Page(
        "pages/10_Geld_und_Kaufkraft.py",
        title="Geld & Kaufkraft",
        icon=":material/savings:",
    ),
    st.Page("pages/11_Energiepreise.py", title="Energiepreise", icon=":material/bolt:"),
    st.Page(
        "pages/12_Preisniveau_und_Wohnen.py",
        title="Preisniveau & Wohnen",
        icon=":material/lunch_dining:",
    ),
    st.Page(
        "pages/13_Bund_und_Schuldendienst.py",
        title="Bund & Schuldendienst",
        icon=":material/account_balance_wallet:",
    ),
    st.Page("pages/14_Wirtschaft.py", title="Wirtschaft", icon=":material/trending_up:"),
    st.Page("pages/15_Insights.py", title="Insights", icon=":material/slideshow:"),
]

st.navigation(pages).run()
