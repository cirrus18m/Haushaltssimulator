"""Tests für die Quellenbibliothek und die daraus abgeleiteten Datensätze."""

from __future__ import annotations

import pytest

from haushaltssimulator import dataset, paths, sources


def test_library_lists_all_configured_sources() -> None:
    entries = sources.read_library()["quellen"]
    keys = {entry["key"] for entry in entries}
    assert keys == {source.key for source in sources.SOURCES}


def test_library_documents_every_processed_dataset() -> None:
    entries = sources.read_library()["quellen"]
    documented = {name for entry in entries for name in entry["datensaetze"]}
    assert set(dataset.DATASET_LABELS) <= documented


def test_library_entries_are_complete() -> None:
    for entry in sources.read_library()["quellen"]:
        assert entry["titel"]
        assert entry["herausgeber"]
        assert entry["lizenz"]
        assert entry["url"].startswith("https://")
        assert entry["abgerufen_am"]
        assert len(entry["sha256"]) == 64
        assert entry["bytes"] > 0


def test_every_processed_file_from_the_library_exists() -> None:
    for filename in dataset.DATASET_LABELS:
        assert (paths.PROCESSED_DIR / filename).exists(), filename


def test_manual_source_requires_existing_file(tmp_path) -> None:
    source = sources.Source(
        key="manuell",
        filename="manuell.csv",
        url="https://example.org/tabelle",
        description="Test",
        title="Test",
        publisher="Test",
        license="Test",
        datasets=("manuell.csv",),
        fetch_mode="manual",
    )
    with pytest.raises(RuntimeError, match="manuell.csv"):
        sources.download(source, tmp_path)


def test_retrieved_timestamp_survives_without_new_download(tmp_path) -> None:
    library_file = tmp_path / "sources.json"
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    source = sources.Source(
        key="test",
        filename="test.csv",
        url="https://example.org/test.csv",
        description="Test",
        title="Test",
        publisher="Test",
        license="Test",
        datasets=("test.csv",),
    )
    (raw_dir / "test.csv").write_text("a\n1\n", encoding="utf-8")
    first = sources.download_all(
        raw_dir, sources=(source,), library_file=library_file
    )
    assert first[0].exists()
    stamp = sources.read_library(library_file)["quellen"][0]["abgerufen_am"]

    sources.download_all(raw_dir, sources=(source,), library_file=library_file)
    again = sources.read_library(library_file)["quellen"][0]["abgerufen_am"]
    assert again == stamp
