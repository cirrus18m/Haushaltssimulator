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
    result["zins_theoretisch_mio_eur"] = result["schulden_mio_eur"] * result["rendite_pct"] / 100
    result["zins_quote_einnahmen_pct"] = (
        result["zins_theoretisch_mio_eur"] / result["einnahmen_mio_eur"] * 100
    )
    result["zins_quote_bip_pct"] = result["zins_theoretisch_mio_eur"] / result["bip_mio_eur"] * 100
    return result


def theoretical_interest_by_country(
    debt: pd.DataFrame,
    budget: pd.DataFrame,
    yields: pd.DataFrame,
) -> pd.DataFrame:
    """Theoretische Zinslast je Land: aktueller Marktzins auf den Schuldenstand.

    Verknüpft den Schuldenstand und die Einnahmen des letzten verfügbaren Jahres mit
    der aktuellsten 10-jährigen Rendite. Das Ergebnis ist eine Modellrechnung und
    nicht mit den tatsächlich gebuchten Zinsausgaben gleichzusetzen.
    """
    latest_debt = (
        debt.dropna(subset=["schulden_mio_eur"])
        .sort_values(["land", "jahr"])
        .groupby("land", as_index=False)
        .tail(1)
    )
    latest_budget = (
        budget.dropna(subset=["einnahmen_mio_eur"])
        .sort_values(["land", "jahr"])
        .groupby("land", as_index=False)
        .tail(1)
    )
    latest_yield = (
        yields.dropna(subset=["rendite_pct"])
        .sort_values(["land", "monat"])
        .groupby("land", as_index=False)
        .tail(1)
    )

    frame = latest_debt[["land", "jahr", "schulden_mio_eur", "schuldenquote_pct"]].merge(
        latest_budget[["land", "einnahmen_mio_eur", "bip_mio_eur", "bevoelkerung"]],
        on="land",
        how="inner",
    )
    # Ohne aktuelle Rendite lässt sich keine theoretische Zinslast berechnen.
    frame = frame.merge(latest_yield[["land", "monat", "rendite_pct"]], on="land", how="inner")
    frame["zins_theoretisch_mio_eur"] = frame["schulden_mio_eur"] * frame["rendite_pct"] / 100
    frame["zins_quote_bip_pct"] = frame["zins_theoretisch_mio_eur"] / frame["bip_mio_eur"] * 100
    frame["zins_quote_einnahmen_pct"] = (
        frame["zins_theoretisch_mio_eur"] / frame["einnahmen_mio_eur"] * 100
    )
    frame["zins_je_einwohner_eur"] = (
        frame["zins_theoretisch_mio_eur"] * 1_000_000 / frame["bevoelkerung"]
    )
    columns = [
        "land",
        "jahr",
        "schulden_mio_eur",
        "schuldenquote_pct",
        "monat",
        "rendite_pct",
        "zins_theoretisch_mio_eur",
        "zins_quote_bip_pct",
        "zins_quote_einnahmen_pct",
        "zins_je_einwohner_eur",
    ]
    return frame[columns].sort_values("zins_quote_bip_pct", ascending=False).reset_index(drop=True)


def real_interest_rate(yields: pd.DataFrame, inflation: pd.DataFrame) -> pd.DataFrame:
    """Realzins je Monat und Land: Rendite minus Inflationsrate."""
    frame = yields.merge(inflation[["monat", "land", "inflation_pct"]], on=["monat", "land"])
    frame["realzins_pct"] = frame["rendite_pct"] - frame["inflation_pct"]
    columns = ["monat", "land", "rendite_pct", "inflation_pct", "realzins_pct"]
    return frame[columns].dropna(subset=["realzins_pct"]).reset_index(drop=True)


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
