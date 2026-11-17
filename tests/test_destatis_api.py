"""Tests für den GENESIS-Online-API-Client (ohne Netzzugriff)."""

from __future__ import annotations

import io
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import pytest

from haushaltssimulator import config
from haushaltssimulator.destatis_api import DestatisApi, DestatisApiError, extract_csv


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


def _capture(monkeypatch, payload: bytes) -> dict:
    captured: dict = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = request.headers
        captured["data"] = urllib.parse.parse_qs(request.data.decode("utf-8"))
        return _FakeResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return captured


def test_login_check_sends_token_as_username_header(monkeypatch) -> None:
    captured = _capture(
        monkeypatch, b'{"Status":"Sie wurden erfolgreich an- und abgemeldet!"}'
    )
    api = DestatisApi(config.DestatisCredentials(token="geheim"))

    message = api.login_check()

    assert "erfolgreich" in message
    assert captured["url"].endswith("/helloworld/logincheck")
    assert captured["headers"]["Username"] == "geheim"
    assert captured["headers"]["Password"] == ""
    assert captured["data"]["language"] == ["de"]
    assert "password" not in captured["data"]


def test_user_and_password_headers(monkeypatch) -> None:
    captured = _capture(monkeypatch, b'{"Status":"ok"}')
    api = DestatisApi(config.DestatisCredentials(username="nutzer", password="passwort"))

    api.login_check()

    assert captured["headers"]["Username"] == "nutzer"
    assert captured["headers"]["Password"] == "passwort"


def test_login_check_raises_on_error_status(monkeypatch) -> None:
    _capture(monkeypatch, '{"Status":"Fehler: Token ungültig"}'.encode())
    api = DestatisApi(config.DestatisCredentials(token="falsch"))

    with pytest.raises(DestatisApiError, match="ungültig"):
        api.login_check()


def test_tablefile_sends_name_period_and_format(monkeypatch) -> None:
    captured = _capture(monkeypatch, b"PK-fake")
    api = DestatisApi(config.DestatisCredentials(token="geheim"))

    api.tablefile("52411-0017", startyear=2003, endyear=2026)

    assert captured["url"].endswith("/data/tablefile")
    assert captured["data"]["name"] == ["52411-0017"]
    assert captured["data"]["startyear"] == ["2003"]
    assert captured["data"]["endyear"] == ["2026"]
    assert captured["data"]["format"] == ["ffcsv"]
    assert captured["data"]["compress"] == ["false"]


def test_extract_csv_unzips_zip_payload() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("tabelle.csv", "jahr;wert\n2024;1\n")

    assert extract_csv(buffer.getvalue()) == b"jahr;wert\n2024;1\n"
    assert extract_csv(b"jahr;wert\n") == b"jahr;wert\n"


def test_client_without_credentials(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("DESTATIS_API_USER", raising=False)
    monkeypatch.delenv("DESTATIS_API_PASSWORD", raising=False)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    with pytest.raises(DestatisApiError, match="Zugangsdaten"):
        DestatisApi.from_env()


def test_error_never_contains_the_token(monkeypatch) -> None:
    def failing_urlopen(request, timeout):
        raise urllib.error.URLError("kein Netz")

    monkeypatch.setattr(urllib.request, "urlopen", failing_urlopen)
    api = DestatisApi(config.DestatisCredentials(token="streng-geheim"))

    with pytest.raises(DestatisApiError) as error:
        api.login_check()

    assert "streng-geheim" not in str(error.value)
