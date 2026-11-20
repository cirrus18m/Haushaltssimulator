# CLAUDE.md

Hinweise für Claude Code zur Arbeit in diesem Repository.

**Verbindlich** sind die Projektregeln in
[.github/copilot-instructions.md](.github/copilot-instructions.md) (Sprache, Diagramme,
Quellenpflicht, Datenfluss, Qualität, Zugangsdaten). Sie werden hier nicht wiederholt,
sondern nur ergänzt. Der Ausbauplan steht in [PLAN.md](PLAN.md); `TODO.md` ist lokal und
gitignoriert.

## Projekt in einem Satz

Streamlit-App (Python 3.12, `uv`, Plotly, pandas), die deutsche Staatsschulden, Haushalt,
Zinsen und Wirtschaftsindikatoren aus frei verfügbaren Quellen (Eurostat, Destatis,
Bundesbank, EZB, FRED, IWF, Bank of Russia u. a.) darstellt. Alles – UI, Doku,
Commit-Messages, Bezeichner für Fachbegriffe – ist **auf Deutsch**.

## Befehle

```bash
uv sync                                   # Umgebung inkl. Dev-Gruppe (pytest, ruff)
uv run streamlit run app/main.py          # App starten
uv run scripts/build_data.py              # Rohdaten laden (nur fehlende) + data/processed/ neu bauen
uv run scripts/build_data.py --refresh    # alle Rohdaten neu laden (neuer Zeitstempel)
uv run pytest                             # alle Tests
uv run pytest tests/test_analysis.py -k zins   # einzelne Tests
uv run ruff check . && uv run ruff format .
uv run scripts/check_destatis_api.py      # API-Zugang prüfen (zeigt nur Status, nie Werte)
uv run scripts/check_fred_api.py
```

Vor jedem Commit: `uv run ruff check .` und `uv run pytest`.

## Architektur

Datenfluss (Details in den Projektregeln, Abschnitt 4):

```
sources.py  ──download_all──▶ data/raw/ (+ data/sources.json)
build.py    ──BUILDERS──────▶ data/processed/*.csv   (versioniert)
dataset.py  ──load_*────────▶ ui.py (st.cache_data-Wrapper) ──▶ app/pages/*.py
```

Paket `src/haushaltssimulator/`:

| Modul | Rolle |
| --- | --- |
| `sources.py` | `Source`-Dataclass und Tupel `SOURCES` (alle Quellen mit Lizenz, URL, `fetch_mode`), `PROVIDER_LINKS` für die Quellenseite, Download und Fortschreibung von `data/sources.json` (SHA-256, Abrufzeit). Größte Datei. |
| `build.py` | Je Ausgabedatei eine `build_*(raw_dir)`-Funktion; registriert im Dict `BUILDERS` (Dateiname → Funktion), Nachkommastellen in `FLOAT_FORMATS` (Standard `%.1f`). `main()` = Einstieg von `scripts/build_data.py`. |
| `destatis.py`, `eurostat.py`, `bundesbank.py`, `fred.py`, `cbr.py`, `ecb.py`, `imf.py`, `oil.py`, `bigmac.py`, `bmf.py`, `rosstat.py`, `weltbank.py` | Reine Parser je Quelle: Bytes/Dateien → DataFrame, ohne Netzwerk, ohne Streamlit. |
| `destatis_api.py`, `fred_api.py`, `config.py` | API-Clients und Zugangsdaten (`.env`, `KNOWN_SECRETS`, Platzhalter `MY_…_HERE` gilt als „nicht gesetzt“). Nur für Skripte/Datenaufbau. |
| `analysis.py` | Berechnungen (Wachstumsraten, CAGR, Trends, Zinslast …), ohne Streamlit testbar. |
| `laender.py` | Länderlisten/-namen für den europäischen Vergleich (`EUROPA_LAENDER`). |
| `dataset.py` | Dateinamen-Konstanten der Processed-CSVs, `DATASET_LABELS`, `load_*`-Funktionen (parsen Datumsspalten `stichtag`, `quartalsende`, `datum`). |
| `ui.py` | Gecachte Lader für die Seiten, Farbpaletten (`EBENE_COLORS`, `CHART_COLORS`), deutsche Zahlenformatierung (`format_number`, `format_mrd`, `format_eur`, `format_month`), `style()` und `plot()`. |
| `paths.py` | `PROJECT_ROOT`, `RAW_DIR`, `PROCESSED_DIR`, `SOURCES_FILE`. |

