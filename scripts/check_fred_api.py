"""Prüft den FRED-API-Key mit einer kleinen Abfrage."""

from __future__ import annotations

from haushaltssimulator import config
from haushaltssimulator.fred_api import FredApi, FredApiError


def main() -> int:
    present = config.get_secret("FRED_API_KEY") is not None
    print("Konfigurierte Zugangsdaten (nur Status, keine Werte):")
    print(f"  FRED_API_KEY: {'gesetzt' if present else 'fehlt'}")

    if not present:
        print()
        print(f"Bitte FRED_API_KEY in {config.ENV_FILE} eintragen")
        print("(kostenlos unter https://fredaccount.stlouisfed.org/apikeys).")
        return 1

    try:
        observations = FredApi.from_env().series_observations(
            "DGS10", limit=1, sort_order="desc"
        )
    except FredApiError as error:
        print(f"\nAbfrage fehlgeschlagen: {error}")
        return 1

    if not observations:
        print("\nAbfrage erfolgreich, aber keine Beobachtungen erhalten.")
        return 0

    letzte = observations[0]
    print(
        f"\nAbfrage erfolgreich: DGS10, {letzte.get('date', '?')} = "
        f"{letzte.get('value', '?')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
