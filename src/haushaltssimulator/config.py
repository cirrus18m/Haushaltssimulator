"""Zentrale Konfiguration für Zugangsdaten zu Datenquellen-APIs.

Werte werden ausschließlich aus der Umgebung oder aus der nicht versionierten
``.env``-Datei gelesen. Die Streamlit-App nutzt diese Werte nicht: Sie liest
ausschließlich aufbereitete Tabellen aus ``data/processed/``. Zugangsdaten werden
nur von Skripten und dem Datenaufbau verwendet.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .paths import PROJECT_ROOT

ENV_FILE = PROJECT_ROOT / ".env"
PLACEHOLDER_PREFIX = "MY_"
KNOWN_SECRETS = ("DESTATIS_API_USER", "DESTATIS_API_TOKEN")


def load_environment() -> None:
    """Lädt ``.env``, ohne bereits gesetzte Umgebungsvariablen zu überschreiben."""
    load_dotenv(ENV_FILE, override=False)


def get_secret(name: str) -> str | None:
    """Liest einen Wert; Platzhalter aus ``.env.example`` gelten als nicht gesetzt."""
    load_environment()
    value = os.environ.get(name, "").strip()
    if not value or value.startswith(PLACEHOLDER_PREFIX):
        return None
    return value


def secret_status() -> dict[str, bool]:
    """Status der bekannten Zugangsdaten – nur Namen, niemals Werte."""
    return {name: get_secret(name) is not None for name in KNOWN_SECRETS}


@dataclass(frozen=True)
class DestatisCredentials:
    """Zugangsdaten für die GENESIS-Online-REST-API."""

    username: str
    token: str

    @classmethod
    def from_env(cls) -> DestatisCredentials | None:
        """Liest die Zugangsdaten; fehlt einer der Werte, wird ``None`` geliefert."""
        username = get_secret("DESTATIS_API_USER")
        token = get_secret("DESTATIS_API_TOKEN")
        if username is None or token is None:
            return None
        return cls(username=username, token=token)
