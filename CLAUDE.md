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
Bundesbank, EZB, FRED, IWF, Bank of Russia u. a.) darstellt. Die **Website ist
deutsch**, der **Code englisch** (siehe „Sprache“).

## Sprache

* **Deutsch** ist alles, was Nutzerinnen und Nutzer sehen: Seitentitel, Texte,
  Diagrammtitel, Achsen, Legenden, Hover, Captions, Tabellenköpfe, Fehlermeldungen in
  der App, Foliensätze. Ebenso Doku (README, `docs/`, diese Datei) und Commit-Messages.
* **Englisch** ist der Code: Modul-, Klassen-, Funktions-, Variablen- und
  Konstantennamen, Parameter, Kommentare, Docstrings, Test-Namen und Dateinamen
  (`federal_core_budget_svr.csv`). Also `class Block`, nicht `class Baustein`;
  `charts.core_budget()`, nicht `diagramme.kernhaushalt()`.
* **Spaltennamen der Datensätze** bleiben so, wie die **Quelle** sie liefert (SVR-Reihe
  „Ausgaben für Soziale Sicherung, Verteidigung und Zinsen Zinsen“, `geo`, `na_item`),
  oder so, wie die **App sie zeigt**, wenn ein Datensatz als Tabelle eingeblendet wird.
  Sie werden nicht ins Englische übersetzt. Der Code greift über Konstanten in
  `dataset.py` darauf zu (`dataset.CORE_BUDGET_INTEREST`), nicht über verstreute
  Zeichenketten. Selbst gebildete Spalten tragen die Einheit im Namen (`_mio_eur`,
  `_pct`); bei Quellnamen steht die Einheit in `DATASET_LABELS` und `data/README.md`.
* **Ausnahmen vom englischen Code:** Namen von App-Seiten
  (`app/pages/6_Haushalt_und_Zinsen.py` – sie bilden die URL), Codes und Feldnamen der
  Quellen (`geo`, `S1311`, `na_item`) sowie deutsche Rechts- und Haushaltsbegriffe ohne
  genaue englische Entsprechung (`einzelplan`, `behg`, `maastricht`).
* **Erweiterbar auf Deutsch:** Auch Menschen ohne Englischkenntnisse sollen die Website
  mit Claude auf Deutsch erweitern können. Darum:
  * Claude antwortet, plant und erklärt auf Deutsch – auch englische Bezeichner,
    Fehlermeldungen und Testausgaben – und fragt nach, statt englische Fachbegriffe
    vorauszusetzen.
  * Aufträge in deutscher Sprache genügen, etwa „Füge Abbildung 12 aus dem
    SVR-Gutachten auf der Seite Haushalt und Zinsen hinzu“. Claude findet die Stelle über
    die sichtbaren deutschen Texte: Titel, Achsen und Captions stehen als Zeichenketten
    im Code (`charts.CORE_BUDGET_TITLE`), eine Suche nach dem Text auf der Website führt
    zur Funktion.
  * Die Rezepte in dieser Datei und die Doku bleiben deutsch und beschreiben Aufgaben
    in den Worten der Website („neue Datenreihe“, „neue Seite“).
  * Bausteine tragen deutsche Titel, Kernaussagen und Erklärungen; nur ihre Namen im Code
    sind englisch.
