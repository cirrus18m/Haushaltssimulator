"""Berechnungen für die analytischen Auswertungen der App."""

from __future__ import annotations

import pandas as pd


def year_over_year(frame: pd.DataFrame, value_column: str, group_column: str) -> pd.DataFrame:
    """Ergänzt absolute und relative Veränderung gegenüber dem Vorjahr."""
    result = frame.sort_values([group_column, "jahr"]).copy()
    result["veraenderung_mio_eur"] = result.groupby(group_column, observed=True)[
        value_column
    ].diff()
    result["veraenderung_pct"] = (
        result.groupby(group_column, observed=True)[value_column].pct_change() * 100
    )
    return result


def cagr(start_value: float, end_value: float, years: int) -> float:
    """Durchschnittliche jährliche Wachstumsrate in Prozent."""
    if years <= 0 or not start_value or start_value <= 0 or end_value <= 0:
        return float("nan")
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def with_interest_burden(frame: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt die theoretische Zinslast und ihre Anteile an Einnahmen und BIP.

    Die theoretische Zinslast ist der Schuldenstand multipliziert mit der
    Marktrendite des jeweiligen Jahres. Sie ist eine Modellrechnung und nicht mit
    den tatsächlich gebuchten Zinsausgaben gleichzusetzen.
    """
    result = frame.copy()
    result["zins_theoretisch_mio_eur"] = (
        result["schulden_mio_eur"] * result["rendite_pct"] / 100
    )
    result["zins_quote_einnahmen_pct"] = (
        result["zins_theoretisch_mio_eur"] / result["einnahmen_mio_eur"] * 100
    )
    result["zins_quote_bip_pct"] = result["zins_theoretisch_mio_eur"] / result["bip_mio_eur"] * 100
    return result


def simulate_debt_ratio(
    schulden_mio_eur: float,
    bip_mio_eur: float,
    schuldenwachstum_pct: float,
    bip_wachstum_pct: float,
    jahre: int,
    startjahr: int,
) -> pd.DataFrame:
    """Projiziert Schuldenstand und Schuldenquote bei konstanten Wachstumsraten.

    Die Rechnung ist bewusst einfach: Schulden und BIP wachsen jedes Jahr mit der
    angegebenen Rate, die Schuldenquote ergibt sich als Verhältnis beider Größen.
    """
    records = []
    schulden = schulden_mio_eur
    bip = bip_mio_eur
    for offset in range(jahre + 1):
        jahr = startjahr + offset
        records.append(
            {
                "jahr": jahr,
                "schulden_mio_eur": schulden,
                "bip_mio_eur": bip,
                "schuldenquote_pct": schulden / bip * 100 if bip else float("nan"),
            }
        )
        schulden *= 1 + schuldenwachstum_pct / 100
        bip *= 1 + bip_wachstum_pct / 100
    return pd.DataFrame.from_records(records)
