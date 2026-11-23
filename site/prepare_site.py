"""Pre-render step: files the pages load in the browser.

* plotly.min.js from the installed plotly package -> assets/
* stylesheets and charts of the insights decks -> folien/<topic>/
* data for filters in the browser -> data/*.json

Runs before Quarto resolves ``resources``; files written later by page cells would not
be copied to ``_site`` on the first render.
"""

import json
import shutil
from pathlib import Path

import plotly

from haushaltssimulator import charts, dataset

SITE = Path(__file__).parent
INSIGHTS = SITE.parent / "insights"


def copy_if_changed(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_bytes() != source.read_bytes():
        shutil.copyfile(source, target)


copy_if_changed(
    Path(plotly.__file__).parent / "package_data" / "plotly.min.js",
    SITE / "assets" / "plotly.min.js",
)
for topic in ("zinslast",):
    source_dir = INSIGHTS / topic
    for source in [*source_dir.glob("*.css"), *(source_dir / "bilder").glob("*.svg")]:
        copy_if_changed(source, SITE / "folien" / topic / source.relative_to(source_dir))


def write_json(name: str, payload: object) -> None:
    target = SITE / "data" / name
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


# haushalt.qmd: expenditure blocks of the core budget (SVR figure 37)
core_budget = dataset.load_federal_core_budget_svr()
write_json(
    "core_budget.json",
    {
        "rows": core_budget.to_dict(orient="list"),
        "blocks": [
            {"column": column, "name": name, "colour": colour}
            for column, name, colour in charts.CORE_BUDGET_BLOCKS
        ],
    },
)

# laender.qmd: ten-year government bond yields per country, with the source per country
yields = dataset.load_international_yields().sort_values(["land", "monat"])
write_json(
    "yields.json",
    {
        land: {
            "monat": part["monat"].tolist(),
            "rendite_pct": part["rendite_pct"].tolist(),
            "quelle": " / ".join(part["quelle"].unique()),
        }
        for land, part in yields.groupby("land")
    },
)
