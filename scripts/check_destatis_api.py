"""Prüft die Destatis-Zugangsdaten gegen die GENESIS-Online-API."""

from __future__ import annotations

from haushaltssimulator import config
from haushaltssimulator.destatis_api import DestatisApi, DestatisApiError


def main() -> int:
    status = config.secret_status()
    print("Konfigurierte Zugangsdaten (nur Status, keine Werte):")
    for name in ("DESTATIS_API_TOKEN", "DESTATIS_API_USER", "DESTATIS_API_PASSWORD"):
        print(f"  {name}: {'gesetzt' if status[name] else 'fehlt'}")

    if config.DestatisCredentials.from_env() is None:
        print()
        print(f"Bitte die Platzhalter in {config.ENV_FILE} ersetzen")
        print("(Datei bei Bedarf aus .env.example anlegen):")
        print("  DESTATIS_API_TOKEN=MY_DESTATIS_TOKEN_HERE")
        print("  optional: DESTATIS_API_USER / DESTATIS_API_PASSWORD")
        return 1

    try:
        message = DestatisApi.from_env().login_check()
    except DestatisApiError as error:
        print(f"\nAnmeldung fehlgeschlagen: {error}")
        return 1

    print(f"\nAnmeldung erfolgreich: {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
