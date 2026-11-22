"""Output helpers for the Quarto prototype: base layout and HTML fragment per figure."""

from __future__ import annotations

import plotly.graph_objects as go

CONFIG = {"displaylogo": False, "responsive": True, "locale": "de"}


def show(
    figure: go.Figure, *, height: int = 640, top_margin: int = 60, css_class: str = ""
) -> None:
    """Apply the general look (like ui.style) and print the figure as raw HTML.

    Use in a cell with ``#| output: asis``. Printing a raw HTML block instead of
    returning a Jupyter display object keeps Quarto from adding require.js and jQuery
    from a CDN. plotly.js itself is loaded once per page from assets/ (_quarto.yml).
    """
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 10, "r": 10, "t": top_margin, "b": 10},
        font={"family": "Inter, Segoe UI, sans-serif", "size": 13},
        separators=",.",
    )
    html = figure.to_html(full_html=False, include_plotlyjs=False, config=CONFIG)
    print(f'```{{=html}}\n<div class="{css_class}">{html}</div>\n```\n')


def show_responsive(wide: go.Figure, narrow: go.Figure, *, height: int, narrow_height: int) -> None:
    """Print a wide and a narrow variant; CSS in styles.css shows one depending on width."""
    show(wide, height=height, css_class="chart-wide")
    show(narrow, height=narrow_height, css_class="chart-narrow")
