"""Tests für den FRED-API-Client (ohne Netzzugriff)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

import pytest

from haushaltssimulator import config
from haushaltssimulator.fred_api import FredApi, FredApiError


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def close(self) -> None:
        return None


def test_series_observations_parses_payload(monkeypatch) -> None:
    captured: dict = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        payload = {"observations": [{"date": "2026-10-01", "value": "4.5"}]}
        return _FakeResponse(json.dumps(payload).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    observations = FredApi("geheim").series_observations("DGS10", limit=1, sort_order="desc")

    assert observations[0]["date"] == "2026-10-01"
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(captured["url"]).query)
    assert query["api_key"] == ["geheim"]
    assert query["series_id"] == ["DGS10"]
    assert query["limit"] == ["1"]
    assert query["file_type"] == ["json"]
    assert captured["url"].startswith("https://api.stlouisfed.org/fred/series/observations")


def test_error_message_from_fred_is_raised(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return _FakeResponse(json.dumps({"error_message": "Bad Request"}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(FredApiError, match="Bad Request"):
        FredApi("geheim").series_observations("DGS10")


def test_client_without_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(FredApiError, match="FRED_API_KEY"):
        FredApi.from_env()


def test_http_error_does_not_contain_key(monkeypatch) -> None:
    def failing_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, 400, "Bad Request", {}, _FakeResponse(b'{"error":"x"}')
        )

    monkeypatch.setattr(urllib.request, "urlopen", failing_urlopen)

    with pytest.raises(FredApiError) as error:
        FredApi("streng-geheim").series_observations("DGS10")

    assert "streng-geheim" not in str(error.value)