* **Bestand:** Viele ältere Bezeichner sind noch deutsch (`bausteine/`, `ZEITMARKEN`).
  Neuer Code ist englisch; ein Modul wird beim größeren Umbau insgesamt umgestellt,
  nicht Zeile für Zeile. Umbenennungen von Spalten in `data/processed/` ändern die
  Datenschnittstelle und brauchen Tests und Rücksprache.

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
| `destatis.py`, `eurostat.py`, `bundesbank.py`, `fred.py`, `cbr.py`, `ecb.py`, `imf.py`, `oil.py`, `bigmac.py`, `bmf.py`, `rosstat.py`, `weltbank.py`, `svr.py` | Reine Parser je Quelle: Bytes/Dateien → DataFrame, ohne Netzwerk, ohne Streamlit. |
| `destatis_api.py`, `fred_api.py`, `config.py` | API-Clients und Zugangsdaten (`.env`, `KNOWN_SECRETS`, Platzhalter `MY_…_HERE` gilt als „nicht gesetzt“). Nur für Skripte/Datenaufbau. |
| `analysis.py` | Berechnungen (Wachstumsraten, CAGR, Trends, Zinslast …), ohne Streamlit testbar. |
| `laender.py` | Länderlisten/-namen für den europäischen Vergleich (`EUROPA_LAENDER`). |
| `dataset.py` | Dateinamen-Konstanten der Processed-CSVs, `DATASET_LABELS`, `load_*`-Funktionen (parsen Datumsspalten `stichtag`, `quartalsende`, `datum`). |
| `ui.py` | Gecachte Lader für die Seiten, Farbpaletten (`EBENE_COLORS`, `CHART_COLORS`), deutsche Zahlenformatierung (`format_number`, `format_mrd`, `format_eur`, `format_month`), `style()` und `plot()`. |
| `paths.py` | `PROJECT_ROOT`, `RAW_DIR`, `PROCESSED_DIR`, `SOURCES_FILE`. |
| `format.py` | Deutsche Formatierung ohne Streamlit (`format_number`, `format_signed` …); `ui` re-exportiert sie. |
| `bausteine/` | `kern.py`: `Baustein` (Titel, Art, Ebene einfach/Experte, Quellen, Kernaussage, Erklärung, Methodik, `Parameter`, reine `erzeuge(Kontext)`), `Seite`/`Abschnitt`, `REGISTRY`, `SEITEN`. Je Thema ein Modul (bisher `insolvenzen.py`), in `bausteine/__init__.py` importiert. Ohne Streamlit. |
| `bericht.py` | `BerichtKonfiguration` (JSON) → `erzeuge_bericht()`: Reveal.js-HTML mit Titel-, Baustein- und Quellenfolie; Formate `quer`/`hoch`, Diagramme interaktiv (Plotly-JSON im Browser) oder statisch (SVG). CSS in `vorlagen/bericht.css`. |

Insights: `insights/<thema>/` enthält je eine Reveal.js-Präsentation (`index.html`,
Hochformat 1080 × 1920) mit `diagramme.py`, das Diagramme (`bilder/*.svg`) und
`kennzahlen.json` aus `data/processed/` erzeugt. `tests/test_insights.py` prüft, dass die
Zahlen im Foliensatz zu `kennzahlen.json` passen. Details: `insights/README.md`.

App: `app/main.py` definiert die Navigation explizit mit `st.Page(...)`; die Nummern in
den Dateinamen unter `app/pages/` bestimmen **nicht** die Reihenfolge. Seiten enthalten
nur Laden, Filtern, Darstellen – Fachlogik gehört nach `analysis.py` oder `build.py`.

## Rezepte

**Neue Datenreihe**
1. `Source(...)` in `sources.SOURCES` ergänzen (Titel, Herausgeber, Lizenz, Datensätze).
   Neuer Anbieter → auch `PROVIDER_LINKS`. Manueller Export → Datei nach
   `data/raw/manual/`, `fetch_mode="manual"`.
2. Parser im passenden Quellmodul (rein, testbar). Abbildungen aus dem
   SVR-Jahresgutachten: Das PDF enthält je Abbildung die Daten als Anhang `AbbNNN.csv`
   (Annotation „Daten (CSV)“); extrahieren z. B. mit
   `uv run --with pypdf python -c "from pypdf import PdfReader; ..."` über
   `PdfReader(pfad).attachments`, unverändert nach `data/raw/manual/` legen und mit
   `svr.parse_figure_csv` lesen.
3. `build_*`-Funktion in `build.py`, Eintrag in `BUILDERS` und ggf. `FLOAT_FORMATS`.
4. Dateinamen-Konstante, `DATASET_LABELS`-Eintrag und `load_*` in `dataset.py`;
   gecachter Wrapper in `ui.py`.
5. `uv run scripts/build_data.py` ausführen und die geänderten `data/processed/*.csv`
   **und** `data/sources.json` mit committen. `sources.json` nie von Hand bearbeiten.
6. Tests in `tests/` (Parser/Analyse) und ggf. Plausibilitätstest in `tests/test_app.py`.

**Neuer Baustein / Seite aus Bausteinen** (Pilot: `bausteine/insolvenzen.py`)
1. Im Themenmodul unter `bausteine/` eine reine Funktion `f(k: Kontext) -> Diagramm | list[Kennzahl] | DataFrame | str` mit `@baustein(id="<thema>.<name>", …)` versehen. Daten über `k.daten("insolvencies")` (= `dataset.load_insolvencies` bzw. `ui.insolvencies`), Einstellungen als `Parameter` und `k.wert(name)`. Kein Endlayout – das setzen `ui.plot` bzw. `bericht.folienlayout`.
2. `ebene=Ebene.EINFACH` nur für Kernaussagen-Diagramme; alles andere `EXPERTE`. Kernaussagen mit Zahlen als Funktion von `Kontext`, nie als feste Zahl.
3. Baustein in einen `Abschnitt` der `Seite` aufnehmen (`registriere_seite`); die Seitendatei ruft nur `ui.zeige_seite(SEITE)`.
4. `tests/test_bausteine.py` prüft Quellen, Kernaussage, Achsentitel und Erzeugung automatisch für alle Bausteine.

