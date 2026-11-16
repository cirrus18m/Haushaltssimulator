"""Tests für den Eurostat-Parser."""

from __future__ import annotations

import pytest

from haushaltssimulator import eurostat

DOCUMENT = {
    "id": ["unit", "time"],
    "size": [2, 3],
    "dimension": {
        "unit": {"category": {"index": {"MIO_EUR": 0, "PC_GDP": 1}}},
        "time": {"category": {"index": {"1995": 0, "1996": 1, "1997": 2}}},
    },
    "value": {"0": 100.0, "1": 110.0, "2": 120.0, "3": 55.5, "4": 56.0},
}


def test_jsonstat_to_frame_orders_dimensions_correctly() -> None:
    frame = eurostat.jsonstat_to_frame(DOCUMENT)
    assert len(frame) == 5
    assert set(frame.columns) == {"unit", "time", "value"}

    mio = frame[frame["unit"] == "MIO_EUR"].set_index("time")["value"]
    assert mio["1995"] == 100.0
    assert mio["1996"] == 110.0
    assert mio["1997"] == 120.0

    quote = frame[frame["unit"] == "PC_GDP"].set_index("time")["value"]
    assert quote["1995"] == 55.5
    assert quote["1996"] == 56.0


def test_jsonstat_to_frame_detects_inconsistent_size() -> None:
    broken = {**DOCUMENT, "size": [2, 4]}
    with pytest.raises(ValueError, match="Dimensionsgröße"):
        eurostat.jsonstat_to_frame(broken)
