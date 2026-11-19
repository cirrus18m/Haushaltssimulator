"""Prüft den EMISS-API-Key für die Rosstat-Reihen."""

from __future__ import annotations

import urllib.error
import urllib.request

from haushaltssimulator import config, rosstat, sources


def main() -> int:
    present = config.get_secret("ROSSTAT_API_KEY") is not None
    print("Konfigurierte Zugangsdaten (nur Status, keine Werte):")
    print(f"  ROSSTAT_API_KEY: {'gesetzt' if present else 'fehlt'}")

    if not present:
        print()
        print(f"Bitte ROSSTAT_API_KEY in {config.ENV_FILE} eintragen")
        print("(kostenlos nach Registrierung unter https://fedstat.ru/).")
        print("Ohne Schlüssel nutzt der Datenaufbau die Preisdynamik der Bank of Russia.")
        return 1

    request = urllib.request.Request(
        sources.EMISS_URL.format(indicator=sources.ROSSTAT_CPI_INDICATOR),
        headers={
            "User-Agent": sources.USER_AGENT,
            "Accept": "text/csv",
            "X-API-KEY": config.get_secret("ROSSTAT_API_KEY") or "",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            frame = rosstat.parse_emiss_csv(response.read())
    except (urllib.error.URLError, OSError, ValueError) as error:
        print(f"\nAbfrage fehlgeschlagen: {error}")
        return 1

    if frame.empty:
        print("\nAbfrage erfolgreich, aber keine Beobachtungen erhalten.")
        return 0

    letzte = frame.iloc[-1]
    print(
        f"\nAbfrage erfolgreich: Indikator {sources.ROSSTAT_CPI_INDICATOR}, "
        f"{letzte['monat']} = {letzte['inflation_pct']:.1f} %"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