App: `app/main.py` definiert die Navigation explizit mit `st.Page(...)`; die Nummern in
den Dateinamen unter `app/pages/` bestimmen **nicht** die Reihenfolge. Seiten enthalten
nur Laden, Filtern, Darstellen – Fachlogik gehört nach `analysis.py` oder `build.py`.

## Rezepte

**Neue Datenreihe**
1. `Source(...)` in `sources.SOURCES` ergänzen (Titel, Herausgeber, Lizenz, Datensätze).
   Neuer Anbieter → auch `PROVIDER_LINKS`. Manueller Export → Datei nach
   `data/raw/manual/`, `fetch_mode="manual"`.
2. Parser im passenden Quellmodul (rein, testbar).
3. `build_*`-Funktion in `build.py`, Eintrag in `BUILDERS` und ggf. `FLOAT_FORMATS`.
4. Dateinamen-Konstante, `DATASET_LABELS`-Eintrag und `load_*` in `dataset.py`;
   gecachter Wrapper in `ui.py`.
5. `uv run scripts/build_data.py` ausführen und die geänderten `data/processed/*.csv`
   **und** `data/sources.json` mit committen. `sources.json` nie von Hand bearbeiten.
6. Tests in `tests/` (Parser/Analyse) und ggf. Plausibilitätstest in `tests/test_app.py`.

**Neue Seite**
1. Datei unter `app/pages/` anlegen, in `app/main.py` als `st.Page` eintragen.
2. In die Parametrisierung von `test_streamlit_pages_run_without_exception` in
   `tests/test_app.py` aufnehmen.
3. README-Tabelle „Seiten der App“ ergänzen.

**Diagramme**: immer `ui.plot(fig, filename="…")` (eindeutiger `filename`, er wird auch
als Widget-Key der Download-Buttons genutzt), nie `st.plotly_chart` direkt. Titel,
Achsen mit Einheit und Quellen-Caption gehören dazu.

## Stolpersteine

* **Streamlit-Neustart nötig** nach Änderungen in `src/haushaltssimulator/`: beim Rerun
  bleiben importierte Module im Speicher, neue Funktionen fehlen sonst
  (`AttributeError: module 'haushaltssimulator.ui' has no attribute …`). Außerdem
  cacht `ui.py` die Daten per `st.cache_data`.
* **Langsame Seitentests**: `AppTest` rendert jedes Diagramm auch als SVG (Kaleido),
  Timeout 180 s pro Seite. Für schnelle Iteration gezielt einzelne Testdateien laufen
  lassen. Fehlt Kaleido/Chrome, liefert `ui._svg_bytes` `None` und die App zeigt einen
  Hinweis statt des SVG-Buttons.
* `tests/test_app.py` wird übersprungen, wenn `data/processed/` fehlt.
* `test_app_does_not_import_api_clients` schlägt fehl, sobald eine Datei unter `app/`
  `destatis_api` oder `urllib.request` enthält.
* `data/raw/*` ist gitignoriert (Ausnahme `data/raw/manual/`). Ein Datenaufbau ohne
  Netz funktioniert nur mit bereits vorhandenen Rohdaten; manuelle Quellen ohne Datei
  brechen mit `RuntimeError` ab.
* Ohne `FRED_API_KEY` fällt `fetch_mode="fred_api"` auf den öffentlichen CSV-Export
  zurück; die App selbst braucht keine Schlüssel. `.env` nie committen oder ausgeben.
* Abgrenzungen nicht vermischen: Maastricht-Schulden (Eurostat) ≠ Schulden beim
  nicht-öffentlichen Bereich (Destatis); Zinsausgaben ≠ theoretische Zinslast;
  Bundeshaushalt (Kernhaushalt) ≠ Gesamtstaat (VGR). Siehe README „Abgrenzungen“.
* Spaltennamen tragen die Einheit (`_mio_eur`, `_mrd_eur`, `_pct`, `_eur_kwh` …);
  Quell-Codes wie `geo`, `S13`, `TR` bleiben unverändert.

## Deployment

Streamlit Community Cloud mit `app/main.py`, `uv.lock`, Python 3.12
(`.python-version`), Theme in `.streamlit/config.toml`. Keine Secrets nötig, weil die
Daten als CSV im Repo liegen.
