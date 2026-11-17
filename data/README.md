# Daten

Alle Dateien werden aus frei verfügbaren Quellen erzeugt. Rohdaten liegen in `raw/`
(nicht versioniert, per `uv run scripts/build_data.py` reproduzierbar), die für die App
aufbereiteten Tabellen in `processed/` (versioniert, tidy long format).

## `processed/`

| Datei | Inhalt | Quelle | Zeitraum |
| --- | --- | --- | --- |
| `schulden_jahresreihe.csv` | Maastricht-Schuldenstand je Jahr und Ebene | Eurostat `gov_10dd_edpt1`, `nama_10_gdp` | 1995–2025 |
| `schulden_quartalsreihe.csv` | Maastricht-Schuldenstand je Quartal und Ebene | Eurostat `gov_10q_ggdebt` | 2000-Q1–2026-Q2 |
| `schulden_destatis_jahr.csv` | Schulden beim nicht-öffentlichen Bereich, jährlich | Destatis 71321-0005 | 2010–2025 |
| `schulden_destatis_quartal.csv` | Dasselbe, vierteljährlich | Destatis 71311-0001 | letzte 10 Quartale |
| `schulden_destatis_bundeslaender.csv` | Dasselbe je Bundesland | Destatis 71311-0003 | letzte 10 Quartale |
| `bip_bevoelkerung.csv` | BIP, Bevölkerung, BIP je Einwohner:in | Eurostat `nama_10_gdp`, `demo_pjan` | 1995–2026 |
| `haushalt_jahr.csv` | Einnahmen, Ausgaben, Zinsausgaben, Finanzierungssaldo je Jahr und Ebene | Eurostat `gov_10a_main` | 1995–2025 |
| `zins_bund_10j.csv` | Tagesrendite der 10-jährigen Bundesanleihe | Deutsche Bundesbank | 2001–2026 |
| `zins_vergleich.csv` | Renditen 10-jähriger Staatsanleihen je Land und Monat | Eurostat `irt_lt_mcby_m`, FRED, Bank of Russia | 1993–2026 |
| `zinslast_jahr.csv` | Schuldenstand, Rendite, theoretische und tatsächliche Zinslast | Eurostat, Bundesbank | 1995–2025 |

### Spalten

**`schulden_jahresreihe.csv` / `schulden_quartalsreihe.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `quartal`, `quartalsende` | Quartalsbezeichnung (`2026-Q2`) und Stichtag (nur Quartalsreihe) |
| `sector` | ESA-2010-Sektor: `S13` Gesamtstaat, `S1311` Bund, `S1312` Länder, `S1313` Gemeinden, `S1314` Sozialversicherung |
| `ebene` | Deutsche Bezeichnung des Sektors |
| `schulden_mio_eur` | Schuldenstand in Mio. € |
| `schuldenquote_pct` | Schuldenstand in % des BIP (amtliche Quote von Eurostat) |
| `bip_mio_eur` | Bruttoinlandsprodukt in Mio. € (nur Jahresreihe) |

**`schulden_destatis_*.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `stichtag` | Quartals- bzw. Jahresende |
| `jahr` | Berichtsjahr (nur Jahresdatei) |
| `bundesland` | Bundesland (nur Länderdatei) |
| `ebene` | `Bund`, `Länder`, `Gemeinden / Gemeindeverbände`, `Sozialversicherung`, `Insgesamt` |
| `haushalt` | `Kernhaushalt`, `Extrahaushalte`, `Insgesamt` |
| `schuldenart` | `Wertpapierschulden`, `Kredite beim nicht-öffentlichen Bereich`, `Kassenkredite beim nicht-öffentlichen Bereich`, `Insgesamt` |
| `schulden_mio_eur` | Schulden in Mio. € (fehlende Werte sind nicht berichtet, `NaN`) |

In der Länderdatei bedeutet `ebene = Insgesamt` die Summe aus Land und seinen Gemeinden
(bei Stadtstaaten entspricht das der Landesebene).

