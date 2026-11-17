"""Client für die GENESIS-Online-REST-API der Statistischen Ämter.

Dieses Modul ist **nicht** für die Streamlit-App gedacht. Die App liest
ausschließlich aufbereitete Tabellen aus ``data/processed/``. Der Client wird nur
von Skripten und dem Datenaufbau genutzt:

    API → ``data/raw/`` → ``build.py`` → ``data/processed/`` → App

Die Zugangsdaten stehen laut API-Handbuch in den HTTP-Headern ``username`` und
``password``. Ein API-Token wird als ``username`` mit leerem Passwort gesendet.
Die Endpunkte sind ``helloworld/logincheck``, ``data/tablefile`` und
``data/cubefile``; CSV-Antworten kommen als ZIP mit genau einer CSV-Datei.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from . import config

BASE_URL = "https://genesis.destatis.de/genesisWS/rest/2020"
USER_AGENT = "Haushaltssimulator/0.1 (+https://github.com/cirrus18m/Haushaltssimulator)"
TIMEOUT_SECONDS = 120


class DestatisApiError(RuntimeError):
    """Fehler bei der Kommunikation mit der GENESIS-Online-API."""


def _format_form_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def extract_csv(payload: bytes) -> bytes:
    """Entpackt eine CSV-Antwort; CSV und ffcsv liefert GENESIS als ZIP."""
    if payload[:2] != b"PK":
        return payload
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if not names:
            raise DestatisApiError("ZIP-Antwort enthält keine Datei")
        return archive.read(names[0])


class DestatisApi:
    """Dünner Client für die GENESIS-Endpunkte, die der Datenaufbau benötigt."""

    def __init__(self, credentials: config.DestatisCredentials) -> None:
        self._credentials = credentials

    @classmethod
    def from_env(cls) -> DestatisApi:
        """Erzeugt den Client aus ``.env`` bzw. der Umgebung."""
        credentials = config.DestatisCredentials.from_env()
        if credentials is None:
            raise DestatisApiError(
                "Keine Destatis-Zugangsdaten gefunden. Bitte DESTATIS_API_TOKEN oder "
                "DESTATIS_API_USER/DESTATIS_API_PASSWORD in .env eintragen "
                "(Vorlage: .env.example)."
            )
        return cls(credentials)

    def _post(self, endpoint: str, **params: object) -> bytes:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "username": self._credentials.header_username,
            "password": self._credentials.header_password,
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        }
        data = {
            "language": "de",
            **{
                key: _format_form_value(value)
                for key, value in params.items()
                if value is not None
            },
        }
        request = urllib.request.Request(
            f"{BASE_URL}/{endpoint}",
            data=urllib.parse.urlencode(data).encode("utf-8"),
            headers=headers,
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
        """Prüft die Zugangsdaten über ``helloworld/logincheck``."""
        text = self._post("helloworld/logincheck").decode("utf-8", errors="replace").strip()
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            document = {}
        status = str(document.get("Status", text))
        if "fehler" in status.lower():
            raise DestatisApiError(status)
        return status

    def tablefile(
        self,
        name: str,
        *,
        startyear: int | None = None,
        endyear: int | None = None,
        format: str = "ffcsv",
        compress: bool = False,
    ) -> bytes:
        """Lädt eine Tabelle; ``ffcsv`` wird für die Weiterverarbeitung empfohlen."""
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
        format: str | None = None,
        compress: bool | None = None,
    ) -> bytes:
        """Lädt einen Cube als Datei."""
        return self._post(
            "data/cubefile",
            name=name,
            startyear=startyear,
            endyear=endyear,
            format=format,
            compress=compress,
        )
