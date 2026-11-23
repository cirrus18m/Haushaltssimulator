"""Tests for the figure data of the German Council of Economic Experts (SVR 2026/27)."""

from __future__ import annotations

import plotly.graph_objects as go
import pytest

from haushaltssimulator import analysis, build, charts, dataset, paths, svr

# Shortened layout of an embedded figure CSV: BOM, semicolons, German decimals, empty
# years, an empty row and the trailing text.
FIGURE_CSV = (
    b"\xef\xbb\xbf"
    + (
        '"Jahr";"Einnahmen Kreditaufnahme²";"Ausgaben Verteidigung⁴"\r\n'
        '"2009";;\r\n'
        '"2010";"1,7";"12,29"\r\n'
        '"2011";"0";"11,45"\r\n'
        '""\r\n'
        '"Titel: Einnahmen- und Ausgabenentwicklung"\r\n'
        '"Quellen: BMF, eigene Berechnungen "\r\n'
        '"© Sachverständigenrat | 26-200-02"\r\n'
    ).encode()
)


def test_parse_figure_csv_reads_values_and_text() -> None:
    figure = svr.parse_figure_csv(FIGURE_CSV)

    assert list(figure.data.columns) == [
        "Jahr",
        "Einnahmen Kreditaufnahme",
        "Ausgaben Verteidigung",
    ]
    assert figure.data["Jahr"].tolist() == [2010, 2011]
    assert figure.data["Einnahmen Kreditaufnahme"].tolist() == [1.7, 0.0]
    assert figure.data["Ausgaben Verteidigung"].tolist() == [12.29, 11.45]
    assert figure.title == "Einnahmen- und Ausgabenentwicklung"
    assert figure.notes == (
        "Quellen: BMF, eigene Berechnungen",
        "© Sachverständigenrat | 26-200-02",
    )


def test_parse_figure_csv_rejects_other_files() -> None:
    with pytest.raises(ValueError, match="Jahr"):
        svr.parse_figure_csv(b"Datum;Wert\n2020;1\n")


def test_core_budget_follows_figure_37() -> None:
    """Values from the data CSV of figure 37 in the annual report 2026/27."""
    frame = build.build_svr_core_budget(paths.RAW_DIR)

    # Column names as in the source CSV (without footnote digits).
    assert list(frame.columns) == ["Jahr", "Finanzplan", *dataset.CORE_BUDGET_SVR_SERIES]
    assert dataset.CORE_BUDGET_INTEREST == (
        "Ausgaben für Soziale Sicherung, Verteidigung und Zinsen Zinsen"
    )
    assert frame["Jahr"].tolist() == list(range(2010, 2031))
    assert not frame.loc[frame["Jahr"] < 2026, "Finanzplan"].any()
    assert frame.loc[frame["Jahr"] >= 2026, "Finanzplan"].all()

    year_2030 = frame.set_index("Jahr").loc[2030]
    assert year_2030[dataset.CORE_BUDGET_INTEREST] == pytest.approx(17.24)
    assert year_2030[dataset.CORE_BUDGET_DEFENCE] == pytest.approx(39.23)
    assert year_2030[dataset.CORE_BUDGET_EXPENDITURE] == pytest.approx(12.2)

    # Revenue excluding borrowing plus borrowing equals expenditure (rounded).
    total = frame[dataset.CORE_BUDGET_REVENUE] + frame[dataset.CORE_BUDGET_BORROWING]
    assert (total - frame[dataset.CORE_BUDGET_EXPENDITURE]).abs().max() <= 0.11


def test_core_budget_processed_matches_build() -> None:
    stored = dataset.load_federal_core_budget_svr()
    rebuilt = build.build_svr_core_budget(paths.RAW_DIR)
    assert list(stored.columns) == list(rebuilt.columns)
    assert stored["Jahr"].tolist() == rebuilt["Jahr"].tolist()
    assert stored["Finanzplan"].tolist() == rebuilt["Finanzplan"].tolist()
    assert stored[dataset.CORE_BUDGET_INTEREST].tolist() == pytest.approx(
        rebuilt[dataset.CORE_BUDGET_INTEREST].tolist()
    )


def test_core_budget_highlights() -> None:
    key = analysis.core_budget_highlights(dataset.load_federal_core_budget_svr())

    assert key.last_year == 2030
    assert key.interest_low_year == 2021
    assert key.interest_low_pct == pytest.approx(1.15)
    assert key.first_year_blocks_above_revenue == 2028
    assert key.blocks_last_pct == pytest.approx(114.85)


def test_core_budget_chart_and_summary() -> None:
    frame = dataset.load_federal_core_budget_svr()
    figure = charts.core_budget(frame)

    assert isinstance(figure, go.Figure)
    assert [trace.name for trace in figure.data] == [
        name for _, name, _ in charts.CORE_BUDGET_AREAS
    ] + [name for _, name, _, _ in charts.CORE_BUDGET_LINES] + [
        name for _, name, _ in charts.CORE_BUDGET_BLOCKS
    ]
    assert figure.layout.yaxis.title.text == "% des BIP"
    assert figure.layout.yaxis2.title.text == "% der Einnahmen ohne Kredite"

    summary = charts.core_budget_summary(frame)
    assert "**17,2 %**" in summary
    assert "Ab 2028" in summary
    assert "Quelle: Sachverständigenrat" in charts.CORE_BUDGET_CAPTION
