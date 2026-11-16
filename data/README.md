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

## `raw/`

Die Originaldateien der Quellen (Destatis-CSV in Windows-1252, Eurostat-JSON-stat)
werden unverändert gespeichert. `_quellen.json` dokumentiert URLs, Abrufzeitpunkt und
Prüfsummen. Der Ordner ist per `.gitignore` ausgeschlossen.

## Aktualisieren

```bash
uv run scripts/build_data.py --refresh
```

Neue Quartale und Jahre werden dabei automatisch übernommen; die App liest immer die
CSV-Dateien aus `processed/`.

## Lizenzhinweise

* Eurostat-Daten: © Europäische Union, Lizenz [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
* Destatis-Daten: © Statistisches Bundesamt (Destatis), Lizenz [DL-DE-BY-2.0](https://www.govdata.de/dl-de/by-2-0)
