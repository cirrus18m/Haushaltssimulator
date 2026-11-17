# Haushaltssimulator

Streamlit-App zur Visualisierung und Analyse der deutschen Staatsschulden – mit frei
verfügbaren Daten von Eurostat und dem Statistischen Bundesamt (Destatis).

[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](pyproject.toml)

## Schnellstart

```bash
# uv installieren, falls noch nicht vorhanden: https://docs.astral.sh/uv/
uv sync
uv run scripts/build_data.py   # lädt die Datenquellen und baut data/processed/*.csv
uv run streamlit run app/main.py
```

Die aufbereiteten CSV-Dateien liegen bereits im Repository – der Aufbereitungsschritt ist
nur nötig, wenn die Daten aktualisiert werden sollen. Ohne `--refresh` werden vorhandene
Rohdaten wiederverwendet, mit `--refresh` neu von den Servern geladen:

```bash
uv run scripts/build_data.py --refresh
```

## Veröffentlichen auf Streamlit Community Cloud

Das Repository ist für ein Deployment ohne weitere Anpassungen vorbereitet:

* Einstiegspunkt der App: `app/main.py`
* Abhängigkeiten: `uv.lock` (Community Cloud erkennt die Datei und installiert die
  Umgebung mit `uv`; das Paket `haushaltssimulator` wird dabei aus `src/` mitinstalliert)
* Python-Version: **3.12** (siehe `.python-version`)
* Theme und Serververhalten: [.streamlit/config.toml](.streamlit/config.toml)
* Die Daten liegen als CSV im Repo – es werden keine Secrets oder API-Schlüssel benötigt

Schritte:

