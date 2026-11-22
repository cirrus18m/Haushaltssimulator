"""Pure chart functions: data in, Plotly figure out - no Streamlit.

Used by the Streamlit pages (via ``ui.plot``) and by static outputs such as the Quarto
site under ``site/``. Functions here build content and chart-specific layout (axes,
legends, colours of the original figure); the general look (template, font, margins)
is set by the output target, e.g. ``ui.style``.

User-facing strings (titles, axis labels, hover texts, captions) are German.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import analysis, dataset
from .format import format_number

# Series and colours as in figure 37 of the SVR annual report 2026/27.
CORE_BUDGET_AREAS = (
    (dataset.CORE_BUDGET_REVENUE, "Steuereinnahmen und sonstige Einnahmen", "#1d5c9b"),
    (dataset.CORE_BUDGET_BORROWING, "Kreditaufnahme", "#f7941d"),
)
CORE_BUDGET_LINES = (
    (dataset.CORE_BUDGET_EXPENDITURE, "Insgesamt", "#e2001a", "solid"),
    (
        dataset.CORE_BUDGET_SOCIAL_DEFENCE_INTEREST,
        "Soziale Sicherung, Verteidigung und Zinsen",
        "#1a1a1a",
        "dot",
    ),
)
CORE_BUDGET_BLOCKS = (
    (dataset.CORE_BUDGET_SOCIAL_INSURANCE, "Zuschüsse an die Sozialversicherungen", "#00786a"),
    (dataset.CORE_BUDGET_OTHER_SOCIAL, "Sonstige Soziale Sicherung", "#7fc79a"),
    (dataset.CORE_BUDGET_DEFENCE, "Verteidigung (Einzelplan 14)", "#9b1b6b"),
    (dataset.CORE_BUDGET_INTEREST, "Zinsen", "#f6c925"),
)

CORE_BUDGET_TITLE = "Kernhaushalt des Bundes: Einnahmen, Ausgaben und ihre Schwerpunkte"
CORE_BUDGET_INTRO = (
    "Die Darstellung folgt Abbildung 37 aus dem **Jahresgutachten 2026/27 des "
    "Sachverständigenrats Wirtschaft**. Sie zeigt den **Kernhaushalt des Bundes** – also "
    "ohne Sondervermögen, Länder, Gemeinden und Sozialversicherung. Links stehen "
    "Einnahmen und Ausgaben im Verhältnis zur Wirtschaftsleistung. Rechts steht, wie viel "
    "der Steuer- und sonstigen Einnahmen (ohne Kredite) allein für Soziale Sicherung, "
    "Verteidigung und Zinsen gebunden ist. Ab 2026 gilt der Finanzplan der "
    "Bundesregierung."
)
CORE_BUDGET_CAPTION = (
    "Links in % des BIP gemäß Frühjahrsprojektion der Bundesregierung; Kreditaufnahme "
    "inklusive Rücklagenentnahmen 2022 und 2023. Rechts in % der Steuereinnahmen und "
    "sonstigen Einnahmen; Soziale Sicherung = Zuschüsse an die Sozialversicherungen und "
    "sonstige Soziale Sicherung, Verteidigung = Einzelplan 14. Quelle: Sachverständigenrat "
    "Wirtschaft, Jahresgutachten 2026/27, Abbildung 37 (S. 96, Daten-CSV aus dem PDF); "
    "dort: BMF, BMWE, Statistisches Bundesamt, eigene Berechnungen."
)


def _short_year_ticks(years: pd.Series, step: int = 2) -> dict:
    """First year with four digits, then two digits, so labels stay horizontal."""
    ticks = list(range(int(years.min()), int(years.max()) + 1, step))
    labels = [str(year) if index == 0 else f"{year % 100:02d}" for index, year in enumerate(ticks)]
    return {"tickvals": ticks, "ticktext": labels, "tickangle": 0}


def core_budget(frame: pd.DataFrame, *, narrow: bool = False) -> go.Figure:
    """SVR figure 37: revenue and expenditure (% of GDP) next to stacked expenditure blocks.

    ``frame`` is ``dataset.load_federal_core_budget_svr()``. Each subplot has its own
    legend below it, so callers must keep the legend layout (``own_legends=True``).
    ``narrow=True`` stacks the two subplots vertically for phone screens (about 1100 px
    high instead of 640 px).
    """
    years = frame[dataset.CORE_BUDGET_YEAR]
    block_total = analysis.core_budget_block_total(frame)
    first_plan_year = int(years[frame[dataset.CORE_BUDGET_PLAN]].min())

    titles = ("Einnahmen und Ausgaben", "Soziale Sicherung, Verteidigung, Zinsen")
    if narrow:
        # Wide gap between the rows: the legend of the upper subplot sits in it.
        figure = make_subplots(rows=2, cols=1, vertical_spacing=0.26, subplot_titles=titles)
        second = {"row": 2, "col": 1}
    else:
        figure = make_subplots(rows=1, cols=2, horizontal_spacing=0.12, subplot_titles=titles)
        second = {"row": 1, "col": 2}
    for column, name, colour in CORE_BUDGET_AREAS:
        figure.add_trace(
            go.Scatter(
                x=years,
                y=frame[column],
                name=name,
                stackgroup="revenue",
                mode="lines",
                line={"color": colour, "width": 0.5},
                fillcolor=colour,
                legend="legend",
                legendgroup="revenue",
                legendgrouptitle_text="Einnahmen",
                hovertemplate="%{y:.1f} % des BIP<extra>" + name + "</extra>",
            ),
            row=1,
            col=1,
        )
    for column, name, colour, dash in CORE_BUDGET_LINES:
        figure.add_trace(
            go.Scatter(
                x=years,
                y=frame[column],
                name=name,
                mode="lines",
                line={"color": colour, "dash": dash, "width": 3},
                legend="legend",
                legendgroup="expenditure",
                legendgrouptitle_text="Ausgaben",
                hovertemplate="%{y:.1f} % des BIP<extra>Ausgaben: " + name + "</extra>",
            ),
            row=1,
            col=1,
        )
    for column, name, colour in CORE_BUDGET_BLOCKS:
        figure.add_trace(
            go.Bar(
                x=years,
                y=frame[column],
                name=name,
                marker_color=colour,
                legend="legend2",
                customdata=block_total,
                hovertemplate=(
                    "%{y:.1f} % der Einnahmen (alle vier: %{customdata:.0f} %)<extra>"
                    + name
                    + "</extra>"
                ),
            ),
            **second,
        )
    for position in ({"row": 1, "col": 1}, second):
        figure.add_vrect(
            x0=first_plan_year - 0.5,
            x1=int(years.max()) + 0.5,
            fillcolor="#8fb8de",
            opacity=0.15,
            line_width=0,
            annotation_text="Finanzplan",
            annotation_position="top left",
            annotation_font={"color": "#4a7fb0", "size": 12},
            **position,
        )
    legend_below = {"yanchor": "top", "orientation": "v", "font": {"size": 12}}
    if narrow:
        upper_bottom = figure.layout.yaxis.domain[0]
        legends = ({"x": 0, "y": upper_bottom - 0.035}, {"x": 0, "y": -0.035})
    else:
        legends = ({"x": 0, "y": -0.12}, {"x": 0.56, "y": -0.12})
    figure.update_layout(
        barmode="stack",
        bargap=0.25,
        hovermode="x unified",
        legend={**legend_below, **legends[0], "groupclick": "toggleitem", "traceorder": "grouped"},
        legend2={**legend_below, **legends[1], "traceorder": "normal"},
    )
    figure.update_xaxes(**_short_year_ticks(years), range=[years.min() - 0.6, years.max() + 0.6])
    # The expenditure line peaks at about 15 % of GDP in 2021; like the original, the
    # axis ends at 16 %.
    figure.update_yaxes(title_text="% des BIP", range=[0, 16], dtick=4, row=1, col=1)
    figure.update_yaxes(title_text="% der Einnahmen ohne Kredite", dtick=25, **second)
    return figure


def core_budget_summary(frame: pd.DataFrame) -> str:
    """German summary sentence (Markdown) with the key figures from the data."""
    key = analysis.core_budget_highlights(frame)
    text = (
        f"Die Zinsen binden {key.last_year} laut Finanzplan "
        f"**{format_number(key.interest_last_pct, 1)} %** der Einnahmen ohne Kredite – nach "
        f"{format_number(key.interest_low_pct, 1)} % im Jahr {key.interest_low_year}. Die "
        f"Verteidigung steigt auf **{format_number(key.defence_last_pct, 1)} %**."
    )
    if key.first_year_blocks_above_revenue is not None:
        text += (
            f" Ab {key.first_year_blocks_above_revenue} übersteigen die vier Posten zusammen "
            f"die gesamten Steuer- und sonstigen Einnahmen; {key.last_year} sind es "
            f"{format_number(key.blocks_last_pct, 0)} %."
        )
    return text
