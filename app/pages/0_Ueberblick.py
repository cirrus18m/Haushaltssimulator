"""Haushaltssimulator – Startseite mit Überblick über die deutschen Staatsschulden."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from haushaltssimulator import dataset, ui


def main() -> None:
    st.title("Deutsche Staatsschulden im Überblick")
    st.markdown(
        "Der Schuldenstand des Staates nach der **Maastricht-Abgrenzung** – also die "
        "konsolidierten Verbindlichkeiten von Bund, Ländern, Gemeinden und Sozialversicherung "
        "gegenüber anderen Sektoren. Grundlage sind die frei verfügbaren Daten von Eurostat "
        "und dem Statistischen Bundesamt."
    )

    annual = ui.annual_debt()
    population = ui.gdp_population()

    total = annual[annual["sector"] == "S13"].dropna(subset=["schulden_mio_eur"])
    total = total.sort_values("jahr").reset_index(drop=True)
    if total.empty:
        st.warning("Keine Daten gefunden. Bitte `uv run scripts/build_data.py` ausführen.")
        return

    total = dataset.with_debt_per_capita(total, population)
    latest = total.iloc[-1]
    previous = total.iloc[-2] if len(total) > 1 else latest

    change = latest["schulden_mio_eur"] - previous["schulden_mio_eur"]
    change_pct = change / previous["schulden_mio_eur"] * 100

    left, middle, right = st.columns(3)
    left.metric(
        f"Schuldenstand {int(latest['jahr'])}",
        ui.format_mrd(latest["schulden_mio_eur"], decimals=0),
        delta=f"{ui.format_mrd(change)} ({ui.format_number(change_pct)} %)",
        delta_color="inverse",
    )
    quote_delta = latest["schuldenquote_pct"] - previous["schuldenquote_pct"]
    middle.metric(
        "Schuldenquote",
        ui.format_number(latest["schuldenquote_pct"], 1, " %"),
        delta=f"{ui.format_number(quote_delta, 1)} %-Pkt. zum Vorjahr",
        delta_color="inverse",
    )
    right.metric(
        "Schulden je Einwohner:in",
        ui.format_eur(latest["schulden_je_einwohner_eur"]),
        delta=ui.format_eur(
            latest["schulden_je_einwohner_eur"] - previous["schulden_je_einwohner_eur"]
        ),
        delta_color="inverse",
    )
    st.caption(
        f"Maastricht-Referenz: 60 % des BIP – aktuell "
        f"{ui.format_number(latest['schuldenquote_pct'] - 60, 1)} Prozentpunkte darüber."
    )

    left_column, right_column = st.columns([3, 2])

    with left_column:
        st.subheader("Schuldenstand und Schuldenquote")
        figure = make_subplots(specs=[[{"secondary_y": True}]])
        figure.add_trace(
            go.Scatter(
                x=total["jahr"],
                y=total["schulden_mio_eur"] / 1000,
                name="Schuldenstand (Mrd. €)",
                line={"color": "#1f4e79", "width": 3},
                hovertemplate="%{y:,.0f} Mrd. €<extra></extra>",
            ),
            secondary_y=False,
        )
        figure.add_trace(
            go.Scatter(
                x=total["jahr"],
                y=total["schuldenquote_pct"],
                name="Schuldenquote (% BIP)",
                line={"color": "#c9a227", "width": 2, "dash": "dot"},
                hovertemplate="%{y:.1f} % des BIP<extra></extra>",
            ),
            secondary_y=True,
        )
        figure.add_hline(
            y=60,
            line={"color": "#b03a2e", "width": 1, "dash": "dash"},
            annotation_text="Maastricht: 60 %",
            annotation_position="top left",
            secondary_y=True,
        )
        figure.update_yaxes(title_text="Mrd. €", secondary_y=False)
        figure.update_yaxes(
            title_text="% des BIP",
            range=[0, 90],
            tickvals=[0, 15, 30, 45, 60, 75, 90],
            secondary_y=True,
        )
        st.plotly_chart(ui.style(figure, height=460), width="stretch")

    with right_column:
        st.subheader("Wer schuldet was?")
        latest_year = int(
            annual[annual["sector"] != "S13"].dropna(subset=["schulden_mio_eur"])["jahr"].max()
        )
        composition = annual[
            (annual["jahr"] == latest_year) & (annual["sector"] != "S13")
        ].sort_values("schulden_mio_eur")
        consolidated = annual[(annual["jahr"] == latest_year) & (annual["sector"] == "S13")][
            "schulden_mio_eur"
        ].max()
        figure = go.Figure(
            go.Pie(
                labels=composition["ebene"],
                values=composition["schulden_mio_eur"],
                hole=0.55,
                sort=False,
                marker={
                    "colors": [
                        ui.EBENE_COLORS.get(ebene, "#1f4e79") for ebene in composition["ebene"]
                    ]
                },
                text=composition["schulden_mio_eur"]
                .div(composition["schulden_mio_eur"].sum())
                .mul(100)
                .map(lambda share: f"{ui.format_number(share, 1)} %"),
                textinfo="text",
                hovertemplate="%{label}: %{value:,.0f} Mio. € (%{percent})<extra></extra>",
            )
        )
        figure.add_annotation(
            text=f"konsolidiert<br><b>{ui.format_mrd(consolidated, 0)}</b>",
            showarrow=False,
            font={"size": 14},
        )
        figure.update_layout(legend={"orientation": "h", "y": -0.1, "x": 0})
        st.plotly_chart(ui.style(figure, height=460), width="stretch")
        st.caption(
            f"Anteile der Ebenen am Schuldenstand {latest_year} (Summe der Ebenen: "
            f"{ui.format_mrd(composition['schulden_mio_eur'].sum(), 0)}). Die konsolidierte "
            "Gesamtsumme ist niedriger, weil Forderungen zwischen staatlichen Einheiten "
            "verrechnet werden. Eurostat liefert die Aufteilung erst ab 2022."
        )

    st.divider()
    st.subheader("Veränderung gegenüber dem Vorjahr")
    with_changes = total.copy()
    with_changes["veraenderung_mio_eur"] = with_changes["schulden_mio_eur"].diff()
    last_years = with_changes.tail(20)
    figure = go.Figure(
        go.Bar(
            x=last_years["jahr"],
            y=last_years["veraenderung_mio_eur"] / 1000,
            marker_color=[
                "#b03a2e" if value > 0 else "#2e7d32"
                for value in last_years["veraenderung_mio_eur"]
            ],
            hovertemplate="%{x}: %{y:,.0f} Mrd. €<extra></extra>",
        )
    )
    figure.update_yaxes(title_text="Veränderung in Mrd. €")
    st.plotly_chart(ui.style(figure, height=320, legend=False), width="stretch")

    retrieved = ui.data_retrieved_at()
    st.caption(
        "Quellen: Eurostat (gov_10dd_edpt1, nama_10_gdp, demo_pjan) und Statistisches Bundesamt "
        "(GENESIS-Online 71311-0001, 71311-0003, 71321-0005). "
        + (f"Datenabruf: {retrieved:%d.%m.%Y}. " if retrieved else "")
        + "Weitere Auswertungen über die Seiten in der Seitenleiste."
    )


main()
