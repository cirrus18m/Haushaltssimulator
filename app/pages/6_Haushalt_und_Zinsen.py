"""Haushalt, Schulden und Zinslast: von der theoretischen Zinslast zum Haushalt."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import analysis, ui

# Zeitmarken für die Diagramme: Beschriftung, Datum, Höhe im oberen Teilbild, Anker.
ZEITMARKEN = (
    ("Start Agenda 2010", "2003-03-14", 0.02, "left"),
    ("Lehman-Pleite", "2008-09-15", 0.02, "left"),
    ("Corona", "2020-03-16", 0.02, "left"),
    ("Russland Sanktionen", "2022-03-02", 0.14, "left"),
    ("Hormus", "2026-02-28", 0.02, "right"),
)

# Achsen der vier Teilbilder: je Zeile die x-Achse und die senkrechte Hauptachse.
# Nur das Zinslast-Teilbild (Zeile 3) hat eine zweite y-Achse (y4).
# Die Zeitmarken werden in allen Zeilen an derselben Stelle der Achsenhöhe beschriftet.
TEILBILD_ACHSEN = (
    ("x", "y domain"),
    ("x2", "y2 domain"),
    ("x3", "y3 domain"),
    ("x4", "y5 domain"),
)

# Farben der Leitzinsen: EZB in Blautönen, Fed in Grün.
LEITZINS_FARBEN = {
    "EZB Hauptrefinanzierungssatz": ("#2c7fb8", "solid"),
    "EZB Einlagesatz": ("#7fcdbb", "dot"),
    "Fed Funds Zielsatz (ab 16.12.2008 Obergrenze)": ("#2ca02c", "dash"),
}

st.title("Haushalt, Schulden und Zinslast")
st.markdown(
    "Die Seite beginnt bei der **Zinslast**: Sie ist der gesamte Schuldenstand "
    "multipliziert mit der Rendite der aktuellen 10-jährigen Bundesanleihe und zeigt, "
    "was der Schuldenstand kosten würde, wenn er vollständig zum aktuellen Marktzins "
    "verzinst würde – die tatsächlich gebuchten Zinsausgaben liegen wegen der "
    "niedrigeren Zinsen älterer Anleihen meist darunter. Danach folgen der Haushalt und "
    "der Schuldenstand, aus dem die Zinslast stammt."
)

household = ui.household()
total = household[household["sector"] == "S13"].dropna(subset=["einnahmen_mio_eur"])
total = total.sort_values("jahr").reset_index(drop=True)
zinslast = ui.interest_burden()
bund_plan = ui.bund_interest_plan()
daily_yield = ui.bund_yield()
inflation = ui.purchasing_power()
leitzinsen = ui.key_rates()

if total.empty or zinslast.empty:
    st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
    st.stop()

latest = total.iloc[-1]
previous = total.iloc[-2] if len(total) > 1 else latest
retrieved = ui.data_retrieved_at()
debt = zinslast.dropna(subset=["schulden_mio_eur"]).sort_values("jahr")

st.divider()
st.header("1. Zinslast")
st.markdown(
    "Die 10-jährige Bundesanleihe ist der Referenzzins für die Refinanzierung des Bundes. "
    "Multipliziert mit dem gesamten Schuldenstand ergibt sie die theoretische Zinslast. "
    "Der Schuldenstand ist nur zum Jahresende verfügbar; für die Monatsrechnung wird er "
    "zwischen den Jahresenden interpoliert und ab dem letzten Jahresende mit dem Trend "
    "der letzten beiden Stichtage bis zum letzten Renditemonat fortgeschrieben."
)

monatsrendite = daily_yield.groupby("monat", as_index=False)["rendite_pct"].mean()
monatsrendite["datum"] = pd.to_datetime(monatsrendite["monat"])
monatszinslast = analysis.monthly_interest_burden(zinslast, monatsrendite)
# Leitzinsen sind Stufen an Änderungstagen; bis zum letzten Renditemonat verlängern.
leitzinsen = analysis.extend_steps(leitzinsen, daily_yield["datum"].max(), "leitzins")

st.subheader("Rendite der 10-jährigen Bundesanleihe (Monatsmittel)")
st.markdown(
    "Das obere Teilbild zeigt das Monatsmittel der Tagesrendite. Darunter stehen die "
    "**Inflationsrate** und die **Leitzinsen von EZB und Fed**, an denen sich die "
    "Marktzinsen orientieren. Das dritte Teilbild stellt die daraus folgende "
    "**theoretische Zinslast** den **tatsächlich gebuchten Zinsausgaben** gegenüber, "
    "ergänzt um den **Effektivzins** auf den Schuldenstand und um die im Finanzplan "
    "veranschlagten Zinsausgaben des Bundes. Das untere Teilbild zeigt den "
    "**Schuldenstand im Monatsraster**, der in die Rechnung eingeht: die "
    "Jahresendbestände und die daraus interpolierte Monatsreihe."
)

plan = bund_plan.dropna(subset=["zinsausgaben_mrd_eur"]).sort_values("jahr")

figure = make_subplots(
    rows=4,
    cols=1,
    row_heights=[0.22, 0.24, 0.30, 0.24],
    vertical_spacing=0.06,
    specs=[
        [{"secondary_y": False}],
        [{"secondary_y": False}],
        [{"secondary_y": True}],
        [{"secondary_y": False}],
    ],
    shared_xaxes=True,
)
figure.add_trace(
    go.Scatter(
        x=monatsrendite["datum"],
        y=monatsrendite["rendite_pct"],
        name="Monatsmittel der Tagesrendite",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{x|%m.%Y}: %{y:.2f} %<extra></extra>",
    ),
    row=1,
    col=1,
)

# Teilbild 2: Inflation und Leitzinsen von EZB und Fed, alle in Prozent auf einer Achse.
figure.add_trace(
    go.Scatter(
        x=pd.to_datetime(inflation["monat"]),
        y=inflation["inflation_de_pct"],
        name="Inflation Deutschland (HVPI)",
        line={"color": "#c9a227", "width": 2},
        hovertemplate="%{x|%m.%Y}: %{y:.1f} %<extra>Inflation</extra>",
    ),
    row=2,
    col=1,
)
for leitzins, (farbe, strich) in LEITZINS_FARBEN.items():
    reihe = leitzinsen[leitzinsen["leitzins"] == leitzins]
    figure.add_trace(
        go.Scatter(
            x=reihe["datum"],
            y=reihe["zins_pct"],
            name=leitzins,
            line={"color": farbe, "width": 2, "dash": strich, "shape": "hv"},
            hovertemplate="%{x|%d.%m.%Y}: %{y:.2f} %<extra>" + leitzins + "</extra>",
        ),
        row=2,
        col=1,
    )

jahresmitte = pd.to_datetime(zinslast["jahr"].astype(str) + "-07-01")
# Gemeinsame Zeitachse aller Teilbilder: Jahresraster von der ersten Jahresreihe
# bis kurz hinter das letzte Finanzplanjahr.
achse_start = pd.Timestamp(f"{int(zinslast['jahr'].min())}-01-01")
achse_ende = pd.Timestamp(f"{int(plan['jahr'].max())}-12-01")

figure.add_trace(
    go.Scatter(
        x=monatszinslast["datum"],
        y=monatszinslast["zins_theoretisch_mio_eur"] / 1000,
        name="theoretische Zinslast (Modell)",
        line={"color": "#1f4e79", "width": 2.5},
        hovertemplate="%{x|%m.%Y}: %{y:,.1f} Mrd. €<extra></extra>",
    ),
    row=3,
    col=1,
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=jahresmitte,
        y=zinslast["zinsausgaben_mio_eur"] / 1000,
        name="tatsächliche Zinsausgaben",
        mode="lines+markers",
        line={"color": "#b03a2e", "width": 2.5},
        marker={"size": 6},
        hovertemplate="%{x|%Y}: %{y:,.1f} Mrd. €<extra></extra>",
    ),
    row=3,
    col=1,
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=pd.to_datetime(plan["jahr"].astype(str) + "-07-01"),
        y=plan["zinsausgaben_mrd_eur"],
        name="Zinsausgaben Haushaltsplan (Bund)",
        mode="lines+markers",
        line={"color": "#6a3d9a", "width": 2.5, "dash": "dash"},
        marker={"size": 6},
        customdata=plan["art"],
        hovertemplate="%{x|%Y}: %{y:,.1f} Mrd. € (%{customdata})<extra></extra>",
    ),
    row=3,
    col=1,
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=jahresmitte,
        y=zinslast["effektivzins_pct"],
        name="Effektivzins auf den Schuldenstand",
        line={"color": "#8c564b", "width": 2, "dash": "dashdot"},
        hovertemplate="%{x|%Y}: %{y:.2f} %<extra></extra>",
    ),
    row=3,
    col=1,
    secondary_y=True,
)

# Schuldenstand im Monatsraster: die Jahresendbestände und die daraus interpolierte
# Reihe, mit der die theoretische Zinslast im dritten Teilbild gerechnet wird.
jahresende = pd.to_datetime(debt["jahr"].astype(int).astype(str) + "-12-31")
letzter_stichtag = jahresende.iloc[-1]
figure.add_trace(
    go.Scatter(
        x=monatszinslast["datum"],
        y=monatszinslast["schulden_mio_eur"] / 1000,
        name="Schuldenstand im Monatsraster (interpoliert, danach fortgeschrieben)",
        line={"color": "#0f766e", "width": 2},
        hovertemplate="%{x|%m.%Y}: %{y:,.0f} Mrd. €<extra></extra>",
    ),
    row=4,
    col=1,
)
figure.add_trace(
    go.Scatter(
        x=jahresende,
        y=debt["schulden_mio_eur"] / 1000,
        name="Schuldenstand am Jahresende",
        mode="markers",
        marker={"color": "#b03a2e", "size": 7, "symbol": "diamond"},
        hovertemplate="%{x|%d.%m.%Y}: %{y:,.0f} Mrd. €<extra></extra>",
    ),
    row=4,
    col=1,
)
# Der schattierte Bereich markiert die Fortschreibung hinter dem letzten Stichtag.
figure.add_vrect(
    x0=letzter_stichtag,
    x1=monatszinslast["datum"].max(),
    fillcolor="#1f4e79",
    opacity=0.08,
    line_width=0,
    layer="below",
    row=4,
    col=1,
)

for label, datum, hoehe, anker in ZEITMARKEN:
    for zeile, (xref, yref) in enumerate(TEILBILD_ACHSEN, start=1):
        figure.add_vline(
            x=pd.Timestamp(datum),
            line={"color": "#b03a2e", "width": 1, "dash": "dot"},
            row=zeile,
            col=1,
        )
        figure.add_annotation(
            x=pd.Timestamp(datum),
            y=hoehe,
            xref=xref,
            yref=yref,
            text=label,
            showarrow=False,
            textangle=-90,
            xanchor=anker,
            yanchor="bottom",
            font={"size": 9, "color": "#b03a2e"},
            bgcolor="rgba(255,255,255,0.85)",
            borderpad=1,
        )

figure.update_yaxes(title_text="Rendite in %", row=1, col=1)
figure.update_yaxes(title_text="Inflation / Leitzins in %", row=2, col=1)
figure.update_yaxes(title_text="Mrd. €", row=3, col=1, secondary_y=False)
figure.update_yaxes(
    title_text="Effektivzins in %",
    showgrid=False,
    dtick=1,
    tickformat=".1f",
    row=3,
    col=1,
    secondary_y=True,
)
figure.update_yaxes(title_text="Schuldenstand in Mrd. €", row=4, col=1)
figure.update_xaxes(
    range=[achse_start, achse_ende],
    dtick="M12",
    tick0=achse_start.strftime("%Y-%m-%d"),
    tickformat="%Y",
    tickfont={"size": 11},
)
for zeile in (1, 2, 3):
    figure.update_xaxes(showticklabels=False, row=zeile, col=1)
    figure.add_hline(y=0, line={"color": "#999", "width": 1}, row=zeile, col=1)
ui.plot(figure, filename="zins_bund_10j_und_zinslast", height=1300, top_margin=170)
st.caption(
    "Oben: Monatsmittel der Tagesrenditen (Deutsche Bundesbank). Darunter: Inflation als "
    "Vorjahresrate des HVPI für Deutschland (EZB ICP, bis Dezember 2025) und die "
    "Leitzinsen an den Tagen ihrer Änderung, bis zum letzten Renditemonat fortgeführt – "
    "EZB-Hauptrefinanzierungssatz (Juni 2000 bis Oktober 2008 Mindestbietungssatz der "
    "Zinstender) und Einlagesatz (EZB FM) sowie der Federal-Funds-Zielsatz der Fed, ab "
    "16.12.2008 die Obergrenze der Zielspanne (Federal Reserve über FRED, DFEDTAR und "
    "DFEDTARU). Drittes Teilbild: theoretische Zinslast (Monatsmodell aus interpoliertem "
    "Schuldenstand und Monatsmittel der Rendite), Zinsausgaben des Gesamtstaats (Eurostat, VGR), "
    "Effektivzins (Zinsausgaben / Schuldenstand) sowie die im Finanzplan des Bundes 2026 "
    "bis 2030 veranschlagten Zinsausgaben des Bundes im Kernhaushalt (Drucksache 21/7301, "
    "Tabelle 9) – eine engere Abgrenzung als die VGR, die die Zinsausgaben des Bundes "
    "fortschreibt und nicht die höheren des Gesamtstaats. Unten: der Schuldenstand, aus "
    "dem die Zinslast stammt – die Jahresendbestände des Maastricht-Schuldenstands "
    "(Eurostat, VGR) als Rauten und die daraus linear interpolierte Monatsreihe; der "
    "schattierte Bereich nach dem letzten Jahresende ist die Fortschreibung mit dem "
    "Trend der letzten beiden Stichtage bis zum letzten Renditemonat. Alle Teilbilder "
    "teilen die Jahresachse, die gestrichelten Marken "
    "gelten in allen Teilbildern: Start der Agenda 2010 (14.03.2003), Lehman-Pleite "
    "(15.09.2008), Beginn der Corona-Shutdowns (16.03.2020), Beginn der "
    "Russland-Sanktionen (02.03.2022) und die Schließung der Straße von Hormus nach dem "
    "Angriff der USA und Israels auf den Iran (28.02.2026)."
)

aktuell = monatszinslast.iloc[-1]
latest_debt = debt.iloc[-1]
theoretical_mio = aktuell["zins_theoretisch_mio_eur"]
quote_einnahmen = theoretical_mio / latest_debt["einnahmen_mio_eur"] * 100
quote_bip = theoretical_mio / latest_debt["bip_mio_eur"] * 100
actual_mio = latest_debt["zinsausgaben_mio_eur"]

st.markdown(
    f"**Aktuelle Rechnung:** {ui.format_mrd(aktuell['schulden_mio_eur'], 0)} Schuldenstand "
    f"(Jahresende {int(latest_debt['jahr'])}, fortgeschrieben bis "
    f"{ui.format_month(aktuell['monat'])}) × "
    f"{ui.format_number(aktuell['rendite_pct'], 2)} % Monatsrendite = "
    f"**{ui.format_mrd(theoretical_mio, 1)}** theoretische Zinslast pro Jahr."
)

columns = st.columns(3)
columns[0].metric(
    "Theoretische Zinslast (Mrd. €)",
    ui.format_number(theoretical_mio / 1000, 1),
    f"tatsächlich {ui.format_number(actual_mio / 1000, 1)}",
    delta_color="off",
)
columns[1].metric(
    "in % der Einnahmen",
    ui.format_number(quote_einnahmen, 1, " %"),
    "ohne neue Schulden",
    delta_color="off",
)
columns[2].metric(
    "in % des BIP",
    ui.format_number(quote_bip, 1, " %"),
    f"BIP {int(latest_debt['jahr'])}",
    delta_color="off",
)

with st.expander("Berechnung und Abgrenzung"):
    st.markdown(
        "**Theoretische Zinslast** = interpolierter Schuldenstand × Monatsmittel der "
        "Tagesrendite der aktuellen 10-jährigen Bundesanleihe / 100. Der Schuldenstand ist "
        "nur zum Jahresende verfügbar und wird zwischen den Jahresenden linear "
        "interpoliert; ab dem letzten Jahresende wird er mit dem Trend der letzten "
        "beiden Jahresenden bis zum letzten Renditemonat fortgeschrieben. "
        "Jeder Monatswert ist die auf ein Jahr hochgerechnete Last beim damaligen "
        "Marktzins.\n\n"
        "**Effektivzins** = tatsächliche Zinsausgaben / Schuldenstand × 100. Er liegt "
        "unter der Marktrendite, weil Altbestände noch zu niedrigeren Zinsen laufen.\n\n"
        "**Zinsquote der Einnahmen** = theoretische Zinslast / Gesamteinnahmen × 100. "
        "Die Gesamteinnahmen der Volkswirtschaftlichen Gesamtrechnung enthalten keine "
        "Kreditaufnahme.\n\n"
        "**Geplante Zinsausgaben** = Ansätze des Bundes im Kernhaushalt (Finanzplan "
        "2026 bis 2030, Drucksache 21/7301, Tabelle 9) für Ist 2025, Soll 2026, "
        "Entwurf 2027 und Finanzplan 2028 bis 2030. Sie enthalten auch die Zinsausgaben "
        "des SVIK und sind enger abgegrenzt als die Zinsausgaben des Gesamtstaats in "
        "der VGR.\n\n"
        "Negative Werte in den Jahren 2019 bis 2021 spiegeln die damals negativen "
        "Renditen am Kapitalmarkt wider. Die Rechnung ist ein Modell und keine Prognose "
        "der tatsächlichen Haushaltsbelastung."
    )

st.divider()
st.header("2. Haushalt")
st.markdown(
    "Einnahmen und Ausgaben des Gesamtstaats in der Abgrenzung der Volkswirtschaftlichen "
    "Gesamtrechnung. Die Einnahmen enthalten **keine Kreditaufnahme** – sie sind damit das "
    "Haushaltseinkommen ohne neue Schulden."
)

st.subheader(f"Haushalt {int(latest['jahr'])}")
columns = st.columns(4)
columns[0].metric(
    "Einnahmen (Mrd. €)",
    ui.format_number(latest["einnahmen_mio_eur"] / 1000, 0),
    f"{ui.format_number((latest['einnahmen_mio_eur'] - previous['einnahmen_mio_eur']) / 1000, 1)}"
    " zum Vorjahr",
    delta_color="off",
)
columns[1].metric(
    "Ausgaben (Mrd. €)",
    ui.format_number(latest["ausgaben_mio_eur"] / 1000, 0),
    f"{ui.format_number((latest['ausgaben_mio_eur'] - previous['ausgaben_mio_eur']) / 1000, 1)}"
    " zum Vorjahr",
    delta_color="inverse",
)
columns[2].metric(
    "Zinsausgaben (Mrd. €)",
    ui.format_number(latest["zinsausgaben_mio_eur"] / 1000, 1),
    f"{ui.format_number(latest['zins_einnahmen_pct'], 1)} % der Einnahmen",
    delta_color="inverse",
)
columns[3].metric(
    "Finanzierungssaldo (Mrd. €)",
    ui.format_number(latest["finanzierungssaldo_mio_eur"] / 1000, 1),
    "Defizit" if latest["finanzierungssaldo_mio_eur"] < 0 else "Überschuss",
    delta_color="off",
)

figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["einnahmen_mio_eur"] / 1000,
        name="Einnahmen",
        marker_color="#2e7d32",
        hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["ausgaben_mio_eur"] / 1000,
        name="Ausgaben",
        marker_color="#b03a2e",
        hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=total["jahr"],
        y=total["finanzierungssaldo_mio_eur"] / 1000,
        name="Finanzierungssaldo",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{y:+,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_layout(barmode="group")
figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
figure.update_yaxes(title_text="Saldo in Mrd. €", secondary_y=True)
ui.plot(figure, filename="haushalt_einnahmen_ausgaben", height=420)

figure = go.Figure()
figure.add_trace(
    go.Bar(
        x=total["jahr"],
        y=total["zinsausgaben_mio_eur"] / 1000,
        name="Zinsausgaben (Mrd. €)",
        marker_color="#c9a227",
        hovertemplate="%{y:,.1f} Mrd. €<extra></extra>",
    )
)
figure.add_trace(
    go.Scatter(
        x=total["jahr"],
        y=total["zins_einnahmen_pct"],
        name="in % der Einnahmen",
        yaxis="y2",
        line={"color": "#1f4e79", "width": 2},
        hovertemplate="%{y:.1f} %<extra></extra>",
    )
)
figure.update_layout(
    yaxis={"title": "Mrd. €"},
    yaxis2={"title": "% der Einnahmen", "overlaying": "y", "side": "right", "showgrid": False},
)
ui.plot(figure, filename="haushalt_zinsausgaben", height=380)

st.subheader("Der Haushaltsplan des Bundes nach Aufgabenbereichen")
st.markdown(
    "Der Haushaltsplan ist enger abgegrenzt als die Gesamtrechnung oben: Er umfasst den "
    "**Kernhaushalt des Bundes**, also ohne Sondervermögen und ohne Länder und Gemeinden. "
    "Die Anteile zeigen, wie sich die Ausgaben zwischen den Aufgabenbereichen verschieben – "
    "vom Ist 2025 über den Regierungsentwurf 2027 bis zum Finanzplan 2030 (Tabelle 8 der "
    "Drucksache 21/7301)."
)

plan_bereiche = ui.bund_budget_areas().dropna(subset=["ausgaben_mrd_eur"])
if plan_bereiche.empty:
    st.info("Keine Daten zum Haushaltsplan verfügbar.")
else:
    anteile = analysis.budget_shares(plan_bereiche)
    anteile["jahr_label"] = anteile["jahr"].astype(str) + "<br>" + anteile["art"]
    anteile["einzelplan_label"] = anteile["einzelplan"].astype(int).astype(str).str.zfill(2)

    # Bereiche unter der Schwelle verschwinden nicht, sondern werden je Jahr zur
    # Sammelposition addiert – sonst wäre das Säulendiagramm bei 26 Einzelplänen unlesbar.
    schwelle = 3.0
    gruppen = analysis.largest_areas(anteile, threshold_pct=schwelle).sort_values("jahr")
    letztes_jahr = gruppen["jahr"].max()
    reihenfolge = list(
        gruppen[gruppen["jahr"] == letztes_jahr]
        .sort_values("anteil_pct", ascending=False)["aufgabenbereich"]
    )
    farben = {
        name: ("#7f7f7f" if name.startswith("Übrige") else ui.chart_color(index))
        for index, name in enumerate(reihenfolge)
    }

    figure = go.Figure()
    for name in reihenfolge:
        teil = gruppen[gruppen["aufgabenbereich"] == name]
        figure.add_trace(
            go.Bar(
                x=teil["jahr_label"],
                y=teil["anteil_pct"],
                name=name,
                marker_color=farben[name],
                customdata=list(
                    zip(teil["ausgaben_mrd_eur"], teil["einzelplan_label"], strict=True)
                ),
                hovertemplate=(
                    "%{x}: %{y:.1f} % der Ausgaben<br>%{customdata[0]:,.1f} Mrd. € "
                    "(Epl. %{customdata[1]})<extra>" + name + "</extra>"
                ),
            )
        )
    # "relative" stapelt positive Anteile nach oben und negative Gegenposten nach unten.
    figure.update_layout(barmode="relative")
    figure.update_yaxes(
        title_text="Anteil an den Gesamtausgaben in %", range=[-5, 105], dtick=10
    )
    ui.plot(figure, filename="bund_ausgaben_anteile", height=520, top_margin=150)
    st.caption(
        f"Säulen: Anteile an den Gesamtausgaben des jeweiligen Jahres. Einzeln gezeigt "
        f"werden alle Aufgabenbereiche mit mindestens {schwelle:.0f} % Anteil in "
        f"mindestens einem Jahr, der Rest ist zur Sammelposition „Übrige "
        f"Aufgabenbereiche“ addiert. Negative Anteile entstehen bei der Allgemeinen "
        f"Finanzverwaltung, weil dort Gegenposten wie globale Minderausgaben veranschlagt "
        f"sind. Quelle: Deutscher Bundestag, Drucksache 21/7301, Tabelle 8 (Kernhaushalt)."
    )

    auswahl = st.multiselect(
        "Aufgabenbereiche im Zeitverlauf",
        options=reihenfolge,
        default=[name for name in reihenfolge if not name.startswith("Übrige")][:5],
        key="bund_plan_bereiche",
    )
    if not auswahl:
        st.info("Bitte mindestens einen Aufgabenbereich auswählen.")
    figure = go.Figure()
    for name in auswahl:
        teil = gruppen[gruppen["aufgabenbereich"] == name].sort_values("jahr")
        figure.add_trace(
            go.Scatter(
                x=teil["jahr_label"],
                y=teil["anteil_pct"],
                name=name,
                mode="lines+markers",
                line={"color": farben[name], "width": 2.5},
                marker={"size": 7},
                hovertemplate="%{x}: %{y:.1f} %<extra>" + name + "</extra>",
            )
        )
    figure.update_yaxes(title_text="Anteil an den Gesamtausgaben in %")
    if auswahl:
        ui.plot(figure, filename="bund_ausgaben_anteile_zeitreihe", height=380)
    st.caption(
        "Anteile derselben Aufgabenbereiche im Zeitverlauf, in Prozent der "
        "Gesamtausgaben des jeweiligen Jahres. Quelle: Deutscher Bundestag, Drucksache "
        "21/7301, Tabelle 8 (Kernhaushalt)."
    )

    start_jahr, end_jahr = int(anteile["jahr"].min()), int(anteile["jahr"].max())
    vergleich = analysis.share_change(anteile, start_year=start_jahr, end_year=end_jahr)
    spalten = {
        "aufgabenbereich": "Aufgabenbereich",
        f"ausgaben_{end_jahr}_mrd_eur": f"Ausgaben {end_jahr} (Mrd. €)",
        f"anteil_{start_jahr}_pct": f"Anteil {start_jahr} (%)",
        f"anteil_{end_jahr}_pct": f"Anteil {end_jahr} (%)",
        "anteil_veraenderung_pp": "Veränderung (Prozentpunkte)",
    }
    tabelle = vergleich.round(1)[list(spalten)].rename(columns=spalten)
    st.dataframe(
        tabelle,
        hide_index=True,
        width="stretch",
        column_config={
            spalte: st.column_config.NumberColumn(format="%.1f")
            for spalte in list(spalten.values())[1:]
        },
    )
    st.caption(
        f"Ausgaben in Mrd. € und Anteile in Prozent der Gesamtausgaben; die letzte Spalte "
        f"ist die Veränderung des Anteils in Prozentpunkten von {start_jahr} bis "
        f"{end_jahr}. Werte gerundet, Rundungsdifferenzen möglich. Quelle: Deutscher "
        f"Bundestag, Drucksache 21/7301, Tabelle 8 (Kernhaushalt)."
    )

    with st.expander("Abgrenzung des Haushaltsplans"):
        st.markdown(
            "Die Tabelle 8 der Drucksache 21/7301 weist die Ausgaben des Bundes nach "
            "Aufgabenbereichen (Einzelplänen) im **Kernhaushalt** aus: Ist 2025, Soll 2026, "
            "Entwurf 2027 und Finanzplan 2028 bis 2030.\n\n"
            "Nicht enthalten sind die Sondervermögen (z. B. Sondervermögen Bundeswehr, "
            "Klima- und Transformationsfonds) sowie Länder und Gemeinden. Die Summen sind "
            "deshalb kleiner als die Ausgaben des Gesamtstaats in der Abgrenzung der "
            "Volkswirtschaftlichen Gesamtrechnung und dürfen nicht mit ihnen saldiert "
            "werden. Planjahre sind Beschlusslagen, keine Prognosen.\n\n"
            "Der Einzelplan 24 (Digitales und Staatsmodernisierung) ist erst ab 2026 "
            "veranschlagt; für 2025 weist die Drucksache keinen Wert aus."
        )

st.divider()
st.header("3. Schulden")
st.markdown(
    "Maastricht-Schuldenstand des Gesamtstaats. Er ist die Bezugsgröße für die "
    "Zinslast im ersten Abschnitt."
)
figure = make_subplots(specs=[[{"secondary_y": True}]])
figure.add_trace(
    go.Scatter(
        x=debt["jahr"],
        y=debt["schulden_mio_eur"] / 1000,
        name="Schuldenstand",
        line={"color": "#1f4e79", "width": 3},
        hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
    ),
    secondary_y=False,
)
figure.add_trace(
    go.Scatter(
        x=debt["jahr"],
        y=debt["schulden_mio_eur"] / debt["bip_mio_eur"] * 100,
        name="Schuldenquote",
        line={"color": "#c9a227", "width": 2, "dash": "dot"},
        hovertemplate="%{y:.1f} % des BIP<extra></extra>",
    ),
    secondary_y=True,
)
figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
figure.update_yaxes(title_text="% des BIP", secondary_y=True)
ui.plot(figure, filename="zinslast_schuldenstand", height=400)

st.divider()
st.subheader("Jahreswerte")
st.markdown(
    "Die Tabelle zeigt die Jahresrechnung aus dem Schuldenstand des Jahres und dem "
    "Jahresmittel der Rendite; das Diagramm im ersten Abschnitt rechnet dagegen monatlich."
)
recent = zinslast.tail(15).copy()
st.dataframe(
    recent.rename(
        columns={
            "jahr": "Jahr",
            "schulden_mio_eur": "Schulden (Mio. €)",
            "rendite_pct": "Rendite (%)",
            "zins_theoretisch_mio_eur": "Theoretische Zinslast (Mio. €)",
            "einnahmen_mio_eur": "Einnahmen (Mio. €)",
            "zins_quote_einnahmen_pct": "in % der Einnahmen",
            "zins_quote_bip_pct": "in % des BIP",
            "zinsausgaben_mio_eur": "Zinsausgaben (Mio. €)",
            "effektivzins_pct": "Effektivzins (%)",
        }
    ),
    hide_index=True,
    width="stretch",
    column_config={
        "Schulden (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "Rendite (%)": st.column_config.NumberColumn(format="%.2f"),
        "Theoretische Zinslast (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "Einnahmen (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "in % der Einnahmen": st.column_config.NumberColumn(format="%.1f"),
        "in % des BIP": st.column_config.NumberColumn(format="%.1f"),
        "Zinsausgaben (Mio. €)": st.column_config.NumberColumn(format="%,.0f"),
        "Effektivzins (%)": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.caption(
    "Quellen: Eurostat gov_10a_main (Einnahmen, Ausgaben, Zinsausgaben), "
    "Eurostat gov_10dd_edpt1 (Schuldenstand), Eurostat nama_10_gdp (BIP), "
    "Deutsche Bundesbank BBSSY.D.REN.EUR.A630.000000WT1010.A (10-jährige Bundesanleihe) "
    "und Deutscher Bundestag, Drucksache 21/7301 (Finanzplan des Bundes 2026 bis 2030)."
    + (f" Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
)
