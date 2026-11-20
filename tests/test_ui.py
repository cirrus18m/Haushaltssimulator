"""Tests für die Diagramm-Hilfen in ``haushaltssimulator.ui``."""

from __future__ import annotations

import plotly.graph_objects as go

from haushaltssimulator import ui


def test_svg_export_renders_vector_graphic() -> None:
    """Das SVG entsteht erst beim Klick; dieser Test prüft den Export einmal direkt."""
    figure = ui.style(go.Figure(go.Scatter(x=[1, 2], y=[3, 4])))
    svg = ui._svg_bytes(figure.to_json())
    assert svg.lstrip().startswith(b"<svg")
    assert svg != ui.SVG_NICHT_VERFUEGBAR, "Kaleido rendert kein SVG"


def test_svg_export_falls_back_without_kaleido(monkeypatch) -> None:
    def ohne_kaleido(*args, **kwargs):
        raise RuntimeError("Chrome fehlt")

    monkeypatch.setattr(go.Figure, "to_image", ohne_kaleido)
    ui._svg_bytes.cache_clear()
    try:
        assert ui._svg_bytes('{"data": [], "layout": {}}') == ui.SVG_NICHT_VERFUEGBAR
    finally:
        ui._svg_bytes.cache_clear()


def test_own_legends_keep_figure_legend_layout() -> None:
    figure = go.Figure(go.Scatter(y=[1]))
    figure.update_layout(legend={"x": 1.06, "orientation": "v"})
    ui.style(figure, own_legends=True)
    assert figure.layout.legend.x == 1.06
    ui.style(figure)
    assert figure.layout.legend.orientation == "h"
