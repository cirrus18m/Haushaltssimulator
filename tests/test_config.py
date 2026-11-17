"""Tests für die Zugangsdaten-Konfiguration."""

from __future__ import annotations

from haushaltssimulator import config


def test_placeholder_is_not_a_secret(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DESTATIS_API_TOKEN=MY_DESTATIS_TOKEN_HERE\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    assert config.get_secret("DESTATIS_API_TOKEN") is None


def test_value_is_read_from_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DESTATIS_API_TOKEN=geheim\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    assert config.get_secret("DESTATIS_API_TOKEN") == "geheim"


def test_environment_wins_over_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DESTATIS_API_TOKEN=aus-der-datei\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.setenv("DESTATIS_API_TOKEN", "aus-der-umgebung")

    assert config.get_secret("DESTATIS_API_TOKEN") == "aus-der-umgebung"


def test_token_alone_is_sufficient(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DESTATIS_API_TOKEN=token\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    credentials = config.DestatisCredentials.from_env()

    assert credentials is not None
    assert credentials.header_username == "token"
    assert credentials.header_password == ""


def test_user_requires_password(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DESTATIS_API_USER=nutzer\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("DESTATIS_API_USER", raising=False)
    monkeypatch.delenv("DESTATIS_API_PASSWORD", raising=False)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    assert config.DestatisCredentials.from_env() is None


def test_user_and_password_are_used_without_token(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DESTATIS_API_USER=nutzer\nDESTATIS_API_PASSWORD=passwort\n", encoding="utf-8"
    )
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("DESTATIS_API_USER", raising=False)
    monkeypatch.delenv("DESTATIS_API_PASSWORD", raising=False)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    credentials = config.DestatisCredentials.from_env()

    assert credentials is not None
    assert credentials.header_username == "nutzer"
    assert credentials.header_password == "passwort"


def test_secret_status_contains_only_booleans(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("DESTATIS_API_USER", raising=False)
    monkeypatch.delenv("DESTATIS_API_PASSWORD", raising=False)
    monkeypatch.delenv("DESTATIS_API_TOKEN", raising=False)

    status = config.secret_status()

    assert set(status) == set(config.KNOWN_SECRETS)
    assert all(isinstance(value, bool) for value in status.values())
