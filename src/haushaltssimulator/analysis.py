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


def monthly_interest_burden(debt: pd.DataFrame, yields: pd.DataFrame) -> pd.DataFrame:
    """Theoretische Zinslast je Monat aus Schuldenstand und Monatsrendite.

    Der Schuldenstand liegt nur als Jahresendbestand vor und wird linear zwischen den
    Jahresenden interpoliert. Über den letzten Stichtag hinaus wird er mit dem Trend
    der letzten beiden Jahresenden bis zum letzten Renditemonat fortgeschrieben – eine
    konstante Festschreibung würde einen ganzen Jahresverlauf mit dem Vorjahreswert
    belegen. Verzinst wird mit dem Monatsmittel der Rendite; jeder Monatswert ist damit
    die auf ein Jahr hochgerechnete Last, die der Schuldenstand beim damaligen
    Marktzins kosten würde. Das Ergebnis ist eine Modellrechnung und nicht mit den
    tatsächlich gebuchten Zinsausgaben gleichzusetzen.
    """
    monatsrendite = (
        yields.dropna(subset=["rendite_pct"])
        .groupby("monat", as_index=False)["rendite_pct"]
        .mean()
        .sort_values("monat")
        .reset_index(drop=True)
    )
    jahresbestand = debt.dropna(subset=["schulden_mio_eur"])
    jahresende = pd.to_datetime(jahresbestand["jahr"].astype(int).astype(str) + "-12-31")
    bestand = pd.Series(
        jahresbestand["schulden_mio_eur"].to_numpy(dtype=float),
        index=jahresende.to_numpy(),
    ).sort_index()

    monate = pd.DatetimeIndex(monatsrendite["monat"] + "-01")
    reihe = bestand.reindex(bestand.index.union(monate)).interpolate(method="time")
    reihe = reihe.ffill().bfill()

    if len(bestand) >= 2:
        letzter_stichtag = bestand.index[-1]
        steigung = (bestand.iloc[-1] - bestand.iloc[-2]) / (
            (bestand.index[-1] - bestand.index[-2]).days
        )
        fortschreibung = monate[monate > letzter_stichtag]
        if len(fortschreibung):
            reihe.loc[fortschreibung] = bestand.iloc[-1] + steigung * (
                fortschreibung - letzter_stichtag
            ).days

    result = monatsrendite.assign(
        datum=monate.to_numpy(),
        schulden_mio_eur=reihe.reindex(monate).to_numpy(),
    )
    result["zins_theoretisch_mio_eur"] = result["schulden_mio_eur"] * result["rendite_pct"] / 100
    columns = [
        "monat",
        "datum",
        "schulden_mio_eur",
        "rendite_pct",
        "zins_theoretisch_mio_eur",
    ]
    return result[columns]


