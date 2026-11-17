# Projektregeln für KI-gestützte Mitarbeit

Dieses Repository ist der **Haushaltssimulator**: eine Streamlit-App, die
Staatsschulden, Haushaltsdaten und Zinsen mit frei verfügbaren Daten visualisiert.
Die folgenden Regeln gelten verbindlich für alle Änderungen, unabhängig davon, ob sie
von Menschen oder von KI-Assistenten vorgenommen werden.

## 1. Sprache

* Die gesamte Anwendung, alle Diagramme, Tabellen, Beschriftungen, Captions und
  Dokumentationen sind **auf Deutsch**.
* Fachbegriffe der Datenquellen (z. B. `na_item`, `geo`, `S1311`) bleiben unverändert.
* Variablen- und Spaltennamen folgen der bestehenden Konvention: deutsche
  Fachbegriffe mit Einheit, z. B. `schulden_mio_eur`, `zinsausgaben_mio_eur`,
  `rendite_pct`.
* Zahlen werden deutsch formatiert (Tausenderpunkt, Dezimalkomma). Dafür sind
  `ui.format_number`, `ui.format_mrd` und `ui.format_eur` zu verwenden.
* Einheiten gehören in den Spaltennamen (`_mio_eur`, `_mrd_eur`, `_pct`) oder in die
  Achsenbeschriftung – nicht in den nackten Wert.

## 2. Diagramme: immer SVG und HTML

* Jedes Diagramm wird über `haushaltssimulator.ui.plot()` gerendert, nie direkt über
  `st.plotly_chart`.
* `ui.plot()` stellt für jede Grafik einen **SVG-Download** und einen
  **HTML-Download** bereit. Neue Diagramme, die diesen Weg umgehen, gelten als
  unvollständig.
* Ein Diagramm ohne Titel, Achsenbeschriftung, Einheit und Quellenangabe ist nicht
  fertig.
* Farben und Layout kommen aus `ui.style()` bzw. den dort definierten Paletten, damit
  die App einheitlich bleibt.

## 3. Quellen: lückenlos und nachvollziehbar

* Jede Kennzahl, jede Tabelle und jedes Diagramm nennt ihre Quelle in einer Caption
  oder in einem Quellenabschnitt.
* Keine Daten „aus dem Kopf“ oder aus nicht dokumentierten Webseiten übernehmen.
  Jede neue Datenreihe braucht einen Eintrag in der Quellenbibliothek.
* Die **Quellenbibliothek** `data/sources.json` ist Teil des Repositories. Sie wird
  ausschließlich über `haushaltssimulator.sources` erzeugt und fortgeschrieben –
  niemals manuell bearbeitet.
* Je Quelle sind mindestens zu erfassen: Schlüssel, Titel, Herausgeber, Lizenz, URL,
  Beschreibung, verwendete Datensätze, Dateiname, SHA-256, Größe und **Zeitpunkt des
  Downloads**.
* Der Downloadzeitpunkt wird beim Abruf gesetzt und bei bereits vorhandenen Dateien
  beibehalten. Er wird auf der Seite **Quellen** angezeigt.
* Rohdaten liegen in `data/raw/` (nicht versioniert), aufbereitete Daten in
  `data/processed/` (versioniert). Aufbereitete Daten werden ausschließlich aus
  Rohdaten erzeugt (`uv run scripts/build_data.py`), nie von Hand gepflegt.
* Lizenzangaben der Quellen (z. B. DL-DE-BY-2.0, CC BY 4.0) müssen in der
  Quellenbibliothek und auf der Quellenseite erscheinen.

## 4. Aufbau und Datenfluss

```
data/raw/          Rohdaten, unverändert, mit Zeitstempel in data/sources.json
      │  sources.py   (Download, Metadaten, Prüfsummen)
      ▼
src/haushaltssimulator/build.py   (Parser → tidy DataFrames)
      │
      ▼
data/processed/    aufbereitete CSVs, versioniert
      │  dataset.py   (Laden, Typprüfung)
      ▼
app/pages/        Streamlit-Seiten, nur Darstellung
```

* Parser je Quelle in einem eigenen Modul (`destatis.py`, `eurostat.py`,
  `bundesbank.py`, `fred.py`, `cbr.py`). Parser sind reine Funktionen ohne Netzwerk-
  zugriff und ohne Streamlit-Abhängigkeit.
* Zugangsdaten liest `config.py`; API-Clients (z. B. `destatis_api.py`) werden nur von
  Skripten und `build.py` verwendet, nie von der App.
* Berechnungen gehören nach `analysis.py` und müssen ohne Streamlit testbar sein.
* Die Streamlit-Seiten enthalten keine Fachlogik: laden, filtern, darstellen.

## 5. Qualität

* Python 3.12, `ruff` mit `E`, `F`, `I`, `UP`, `B` und Zeilenlänge 100.
* Neue Fachlogik erhält Tests in `tests/`. Neue Seiten werden in die
  Seiten-Parametrisierung von `tests/test_app.py` aufgenommen.
* Vor dem Commit: `uv run ruff check .` und `uv run pytest`.
* Änderungen an Datenquellen erfordern einen erneuten Datenaufbau, damit
  `data/processed/` und `data/sources.json` zum Code passen.

## 6. Inhalte und Genauigkeit

* Zwischen **Schuldenstand** (Bestand), **Zinsausgaben** (tatsächlich gebucht) und
  **theoretischer Zinslast** (Schuldenstand × aktuelle Marktrendite) klar
  unterscheiden. Die theoretische Zinslast ist eine Modellrechnung und wird als
  solche gekennzeichnet.
* „Einnahmen ohne neue Schulden“ sind die Gesamteinnahmen der Volkswirtschaftlichen
  Gesamtrechnung (Eurostat `TR`); Kreditaufnahme ist dort keine Einnahme.
* Zeitreihenvergleiche nur mit übereinstimmender Frequenz, Einheit und Abgrenzung.
  Abweichungen (z. B. Monatsendwerte statt Tagesdurchschnitte) dokumentieren.
* Keine Prognosen als Fakten darstellen; Szenarien bleiben als Szenarien erkennbar.

## 7. Zugangsdaten und Sicherheit

* Zugangsdaten ausschließlich in `.env` oder in Umgebungsvariablen. `.env` ist
  gitignoriert; `.env.example` enthält nur Platzhalter der Form `MY_..._HERE`.
* Neue Quellen: Schlüsselnamen in `config.KNOWN_SECRETS` ergänzen, ein eigenes
  Client-Modul anlegen und ein Prüfskript unter `scripts/` bereitstellen.
* Die Streamlit-App liest ausschließlich `data/processed/` und importiert keine
  API-Clients. API-Aufrufe gehören in den Datenaufbau
  (API → `data/raw/` → `build.py` → `data/processed/`).
* Keine Zugangsdaten, API-Schlüssel oder personenbezogenen Daten im Repository.
* Nur frei lizenzierte, öffentlich zugängliche Quellen anbinden.