**Neue Seite**
1. Datei unter `app/pages/` anlegen, in `app/main.py` als `st.Page` eintragen.
2. In die Parametrisierung von `test_streamlit_pages_run_without_exception` in
   `tests/test_app.py` aufnehmen.
3. README-Tabelle „Seiten der App“ ergänzen.

**Legende je Teilbild**: `trace.legend = "legend2"` usw. setzen, die Legenden in
`layout.legend2` … positionieren und `ui.plot(..., own_legends=True)` übergeben –
sonst überschreibt `ui.style()` die Legende mit der Standardlegende oben. Beispiel:
erstes Diagramm in `app/pages/6_Haushalt_und_Zinsen.py`.

**Diagramme**: immer `ui.plot(fig, filename="…")` (eindeutiger `filename`, er wird auch
als Widget-Key der Download-Buttons genutzt), nie `st.plotly_chart` direkt. Titel,
Achsen mit Einheit und Quellen-Caption gehören dazu.

## Stolpersteine

* **Streamlit-Neustart nötig** nach Änderungen in `src/haushaltssimulator/`: beim Rerun
  bleiben importierte Module im Speicher, neue Funktionen fehlen sonst
  (`AttributeError: module 'haushaltssimulator.ui' has no attribute …`). Außerdem
  cacht `ui.py` die Daten per `st.cache_data`.
* **SVG/HTML-Downloads entstehen erst beim Klick**: `ui.plot()` übergibt
  `download_button` eine Funktion statt fertiger Bytes. Vorher renderte Kaleido jedes
  Diagramm bei jedem Seitenaufruf – die 16 Seitentests brauchten 173 s statt 7 s.
  Keine Bytes mehr vorab erzeugen; den Export prüft `tests/test_ui.py`. Fehlt
  Kaleido/Chrome, liefert `ui._svg_bytes` die Ersatzgrafik `SVG_NICHT_VERFUEGBAR`.
* `tests/test_app.py` wird übersprungen, wenn `data/processed/` fehlt.
* Ansicht (`st.session_state["experte"]`) und Berichtskorb (`st.session_state["bericht"]`) setzt `app/main.py`; Seiten, die allein laufen (AppTest), nutzen die einfache Ansicht. Widgets der Seite Bericht hält `ui.optionen_erhalten()` beim Seitenwechsel fest – neue Optionen dort in `ui.BERICHT_OPTIONEN` eintragen.
* `test_app_does_not_import_api_clients` schlägt fehl, sobald eine Datei unter `app/`
  `destatis_api` oder `urllib.request` enthält.
* `data/raw/*` ist gitignoriert (Ausnahme `data/raw/manual/`). Ein Datenaufbau ohne
  Netz funktioniert nur mit bereits vorhandenen Rohdaten; manuelle Quellen ohne Datei
  brechen mit `RuntimeError` ab.
* Ohne `FRED_API_KEY` fällt `fetch_mode="fred_api"` auf den öffentlichen CSV-Export
  zurück, ohne `DESTATIS_API_TOKEN` fällt `fetch_mode="destatis_api"` auf den
  Destatis-Export zurück – der enthält nur die letzten Jahre, die VPI-Langreihe in
  `inflation_de_monat.csv` würde dann kürzer. Die App selbst braucht keine Schlüssel. `.env` nie committen oder ausgeben.
* Abgrenzungen nicht vermischen: Maastricht-Schulden (Eurostat) ≠ Schulden beim
  nicht-öffentlichen Bereich (Destatis); Zinsausgaben ≠ theoretische Zinslast;
  Bundeshaushalt (Kernhaushalt) ≠ Gesamtstaat (VGR). Siehe README „Abgrenzungen“.
* Selbst gebildete Spaltennamen tragen die Einheit (`_mio_eur`, `_mrd_eur`, `_pct`,
  `_eur_kwh` …); Spaltennamen und Codes der Quelle (`geo`, `S13`, `TR`, SVR-Reihennamen)
  bleiben unverändert (siehe „Sprache“).

## Deployment

Streamlit Community Cloud mit `app/main.py`, `uv.lock`, Python 3.12
(`.python-version`), Theme in `.streamlit/config.toml`. Keine Secrets nötig, weil die
Daten als CSV im Repo liegen.
