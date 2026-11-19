# Umsetzungsplan

Dieser Plan beschreibt, wie die Ideen aus [TODO.md](TODO.md) in mehreren, jeweils
lauffähigen Stufen in den Haushaltssimulator einfließen. Jede Stufe endet mit einem
lauffähigen Stand (App startet, Tests grün, Daten reproduzierbar) und einem Commit.

Legende: ✅ umgesetzt · 🟡 teilweise umgesetzt · ⬜ offen

## Umsetzungsstand

| Stufe | Inhalt | Stand |
| --- | --- | --- |
| 0 | Fundament: Quellenbibliothek, Zeitstempel, Quellenseite, Export | ✅ umgesetzt |
| 1 | Haushalt: Einnahmen ohne neue Schulden, Ausgaben, Zinsausgaben | ✅ umgesetzt |
| 2 | Schulden und Zinslast: 10-jährige Bundesanleihe × Schuldenstand | ✅ umgesetzt |
| 3 | Internationaler Zinsvergleich | ✅ umgesetzt |
| 4 | Wirtschafts- und Geldindikatoren | ✅ umgesetzt (Sondervermögen ⬜) |
| 5 | Haushaltspläne im Vergleich | ⬜ offen |
| 6 | Zugangsdaten und API-Struktur | 🟡 umgesetzt (FRED im Datenaufbau ✅, Destatis-Tabellen ⬜) |

## Leitplanken

Verbindlich für alle Stufen sind die Projektregeln in
[.github/copilot-instructions.md](.github/copilot-instructions.md): deutsche Sprache,
jede Grafik als SVG und HTML herunterladbar, jede Kennzahl mit Quelle und Abrufdatum,
Quellenbibliothek im Repository.

## Stufe 0 – Fundament (Quellen und Regeln) ✅

Ziel: Nachvollziehbarkeit ist keine Nacharbeit, sondern Voraussetzung.

* ✅ `data/sources.json` als versionierte Quellenbibliothek: je Quelle Titel,
  Herausgeber, Lizenz, URL, Beschreibung, verwendete Datensätze, Datei, SHA-256 und
  Abrufzeitpunkt.
* ✅ `sources.py` schreibt die Bibliothek bei jedem Datenabruf fort; bereits geladene
  Dateien behalten ihren ursprünglichen Abrufzeitpunkt.
* ✅ Neue Seite **Quellen**: Übersicht „Welche Quelle liefert welche Daten?“, Details je
  Quelle und der Zeitpunkt des letzten Abrufs.
* ✅ Abschnitt **Quellen & Links** auf der Quellenseite: Portale, API-Dokumentation und
  Zugangsbedingungen aller Anbieter (Destatis GENESIS, Eurostat, Bundesbank, FRED,
  EZB Data Portal, Bank of Russia, energy-charts.info, EU Oil Bulletin, The Economist,
  BMF). Gepflegt in `sources.PROVIDER_LINKS`.
* ✅ `ui.plot()` ersetzt alle direkten `st.plotly_chart`-Aufrufe und bietet je Diagramm
  einen SVG- und einen HTML-Download.
* ✅ Projektregeln, Plan und README beschreiben den Ablauf.

Abnahmekriterien: Jede aufbereitete Tabelle lässt sich mindestens einer Quelle
zuordnen; die Quellenseite zeigt den Abrufzeitpunkt; jedes Diagramm ist als SVG und
HTML exportierbar.

## Stufe 1 – Haushalt („Haushaltseinkommen ohne neue Schulden“) ✅

Ziel: Die Einnahmenseite des Staates als Bezugsgröße für Zinslasten verfügbar machen.

* ✅ Neue Quelle: Eurostat `gov_10a_main` (jährliche Einnahmen `TR`, Ausgaben `TE`,
  Zinsausgaben `D41PAY`, Finanzierungssaldo `B9`).
* ✅ Aufbereitung `haushalt_jahr.csv` für Gesamtstaat und Ebenen.
* ✅ Seite **Haushalt & Zinsen**, Abschnitt Haushalt: Einnahmen, Ausgaben,
  Zinsausgaben und Finanzierungssaldo im Zeitverlauf, jeweils mit Quote zum BIP.
* ✅ Wichtig: Einnahmen in der Volkswirtschaftlichen Gesamtrechnung enthalten keine
  Kreditaufnahme – sie entsprechen damit dem „Haushaltseinkommen ohne neue Schulden“.

Abnahmekriterien: Einnahmen, Ausgaben und Zinsausgaben liegen ab 1995 jährlich vor;
die Zinsausgabenquote (Zinsausgaben/Einnahmen) ist ausgewiesen.

## Stufe 2 – Schulden und Zinslast ✅

Ziel: Die 10-jährige Bundesanleihe mit dem Schuldenstand verknüpfen.

* ✅ Neue Quelle: Deutsche Bundesbank, `BBSSY.D.REN.EUR.A630.000000WT1010.A`
  (Tagesrendite der aktuellen 10-jährigen Bundesanleihe).
