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
| `laender_schulden_jahr.csv` | Schuldenstand und Schuldenquote im Ländervergleich | Eurostat `gov_10dd_edpt1`; IWF WEO/FPP für USA und Russland | 1995–2024 |
| `laender_haushalt_jahr.csv` | Einnahmen, Zinsausgaben, Quoten und Zins je Einwohner:in im Ländervergleich | Eurostat `gov_10a_main`, `nama_10_gdp`, `demo_pjan`; IWF WEO/FPP | 1995–2024 |
| `laender_inflation_monat.csv` | Inflationsrate je Land | Eurostat `prc_hicp_manr`, FRED `CPIAUCSL`, Rosstat/EMISS bzw. Bank of Russia | 1997-01–2026-10 |
| `laender_einkommen_jahr.csv` | Durchschnittseinkommen in drei Abgrenzungen | Eurostat `nama_10_gdp`, `demo_pjan`, `ilc_di03`, `nama_10_lp_ulc`; IWF WEO; FRED; Weltbank | 1995–2025 |
| `bip_deutschland_jahr.csv` | BIP nominal, realer Index und Wachstumsraten | Destatis 81000-0001 | 2016–2025 |
| `bip_wachstum_jahr.csv` | Reales BIP-Wachstum im Ländervergleich | Eurostat `nama_10_gdp`; IWF WEO für USA und Russland | 1995–2025 |
| `investitionen_jahr.csv` | Private und staatliche Bruttoanlageinvestitionen | Destatis 81000-0025, 81000-0001 | 2016–2025 |
| `produktion_deutschland_monat.csv` | Produktionsindex des Verarbeitenden Gewerbes | Destatis 42153-0001 | 2025-01–2026-09 |
| `produktion_deutschland_lang.csv` | Industrieproduktion mit Langfristtrend | Eurostat `sts_inpr_m` | 1993-01–2026-09 |
| `produktion_vergleich_monat.csv` | Produktionsindex im Ländervergleich | Eurostat `sts_inpr_m` | 1995-01–2026-09 |
| `energie_maerkte_monat.csv` | Heizöl sowie regionale Gas- und Öl-Benchmarks | EU Weekly Oil Bulletin; IWF und EIA über FRED; EZB | 1999-01–2026-11 |
| `inflation_de_monat.csv` | Inflation Deutschland: HVPI, Kerninflation, VPI | EZB ICP; Destatis 61111-0002 | 1992-01–2026-10 |
| `leitzinsen.csv` | Leitzinsen von EZB und Fed an den Tagen ihrer Änderung | EZB FM; Federal Reserve über FRED (`DFEDTAR`, `DFEDTARU`) | 1982–2026 |

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

**`inflation_de_monat.csv`** – Vorjahresraten in Prozent; die Reihen reichen
unterschiedlich weit (HVPI und Kerninflation bei der EZB bis Dezember 2025, VPI ab 1992).

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat |
| `hvpi_pct` | Harmonisierter Verbraucherpreisindex (EZB ICP `000000`) |
| `hvpi_kern_pct` | Kerninflation: HVPI ohne Energie, Nahrungsmittel, Alkohol und Tabak (EZB ICP `XEF000`) |
| `vpi_pct` | Nationaler Verbraucherpreisindex mit selbst genutztem Wohneigentum (Destatis 61111-0002) |

**`leitzinsen.csv`** – eine Zeile je Zinsänderung (Stufenreihe; der letzte
Beobachtungstag der Fed-Reihe ist als Endpunkt enthalten).

| Spalte | Bedeutung |
| --- | --- |
| `datum` | Tag, ab dem der Satz gilt |
| `leitzins` | `EZB Hauptrefinanzierungssatz` (Festzins; Juni 2000 bis Oktober 2008 Mindestbietungssatz der Zinstender), `EZB Einlagesatz`, `Fed Funds Zielsatz (ab 16.12.2008 Obergrenze)` |
| `zins_pct` | Zinssatz in Prozent |
| `quelle` | Kurzangabe der Quelle |

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

