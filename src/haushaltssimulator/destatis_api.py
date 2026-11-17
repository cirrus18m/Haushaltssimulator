"""Client für die GENESIS-Online-REST-API der Statistischen Ämter.

Dieses Modul ist **nicht** für die Streamlit-App gedacht. Die App liest
ausschließlich aufbereitete Tabellen aus ``data/processed/``. Der Client wird nur
von Skripten und dem Datenaufbau genutzt:

    API → ``data/raw/`` → ``build.py`` → ``data/processed/`` → App

Neue Quellen werden nach demselben Muster angebunden: Zugangsdaten in
``config.KNOWN_SECRETS`` ergänzen, einen Client in einem eigenen Modul anlegen und
die Rohantwort im Datenaufbau ablegen. Die App bleibt ohne Netzzugriff.
"""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request

from . import config

BASE_URL = "https://www-genesis.destatis.de/genesisWS/rest/2020"
USER_AGENT = "Haushaltssimulator/0.1 (+https://github.com/cirrus18m/Haushaltssimulator)"
TIMEOUT_SECONDS = 120


class DestatisApiError(RuntimeError):
    """Fehler bei der Kommunikation mit der GENESIS-Online-API."""


def _format_form_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class DestatisApi:
    """Dünner Client für ``login/check``, ``data/tablefile`` und ``data/cubefile``."""

    def __init__(self, credentials: config.DestatisCredentials) -> None:
        self._credentials = credentials

    @classmethod
    def from_env(cls) -> DestatisApi:
        """Erzeugt den Client aus ``.env`` bzw. der Umgebung."""
        credentials = config.DestatisCredentials.from_env()
        if credentials is None:
            raise DestatisApiError(
                "Keine Destatis-Zugangsdaten gefunden. Bitte DESTATIS_API_USER und "
                "DESTATIS_API_TOKEN in .env eintragen (Vorlage: .env.example)."
            )
        return cls(credentials)

    def _post(self, endpoint: str, **params: object) -> bytes:
        form = {
            "username": self._credentials.username,
            "password": self._credentials.token,
            "language": "de",
            **{
                key: _format_form_value(value)
                for key, value in params.items()
                if value is not None
            },
        }
        request = urllib.request.Request(
            f"{BASE_URL}/{endpoint}",
            data=urllib.parse.urlencode(form).encode("utf-8"),
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            raise DestatisApiError(f"HTTP {error.code} bei {endpoint}") from error
        except urllib.error.URLError as error:
            raise DestatisApiError(f"Verbindungsfehler bei {endpoint}: {error.reason}") from error
        if not payload:
            raise DestatisApiError(f"Leere Antwort von {endpoint}")
        return payload

    def login_check(self) -> str:
        """Prüft Nutzerkennung und Token. Gibt die Antwort von Destatis zurück."""
        text = self._post("login/check").decode("utf-8", errors="replace").strip()
        lowered = text.lower()
        if "fehler" in lowered or "ungültig" in lowered or "falsch" in lowered:
            raise DestatisApiError(text)
        return text

    def tablefile(
        self,
        name: str,
        *,
        startyear: int | None = None,
        endyear: int | None = None,
        format: str = "csv",
        compress: bool = False,
    ) -> bytes:
        """Lädt eine Tabelle als Datei.

        ``name`` ist die Tabellenkennung (z. B. ``52411-0017``). Die Antwort wird
        unverändert zurückgegeben und im Datenaufbau unter ``data/raw/`` abgelegt.
        """
        return self._post(
            "data/tablefile",
            name=name,
            startyear=startyear,
            endyear=endyear,
            format=format,
            compress=compress,
        )

    def cubefile(
        self,
        name: str,
        *,
        startyear: int | None = None,
        endyear: int | None = None,
        format: str = "csv",
        compress: bool = False,
    ) -> bytes:
        """Lädt einen Cube als Datei (gleiche Rückgabe wie :meth:`tablefile`)."""
        return self._post(
            "data/cubefile",
            name=name,
            startyear=startyear,
            endyear=endyear,
            format=format,
            compress=compress,
        )