* ✅ Aufbereitung `zins_bund_10j.csv` (täglich, mit Jahresdurchschnitt).
* ✅ Aufbereitung `zinslast_jahr.csv`: Schuldenstand × Jahresdurchschnittsrendite =
  theoretische Zinslast in Mrd. Euro, dazu Anteil an den Einnahmen (ohne neue
  Schulden) und am BIP – ergänzt um die tatsächlich gebuchten Zinsausgaben und die
  effektive Verzinsung (Zinsausgaben/Schuldenstand).
* ✅ Seite **Haushalt & Zinsen**, Abschnitte Schulden und Zinslast: Darstellung von
  Rendite, Schuldenstand und den drei Kennzahlen, inklusive Vergleich „theoretisch
  gegen tatsächlich“.

Abnahmekriterien: Für das letzte Datenjahr existieren theoretische Zinslast in
Mrd. Euro, in Prozent der Einnahmen und in Prozent des BIP; die Rechenwege sind im
Code dokumentiert und getestet.

## Stufe 3 – Internationaler Zinsvergleich ✅

Ziel: Staatsanleiherenditen im europäischen und internationalen Vergleich.

* ✅ Neue Quellen: Eurostat `irt_lt_mcby_m` (monatliche Konvergenzrenditen der EU-
  Länder inkl. Vereinigtes Königreich), FRED `IRLTLT01USM156N` (USA, 10 Jahre) und
  Bank of Russia, Zero-Coupon-Yield-Curve (10-jährige OFZ-Rendite, Monatsendwerte).
* ✅ Aufbereitung `zins_vergleich.csv` (Monat, Land, Rendite, Quelle).
* ✅ Seite **Zinsvergleich**: Länderauswahl, Zeitraumauswahl, Verlauf der Renditen,
  Tabelle der letzten Werte inklusive Quelle und Datenstand.

Ausbau derselben Seite um Schulden, Zinsausgaben und Preise:

* ✅ **Schuldenstand und Schuldenquote** der europäischen Länder über die Zeit
  (Eurostat `gov_10dd_edpt1`).
* ✅ **Zinsausgaben** je Land in Prozent des BIP und je Einwohner:in in Euro
  (Eurostat `gov_10a_main`, `nama_10_gdp`, `demo_pjan`) – die Pro-Kopf-Angabe macht
  Länder unterschiedlicher Größe vergleichbar.
* ✅ **Theoretische Zinslast bei aktuellem Marktzins** je Land: Schuldenstand des
  letzten Jahres × aktuelle 10-jährige Rendite, ausgewiesen in Mrd. Euro, in Prozent
  des BIP, in Prozent der Einnahmen und je Einwohner:in (`analysis.theoretical_interest_by_country`).
* ✅ **Inflation (HVPI) und Realzins** je Land, monatlich; der Realzins ist die
  Rendite minus Inflationsrate (`analysis.real_interest_rate`).
* ✅ **USA und Russland** in allen Abschnitten: Schuldenquote, Einnahmen und
  Zinsausgaben aus der IWF-Datenbank *Public Finances in Modern History*, BIP und
  Bevölkerung aus dem *World Economic Outlook*, umgerechnet mit dem
  EZB-Jahresdurchschnitt des Dollar-Euro-Kurses. Monatliche Inflation: CPI über
  FRED für die USA, Rosstat/EMISS für Russland (ohne Schlüssel: verkettete
  12-Monats-Rate der Bank of Russia).
* ✅ **Durchschnittseinkommen** in drei Abgrenzungen (BIP je Einwohner:in,
  verfügbares Einkommen je Einwohner:in, Bruttoverdienst je Beschäftigten), in der
  App umschaltbar. Die theoretische Zinslast je Einwohner:in wird zusätzlich als
  Prozentsatz der gewählten Einkommensgröße ausgewiesen.
* ⬜ Für Russland liegt weder das verfügbare Haushaltseinkommen (derzeit ersatzweise
  BNE je Einwohner:in der Weltbank) noch der Bruttoverdienst automatisch abrufbar
  vor; dafür wäre ein Rosstat-Abruf mit API-Key beziehungsweise ein manueller
  Export nötig.

Abnahmekriterien: Mindestens Deutschland, Frankreich, Italien, Spanien, USA und
Russland sind auswählbar; Herkunft und Datenstand jeder Reihe sind sichtbar; für
alle Länder liegen Schuldenquote, Zinsquote, Zins je Einwohner:in, theoretische
Zinslast, Inflation und Realzins vor.

## Stufe 4 – Wirtschafts- und Geldindikatoren ✅

Ideen aus [TODO.md](TODO.md), umgesetzt als sechs Seiten mit eigenen Quellen:

* ✅ **Insolvenzen** – Destatis 52411-0002 und 52411-0011 (Verfahren, Forderungen,
  betroffene Arbeitnehmer), dazu die manuell exportierte Langreihe 52411-0017.
