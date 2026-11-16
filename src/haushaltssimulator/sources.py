"""Definition und Download der frei verfügbaren Datenquellen.

Quellen:
* Destatis (GENESIS-Online): Tabellen als CSV, Lizenz DL-DE-BY-2.0
* Eurostat (Data Browser API): JSON-stat, Lizenz CC BY 4.0
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DESTATIS_TABLE_URL = "https://genesis.destatis.de/genesisWS/downloads/00/tables/{code}_00.csv"
EUROSTAT_DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}"

USER_AGENT = "Haushaltssimulator/0.1 (Datenabruf Staatsschulden; Kontakt: lokal)"


@dataclass(frozen=True)
class Source:
    """Eine herunterladbare Datenquelle."""

    key: str
    filename: str
    url: str
    description: str


def _eurostat(dataset: str, **params: str) -> str:
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return f"{EUROSTAT_DATA_URL.format(dataset=dataset)}?{query}"


SOURCES: tuple[Source, ...] = (
    Source(
        key="destatis_schulden_quartal",
        filename="destatis_71311-0001_quartal.csv",
        url=DESTATIS_TABLE_URL.format(code="71311-0001"),
        description=(
            "Destatis 71311-0001: Schulden beim nicht-öffentlichen Bereich, Deutschland, "
            "Stichtag zum Quartalsende, Ebenen/Haushalte/Schuldenarten (letzte 10 Quartale)"
        ),
    ),
    Source(
        key="destatis_schulden_bundeslaender",
        filename="destatis_71311-0003_bundeslaender.csv",
        url=DESTATIS_TABLE_URL.format(code="71311-0003"),
        description=(
            "Destatis 71311-0003: Schulden beim nicht-öffentlichen Bereich, Bundesländer, "
            "Stichtag zum Quartalsende, Ebenen/Haushalte/Schuldenarten (letzte 10 Quartale)"
        ),
    ),
    Source(
        key="destatis_schulden_jahr",
        filename="destatis_71321-0005_jahr.csv",
        url=DESTATIS_TABLE_URL.format(code="71321-0005"),
        description=(
            "Destatis 71321-0005: Schulden beim nicht-öffentlichen Bereich, Deutschland, "
            "jährlich ab 31.12.2010, Ebenen/Haushalte/Schuldenarten"
        ),
    ),
    Source(
        key="eurostat_schulden_jahr",
        filename="eurostat_gov_10dd_edpt1.json",
        url=_eurostat(
            "gov_10dd_edpt1",
            format="JSON",
            lang="EN",
            geo="DE",
            na_item="GD",
            sinceTimePeriod="1995",
        ),
        description=(
            "Eurostat gov_10dd_edpt1: Maastricht-Schuldenstand, Deutschland, jährlich, "
            "Sektoren S13/S1311/S1312/S1313/S1314, Mio. EUR und % des BIP"
        ),
    ),
    Source(
        key="eurostat_schulden_quartal",
        filename="eurostat_gov_10q_ggdebt.json",
        url=_eurostat(
            "gov_10q_ggdebt",
            format="JSON",
            lang="EN",
            geo="DE",
            na_item="GD",
            sinceTimePeriod="1999",
        ),
        description=(
            "Eurostat gov_10q_ggdebt: Maastricht-Schuldenstand, Deutschland, vierteljährlich, "
            "Sektoren S13/S1311/S1312/S1313/S1314, Mio. EUR und % des BIP"
        ),
    ),
    Source(
        key="eurostat_bip",
        filename="eurostat_nama_10_gdp.json",
        url=_eurostat(
            "nama_10_gdp",
            format="JSON",
            lang="EN",
            geo="DE",
            na_item="B1GQ",
            unit="CP_MEUR",
            sinceTimePeriod="1995",
        ),
        description="Eurostat nama_10_gdp: Bruttoinlandsprodukt, Deutschland, jährlich, Mio. EUR",
    ),
    Source(
        key="eurostat_bevoelkerung",
        filename="eurostat_demo_pjan.json",
        url=_eurostat(
            "demo_pjan",
            format="JSON",
            lang="EN",
            geo="DE",
            sex="T",
            age="TOTAL",
            sinceTimePeriod="1995",
        ),
        description="Eurostat demo_pjan: Bevölkerung, Deutschland, jährlich, Stichtag 1. Januar",
    ),
)


def download(source: Source, target_dir: Path, *, refresh: bool = False) -> Path:
    """Lädt eine Quelle herunter und legt sie in ``target_dir`` ab.

    Existierende Dateien werden nur mit ``refresh=True`` erneut geladen.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.filename
    if target.exists() and not refresh:
        return target

    request = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise RuntimeError(f"Leere Antwort für {source.url}")
    target.write_bytes(payload)
    return target


def download_all(
    target_dir: Path, *, refresh: bool = False, sources: tuple[Source, ...] = SOURCES
) -> list[Path]:
    """Lädt alle Quellen und schreibt eine Metadatendatei."""
    paths = [download(source, target_dir, refresh=refresh) for source in sources]
    metadata = {
        "abgerufen_am": datetime.now(UTC).isoformat(timespec="seconds"),
        "quellen": [
            {
                "key": source.key,
                "datei": source.filename,
                "url": source.url,
                "beschreibung": source.description,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for source, path in zip(sources, paths, strict=True)
        ],
    }
    (target_dir / "_quellen.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return paths
