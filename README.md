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
| **Zinsvergleich** | Renditen 10-jähriger Staatsanleihen europäischer Länder, der USA und Russlands, dazu Schuldenstand, Schuldenquote, Zinsausgaben je Einwohner:in, theoretische Zinslast, drei Einkommensgrößen, Inflation und Realzins |
| **Quellen** | Welche Quelle liefert welche Daten – inklusive Lizenz, Prüfsumme, Abrufdatum und Links zu Portalen und API-Dokumentation |
| **Insolvenzen** | Beantragte Verfahren gesamt und von Unternehmen, Forderungen und betroffene Arbeitnehmer |
| **Geld & Kaufkraft** | Geldmenge M3, Inflation und kumulierter Kaufkraftverlust |
| **Energiepreise** | Strom- und Gaspreise für Haushalte, Börsenstrompreis, Kraftstoffe im EU-Vergleich, Heizöl sowie regionale Gas- und Öl-Benchmarks (TTF, JKM, Henry Hub; Brent, WTI, Dubai) |
| **Preisniveau & Wohnen** | Big-Mac-Index und Eigentumsquote in Europa |
| **Bund & Schuldendienst** | Zinsausgaben und Schuldenstand des Bundes, Planwerte aus dem Bundeshaushalt |
| **Wirtschaft** | Reales BIP-Wachstum, Produktion im Verarbeitenden Gewerbe, Industrieproduktion im langfristigen Trend sowie private/staatliche Investitionen |

## Projektstruktur

```text
Haushaltssimulator/
├── app/                      # Streamlit-App
│   ├── main.py               # Einstiegspunkt und Navigation
│   └── pages/                # einzelne Seiten
├── data/
│   ├── raw/                  # automatisch geladene Rohdaten (nicht versioniert)
│   │   └── manual/           # von Hand geladene Rohdaten (versioniert)
│   └── processed/            # aufbereitete CSVs für die App
├── scripts/
│   └── build_data.py         # Datenabruf und -aufbereitung
├── src/haushaltssimulator/   # Datenlogik (Parsing, Aufbereitung, Analysen)
└── tests/                    # pytest-Tests inkl. Smoke-Tests der Streamlit-Seiten
```

## Datenquellen