**`bip_bevoelkerung.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `bip_mio_eur` | Bruttoinlandsprodukt, nominal (Mio. €) |
| `bevoelkerung` | Bevölkerung am 1. Januar |
| `bip_je_einwohner_eur` | BIP je Einwohner:in |

**`haushalt_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr`, `sector`, `ebene` | Berichtsjahr und staatliche Ebene |
| `einnahmen_mio_eur` | Gesamteinnahmen (`TR`) – ohne Kreditaufnahme |
| `ausgaben_mio_eur` | Gesamtausgaben (`TE`) |
| `zinsausgaben_mio_eur` | Tatsächlich gebuchte Zinsausgaben (`D41PAY`) |
| `finanzierungssaldo_mio_eur` | Nettofinanzierungssaldo (`B9`), negativ = Defizit |
| `einnahmenquote_pct`, `ausgabenquote_pct` | Anteil am BIP |
| `zins_einnahmen_pct` | Zinsausgaben in % der Einnahmen |

**`zins_bund_10j.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `datum` | Handelstag |
| `jahr`, `monat` | Jahr und Monat (`JJJJ-MM`) |
| `rendite_pct` | Tagesrendite der aktuellen 10-jährigen Bundesanleihe in % |

**`zins_vergleich.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Monat (`JJJJ-MM`) |
| `land` | Deutsche Länderbezeichnung |
| `rendite_pct` | Rendite 10-jähriger Staatsanleihen in % |
| `quelle`, `quelle_key` | Quellenbezeichnung und Schlüssel in `data/sources.json` |

**`zinslast_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `schulden_mio_eur` | Maastricht-Schuldenstand des Gesamtstaats |
| `rendite_pct` | Jahresdurchschnitt der 10-jährigen Bundesanleihe |
| `zins_theoretisch_mio_eur` | Schuldenstand × Rendite |
| `einnahmen_mio_eur` | Gesamteinnahmen ohne neue Schulden |
| `zins_quote_einnahmen_pct` | theoretische Zinslast in % der Einnahmen |
| `bip_mio_eur`, `zins_quote_bip_pct` | BIP und theoretische Zinslast in % des BIP |
| `zinsausgaben_mio_eur` | tatsächlich gebuchte Zinsausgaben |
| `effektivzins_pct` | Zinsausgaben / Schuldenstand × 100 |

Die theoretische Zinslast ist eine Modellrechnung; negative Werte 2019–2021 folgen aus
den damals negativen Renditen.

## `raw/`

Die Originaldateien der Quellen (Destatis-CSV in Windows-1252, Eurostat-JSON-stat,
Bundesbank- und FRED-CSV, OFZ-Monatsendwerte der Bank of Russia) werden unverändert
gespeichert. Der Ordner ist per `.gitignore` ausgeschlossen.

Die **Quellenbibliothek** [`sources.json`](sources.json) ist versioniert und dokumentiert
je Quelle Titel, Herausgeber, Lizenz, URL, verwendete Datensätze, Dateiname, SHA-256,
Größe und Abrufzeitpunkt. Sie wird ausschließlich von
`haushaltssimulator.sources.download_all` geschrieben und auf der Seite **Quellen**
angezeigt.

## Aktualisieren

```bash
uv run scripts/build_data.py --refresh
```

Neue Quartale und Jahre werden dabei automatisch übernommen; die App liest immer die
CSV-Dateien aus `processed/`.

## Lizenzhinweise

* Eurostat-Daten: © Europäische Union, Lizenz [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
* Destatis-Daten: © Statistisches Bundesamt (Destatis), Lizenz [DL-DE-BY-2.0](https://www.govdata.de/dl-de/by-2-0)
* Bundesbank-Daten: © Deutsche Bundesbank, Quellenangabe erforderlich
* FRED/OECD-Daten: OECD-Nutzungsbedingungen, Quellenangabe erforderlich
* Bank-of-Russia-Daten: Quellenangabe erforderlich