1. [share.streamlit.io](https://share.streamlit.io) öffnen und mit GitHub anmelden.
2. **Create app** → **Deploy a public app from GitHub** wählen.
3. Repository `cirrus18m/Haushaltssimulator`, Branch `main` (oder der eigene Branch) und
   als **Main file path** `app/main.py` eintragen.
4. Unter *Advanced settings* Python **3.12** auswählen und deployen.

Nach dem ersten Deployment aktualisiert sich die App bei jedem Push automatisch. Sollen
die Daten regelmäßig aufgefrischt werden, kann ein GitHub-Actions-Workflow
`uv run scripts/build_data.py --refresh` ausführen und die geänderten CSVs committen.

## Seiten der App

| Seite | Inhalt |
| --- | --- |
| **Überblick** | Schuldenstand, Schuldenquote, Schulden je Einwohner:in, Verteilung auf die Ebenen |
| **Zeitreihe** | Jährliche und vierteljährliche Maastricht-Schulden seit 1995, Kennzahlentabelle |
| **Ebenen & Schuldenarten** | Bund, Länder, Gemeinden, Sozialversicherung; Wertpapier-, Kredit- und Kassenkreditschulden |
| **Bundesländer** | Ranking und Entwicklung der 16 Länder, Anteile, Veränderung seit 2024 |
| **Analysen** | Wachstumsraten, CAGR, Schuldenquote vs. 60-%-Referenz, Schuldenwachstum vs. BIP-Wachstum |
| **Szenario-Rechner** | Einfache Fortschreibung von Schulden und BIP mit einstellbaren Wachstumsraten |
| **Haushalt & Zinsen** | Einnahmen ohne neue Schulden, Ausgaben, Schuldenstand, 10-jährige Bundesanleihe und die daraus folgende theoretische Zinslast in Mrd. €, in % der Einnahmen und in % des BIP |
| **Zinsvergleich** | Renditen 10-jähriger Staatsanleihen europäischer Länder, der USA und Russlands |
| **Quellen** | Welche Quelle liefert welche Daten – inklusive Lizenz, Prüfsumme und Abrufdatum |

## Projektstruktur

```text
Haushaltssimulator/
├── app/                      # Streamlit-App
│   ├── main.py               # Einstiegspunkt und Navigation
│   └── pages/                # einzelne Seiten
├── data/
│   ├── raw/                  # unveränderte Quelldateien (nicht versioniert)
│   └── processed/            # aufbereitete CSVs für die App
├── scripts/
│   └── build_data.py         # Datenabruf und -aufbereitung
├── src/haushaltssimulator/   # Datenlogik (Parsing, Aufbereitung, Analysen)
└── tests/                    # pytest-Tests inkl. Smoke-Tests der Streamlit-Seiten
```

## Datenquellen

Alle Quellen sind frei verfügbar und werden ohne API-Schlüssel abgerufen.

| Quelle | Inhalt | Lizenz |
| --- | --- | --- |
| [Eurostat `gov_10dd_edpt1`](https://ec.europa.eu/eurostat/databrowser/view/gov_10dd_edpt1/default/table) | Maastricht-Schuldenstand, jährlich ab 1995, nach Sektoren | CC BY 4.0 |
| [Eurostat `gov_10q_ggdebt`](https://ec.europa.eu/eurostat/databrowser/view/gov_10q_ggdebt/default/table) | Maastricht-Schuldenstand, vierteljährlich ab 2000 | CC BY 4.0 |
| [Eurostat `nama_10_gdp`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table) | Bruttoinlandsprodukt, jährlich | CC BY 4.0 |
| [Eurostat `demo_pjan`](https://ec.europa.eu/eurostat/databrowser/view/demo_pjan/default/table) | Bevölkerung, jährlich | CC BY 4.0 |
| [Destatis 71311-0001](https://www-genesis.destatis.de/datenbank/online/statistic/71311/table/71311-0001) | Schulden beim nicht-öffentlichen Bereich, vierteljährlich | DL-DE-BY-2.0 |
| [Destatis 71311-0003](https://www-genesis.destatis.de/datenbank/online/statistic/71311/table/71311-0003) | Dasselbe je Bundesland | DL-DE-BY-2.0 |
| [Destatis 71321-0005](https://www-genesis.destatis.de/datenbank/online/statistic/71321/table/71321-0005) | Dasselbe jährlich ab 2010 | DL-DE-BY-2.0 |
| [Eurostat `gov_10a_main`](https://ec.europa.eu/eurostat/databrowser/view/gov_10a_main/default/table) | Einnahmen, Ausgaben, Zinsausgaben und Finanzierungssaldo des Staates | CC BY 4.0 |
| [Deutsche Bundesbank BBSSY.D.REN.EUR.A630.000000WT1010.A](https://www.bundesbank.de/dynamic/action/de/statistiken/zeitreihen-datenbanken/zeitreihe/723452/723452) | Tagesrendite der aktuellen 10-jährigen Bundesanleihe | Quellenangabe erforderlich |
| [Eurostat `irt_lt_mcby_m`](https://ec.europa.eu/eurostat/databrowser/view/irt_lt_mcby_m/default/table) | Konvergenzrenditen 10-jähriger Staatsanleihen, monatlich | CC BY 4.0 |
| [FRED `IRLTLT01USM156N`](https://fred.stlouisfed.org/series/IRLTLT01USM156N) | Langfristige Staatsanleiherendite der USA (OECD MEI) | OECD-Bedingungen |
| [Bank of Russia](https://www.cbr.ru/eng/hd_base/zcyc_params/) | Zero-Coupon-Yield-Curve, 10-jährige OFZ-Rendite | Quellenangabe erforderlich |

Details zu Dateien und Spalten: [data/README.md](data/README.md).

## Quellenbibliothek und Datenstand

Jeder Download wird in der versionierten Quellenbibliothek
[`data/sources.json`](data/sources.json) festgehalten: Titel, Herausgeber, Lizenz, URL,
verwendete Datensätze, Dateiname, SHA-256, Größe und **Zeitpunkt des Downloads**. Bereits
vorhandene Rohdaten behalten ihren ursprünglichen Zeitstempel; nur `--refresh` setzt einen
neuen. Die Seite **Quellen** zeigt die Bibliothek und die Zuordnung „Quelle → Datensatz“.

Aufbereitete Daten werden ausschließlich aus den Rohdaten erzeugt und nie von Hand
gepflegt. Verbindliche Regeln für Änderungen (Sprache, Quellenpflicht, SVG-/HTML-Export)
stehen in [.github/copilot-instructions.md](.github/copilot-instructions.md); der
mehrstufige Ausbau ist in [PLAN.md](PLAN.md) beschrieben.

## Diagramme exportieren

Jedes Diagramm der App lässt sich direkt unter der Grafik als **SVG** (Vektorgrafik) und
als **HTML** (interaktive Einzeldatei) herunterladen. Zusätzlich bietet die Plotly-
Werkzeugleiste den Kamera-Button im SVG-Format an.

## Abgrenzungen

* **Maastricht-Schuldenstand** (Eurostat): konsolidierte Verbindlichkeiten des gesamten
  Staates (Sektor S13) gegenüber allen anderen Sektoren, Wertpapiere zu Marktwerten.
  Bezugsgröße für die 60-%-Referenz.
* **Schulden beim nicht-öffentlichen Bereich** (Destatis): Schulden von Bund, Ländern,
  Gemeinden und Sozialversicherung gegenüber privaten Gläubigern, getrennt nach Kern- und
  Extrahaushalten. Andere Abgrenzung, daher niedrigere Werte.
* Die Aufteilung des Maastricht-Schuldenstands nach Ebenen veröffentlicht Eurostat erst ab
  2022; für längere Zeitreihen je Ebene dienen die Destatis-Tabellen ab 2010.
* Das Szenario-Modell rechnet mit konstanten Wachstumsraten und ohne Zinsen – es zeigt die
  Richtung, ist aber keine Prognose.

## Entwicklung

```bash
uv run pytest          # Tests (inkl. Streamlit-Smoke-Tests)
uv run ruff check .    # Linting
uv run ruff format .   # Formatierung
```

## Lizenz

Der Quellcode dieses Projekts steht unter der [MIT-Lizenz](LICENSE), © 2026 cirrus18m.
Sie erlaubt die freie Nutzung, Veränderung und Weitergabe, solange der Copyright-Hinweis
erhalten bleibt.

Die **Daten** sind nicht Teil dieser Lizenz und unterliegen den Lizenzen ihrer Quellen:

* Eurostat: © Europäische Union, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
* Statistisches Bundesamt (Destatis): [DL-DE-BY-2.0](https://www.govdata.de/dl-de/by-2-0)

Bei einer Veröffentlichung der App sind diese Quellenangaben sichtbar zu nennen; die App
tut das auf jeder Seite im Fußbereich.

## Ausblick

Der nächste Ausbau ist in [PLAN.md](PLAN.md) beschrieben: Wirtschafts- und
Geldindikatoren (Insolvenzen, Geldmenge, Energiepreise), Sondervermögen sowie der
Vergleich der Haushaltspläne von Regierung und Opposition.
