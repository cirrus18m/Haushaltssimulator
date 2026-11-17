"""Client für die FRED-API (Federal Reserve Bank of St. Louis).

Nur für Skripte und den Datenaufbau gedacht – die Streamlit-App liest ausschließlich
``data/processed/``. Dokumentation: https://fred.stlouisfed.org/docs/api/fred/
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from . import config

BASE_URL = "https://api.stlouisfed.org/fred"
USER_AGENT = "Haushaltssimulator/0.1 (+https://github.com/cirrus18m/Haushaltssimulator)"
TIMEOUT_SECONDS = 60


class FredApiError(RuntimeError):
    """Fehler bei der Kommunikation mit der FRED-API."""


class FredApi:
    """Dünner Client für die FRED-Endpunkte, die die App später nutzen kann."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @classmethod
    def from_env(cls) -> FredApi:
        """Erzeugt den Client aus ``.env`` bzw. der Umgebung."""
        api_key = config.get_secret("FRED_API_KEY")
        if api_key is None:
            raise FredApiError(
                "Kein FRED-API-Key gefunden. Bitte FRED_API_KEY in .env eintragen "
                "(Vorlage: .env.example)."
            )
        return cls(api_key)

    def _get(self, endpoint: str, **params: object) -> dict:
        query = {
            "api_key": self._api_key,
            "file_type": "json",
            **{key: str(value) for key, value in params.items() if value is not None},
        }
        url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise FredApiError(f"HTTP {error.code} bei {endpoint}: {detail}") from error
        except urllib.error.URLError as error:
            raise FredApiError(f"Verbindungsfehler bei {endpoint}: {error.reason}") from error
        try:
            document = json.loads(payload)
        except json.JSONDecodeError as error:
            raise FredApiError(f"Ungültige JSON-Antwort von {endpoint}") from error
        if "error_message" in document:
            raise FredApiError(str(document["error_message"]))
        return document

    def series_observations(
        self,
        series_id: str,
        *,
        limit: int | None = None,
        sort_order: str | None = None,
    ) -> list[dict]:
        """Lädt Beobachtungen einer FRED-Serie (z. B. ``DGS10``)."""
        document = self._get(
            "series/observations", series_id=series_id, limit=limit, sort_order=sort_order
        )
        return list(document.get("observations", []))
