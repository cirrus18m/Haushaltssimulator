"""Tests für die Analysefunktionen."""

from __future__ import annotations

import pandas as pd
import pytest

from haushaltssimulator import analysis


def test_cagr() -> None:
    assert analysis.cagr(100, 121, 2) == pytest.approx(10.0)
    assert analysis.cagr(100, 100, 5) == pytest.approx(0.0)
    assert pd.isna(analysis.cagr(0, 100, 5))
    assert pd.isna(analysis.cagr(100, 100, 0))


def test_year_over_year_uses_groups() -> None:
    frame = pd.DataFrame(
        {
            "sector": ["S13", "S13", "S13", "S1311", "S1311"],
            "jahr": [2020, 2021, 2022, 2020, 2021],
            "schulden_mio_eur": [100.0, 110.0, 121.0, 50.0, 40.0],
        }
    )
    result = analysis.year_over_year(frame, "schulden_mio_eur", "sector").set_index(
        ["sector", "jahr"]
    )
    assert pd.isna(result.loc[("S13", 2020), "veraenderung_mio_eur"])
    assert result.loc[("S13", 2021), "veraenderung_mio_eur"] == pytest.approx(10.0)
    assert result.loc[("S13", 2022), "veraenderung_pct"] == pytest.approx(10.0)
    assert result.loc[("S1311", 2021), "veraenderung_pct"] == pytest.approx(-20.0)


def test_simulate_debt_ratio_constant_growth() -> None:
    projection = analysis.simulate_debt_ratio(
        schulden_mio_eur=1000,
        bip_mio_eur=2000,
        schuldenwachstum_pct=0,
        bip_wachstum_pct=0,
        jahre=2,
        startjahr=2025,
    )
    assert projection["jahr"].tolist() == [2025, 2026, 2027]
    assert projection["schuldenquote_pct"].tolist() == pytest.approx([50.0, 50.0, 50.0])


def test_simulate_debt_ratio_growing_debt_reduces_ratio() -> None:
    projection = analysis.simulate_debt_ratio(
        schulden_mio_eur=1000,
        bip_mio_eur=2000,
        schuldenwachstum_pct=0,
        bip_wachstum_pct=10,
        jahre=1,
        startjahr=2025,
    )
    assert projection.loc[1, "schuldenquote_pct"] == pytest.approx(1000 / 2200 * 100)
