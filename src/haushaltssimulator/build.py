"""Erzeugt aus den Rohdaten die aufbereiteten CSV-Dateien für die App."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import destatis, eurostat, paths, sources

SECTOR_LABELS = {
    "S13": "Staat insgesamt",
    "S1311": "Bund (Zentralstaat)",
    "S1312": "Länder (Staatsebene)",
    "S1313": "Gemeinden (lokale Ebene)",
    "S1314": "Sozialversicherung",
}
EBENE_ORDER = list(SECTOR_LABELS.values())

LEVEL_ORDER = ["Bund", "Länder", "Gemeinden / Gemeindeverbände", "Sozialversicherung", "Insgesamt"]
LAENDER_LEVEL_ORDER = ["Länder", "Gemeinden / Gemeindeverbände", "Insgesamt"]
HAUSHALT_ORDER = ["Kernhaushalt", "Extrahaushalte", "Insgesamt"]
SCHULDENART_ORDER = [
    "Wertpapierschulden",
    "Kredite beim nicht-öffentlichen Bereich",
    "Kassenkredite beim nicht-öffentlichen Bereich",
    "Insgesamt",
]

DESTATIS_COLUMNS = ["stichtag", "ebene", "haushalt", "schuldenart", "schulden_mio_eur"]


def _load_json(raw_dir: Path, filename: str) -> dict:
    return json.loads((raw_dir / filename).read_text(encoding="utf-8"))


def _trim_eurostat(frame: pd.DataFrame) -> pd.DataFrame:
    """Behält nur die Sektoren, die die App nutzt, und ergänzt deutsche Bezeichnungen."""
    trimmed = frame[frame["sector"].isin(SECTOR_LABELS)].copy()
    trimmed["ebene"] = trimmed["sector"].map(SECTOR_LABELS)
    return trimmed


def _unit_wide(frame: pd.DataFrame, index: list[str]) -> pd.DataFrame:
    """Klappt die Eurostat-Einheiten in eigene Spalten um."""
    wide = frame.pivot_table(index=index, columns="unit", values="value", aggfunc="first")
    wide = wide.reset_index()
    for column in ("MIO_EUR", "PC_GDP"):
        if column not in wide.columns:
            raise ValueError(f"Einheit {column} fehlt in der Datenquelle")
    return wide[[*index, "MIO_EUR", "PC_GDP"]].rename(
        columns={"MIO_EUR": "schulden_mio_eur", "PC_GDP": "schuldenquote_pct"}
    )


def _parse_destatis(raw_dir: Path, filename: str, label_columns: list[str]) -> pd.DataFrame:
    raw = destatis.decode((raw_dir / filename).read_bytes())
    frame = destatis.parse_table(raw, label_columns)
    units = set(frame["einheit"].dropna())
    if units != {"Mill. EUR"}:
        raise ValueError(f"Unerwartete Einheit in {filename}: {units}")

    frame = frame.rename(columns={"wert": "schulden_mio_eur"}).drop(columns=["einheit"])
    frame["stichtag"] = pd.to_datetime(frame["stichtag"])
    # Destatis liefert ganzzahlige Millionenbeträge.
    frame["schulden_mio_eur"] = frame["schulden_mio_eur"].round().astype("Int64")
    return frame


def build_annual_debt(raw_dir: Path) -> pd.DataFrame:
    """Jährlicher Maastricht-Schuldenstand je staatlicher Ebene (Eurostat)."""
    document = _load_json(raw_dir, "eurostat_gov_10dd_edpt1.json")
    frame = _trim_eurostat(eurostat.jsonstat_to_frame(document))
    wide = _unit_wide(frame, ["time", "sector", "ebene"])

    wide["jahr"] = wide["time"].astype(int)
    wide = wide.drop(columns=["time"])

    gdp = build_gdp_population(raw_dir)[["jahr", "bip_mio_eur"]]
    wide = wide.merge(gdp, on="jahr", how="left")
    wide["ebene"] = pd.Categorical(wide["ebene"], EBENE_ORDER, ordered=True)
    columns = ["jahr", "sector", "ebene", "schulden_mio_eur", "schuldenquote_pct", "bip_mio_eur"]
    return wide[columns].sort_values(["jahr", "ebene"]).reset_index(drop=True)


def build_quarterly_debt(raw_dir: Path) -> pd.DataFrame:
    """Vierteljährlicher Maastricht-Schuldenstand je staatlicher Ebene (Eurostat)."""
    document = _load_json(raw_dir, "eurostat_gov_10q_ggdebt.json")
    frame = _trim_eurostat(eurostat.jsonstat_to_frame(document))
    wide = _unit_wide(frame, ["time", "sector", "ebene"])

    wide["quartal"] = wide["time"]
    wide["quartalsende"] = (
        pd.PeriodIndex(wide["quartal"], freq="Q").to_timestamp(how="end").normalize()
    )
    wide["jahr"] = wide["quartalsende"].dt.year
    wide["ebene"] = pd.Categorical(wide["ebene"], EBENE_ORDER, ordered=True)
    columns = [
        "quartal",
        "quartalsende",
        "jahr",
        "sector",
        "ebene",
        "schulden_mio_eur",
        "schuldenquote_pct",
    ]
    return wide[columns].sort_values(["quartalsende", "ebene"]).reset_index(drop=True)


def build_annual_debt_destatis(raw_dir: Path) -> pd.DataFrame:
    """Jährliche Schulden beim nicht-öffentlichen Bereich (Destatis, ab 2010)."""
    frame = _parse_destatis(
        raw_dir, "destatis_71321-0005_jahr.csv", ["ebene", "haushalt", "schuldenart"]
    )
    frame["jahr"] = frame["stichtag"].dt.year
    frame["ebene"] = pd.Categorical(frame["ebene"], LEVEL_ORDER, ordered=True)
    frame["haushalt"] = pd.Categorical(frame["haushalt"], HAUSHALT_ORDER, ordered=True)
    frame["schuldenart"] = pd.Categorical(frame["schuldenart"], SCHULDENART_ORDER, ordered=True)
    frame = frame.dropna(subset=["ebene", "haushalt", "schuldenart"])
    return (
        frame[["jahr", *DESTATIS_COLUMNS]]
        .sort_values(["jahr", "ebene", "haushalt", "schuldenart"])
        .reset_index(drop=True)
    )


def build_quarterly_debt_destatis(raw_dir: Path) -> pd.DataFrame:
    """Vierteljährliche Schulden beim nicht-öffentlichen Bereich (Destatis)."""
    frame = _parse_destatis(
        raw_dir, "destatis_71311-0001_quartal.csv", ["ebene", "haushalt", "schuldenart"]
    )
    frame["ebene"] = pd.Categorical(frame["ebene"], LEVEL_ORDER, ordered=True)
    frame["haushalt"] = pd.Categorical(frame["haushalt"], HAUSHALT_ORDER, ordered=True)
    frame["schuldenart"] = pd.Categorical(frame["schuldenart"], SCHULDENART_ORDER, ordered=True)
    frame = frame.dropna(subset=["ebene", "haushalt", "schuldenart"])
    return (
        frame[DESTATIS_COLUMNS]
        .sort_values(["stichtag", "ebene", "haushalt", "schuldenart"])
        .reset_index(drop=True)
    )


def build_quarterly_debt_laender(raw_dir: Path) -> pd.DataFrame:
    """Vierteljährliche Schulden der Bundesländer (Destatis)."""
    frame = _parse_destatis(
        raw_dir,
        "destatis_71311-0003_bundeslaender.csv",
        ["bundesland", "ebene", "haushalt", "schuldenart"],
    )
    frame["ebene"] = pd.Categorical(frame["ebene"], LAENDER_LEVEL_ORDER, ordered=True)
    frame["haushalt"] = pd.Categorical(frame["haushalt"], HAUSHALT_ORDER, ordered=True)
    frame["schuldenart"] = pd.Categorical(frame["schuldenart"], SCHULDENART_ORDER, ordered=True)
    frame = frame.dropna(subset=["bundesland", "ebene", "haushalt", "schuldenart"])
    columns = ["stichtag", "bundesland", "ebene", "haushalt", "schuldenart", "schulden_mio_eur"]
    return (
        frame[columns]
        .sort_values(["stichtag", "bundesland", "ebene", "haushalt", "schuldenart"])
        .reset_index(drop=True)
    )


def build_gdp_population(raw_dir: Path) -> pd.DataFrame:
    """BIP und Bevölkerung je Jahr (Eurostat) inklusive BIP je Einwohner."""
    gdp = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_nama_10_gdp.json"))
    gdp = gdp[(gdp["na_item"] == "B1GQ") & (gdp["unit"] == "CP_MEUR")]
    gdp = gdp.rename(columns={"time": "jahr", "value": "bip_mio_eur"})[["jahr", "bip_mio_eur"]]

    population = eurostat.jsonstat_to_frame(_load_json(raw_dir, "eurostat_demo_pjan.json"))
    population = population.rename(columns={"time": "jahr", "value": "bevoelkerung"})[
        ["jahr", "bevoelkerung"]
    ]

    frame = gdp.merge(population, on="jahr", how="outer")
    frame["jahr"] = frame["jahr"].astype(int)
    frame = frame.sort_values("jahr").reset_index(drop=True)
    frame["bip_je_einwohner_eur"] = frame["bip_mio_eur"] * 1_000_000 / frame["bevoelkerung"]
    return frame


BUILDERS = {
    "schulden_jahresreihe.csv": build_annual_debt,
    "schulden_quartalsreihe.csv": build_quarterly_debt,
    "schulden_destatis_jahr.csv": build_annual_debt_destatis,
    "schulden_destatis_quartal.csv": build_quarterly_debt_destatis,
    "schulden_destatis_bundeslaender.csv": build_quarterly_debt_laender,
    "bip_bevoelkerung.csv": build_gdp_population,
}


def build_all(
    raw_dir: Path = paths.RAW_DIR, processed_dir: Path = paths.PROCESSED_DIR
) -> dict[str, Path]:
    """Schreibt alle aufbereiteten Tabellen und gibt die erzeugten Pfade zurück."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for filename, builder in BUILDERS.items():
        frame = builder(raw_dir)
        target = processed_dir / filename
        frame.to_csv(target, index=False, float_format="%.1f", date_format="%Y-%m-%d")
        written[filename] = target
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true", help="Rohdaten trotz vorhandener Dateien neu laden"
    )
    args = parser.parse_args(argv)

    sources.download_all(paths.RAW_DIR, refresh=args.refresh)
    for filename, target in build_all().items():
        print(f"{filename}: {target.relative_to(paths.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
