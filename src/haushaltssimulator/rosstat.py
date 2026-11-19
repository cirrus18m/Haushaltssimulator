"""Parser für russische Verbraucherpreisdaten (Rosstat/EMISS und Bank of Russia)."""

from __future__ import annotations

import io
import re
from typing import Any

import openpyxl
import pandas as pd

_MONAT_MUSTER = re.compile(
    r"^(?:(?P<jahr>\d{4})[-/.](?P<monat>\d{1,2})|(?P<monat2>\d{1,2})[-/.](?P<jahr2>\d{4}))"
)

# Zeile mit der Gesamtrate in der Arbeitsmappe der Bank of Russia.
_CBR_GESAMT_ZEILE = "Consumer goods and services"


def _decode(raw: bytes) -> str:
    """Dekodiert EMISS-Exporte; ältere Dateien sind in Windows-1251 kodiert."""
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("EMISS-Export lässt sich nicht dekodieren")


def _normiere_monat(wert: Any) -> str | None:
    """Wandelt gängige Periodenschreibweisen in ``YYYY-MM`` um."""
    text = str(wert).strip()
    treffer = _MONAT_MUSTER.match(text)
    if not treffer:
        return None
    jahr = treffer.group("jahr") or treffer.group("jahr2")
    monat = treffer.group("monat") or treffer.group("monat2")
    return f"{int(jahr):04d}-{int(monat):02d}"


def _finde_spalte(spalten: dict[str, str], kandidaten: tuple[str, ...]) -> str | None:
    for name, original in spalten.items():
        if any(kandidat in name for kandidat in kandidaten):
            return original
    return None


def parse_emiss_csv(raw: bytes, wert_spalte: str | None = None) -> pd.DataFrame:
    """Liest einen EMISS-Export mit Perioden- und Wertspalte.

    Die EMISS-API liefert je Indikator eine flache Tabelle. Erwartet wird eine
    Spalte mit der Periode (z. B. ``Период``) und eine Wertspalte
    (``Значение`` oder ``value``). Der Wert wird als Vorjahresrate in Prozent
    interpretiert.
    """
    text = _decode(raw)
    trenner = ";" if text.count(";") >= text.count(",") else ","
    frame = pd.read_csv(io.StringIO(text), sep=trenner, dtype=str)
    spalten = {spalte.strip().lower(): spalte for spalte in frame.columns}

    perioden_spalte = _finde_spalte(spalten, ("период", "period", "monat"))
    if perioden_spalte is None:
        raise ValueError("EMISS-Export enthält keine Periodenspalte")
    werte_spalte = _finde_spalte(spalten, (wert_spalte or "значение", "value", "wert"))
    if werte_spalte is None:
        raise ValueError("EMISS-Export enthält keine Wertspalte")

    frame = frame[[perioden_spalte, werte_spalte]].copy()
    frame.columns = ["monat", "inflation_pct"]
    frame["monat"] = frame["monat"].map(_normiere_monat)
    frame["inflation_pct"] = pd.to_numeric(
        frame["inflation_pct"].str.replace(" ", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    return (
        frame.dropna(subset=["monat", "inflation_pct"])
        .drop_duplicates(subset="monat", keep="last")
        .sort_values("monat")
        .reset_index(drop=True)
    )


def parse_cbr_cpi(raw: bytes) -> pd.DataFrame:
    """Liest die saisonbereinigten Monatsraten der Bank of Russia.

    Die Arbeitsmappe enthält Monatsraten gegenüber dem Vormonat. Daraus wird die
    über zwölf Monate verkettete Rate gebildet; sie ist eine Näherung an die
    amtliche Vorjahresrate und wird entsprechend gekennzeichnet.
    """
    workbook = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    worksheet = workbook.worksheets[0]
    zeilen = worksheet.iter_rows(values_only=True)
    kopf = next(zeilen)
    monate = [_normiere_monat(wert) for wert in kopf[1:] if wert is not None]

    gesamt = None
    for zeile in zeilen:
        if zeile and str(zeile[0]).strip() == _CBR_GESAMT_ZEILE:
            gesamt = list(zeile[1 : 1 + len(monate)])
            break
    if gesamt is None or not monate:
        raise ValueError("Arbeitsmappe der Bank of Russia enthält keine Gesamtrate")

    reihe = pd.Series(
        pd.to_numeric(gesamt, errors="coerce"),
        index=pd.PeriodIndex(pd.to_datetime([f"{monat}-01" for monat in monate]), freq="M"),
    ).dropna()
    verkettet = (1 + reihe / 100).rolling(12).apply(lambda werte: werte.prod(), raw=True)
    rate = (verkettet - 1) * 100

    return pd.DataFrame(
        {
            "monat": rate.index.strftime("%Y-%m"),
            "inflation_pct": rate.to_numpy(),
        }
    ).dropna(subset=["inflation_pct"]).reset_index(drop=True)
