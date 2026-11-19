"""Wirtschaft: BIP-Wachstum, Produktion, Industrieproduktion und Investitionen."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from haushaltssimulator import ui

st.title("Wirtschaft")
st.markdown(
    "Reales Wirtschaftswachstum, die Produktion im Verarbeitenden Gewerbe, die "
    "Industrieproduktion im langfristigen Trend und die Investitionen von Staat und "
    "privaten Sektoren. Die deutschen Werte stammen vom Statistischen Bundesamt, der "
    "Ländervergleich von Eurostat; für die USA und Russland ergänzt der IWF die Reihen."
)

bip_deutschland = ui.gdp_germany()
bip_wachstum = ui.gdp_growth()
investitionen = ui.investments()
produktion = ui.production_germany()
produktion_lang = ui.production_germany_long()
produktion_vergleich = ui.production_comparison()
retrieved = ui.data_retrieved_at()

if bip_deutschland.empty or investitionen.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()


st.header("1. Reales BIP-Wachstum")
letztes = bip_deutschland.dropna(subset=["bip_wachstum_real_pct"]).iloc[-1]
letztes_bip_jahr = int(letztes["jahr"])
durchschnitt = bip_deutschland["bip_wachstum_real_pct"].mean()

columns = st.columns(4)
columns[0].metric(
    f"BIP-Wachstum {letztes_bip_jahr}",
    f"{ui.format_number(letztes['bip_wachstum_real_pct'], 1)} %",
    help="Preisbereinigtes Bruttoinlandsprodukt, Veränderung gegenüber dem Vorjahr",
)
columns[1].metric(
    f"BIP {letztes_bip_jahr} (Mrd. €)",
    ui.format_number(letztes["bip_nominal_mrd_eur"], 0),
    help="Bruttoinlandsprodukt in jeweiligen Preisen",
)
columns[2].metric(
    "Realindex 2020=100",
    ui.format_number(letztes["bip_real_index"], 1),
    help="Preisbereinigtes Bruttoinlandsprodukt, Kettenindex",
)
columns[3].metric(
    "Ø-Wachstum",
    f"{ui.format_number(durchschnitt, 1)} %",
    help=f"Durchschnitt {int(bip_deutschland['jahr'].min())}–{letztes_bip_jahr}",
)

st.subheader("Deutschland: Veränderung des realen BIP")
figure = go.Figure(
    go.Bar(
        x=bip_deutschland["jahr"].astype(str),
        y=bip_deutschland["bip_wachstum_real_pct"],
        name="Reales Wachstum",
        marker_color=[
            "#b03a2e" if wert < 0 else "#1f4e79"
            for wert in bip_deutschland["bip_wachstum_real_pct"]
        ],
        hovertemplate="%{y:.1f} %<extra></extra>",
    )
)
figure.add_hline(y=0, line_color="#7f7f7f", line_width=1)
figure.update_yaxes(title_text="Veränderung gegenüber dem Vorjahr in %")
ui.plot(figure, filename="wirtschaft_bip_wachstum_deutschland", height=380)
st.caption(
    "Preisbereinigtes Bruttoinlandsprodukt (Kettenindex 2020 = 100), Veränderung "
    "gegenüber dem Vorjahr. Die Tabelle 81000-0001 weist die letzten zehn Jahre aus."
)

st.subheader("Im Ländervergleich")
laender_auswahl = sorted(bip_wachstum["land"].unique())
standard = [
    land
    for land in (
        "Deutschland",
        "Frankreich",
        "Italien",
        "Spanien",
        "Vereinigte Staaten",
        "Russland",
    )
    if land in laender_auswahl
]
auswahl = st.multiselect(
    "Länder auswählen",
    options=laender_auswahl,
    default=standard,
    key="bip_wachstum_laender",
)
vergleich = bip_wachstum[bip_wachstum["land"].isin(auswahl)]
figure = go.Figure()
for position, (land, teil) in enumerate(vergleich.groupby("land")):
    figure.add_trace(
        go.Scatter(
            x=teil["jahr"],
            y=teil["wachstum_pct"],
            name=land,
            line={"color": ui.chart_color(position), "width": 2},
            hovertemplate="%{y:.1f} %<extra>" + land + "</extra>",
        )
    )
figure.add_hline(y=0, line_color="#7f7f7f", line_width=1)
figure.update_xaxes(title_text="Jahr")
figure.update_yaxes(title_text="Veränderung gegenüber dem Vorjahr in %")
ui.plot(figure, filename="wirtschaft_bip_wachstum_laender", height=440)
st.caption(
    "Verkettete Volumina (Eurostat `nama_10_gdp`, ab 1995); USA und Russland aus dem "
    "IWF World Economic Outlook. Es sind nur Ist-Jahre enthalten, keine Prognosen."
)

st.header("2. Produktion im Verarbeitenden Gewerbe")
saison = produktion.dropna(subset=["index_2021_saisonbereinigt"]).reset_index(drop=True)
if saison.empty:
    st.info("Für die Produktion liegen noch keine saisonbereinigten Werte vor.")
else:
    letzte = saison.iloc[-1]
    vorjahr_monat = f"{int(letzte['jahr']) - 1}-{letzte['monat'][5:7]}"
    vorjahr = produktion[produktion["monat"] == vorjahr_monat]
    vormonat_wert = saison.iloc[-2]["index_2021_saisonbereinigt"] if len(saison) > 1 else None
    vorjahres_wert = (
        vorjahr["index_2021_kalenderbereinigt"].iloc[0] if not vorjahr.empty else None
    )
    vorjahres_wert = (
        pd.NA if vorjahres_wert is None or pd.isna(vorjahres_wert) else vorjahres_wert
    )
    veraenderung_vormonat = (
        (letzte["index_2021_saisonbereinigt"] / vormonat_wert - 1) * 100
        if vormonat_wert
        else None
    )
    veraenderung_vorjahr = (
        (letzte["index_2021_kalenderbereinigt"] / vorjahres_wert - 1) * 100
        if not pd.isna(vorjahres_wert) and not pd.isna(letzte["index_2021_kalenderbereinigt"])
        else None
    )

    columns = st.columns(4)
    columns[0].metric(
        "Index (2021 = 100)",
        ui.format_number(letzte["index_2021_saisonbereinigt"], 1),
        help="Produktionsindex des Verarbeitenden Gewerbes, saisonbereinigt",
    )
    columns[1].metric(
        "Zum Vormonat",
        f"{ui.format_number(veraenderung_vormonat, 1)} %",
        help="Veränderung des saisonbereinigten Index gegenüber dem Vormonat",
    )
    columns[2].metric(
        "Zum Vorjahr",
        f"{ui.format_number(veraenderung_vorjahr, 1)} %",
        help="Veränderung des kalenderbereinigten Index gegenüber dem Vorjahresmonat",
    )
    columns[3].metric("Stand", ui.format_month(letzte["monat"]))

    st.subheader("Deutschland: Produktionsindex der letzten 24 Monate")
    letzte_24 = produktion.tail(24)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(letzte_24["monat"]),
            y=letzte_24["index_2021_original"],
            name="Originalwerte",
            line={"color": "#7fb2d5", "width": 2},
            hovertemplate="%{y:.1f}<extra>Originalwerte</extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(letzte_24["monat"]),
            y=letzte_24["index_2021_saisonbereinigt"],
            name="saison- und kalenderbereinigt",
            line={"color": "#1f4e79", "width": 3},
            hovertemplate="%{y:.1f}<extra>saisonbereinigt</extra>",
        )
    )
    figure.update_yaxes(title_text="Index 2021 = 100")
    ui.plot(figure, filename="wirtschaft_produktion_deutschland", height=400)
    st.caption(
        "Indizes der Produktion im Verarbeitenden Gewerbe (2021 = 100). Die "
        "Originalwerte zeigen die saisonale Grundlast, die bereinigte Reihe den "
        "konjunkturellen Verlauf."
    )

    if produktion_vergleich.empty:
        st.info("Für den Ländervergleich liegen keine Produktionsdaten vor.")
    else:
        st.subheader("Produktion im Ländervergleich")
        laender_auswahl = sorted(produktion_vergleich["land"].unique())
        standard = [
            land
            for land in (
                "Deutschland",
                "Frankreich",
                "Italien",
                "Spanien",
                "Polen",
                "Niederlande",
            )
            if land in laender_auswahl
        ]
        auswahl_produktion = st.multiselect(
            "Länder auswählen",
            options=laender_auswahl,
            default=standard,
            key="produktion_laender",
        )
        jahre = sorted({int(monat[:4]) for monat in produktion_vergleich["monat"]})
        startjahr = st.select_slider(
            "Zeitraum ab",
            options=jahre,
            value=jahre[max(len(jahre) - 11, 0)],
            key="produktion_startjahr",
        )
        vergleich = produktion_vergleich[
            (produktion_vergleich["land"].isin(auswahl_produktion))
            & (produktion_vergleich["monat"] >= f"{startjahr}-01")
        ]
        figure = go.Figure()
        for position, (land, teil) in enumerate(vergleich.groupby("land")):
            figure.add_trace(
                go.Scatter(
                    x=pd.to_datetime(teil["monat"]),
                    y=teil["index_2021"],
                    name=land,
                    line={"color": ui.chart_color(position), "width": 2},
                    hovertemplate="%{y:.1f}<extra>" + land + "</extra>",
                )
            )
        figure.update_yaxes(title_text="Index 2021 = 100")
        ui.plot(figure, filename="wirtschaft_produktion_laender", height=440)
        st.caption(
            "Produktionsindex des Verarbeitenden Gewerbes (NACE C), kalender- und "
            "saisonbereinigt, 2021 = 100 (Eurostat `sts_inpr_m`)."
        )

st.header("3. Industrieproduktion und langfristiger Trend")
st.markdown(
    "Der Produktionsindex der Industrie ohne Baugewerbe in Deutschland, kalender- und "
    "saisonbereinigt, 2015 = 100. Die gestrichelte Linie ist der lineare Langfristtrend "
    "aus dem Zeitraum 1993–2017, fortgeschrieben bis Februar 2026. Die rote Fläche "
    "zeigt, wie weit die tatsächliche Produktion hinter diesem Trend zurückbleibt."
)

lang = produktion_lang[produktion_lang["monat"] <= "2026-02"].reset_index(drop=True)
if lang.empty:
    st.info("Für die Industrieproduktion liegen keine Daten vor.")
else:
    letzte_lang = lang.iloc[-1]
    columns = st.columns(3)
    columns[0].metric(
        "Industrieproduktion Feb 2026",
        ui.format_number(letzte_lang["index_2015"], 1),
        "2015 = 100",
        delta_color="off",
    )
    columns[1].metric(
        "Langfristtrend",
        ui.format_number(letzte_lang["trend_2015"], 1),
        "Wachstum 1993–2017",
        delta_color="off",
    )
    columns[2].metric(
        "Abweichung vom Trend",
        f"{ui.format_number(letzte_lang['abweichung_pct'], 1)} %",
        "unter dem Trend",
        delta_color="inverse",
    )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(lang["monat"]),
            y=lang["trend_2015"],
            name="Langfristtrend (1993–2017)",
            line={"color": "#7f7f7f", "width": 2, "dash": "dash"},
            hovertemplate="%{x|%m.%Y}: %{y:.1f}<extra>Trend</extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(lang["monat"]),
            y=lang["index_2015"],
            name="Tatsächliche Produktion",
            line={"color": "#1f4e79", "width": 3},
            hovertemplate="%{x|%m.%Y}: %{y:.1f}<extra>Produktion</extra>",
        )
    )
    schatten = lang.copy()
    schatten["luecke"] = lang["index_2015"].where(
        (lang["monat"] < "2018-01") | (lang["index_2015"] >= lang["trend_2015"]),
        lang["trend_2015"],
    )
    figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(schatten["monat"]),
            y=schatten["luecke"],
            name="Abweichung vom Trend",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(176,58,46,0.15)",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    figure.add_annotation(
        x=pd.to_datetime(letzte_lang["monat"]),
        y=letzte_lang["index_2015"],
        text=(
            f"<b>Feb 2026</b><br>"
            f"{ui.format_number(abs(letzte_lang['abweichung_pct']), 0)} % unter dem Trend"
        ),
        showarrow=True,
        arrowhead=2,
        ax=-10,
        ay=-70,
        xanchor="right",
        align="right",
        font={"color": "#b03a2e", "size": 12},
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#b03a2e",
        borderwidth=1,
    )
    figure.update_yaxes(title_text="Index 2015 = 100")
    figure.update_xaxes(title_text="Jahr")
    ui.plot(figure, filename="industrieproduktion_langfristtrend", height=480)
    st.caption(
        "Produktionsindex der Industrie ohne Baugewerbe (NACE B-D), kalender- und "
        "saisonbereinigt, 2015 = 100 (Eurostat `sts_inpr_m`, auf 2015 = 100 umbasiert). "
        "Der Trend ist eine lineare Regression über Januar 1993 bis Dezember 2017, "
        "fortgeschrieben bis Februar 2026. Die rote Fläche markiert die Unterschreitung "
        "des Trends."
    )

    with st.expander("Datenlage und Trendberechnung"):
        st.markdown(
            "Die im Bild genannte FRED-Serie `IPG101DEUQ` ist bei FRED nicht abrufbar "
            "(HTTP 404). Die App nutzt deshalb den amtlichen monatlichen "
            "Produktionsindex der Industrie aus Eurostat `sts_inpr_m` (NACE B-D, "
            "kalender- und saisonbereinigt). Eurostat liefert die Reihe als Index "
            "2021 = 100; der Datenaufbau rechnet sie mit dem Jahresmittel 2015 auf "
            "2015 = 100 um.\n\n"
            "Der Trend ist eine lineare Regression über die Monatswerte von Januar "
            "1993 bis Dezember 2017, fortgeschrieben bis Februar 2026. Die Abweichung "
            "ist die Differenz zwischen tatsächlichem Index und Trend in Prozent des "
            "Trends."
        )

st.header("4. Private und staatliche Investitionen")
letztes_jahr = int(investitionen["jahr"].max())
staat = investitionen[
    (investitionen["jahr"] == letztes_jahr) & (investitionen["sektor"] == "Staat")
].iloc[0]
privat = investitionen[
    (investitionen["jahr"] == letztes_jahr)
    & (investitionen["sektor"] == "Nichtstaatliche Sektoren")
].iloc[0]
staat_vorjahr = investitionen[
    (investitionen["jahr"] == letztes_jahr - 1) & (investitionen["sektor"] == "Staat")
]
privat_vorjahr = investitionen[
    (investitionen["jahr"] == letztes_jahr - 1)
    & (investitionen["sektor"] == "Nichtstaatliche Sektoren")
]


def veraenderung(aktuell: float, vorjahr: pd.DataFrame) -> float:
    if vorjahr.empty or not vorjahr.iloc[0]["investitionen_mrd_eur"]:
        return float("nan")
    wert = (aktuell / vorjahr.iloc[0]["investitionen_mrd_eur"] - 1) * 100
    return 0.0 if abs(wert) < 0.05 else wert


columns = st.columns(4)
columns[0].metric(
    f"Staat {letztes_jahr} (Mrd. €)",
    ui.format_number(staat["investitionen_mrd_eur"], 1),
    f"{ui.format_number(veraenderung(staat['investitionen_mrd_eur'], staat_vorjahr), 1)}"
    " % zum Vorjahr",
    help="Bruttoanlageinvestitionen des Staates, jeweilige Preise",
)
columns[1].metric(
    f"Privat {letztes_jahr} (Mrd. €)",
    ui.format_number(privat["investitionen_mrd_eur"], 1),
    f"{ui.format_number(veraenderung(privat['investitionen_mrd_eur'], privat_vorjahr), 1)}"
    " % zum Vorjahr",
    help="Bruttoanlageinvestitionen der nichtstaatlichen Sektoren, jeweilige Preise",
)
columns[2].metric(
    f"Staatsquote {letztes_jahr}",
    f"{ui.format_number(staat['anteil_bip_pct'], 1)} %",
    help="Anteil der staatlichen Bruttoanlageinvestitionen am nominalen BIP",
)
columns[3].metric(
    f"Privatquote {letztes_jahr}",
    f"{ui.format_number(privat['anteil_bip_pct'], 1)} %",
    help="Anteil der nichtstaatlichen Bruttoanlageinvestitionen am nominalen BIP",
)

st.subheader("Bruttoanlageinvestitionen je Jahr")
figure = go.Figure()
for sektor, farbe in (
    ("Staat", "#1f4e79"),
    ("Nichtstaatliche Sektoren", "#7fb2d5"),
):
    teil = investitionen[investitionen["sektor"] == sektor]
    figure.add_trace(
        go.Bar(
            x=teil["jahr"].astype(str),
            y=teil["investitionen_mrd_eur"],
            name=sektor,
            marker_color=farbe,
            hovertemplate="%{y:.1f} Mrd. €<extra>" + sektor + "</extra>",
        )
    )
figure.update_layout(barmode="group")
figure.update_yaxes(title_text="Mrd. € zu jeweiligen Preisen", rangemode="tozero")
ui.plot(figure, filename="wirtschaft_investitionen_nominal", height=400)
st.caption(
    "Bruttoanlageinvestitionen in jeweiligen Preisen (Destatis 81000-0025). "
    "Nichtstaatliche Sektoren umfassen private Haushalte, Unternehmen und "
    "Organisationen ohne Erwerbszweck."
)

st.subheader("Investitionsquote in Prozent des BIP")
figure = go.Figure()
for position, sektor in enumerate(("Staat", "Nichtstaatliche Sektoren")):
    teil = investitionen[investitionen["sektor"] == sektor]
    figure.add_trace(
        go.Scatter(
            x=teil["jahr"],
            y=teil["anteil_bip_pct"],
            name=sektor,
            line={"color": ui.chart_color(position), "width": 3},
            hovertemplate="%{y:.1f} %<extra>" + sektor + "</extra>",
        )
    )
figure.update_xaxes(title_text="Jahr")
figure.update_yaxes(title_text="Anteil am BIP in %")
ui.plot(figure, filename="wirtschaft_investitionsquote", height=400)
st.caption(
    "Anteil der Investitionen am nominalen Bruttoinlandsprodukt "
    "(Destatis 81000-0001, 81000-0025)."
)

st.subheader("Werte je Jahr")
tabelle = investitionen.pivot(
    index="jahr",
    columns="sektor",
    values=["investitionen_mrd_eur", "anteil_bip_pct", "real_index"],
)
tabelle.columns = [
    f"{sektor} – {groesse}"
    for groesse, sektor in tabelle.columns
]
tabelle = tabelle.rename(
    columns={
        "Staat – investitionen_mrd_eur": "Staat (Mrd. €)",
        "Nichtstaatliche Sektoren – investitionen_mrd_eur": "Private (Mrd. €)",
        "Staat – anteil_bip_pct": "Staat (% des BIP)",
        "Nichtstaatliche Sektoren – anteil_bip_pct": "Private (% des BIP)",
        "Staat – real_index": "Staat, real (2020 = 100)",
        "Nichtstaatliche Sektoren – real_index": "Private, real (2020 = 100)",
    }
).reset_index()
tabelle = tabelle.rename(columns={"jahr": "Jahr"})
tabelle["Jahr"] = tabelle["Jahr"].astype(int).astype(str)
for spalte in tabelle.columns[1:]:
    tabelle[spalte] = tabelle[spalte].map(lambda wert: ui.format_number(wert, 1))
st.dataframe(tabelle, hide_index=True, width="stretch")

with st.expander("Datenlage und Abgrenzung"):
    st.markdown(
        "Die VGR-Tabellen 81000-0001 und 81000-0025 weisen die letzten zehn Jahre "
        "aus. Das reale BIP ist ein Kettenindex (2020 = 100), die Investitionen sind "
        "nominal in Mrd. € und preisbereinigt als Kettenindex angegeben.\n\n"
        "„Nichtstaatliche Sektoren“ ist die Abgrenzung des Statistischen Bundesamts "
        "für die private Wirtschaft: private Haushalte, nichtfinanzielle und "
        "finanzielle Kapitalgesellschaften sowie Organisationen ohne Erwerbszweck. "
        "Der Ländervergleich des BIP-Wachstums nutzt Eurostat; für die USA und "
        "Russland stehen die Ist-Jahre des IWF World Economic Outlook zur Verfügung.\n\n"
        "Der Produktionsindex ist ein Mengenindex (2021 = 100). Die saisonbereinigte "
        "Reihe ist für die konjunkturelle Einordnung maßgeblich, die Originalwerte "
        "zeigen die saisonale Grundlast."
    )

st.caption(
    "Quellen: Statistisches Bundesamt, GENESIS-Online 81000-0001 (BIP), 81000-0025 "
    "(Investitionen) und 42153-0001 (Produktionsindex); Eurostat `nama_10_gdp` "
    "(BIP-Wachstum) und `sts_inpr_m` (Produktionsindizes im Ländervergleich und "
    "langfristige Industrieproduktion); IWF "
    "World Economic Outlook für USA und Russland."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
