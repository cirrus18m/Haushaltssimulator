"""Tests für den GENESIS-Online-API-Client (ohne Netzzugriff)."""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

import pytest

from haushaltssimulator import config
from haushaltssimulator.destatis_api import DestatisApi, DestatisApiError


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _capture(monkeypatch, payload: bytes) -> dict:
    captured: dict = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["data"] = urllib.parse.parse_qs(request.data.decode("utf-8"))
        return _FakeResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return captured


def test_login_check_posts_credentials(monkeypatch) -> None:
    captured = _capture(monkeypatch, b"Nutzerkennung und Passwort sind korrekt.")
    api = DestatisApi(config.DestatisCredentials(username="nutzer", token="geheim"))

    message = api.login_check()

    assert "korrekt" in message
    assert captured["url"].endswith("/login/check")
    assert captured["data"]["username"] == ["nutzer"]
    assert captured["data"]["password"] == ["geheim"]


def test_login_check_raises_on_error_message(monkeypatch) -> None:
    _capture(monkeypatch, "Fehler: Passwort ist ungültig".encode())
    api = DestatisApi(config.DestatisCredentials(username="nutzer", token="falsch"))

    with pytest.raises(DestatisApiError, match="ungültig"):
        api.login_check()


def test_tablefile_sends_name_and_period(monkeypatch) -> None:
    captured = _capture(monkeypatch, b"jahr;wert\n2024;1\n")
    api = DestatisApi(config.DestatisCredentials(username="nutzer", token="geheim"))

    payload = api.tablefile("52411-0017", startyear=2003, endyear=2026)

    assert payload.startswith(b"jahr")
    assert captured["url"].endswith("/data/tablefile")
    assert captured["data"]["name"] == ["52411-0017"]
    assert captured["data"]["startyear"] == ["2003"]
    assert captured["data"]["endyear"] == ["2026"]
    assert captured["data"]["compress"] == ["false"]


def test_client_without_credentials(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("DESTATIS_API_USER", raising=False)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    with pytest.raises(DestatisApiError, match="Zugangsdaten"):
        DestatisApi.from_env()


def test_error_never_contains_the_token(monkeypatch) -> None:
    def failing_urlopen(request, timeout):
        raise urllib.error.URLError("kein Netz")

    monkeypatch.setattr(urllib.request, "urlopen", failing_urlopen)
    api = DestatisApi(config.DestatisCredentials(username="nutzer", token="streng-geheim"))

    with pytest.raises(DestatisApiError) as error:
        api.login_check()

    assert "streng-geheim" not in str(error.value)
