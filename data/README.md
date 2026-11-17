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
| `insolvenzen_monat.csv` | Insolvenzverfahren gesamt und von Unternehmen je Monat | Destatis 52411-0017 (Langreihe), 52411-0002, 52411-0011 | 2003–2026 |
| `geldmenge_monat.csv` | Geldmenge M3 und Jahreswachstumsrate | EZB BSI | 1995–2026 |
| `kaufkraft_monat.csv` | Inflation Deutschland/Euro-Raum und Kaufkraftindex | EZB ICP | 1997–2025 |
| `energiepreise_jahr.csv` | Strom- und Gaspreise für Haushalte | Destatis 61243-0002, 61243-0011 | 2019–2025 |
| `strom_boerse_tag.csv` | Tagesmittel des Day-Ahead-Strompreises | energy-charts.info | 2019–2026 |
| `kraftstoffpreise.csv` | Monatsmittel der Kraftstoffpreise je Land | EU Weekly Oil Bulletin | 2016–2026 |
| `big_mac.csv` | Big-Mac-Preis in US-Dollar und Abweichung | The Economist | 2000–2026 |
| `eigentumsquote.csv` | Eigentums- und Mietquote je Land | Eurostat `ilc_lvho02` | 2010–2025 |
| `bund_zinsausgaben.csv` | Zinsausgaben des Bundes am Kreditmarkt | BMF | 2022–2027 |

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

**`insolvenzen_monat.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat (`JJJJ-MM`) |
| `verfahren_gesamt`, `verfahren_unternehmen` | beantragte Verfahren |
| `forderungen_gesamt_mio_eur`, `forderungen_unternehmen_mio_eur` | voraussichtliche Forderungen |
| `eroeffnet_unternehmen`, `abgewiesen_unternehmen` | Verfahrensausgang der Unternehmensinsolvenzen |
| `schuldenbereinigungsplan_unternehmen` | angenommene Schuldenbereinigungspläne (ab 2021) |
| `betroffene_arbeitnehmer` | von Unternehmensinsolvenzen betroffene Beschäftigte |

Die Langreihe stammt aus der Tabelle 52411-0017 (Monate, Größenklassen) und reicht bis
2003 zurück. Gesamtzahlen aller Verfahren, Forderungen und betroffene Arbeitnehmer
stehen nur für das laufende Berichtsjahr aus den Tabellen 52411-0002 und 52411-0011 zur
Verfügung.

**`geldmenge_monat.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat |
| `index_m3` | Geldmenge M3, Index Dezember 2010 = 100 |
| `wachstum_pct` | Veränderung gegenüber dem Vorjahr in Prozent |

**`kaufkraft_monat.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat |
| `inflation_de_pct`, `inflation_ea_pct` | HVPI-Veränderung gegenüber dem Vorjahr |
| `kaufkraft_index` | Kaufkraft eines Euro, Startmonat = 100 |

**`energiepreise_jahr.csv`** – `jahr`, `verbrauchsklasse`, `strompreis_eur_kwh`,
`gaspreis_eur_kwh` (jeweils inklusive Steuern, Abgaben und Umlagen; Summe der
Preisbestandteile).

**`strom_boerse_tag.csv`** – `datum`, `preis_eur_mwh` (Tagesmittel der stündlichen
Day-Ahead-Preise).

**`kraftstoffpreise.csv`** – `monat`, `land`, `produkt` (`Diesel`,
`Superbenzin (Euro 95)`), `preis_eur_l`.

**`big_mac.csv`** – `datum`, `land`, `preis_usd`, `abweichung_pct` (Abweichung vom
US-Preis).

**`eigentumsquote.csv`** – `jahr`, `geo`, `land`, `eigentumsquote_pct`, `mietquote_pct`.

**`bund_zinsausgaben.csv`** – `jahr`, `art` (`Ist`, `Soll`, `RegE`),
`zinsausgaben_mrd_eur`.

## `raw/`

Die Originaldateien der Quellen (Destatis-CSV in Windows-1252, Eurostat-JSON-stat,
Bundesbank- und FRED-CSV, OFZ-Monatsendwerte der Bank of Russia) werden unverändert
gespeichert.

* `raw/` selbst ist per `.gitignore` ausgeschlossen: automatisch geladene Dateien sind
  jederzeit reproduzierbar und gehören nicht ins Repository.
* `raw/manual/` ist **versioniert**. Hier liegen Exporte, die sich nicht per Skript
  erneuern lassen.

Die **Quellenbibliothek** [`sources.json`](sources.json) ist versioniert und dokumentiert
je Quelle Titel, Herausgeber, Lizenz, URL, verwendete Datensätze, Dateiname, SHA-256,
Größe und Abrufzeitpunkt. Sie wird ausschließlich von
`haushaltssimulator.sources.download_all` geschrieben und auf der Seite **Quellen**
angezeigt; dort steht im Abschnitt „Quellen & Links“ auch die API-Dokumentation der
Anbieter.

Die Tabelle 52411-0017 (Unternehmensinsolvenzen, Langreihe) wird nicht automatisch
geladen. Sie ist als **manuelle Quelle** registriert: Die CSV-Datei wird über
[GENESIS-Online](https://genesis.destatis.de/datenbank/online/table/52411-0017)
exportiert und unter `raw/manual/stat_bundesamt_insolvenzen_52411-0017_de_Nov2026.csv`
abgelegt (exakter Name in `sources.json`). Der Abrufzeitpunkt ist der Zeitpunkt des
Exports.

## Rohdaten aus APIs

Zugangsdaten für Datenquellen-APIs stehen in `.env` (nicht versioniert, Vorlage
`.env.example`): `DESTATIS_API_TOKEN` (GENESIS-Online, Token wird als Header
`username` gesendet) und `FRED_API_KEY`. Die Clients `destatis_api.py` und
`fred_api.py` prüfen die Zugänge mit `uv run scripts/check_destatis_api.py` bzw.
`uv run scripts/check_fred_api.py`. API-Antworten werden unverändert in `raw/`
abgelegt und über `build.py` aufbereitet. Die App liest ausschließlich `processed/`
und macht keine eigenen API-Aufrufe.

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
* EZB-Daten: Europäische Zentralbank, Quellenangabe erforderlich
* energy-charts.info: CC BY 4.0, Daten von Bundesnetzagentur | SMARD.de
* EU Weekly Oil Bulletin: © Europäische Union, Quellenangabe erforderlich
* Big-Mac-Index: The Economist, Quellenangabe erforderlich
* Bundeshaushalt: © Bundesministerium der Finanzen, Quellenangabe erforderlich
