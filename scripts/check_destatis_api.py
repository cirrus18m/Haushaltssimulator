"""Prüft die Destatis-Zugangsdaten gegen die GENESIS-Online-API."""

from __future__ import annotations

from haushaltssimulator import config
from haushaltssimulator.destatis_api import DestatisApi, DestatisApiError


def main() -> int:
    status = config.secret_status()
    print("Konfigurierte Zugangsdaten (nur Status, keine Werte):")
    for name, present in status.items():
        print(f"  {name}: {'gesetzt' if present else 'fehlt'}")

    if not all(status.values()):
        print()
        print(f"Bitte die Platzhalter in {config.ENV_FILE} ersetzen")
        print("(Datei bei Bedarf aus .env.example anlegen):")
        print("  DESTATIS_API_USER=MY_DESTATIS_USER_HERE")
        print("  DESTATIS_API_TOKEN=MY_DESTATIS_TOKEN_HERE")
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