def theoretical_interest_by_country(
    debt: pd.DataFrame,
    budget: pd.DataFrame,
    yields: pd.DataFrame,
    income: pd.DataFrame | None = None,
    einkommensart: str | None = None,
) -> pd.DataFrame:
    """Theoretische Zinslast je Land: aktueller Marktzins auf den Schuldenstand.

    Verknüpft den Schuldenstand und die Einnahmen des letzten verfügbaren Jahres mit
    der aktuellsten 10-jährigen Rendite. Ist ``income`` übergeben, wird zusätzlich
    das jüngste verfügbare Durchschnittseinkommen der gewählten Abgrenzung
    herangezogen und die Zinslast je Einwohner:in ins Verhältnis dazu gesetzt.
    Das Ergebnis ist eine Modellrechnung und nicht mit den tatsächlich gebuchten
    Zinsausgaben gleichzusetzen.
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

    if income is not None and einkommensart:
        latest_income = (
            income[income["einkommensart"] == einkommensart]
            .dropna(subset=["einkommen_eur"])
            .sort_values(["land", "jahr"])
            .groupby("land", as_index=False)
            .tail(1)
            .rename(columns={"jahr": "einkommen_jahr"})
        )
        frame = frame.merge(
            latest_income[["land", "einkommen_jahr", "einkommen_eur"]], on="land", how="left"
        )
    else:
        frame["einkommen_jahr"] = pd.NA
        frame["einkommen_eur"] = pd.NA

    frame["zins_quote_einkommen_pct"] = (
        frame["zins_je_einwohner_eur"] / frame["einkommen_eur"] * 100
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
        "einkommen_jahr",
        "einkommen_eur",
        "zins_quote_einkommen_pct",
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


def linear_trend(
    frame: pd.DataFrame,
    value_column: str,
    *,
    fit_end: str,
    date_column: str = "monat",
) -> pd.Series:
    """Lineare Regression bis ``fit_end``, für alle Zeilen fortgeschrieben.

    Die Regressionsgerade wird über die Monatswerte bis einschließlich ``fit_end``
    geschätzt und anschließend über den gesamten Zeitraum extrapoliert. Die Steigung
    entspricht dem durchschnittlichen Zuwachs je Jahr in Einheiten der Wertspalte.
    """
    dates = pd.to_datetime(frame[date_column])
    x = (dates - dates.min()).dt.days / 365.25
    fit = dates <= pd.Timestamp(fit_end)
    x_fit = x[fit]
    y_fit = frame.loc[fit, value_column]
    if len(x_fit) < 2 or x_fit.var() == 0:
        raise ValueError("Für den Trend sind mindestens zwei verschiedene Zeitpunkte nötig")
    slope = x_fit.cov(y_fit) / x_fit.var()
    intercept = y_fit.mean() - slope * x_fit.mean()
    return intercept + slope * x


def budget_shares(
    frame: pd.DataFrame,
    *,
    value_column: str = "ausgaben_mrd_eur",
    year_column: str = "jahr",
) -> pd.DataFrame:
    """Anteil jeder Zeile an der Jahressumme in Prozent.

    Die Anteile beziehen sich auf die Gesamtausgaben des jeweiligen Jahres, sodass sich
    die Planjahre trotz steigender Summen vergleichen lassen. Fehlende Werte (nicht
    veranschlagte Beträge) bleiben leer und zählen nicht zur Summe.
    """
    result = frame.copy()
    gesamt = result.groupby(year_column, observed=True)[value_column].transform("sum")
    result["anteil_pct"] = result[value_column] / gesamt * 100
    return result


def largest_areas(
    frame: pd.DataFrame,
    *,
    threshold_pct: float,
    label: str = "Übrige Aufgabenbereiche",
    label_column: str = "aufgabenbereich",
    value_column: str = "ausgaben_mrd_eur",
    share_column: str = "anteil_pct",
    year_column: str = "jahr",
) -> pd.DataFrame:
    """Fasst Aufgabenbereiche unterhalb der Anteilsschwelle je Jahr zusammen.

    Ein Bereich bleibt einzeln erhalten, sobald er in mindestens einem Jahr die Schwelle
    erreicht; alle übrigen werden je Jahr zu einer Sammelposition addiert. So bleibt das
    Säulendiagramm lesbar, ohne Bereiche stillschweigend zu verschlucken.
    """
    gross = set(frame.loc[frame[share_column] >= threshold_pct, label_column])
    teile = [frame[frame[label_column].isin(gross)]]
    rest = frame[~frame[label_column].isin(gross)]
    if not rest.empty:
        summe = rest.groupby(year_column, observed=True)[[value_column, share_column]].sum()
        summe[label_column] = label
        teile.append(summe.reset_index())
    return pd.concat(teile, ignore_index=True)[list(frame.columns)]


def share_change(
    frame: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
    label_column: str = "aufgabenbereich",
    value_column: str = "ausgaben_mrd_eur",
    share_column: str = "anteil_pct",
    year_column: str = "jahr",
) -> pd.DataFrame:
    """Ausgaben und Anteile zweier Jahre samt Veränderung des Anteils in Prozentpunkten."""
    start = frame[frame[year_column] == start_year].set_index(label_column)
    ende = frame[frame[year_column] == end_year].set_index(label_column)
    result = pd.DataFrame(
        {
            f"ausgaben_{start_year}_mrd_eur": start[value_column],
            f"ausgaben_{end_year}_mrd_eur": ende[value_column],
            f"anteil_{start_year}_pct": start[share_column],
            f"anteil_{end_year}_pct": ende[share_column],
        }
    )
    result["anteil_veraenderung_pp"] = (
        result[f"anteil_{end_year}_pct"] - result[f"anteil_{start_year}_pct"]
    )
    return result.sort_values(f"anteil_{end_year}_pct", ascending=False).reset_index()


def rate_changes(frame: pd.DataFrame, value_column: str = "zins_pct") -> pd.DataFrame:
    """Reduziert eine Zinsreihe auf die Tage, an denen sich der Satz ändert.

    Der erste und der letzte Beobachtungstag bleiben erhalten, damit die Stufenlinie bis
    zum Ende der Reihe reicht.
    """
    ordered = frame.sort_values("datum").reset_index(drop=True)
    if ordered.empty:
        return ordered
    changed = ordered[value_column].ne(ordered[value_column].shift())
    changed.iloc[-1] = True
    return ordered[changed].reset_index(drop=True)


def extend_steps(frame: pd.DataFrame, end: pd.Timestamp, group_column: str) -> pd.DataFrame:
    """Verlängert Stufenreihen (z. B. Leitzinsen) je Gruppe mit dem letzten Wert bis ``end``.

    Leitzinsen werden nur an Änderungstagen gemeldet; ohne diesen Schritt endete die
    Linie am Tag der letzten Zinsänderung.
    """
    parts = []
    for _, group in frame.sort_values("datum").groupby(group_column, sort=False):
        parts.append(group)
        last = group.iloc[-1]
        if last["datum"] < end:
            parts.append(last.to_frame().T.assign(datum=end))
    if not parts:
        return frame
    result = pd.concat(parts, ignore_index=True)
    return result.astype(frame.dtypes.to_dict())


# Regelsatz der Umsatzsteuer (§ 12 Abs. 1 UStG); der CO₂-Preis ist Teil des Entgelts.
UMSATZSTEUER_PCT = 19.0


def co2_emissions_per_unit(factors: pd.DataFrame) -> pd.DataFrame:
    """CO₂ je Liter bzw. je kWh aus den Standardwerten der EBeV 2030.

    Flüssige Brennstoffe: Dichte (t/1000 l) × Heizwert (GJ/t) × Emissionsfaktor
    (t CO₂/GJ) ergibt t CO₂ je 1000 l = kg CO₂ je Liter. Erdgas: Umrechnungsfaktor
    (GJ/MWh) × Emissionsfaktor ergibt t CO₂ je MWh = kg CO₂ je kWh.
    """
    frame = factors.copy()
    fluessig = frame["einheit"] == "1000 l"
    energie_gj = frame["dichte_t_je_1000l"] * frame["heizwert_gj_je_t"]
    energie_gj = energie_gj.where(fluessig, frame["umrechnung_gj_je_mwh"])
    frame["kg_co2_je_einheit"] = energie_gj * frame["emissionsfaktor_t_co2_je_gj"]
    frame["einheit_verbrauch"] = frame["einheit"].map({"1000 l": "l", "MWh": "kWh"})
    return frame[["brennstoff", "einheit_verbrauch", "kg_co2_je_einheit"]]


def co2_surcharge(prices: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """Aufschlag des CO₂-Preises je Liter bzw. kWh in Cent, netto und mit Umsatzsteuer.

    ``prices`` enthält je Jahr ``preis_min_eur_t`` und ``preis_max_eur_t`` (beim
    Festpreis gleich). Euro je Tonne × kg CO₂ je Einheit / 1000 × 100 ergibt Cent.
    """
    emissionen = co2_emissions_per_unit(factors)
    frame = prices[["jahr", "preis_min_eur_t", "preis_max_eur_t", "art"]].merge(
        emissionen, how="cross"
    )
    for grenze in ("min", "max"):
        netto = frame[f"preis_{grenze}_eur_t"] * frame["kg_co2_je_einheit"] / 10
        frame[f"aufschlag_{grenze}_netto_ct"] = netto
        frame[f"aufschlag_{grenze}_brutto_ct"] = netto * (1 + UMSATZSTEUER_PCT / 100)
    columns = [
        "jahr",
        "brennstoff",
        "einheit_verbrauch",
        "kg_co2_je_einheit",
        "art",
        "aufschlag_min_netto_ct",
        "aufschlag_max_netto_ct",
        "aufschlag_min_brutto_ct",
        "aufschlag_max_brutto_ct",
    ]
    return frame[columns].sort_values(["brennstoff", "jahr"]).reset_index(drop=True)


def co2_share_of_consumer_price(
    surcharge: pd.DataFrame,
    energy_markets: pd.DataFrame,
    fuel_prices: pd.DataFrame,
    jahr: int,
) -> pd.DataFrame:
    """Anteil des CO₂-Aufschlags (mit Umsatzsteuer) am mittleren Verbraucherpreis.

    Heizöl kommt aus ``energy_markets`` (``heizoel_ct_l``), Diesel und Benzin aus
    ``fuel_prices`` (Deutschland). Alle Preise enthalten Steuern. Bei einem
    Preiskorridor wird die Obergrenze verwendet.
    """
    def jahresmittel(frame: pd.DataFrame, column: str) -> float:
        return frame.loc[frame["monat"].str[:4] == str(jahr), column].mean()

    deutschland = fuel_prices[fuel_prices["land"] == "Deutschland"]
    preise = {
        "Heizöl EL": jahresmittel(energy_markets, "heizoel_ct_l"),
        "Diesel": jahresmittel(deutschland[deutschland["produkt"] == "Diesel"], "preis_eur_l")
        * 100,
        "Benzin": jahresmittel(
            deutschland[deutschland["produkt"] == "Superbenzin (Euro 95)"], "preis_eur_l"
        )
        * 100,
    }
    frame = surcharge[(surcharge["jahr"] == jahr) & surcharge["brennstoff"].isin(preise)]
    frame = frame[["brennstoff", "aufschlag_max_brutto_ct"]].copy()
    frame["preis_ct_l"] = frame["brennstoff"].map(preise)
    frame["anteil_pct"] = frame["aufschlag_max_brutto_ct"] / frame["preis_ct_l"] * 100
    return frame.reset_index(drop=True)