Alle Quellen sind frei verfügbar. Automatische Abrufe funktionieren ohne
API-Schlüssel; für Destatis GENESIS und FRED sind Schlüssel hinterlegt (siehe
[Zugangsdaten](#zugangsdaten-und-api-schlüssel)), die App selbst benötigt sie nicht.
Der Rosstat-Abruf über EMISS benötigt einen kostenlosen Schlüssel; ohne Schlüssel
nutzt der Datenaufbau die Preisdynamik der Bank of Russia.
Portale und API-Dokumentation aller Anbieter listet die Seite **Quellen** im Abschnitt
„Quellen & Links“.

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
| [Eurostat `gov_10dd_edpt1`](https://ec.europa.eu/eurostat/databrowser/view/gov_10dd_edpt1/default/table) | Schuldenstand und Schuldenquote der europäischen Länder, jährlich | CC BY 4.0 |
| [Eurostat `gov_10a_main`](https://ec.europa.eu/eurostat/databrowser/view/gov_10a_main/default/table) | Einnahmen und Zinsausgaben der europäischen Länder, jährlich | CC BY 4.0 |
| [Eurostat `nama_10_gdp`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table) | BIP der europäischen Länder, jährlich | CC BY 4.0 |
| [Eurostat `demo_pjan`](https://ec.europa.eu/eurostat/databrowser/view/demo_pjan/default/table) | Bevölkerung der europäischen Länder, jährlich | CC BY 4.0 |
| [Eurostat `prc_hicp_manr`](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_manr/default/table) | Inflationsraten (HVPI) der europäischen Länder, monatlich | CC BY 4.0 |
| [FRED `IRLTLT01USM156N`](https://fred.stlouisfed.org/series/IRLTLT01USM156N) | Langfristige Staatsanleiherendite der USA (OECD MEI) | OECD-Bedingungen |
| [Bank of Russia](https://www.cbr.ru/eng/hd_base/zcyc_params/) | Zero-Coupon-Yield-Curve, 10-jährige OFZ-Rendite | Quellenangabe erforderlich |
| [IWF DataMapper](https://www.imf.org/external/datamapper/api/help) | Schuldenquote, Einnahmen, Zinsausgaben, reales BIP-Wachstum, BIP und Bevölkerung für USA und Russland (WEO, Public Finances in Modern History) | IWF-Bedingungen |
| [FRED `PNGASJPUSDM`](https://fred.stlouisfed.org/series/PNGASJPUSDM) | LNG-Preis Japan, monatlich (IWF; JKM-Referenz) | IWF-Bedingungen |
| [FRED `POILDUBUSDM`](https://fred.stlouisfed.org/series/POILDUBUSDM) | Rohölpreis Dubai, monatlich (IWF) | IWF-Bedingungen |
| [EZB EXR](https://data.ecb.europa.eu/data/datasets/EXR) | Wechselkurs US-Dollar/Euro, Jahres- und Tageswerte | Quellenangabe erforderlich |
| [Rosstat über EMISS](https://fedstat.ru/) | Verbraucherpreise Russlands, monatlich (Rückgriff: Bank of Russia) | Quellenangabe erforderlich |
| [Weltbank WDI `NY.GNP.PCAP.CD`](https://data.worldbank.org/indicator/NY.GNP.PCAP.CD) | Bruttonationaleinkommen je Einwohner:in Russlands (Ersatzreihe) | CC BY 4.0 |
| [Eurostat `ilc_di03`](https://ec.europa.eu/eurostat/databrowser/view/ilc_di03/default/table) | Verfügbares Einkommen je Einwohner:in der europäischen Länder | CC BY 4.0 |
| [Eurostat `nama_10_lp_ulc`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_lp_ulc/default/table) | Arbeitnehmerentgelt je Arbeitnehmer:in der europäischen Länder | CC BY 4.0 |
| [FRED `A229RC0A052NBEA`](https://fred.stlouisfed.org/series/A229RC0A052NBEA) | Verfügbares Einkommen je Einwohner:in der USA | BEA-Bedingungen |
| [FRED `CES0500000011`](https://fred.stlouisfed.org/series/CES0500000011) | Wochenverdienst der USA (BLS) | BLS-Bedingungen |
| [FRED `CPIAUCSL`](https://fred.stlouisfed.org/series/CPIAUCSL) | Verbraucherpreisindex der USA, monatlich | BLS-Bedingungen |
| [Destatis 52411-0002](https://www-genesis.destatis.de/datenbank/online/statistic/52411/table/52411-0002) | Beantragte Insolvenzverfahren, Monate | DL-DE-BY-2.0 |
| [Destatis 52411-0011](https://www-genesis.destatis.de/datenbank/online/statistic/52411/table/52411-0011) | Insolvenzverfahren von Unternehmen, Monate | DL-DE-BY-2.0 |
| [Destatis 52411-0017](https://genesis.destatis.de/datenbank/online/table/52411-0017) | Unternehmensinsolvenzen 2003–2026 nach Größenklassen (manueller Export) | DL-DE-BY-2.0 |
| [Destatis 81000-0001](https://www-genesis.destatis.de/datenbank/online/statistic/81000/table/81000-0001) | Bruttoinlandsprodukt nominal und real, Wachstumsraten, Jahre | DL-DE-BY-2.0 |
| [Destatis 81000-0025](https://www-genesis.destatis.de/datenbank/online/statistic/81000/table/81000-0025) | Bruttoanlageinvestitionen des Staates und der nichtstaatlichen Sektoren | DL-DE-BY-2.0 |
| [Destatis 42153-0001](https://www-genesis.destatis.de/datenbank/online/statistic/42153/table/42153-0001) | Produktionsindex des Verarbeitenden Gewerbes, Monate | DL-DE-BY-2.0 |
| [Eurostat `nama_10_gdp`](https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table) | Reales BIP-Wachstum der europäischen Länder, jährlich | CC BY 4.0 |
| [Eurostat `sts_inpr_m`](https://ec.europa.eu/eurostat/databrowser/view/sts_inpr_m/default/table) | Produktionsindex des Verarbeitenden Gewerbes und der Industrie (NACE B-D), monatlich ab 1993 | CC BY 4.0 |
| [EZB BSI](https://data.ecb.europa.eu/data/datasets/BSI) | Geldmenge M3, monatlich | Quellenangabe erforderlich |
| [EZB ICP](https://data.ecb.europa.eu/data/datasets/ICP) | Harmonisierter Verbraucherpreisindex, monatlich | Quellenangabe erforderlich |
| [Destatis 61243-0002](https://www-genesis.destatis.de/datenbank/online/statistic/61243/table/61243-0002) | Strompreise für Haushalte, Jahre | DL-DE-BY-2.0 |
| [Destatis 61243-0011](https://www-genesis.destatis.de/datenbank/online/statistic/61243/table/61243-0011) | Erdgaspreise für Haushalte, Jahre | DL-DE-BY-2.0 |
| [energy-charts.info](https://api.energy-charts.info/) | Börsenstrompreis Day-Ahead (Bundesnetzagentur \| SMARD.de) | CC BY 4.0 |
| [EU Weekly Oil Bulletin](https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en) | Kraftstoff- und Heizölpreise je Land, wöchentlich | Quellenangabe erforderlich |
| [FRED `DCOILBRENTEU`](https://fred.stlouisfed.org/series/DCOILBRENTEU) | Brent-Rohölpreis, täglich (EIA) | EIA-Bedingungen |
| [FRED `DCOILWTICO`](https://fred.stlouisfed.org/series/DCOILWTICO) | WTI-Rohölpreis, täglich (EIA) | EIA-Bedingungen |
| [FRED `PNGASEUUSDM`](https://fred.stlouisfed.org/series/PNGASEUUSDM) | Gaspreis Europa, monatlich (IWF) | IWF-Bedingungen |
| [FRED `DHHNGSP`](https://fred.stlouisfed.org/series/DHHNGSP) | Henry-Hub-Gaspreis, täglich (EIA) | EIA-Bedingungen |
| [The Economist Big-Mac-Data](https://github.com/TheEconomist/big-mac-data) | Big-Mac-Index je Land | Quellenangabe erforderlich |
| [Eurostat `ilc_lvho02`](https://ec.europa.eu/eurostat/databrowser/view/ilc_lvho02/default/table) | Eigentums- und Mietquote | CC BY 4.0 |
| [BMF Bundeshaushalt](https://www.bundeshaushalt.de/) | Zinsausgaben des Bundes am Kreditmarkt | Quellenangabe erforderlich |

Details zu Dateien und Spalten: [data/README.md](data/README.md).

## Zugangsdaten und API-Schlüssel

Zugangsdaten werden **nie committet**. Die versionierte Vorlage ist
[.env.example](.env.example); die lokale Datei `.env` ist per `.gitignore`
ausgeschlossen. Platzhalter wie `MY_DESTATIS_TOKEN_HERE` erkennt `config.py` als
„nicht gesetzt“.

```bash
cp .env.example .env          # falls noch nicht vorhanden
# .env öffnen und die Platzhalter ersetzen:
#   DESTATIS_API_TOKEN=MY_DESTATIS_TOKEN_HERE
#   FRED_API_KEY=MY_FRED_API_KEY_HERE
uv run scripts/check_destatis_api.py   # GENESIS-Online: helloworld/logincheck
uv run scripts/check_fred_api.py       # FRED: series/observations
```

Die Skripte zeigen nur den Status an, niemals die Werte. Der GENESIS-Client sendet den
Token als HTTP-Header `username` mit leerem `password`; alternativ sind
`DESTATIS_API_USER` und `DESTATIS_API_PASSWORD` möglich. Weitere Anbieter folgen
demselben Muster: Schlüsselname in `config.KNOWN_SECRETS` ergänzen und ein eigenes
Client-Modul anlegen.

| Variable | Anbieter | Zugang |
| --- | --- | --- |
| `DESTATIS_API_TOKEN` | Destatis GENESIS-Online | kostenlos nach Registrierung |
| `DESTATIS_API_USER` / `DESTATIS_API_PASSWORD` | Destatis (Alternative zum Token) | kostenlos nach Registrierung |
| `FRED_API_KEY` | FRED, Federal Reserve Bank of St. Louis | kostenlos, [API-Doku](https://fred.stlouisfed.org/docs/api/fred/) |

Das EZB-Data-Portal (`https://data.ecb.europa.eu/`) und Eurostat bieten frei nutzbare
Schnittstellen ohne Schlüssel; sie sind bereits über öffentliche Export-URLs angebunden.

Genutzt werden die Clients derzeit im Datenaufbau für die US-Staatsanleiherendite
(Quelle `fred_us_zins`, Modus `fred_api`): Mit `FRED_API_KEY` läuft der Abruf über die
FRED-API, ohne Schlüssel automatisch über den öffentlichen CSV-Export. Die
Destatis-Tabellen kommen weiterhin über die Export-URLs, weil das API-CSV-Format
(`transpose`/`ffcsv`) nicht dem Aufbau der Exportdateien entspricht und eigene Parser
braucht.

Die Streamlit-App macht **keine** API-Aufrufe. Der Datenfluss bleibt:
API/Download → `data/raw/` → `build.py` → `data/processed/` → App. Die Clients
`destatis_api.py` und `fred_api.py` werden ausschließlich von Skripten und dem
Datenaufbau genutzt.

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

### Rohdaten: was versioniert wird

* `data/raw/*` – automatisch geladene Dateien. Sie sind reproduzierbar und werden
  deshalb **nicht** versioniert; die Quellenbibliothek hält URL, Prüfsumme und
  Abrufdatum fest.
* `data/raw/manual/*` – von Hand exportierte Dateien (z. B. die GENESIS-Langreihe
  `stat_bundesamt_insolvenzen_52411-0017_de_Nov2026.csv`). Solche Exporte lassen sich
  nicht mit einem Skript wiederherstellen und sind daher **im Repository enthalten**.

Ein neuer manueller Export wird unter `data/raw/manual/` abgelegt, in
`sources.py` als Quelle mit `fetch_mode="manual"` eingetragen und mit
`uv run scripts/build_data.py` eingebunden.

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

Nach Änderungen an `src/haushaltssimulator/` den laufenden Streamlit-Prozess neu
starten. Streamlit führt beim Rerun nur das Seiten-Skript erneut aus; bereits
importierte Module bleiben im Speicher. Neue Funktionen in `ui.py`, `dataset.py` oder
`analysis.py` erscheinen sonst erst nach einem Neustart – der Fehler sieht dann aus wie
`AttributeError: module 'haushaltssimulator.ui' has no attribute ...`.

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

Stufe 4 (Wirtschafts- und Geldindikatoren) ist umgesetzt. Offen sind die
Sondervermögen des Bundes – dafür fehlt eine frei maschinenlesbare Zeitreihe – und
Stufe 5, der Vergleich der Haushaltspläne von Regierung und Opposition. Details stehen
in [PLAN.md](PLAN.md).