* ✅ **Geld & Kaufkraft** – EZB BSI (M3) und ICP (HVPI Deutschland und Euro-Raum).
* ✅ **Energiepreise** – Destatis 61243-0002 und 61243-0011 (Strom/Gas Haushalte),
  energy-charts.info (Day-Ahead), EU Weekly Oil Bulletin (Kraftstoffe und Heizöl)
  sowie regionale Gas- und Öl-Benchmarks (TTF, JKM, Henry Hub; Brent, WTI, Dubai)
  über FRED.
* ✅ **Preisniveau & Wohnen** – The Economist (Big-Mac-Index) und Eurostat ilc_lvho02
  (Eigentumsquote).
* ✅ **Bund & Schuldendienst** – Eurostat gov_10a_main/gov_10dd_edpt1 (Sektor S1311) und
  BMF-Zinsausgaben am Kreditmarkt.
* ✅ **Wirtschaft** – reales BIP-Wachstum (Destatis 81000-0001, Eurostat `nama_10_gdp`,
  IWF-WEO für USA und Russland), Produktionsindex des Verarbeitenden Gewerbes
  (Destatis 42153-0001, Eurostat `sts_inpr_m`) sowie private und staatliche
  Bruttoanlageinvestitionen (Destatis 81000-0025) mit Investitionsquote zum BIP.

Offene Punkte dieser Stufe:

* ✅ Die Insolvenzen nutzen die manuell exportierte GENESIS-Langreihe 52411-0017
  (2003–2026) sowie die Tabellen 52411-0002 und 52411-0011 für das laufende
  Berichtsjahr.
* ⬜ **Sondervermögen** des Bundes liegen nicht als frei maschinenlesbare Zeitreihe vor.
  Die Seite weist sie deshalb noch nicht separat aus.

## Stufe 5 – Haushaltspläne im Vergleich ⬜

* ⬜ Haushaltspläne von Bundesregierung und Opposition als strukturierte Daten erfassen
  (Grundlage unter anderem Bundestagsdrucksache 21/073/2107301).
* ⬜ Einheitliches Schema für Einnahmen und Ausgaben je Ressort, damit Pläne
  vergleichbar werden.
* ⬜ Vergleichsseite mit Differenzen je Ressort.

## Stufe 6 – Zugangsdaten und API-Struktur 🟡

Ziel: Weitere Datenquellen anbindbar machen, ohne Geheimnisse zu versionieren.

* ✅ `.env.example` als Vorlage (versioniert), `.env` mit den echten Werten
  (gitignored), `secrets/` ebenfalls ignoriert.
* ✅ `config.py` lädt Zugangsdaten aus Umgebung und `.env`; Platzhalter wie
  `MY_DESTATIS_TOKEN_HERE` werden als „nicht gesetzt“ erkannt.
* ✅ `destatis_api.py`: GENESIS-Online-Client mit Token als `username`-Header,
  `helloworld/logincheck` und `data/tablefile` (ffcsv, ZIP-Entpackung).
* ✅ `fred_api.py`: FRED-Client für Serienbeobachtungen (`series/observations`).
* ✅ Prüfskripte `scripts/check_destatis_api.py` und `scripts/check_fred_api.py`
  bestätigen die Zugänge, ohne Werte auszugeben.
* ✅ FRED ist im Datenaufbau aktiv: Die US-Rendite (`fred_us_zins`, Modus
  `fred_api`) kommt mit `FRED_API_KEY` aus der FRED-API, ohne Schlüssel aus dem
  öffentlichen CSV-Export. Beide Wege liefern identische aufbereitete Daten.
* ⬜ Die Destatis-Tabellen nutzen weiterhin die Export-URLs. Grund: Das API-Format
  (`format=csv` mit `transpose`) hat eine andere Kopfstruktur als die Exportdateien
  (`{code}_00.csv`), und `ffcsv` liefert eine Zeile je Wert – die vorhandenen Parser
  erwarten die Exportspalten. Nächster Schritt: generischer `parse_ffcsv`-Parser
  (Zeit, Merkmale, `value`, `value_unit`, `value_variable_code`) und Umstellung der
  sechs Destatis-Tabellen auf `fetch_mode="destatis_api"`.

## Offene Punkte

* ✅ Rohdaten: automatisch geladene Dateien bleiben aus `data/raw/` ausgeschlossen,
  von Hand geladene Dateien liegen versioniert unter `data/raw/manual/`.
* ⬜ Die Insolvenz-Langreihe 52411-0017 könnte statt als manueller Export über den
  GENESIS-Webservice abgerufen werden.
* ⬜ Für die Sondervermögen des Bundes fehlt eine frei zugängliche, maschinenlesbare
  Quelle.
* ⬜ Für Russland liefert die OECD-Reihe nur Daten bis 2018; deshalb der Rückgriff auf
  die Tagesdaten der Bank of Russia (Monatsendwerte). Eine dauerhafte Lösung ist offen.
* Hinweis: Die theoretische Zinslast ist eine Modellrechnung (gesamter Schuldenstand zur
  aktuellen Rendite) und keine Prognose der tatsächlichen Zinsausgaben.
