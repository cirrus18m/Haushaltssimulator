"""Parser für Eurostat-JSON-stat-Antworten."""

from __future__ import annotations

from typing import Any

import pandas as pd


def jsonstat_to_frame(document: dict[str, Any]) -> pd.DataFrame:
    """Wandelt ein JSON-stat-2-Dokument in einen tidy DataFrame um.

    Das Ergebnis enthält für jede Dimension eine Spalte mit den Codes sowie
    ``value`` als Messwert.
    """
    dimension_ids: list[str] = document["id"]
    sizes: list[int] = document["size"]

    strides: dict[str, int] = {}
    stride = 1
    for dimension, size in zip(reversed(dimension_ids), reversed(sizes), strict=True):
        strides[dimension] = stride
        stride *= size

    codes: dict[str, list[str]] = {}
    for dimension in dimension_ids:
        index = document["dimension"][dimension]["category"]["index"]
        ordered = sorted(index, key=index.__getitem__)
        if len(ordered) != sizes[dimension_ids.index(dimension)]:
            raise ValueError(f"Dimensionsgröße für {dimension} passt nicht zur Kategorienliste")
        codes[dimension] = ordered

    records = []
    for flat_index, value in document["value"].items():
        position = [0] * len(dimension_ids)
        for dimension_index, dimension in enumerate(dimension_ids):
            position[dimension_index] = (int(flat_index) // strides[dimension]) % sizes[
                dimension_index
            ]
        record: dict[str, Any] = {
            dimension: codes[dimension][position[index]]
            for index, dimension in enumerate(dimension_ids)
        }
        record["value"] = value
        records.append(record)

    frame = pd.DataFrame.from_records(records)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


def dimension_labels(document: dict[str, Any], dimension: str) -> dict[str, str]:
    """Liefert die Klartextbezeichnungen einer Dimension."""
    labels = document["dimension"][dimension]["category"].get("label", {})
    return dict(labels)