**`laender_schulden_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `geo`, `land` | Ländercode (Eurostat bzw. ISO-3166-alpha-3) und deutsche Bezeichnung |
| `schulden_mio_eur` | Schuldenstand des Gesamtstaats in Mio. € |
| `schuldenquote_pct` | Schuldenstand in % des BIP (amtliche Quote) |
| `quelle`, `quelle_key` | Verwendete Quelle und Schlüssel in `data/sources.json` |

**`laender_haushalt_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `geo`, `land` | Ländercode und deutsche Bezeichnung |
| `einnahmen_mio_eur` | Gesamteinnahmen (TR) in Mio. € |
| `zinsausgaben_mio_eur` | Tatsächliche Zinsausgaben (D41PAY) in Mio. € |
| `bip_mio_eur` | Bruttoinlandsprodukt in Mio. € |
| `bevoelkerung` | Bevölkerung |
| `zins_quote_bip_pct` | Zinsausgaben in % des BIP |
| `zins_quote_einnahmen_pct` | Zinsausgaben in % der Einnahmen |
| `zins_je_einwohner_eur` | Zinsausgaben je Einwohner:in in € |
| `quelle`, `quelle_key` | Verwendete Quelle und Schlüssel in `data/sources.json` |

**`laender_inflation_monat.csv`** – `monat`, `geo`, `land`, `inflation_pct`,
`quelle`, `quelle_key`. HVPI für die EU-Länder, CPI für die USA, Rosstat bzw.
verkettete 12-Monats-Rate der Bank of Russia für Russland.

**`laender_einkommen_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `geo`, `land` | Ländercode und deutsche Bezeichnung |
| `einkommensart` | `bip_pro_kopf`, `verfuegbar_pro_kopf` oder `bruttolohn` |
| `einkommen_eur` | Einkommen je Einwohner:in bzw. je Beschäftigten in € |
| `quelle`, `quelle_key` | Verwendete Quelle und Schlüssel in `data/sources.json` |

**`bip_deutschland_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `bip_nominal_mrd_eur` | Bruttoinlandsprodukt in jeweiligen Preisen, Mrd. € |
| `bip_real_index` | Bruttoinlandsprodukt preisbereinigt, Kettenindex 2020 = 100 |
| `bip_wachstum_nominal_pct`, `bip_wachstum_real_pct` | Veränderung gegenüber dem Vorjahr in % |

**`bip_wachstum_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `geo`, `land` | Ländercode (Eurostat bzw. ISO-3166-alpha-3) und deutsche Bezeichnung |
| `wachstum_pct` | Reales BIP-Wachstum in % (verkettete Volumina) |
| `quelle`, `quelle_key` | Verwendete Quelle und Schlüssel in `data/sources.json` |

Die Reihe enthält nur Ist-Jahre; Prognosejahre des IWF werden nicht übernommen.

**`investitionen_jahr.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `jahr` | Berichtsjahr |
| `sektor` | `Staat` oder `Nichtstaatliche Sektoren` (private Haushalte, Unternehmen, Organisationen ohne Erwerbszweck) |
| `investitionen_mrd_eur` | Bruttoanlageinvestitionen in jeweiligen Preisen, Mrd. € |
| `real_index` | Bruttoanlageinvestitionen preisbereinigt, Kettenindex 2020 = 100 |
| `anteil_bip_pct` | Investitionen in % des nominalen BIP |

**`produktion_deutschland_monat.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat (`JJJJ-MM`) |
| `jahr` | Berichtsjahr |
| `index_2021_original` | Produktionsindex, Originalwert (2021 = 100) |
| `index_2021_kalenderbereinigt` | kalenderbereinigt (X13 JDemetra+) |
| `index_2021_saisonbereinigt` | kalender- und saisonbereinigt (X13 JDemetra+) |
| `index_2021_bv4_saisonbereinigt` | kalender- und saisonbereinigt (BV4.1), soweit berichtet |
| `index_2021_trend` | BV4.1-Trend |

**`produktion_deutschland_lang.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat (`JJJJ-MM`) |
| `jahr` | Berichtsjahr |
| `index_2015` | Produktionsindex der Industrie ohne Baugewerbe (NACE B-D), kalender- und saisonbereinigt, 2015 = 100 |
| `trend_2015` | linearer Langfristtrend aus Januar 1993 bis Dezember 2017, fortgeschrieben |
| `abweichung_pct` | Abweichung des Index vom Trend in Prozent des Trends |

Die Reihe stammt aus Eurostat `sts_inpr_m` (Index 2021 = 100) und wird mit dem
Jahresmittel 2015 auf 2015 = 100 umbasiert. Der Trend ist eine lineare Regression
über die Monatswerte bis Dezember 2017.

**`produktion_vergleich_monat.csv`** – `monat`, `geo`, `land`, `index_2021`
(kalender- und saisonbereinigt, 2021 = 100), `quelle`, `quelle_key`.

**`energie_maerkte_monat.csv`**

| Spalte | Bedeutung |
| --- | --- |
| `monat` | Berichtsmonat (`JJJJ-MM`) |
| `heizoel_ct_l` | Heizöl, Verbraucherpreis Deutschland inkl. Steuern, ct/l |
| `heizoel_ct_kwh` | Heizöl, umgerechnet mit 1 l = 10 kWh, ct/kWh |
| `gas_ct_kwh` | Europäischer Gas-Benchmarkpreis (IWF), ct/kWh |
| `gas_ttf_eur_mwh` | TTF/Europa (IWF-Benchmark), €/MWh |
| `gas_jkm_eur_mwh` | JKM/Nordostasien (IWF-Preis für LNG Japan), €/MWh |
| `gas_henry_hub_eur_mwh` | Henry Hub/USA (EIA), €/MWh |
| `brent_eur_barrel` | Brent/Europa, Spotpreis (EIA) mit EZB-Tageskurs, €/Barrel |
| `brent_ct_kwh` | Brent, umgerechnet mit 1 Barrel = 1.700 kWh, ct/kWh |
| `wti_eur_barrel` | WTI/USA (EIA) mit EZB-Tageskurs, €/Barrel |
| `dubai_eur_barrel` | Dubai/Asien (IWF) mit EZB-Monatsdurchschnitt, €/Barrel |

Heizöl ist ein Endverbraucherpreis mit Steuern und Abgaben; Gas und Öl sind
Großhandels- bzw. Börsenpreise. Die Umrechnung in ct/kWh dient dem Vergleich der
Energiegehalte, nicht den tatsächlichen Haushaltskosten. Der JKM selbst ist ein
kostenpflichtiger Platts-Benchmark; die frei verfügbare Reihe ist der IWF-Preis für
LNG Japan.

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

Im Datenaufbau aktiv ist derzeit `fred_api`: Die US-Rendite
(`fred_us_10j_rendite.csv`) wird mit `FRED_API_KEY` über die FRED-API geholt und ohne
Schlüssel über den öffentlichen CSV-Export. Beide Wege erzeugen dieselbe Tabelle.

`destatis_api` lädt den Verbraucherpreisindex 61111-0002 mit `DESTATIS_API_TOKEN` über
`data/tablefile` mit `format=csv` ab 1991. Dieses Format entspricht der Exportdatei
(nur das Jahr steht lediglich beim Januar und wird beim Einlesen nach unten
aufgefüllt). Ohne Token wird der öffentliche Export geladen, der nur die letzten Jahre
enthält. Die übrigen Destatis-Tabellen nutzen weiterhin die Export-URLs.

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
* IWF (Primary Commodity Prices) und EIA (Brent) über FRED: Nutzungsbedingungen, Quellenangabe erforderlich
* Bank-of-Russia-Daten: Quellenangabe erforderlich
* EZB-Daten: Europäische Zentralbank, Quellenangabe erforderlich
* energy-charts.info: CC BY 4.0, Daten von Bundesnetzagentur | SMARD.de
* EU Weekly Oil Bulletin: © Europäische Union, Quellenangabe erforderlich
* Big-Mac-Index: The Economist, Quellenangabe erforderlich
* Bundeshaushalt: © Bundesministerium der Finanzen, Quellenangabe erforderlich
