# Umsetzungsplan

Dieser Plan beschreibt, wie die Ideen aus [TODO.md](TODO.md) in mehreren, jeweils
lauffähigen Stufen in den Haushaltssimulator einfließen. Jede Stufe endet mit einem
lauffähigen Stand (App startet, Tests grün, Daten reproduzierbar) und einem Commit.

## Umsetzungsstand

| Stufe | Inhalt | Stand |
| --- | --- | --- |
| 0 | Fundament: Quellenbibliothek, Zeitstempel, Quellenseite, Export | umgesetzt |
| 1 | Haushalt: Einnahmen ohne neue Schulden, Ausgaben, Zinsausgaben | umgesetzt |
| 2 | Schulden und Zinslast: 10-jährige Bundesanleihe × Schuldenstand | umgesetzt |
| 3 | Internationaler Zinsvergleich | umgesetzt |
| 4 | Wirtschafts- und Geldindikatoren | umgesetzt, Sondervermögen offen |
| 5 | Haushaltspläne im Vergleich | offen |

## Leitplanken

Verbindlich für alle Stufen sind die Projektregeln in
[.github/copilot-instructions.md](.github/copilot-instructions.md): deutsche Sprache,
jede Grafik als SVG und HTML herunterladbar, jede Kennzahl mit Quelle und Abrufdatum,
Quellenbibliothek im Repository.

## Stufe 0 – Fundament (Quellen und Regeln)

Ziel: Nachvollziehbarkeit ist keine Nacharbeit, sondern Voraussetzung.

* `data/sources.json` als versionierte Quellenbibliothek: je Quelle Titel,
  Herausgeber, Lizenz, URL, Beschreibung, verwendete Datensätze, Datei, SHA-256 und
  Abrufzeitpunkt.
* `sources.py` schreibt die Bibliothek bei jedem Datenabruf fort; bereits geladene
  Dateien behalten ihren ursprünglichen Abrufzeitpunkt.
* Neue Seite **Quellen**: Übersicht „Welche Quelle liefert welche Daten?“, Details je
  Quelle und der Zeitpunkt des letzten Abrufs.
* `ui.plot()` ersetzt alle direkten `st.plotly_chart`-Aufrufe und bietet je Diagramm
  einen SVG- und einen HTML-Download.
* Projektregeln, Plan und README beschreiben den Ablauf.

Abnahmekriterien: Jede aufbereitete Tabelle lässt sich mindestens einer Quelle
zuordnen; die Quellenseite zeigt den Abrufzeitpunkt; jedes Diagramm ist als SVG und
HTML exportierbar.

## Stufe 1 – Haushalt („Haushaltseinkommen ohne neue Schulden“)

Ziel: Die Einnahmenseite des Staates als Bezugsgröße für Zinslasten verfügbar machen.

* Neue Quelle: Eurostat `gov_10a_main` (jährliche Einnahmen `TR`, Ausgaben `TE`,
  Zinsausgaben `D41PAY`, Finanzierungssaldo `B9`).
* Aufbereitung `haushalt_jahr.csv` für Gesamtstaat und Ebenen.
* Seite **Haushalt & Zinsen**, Abschnitt Haushalt: Einnahmen, Ausgaben,
  Zinsausgaben und Finanzierungssaldo im Zeitverlauf, jeweils mit Quote zum BIP.
* Wichtig: Einnahmen in der Volkswirtschaftlichen Gesamtrechnung enthalten keine
  Kreditaufnahme – sie entsprechen damit dem „Haushaltseinkommen ohne neue Schulden“.

Abnahmekriterien: Einnahmen, Ausgaben und Zinsausgaben liegen ab 1995 jährlich vor;
die Zinsausgabenquote (Zinsausgaben/Einnahmen) ist ausgewiesen.

## Stufe 2 – Schulden und Zinslast

Ziel: Die 10-jährige Bundesanleihe mit dem Schuldenstand verknüpfen.

* Neue Quelle: Deutsche Bundesbank, `BBSSY.D.REN.EUR.A630.000000WT1010.A`
  (Tagesrendite der aktuellen 10-jährigen Bundesanleihe).
* Aufbereitung `zins_bund_10j.csv` (täglich, mit Jahresdurchschnitt).
* Aufbereitung `zinslast_jahr.csv`: Schuldenstand × Jahresdurchschnittsrendite =
  theoretische Zinslast in Mrd. Euro, dazu Anteil an den Einnahmen (ohne neue
  Schulden) und am BIP – ergänzt um die tatsächlich gebuchten Zinsausgaben und die
  effektive Verzinsung (Zinsausgaben/Schuldenstand).
* Seite **Haushalt & Zinsen**, Abschnitte Schulden und Zinslast: Darstellung von
  Rendite, Schuldenstand und den drei Kennzahlen, inklusive Vergleich „theoretisch
  gegen tatsächlich“.

Abnahmekriterien: Für das letzte Datenjahr existieren theoretische Zinslast in
Mrd. Euro, in Prozent der Einnahmen und in Prozent des BIP; die Rechenwege sind im
Code dokumentiert und getestet.

## Stufe 3 – Internationaler Zinsvergleich

Ziel: Staatsanleiherenditen im europäischen und internationalen Vergleich.

* Neue Quellen: Eurostat `irt_lt_mcby_m` (monatliche Konvergenzrenditen der EU-
  Länder inkl. Vereinigtes Königreich), FRED `IRLTLT01USM156N` (USA, 10 Jahre) und
  Bank of Russia, Zero-Coupon-Yield-Curve (10-jährige OFZ-Rendite, Monatsendwerte).
* Aufbereitung `zins_vergleich.csv` (Monat, Land, Rendite, Quelle).
* Seite **Zinsvergleich**: Länderauswahl, Zeitraumauswahl, Verlauf der Renditen,
  Tabelle der letzten Werte inklusive Quelle und Datenstand.

Abnahmekriterien: Mindestens Deutschland, Frankreich, Italien, Spanien, USA und
Russland sind auswählbar; Herkunft und Datenstand jeder Reihe sind sichtbar.

## Stufe 4 – Wirtschafts- und Geldindikatoren (umgesetzt)

Ideen aus [TODO.md](TODO.md), umgesetzt als fünf Seiten mit eigenen Quellen:

* **Insolvenzen** – Destatis 52411-0002 und 52411-0011 (Verfahren, Forderungen,
  betroffene Arbeitnehmer).
* **Geld & Kaufkraft** – EZB BSI (M3) und ICP (HVPI Deutschland und Euro-Raum).
* **Energiepreise** – Destatis 61243-0002 und 61243-0011 (Strom/Gas Haushalte),
  energy-charts.info (Day-Ahead) und EU Weekly Oil Bulletin (Kraftstoffe).
* **Preisniveau & Wohnen** – The Economist (Big-Mac-Index) und Eurostat ilc_lvho02
  (Eigentumsquote).
* **Bund & Schuldendienst** – Eurostat gov_10a_main/gov_10dd_edpt1 (Sektor S1311) und
  BMF-Zinsausgaben am Kreditmarkt.

Offene Punkte dieser Stufe:

* Die GENESIS-Tabelle der Insolvenzen liefert nur das laufende Berichtsjahr. Für eine
  längere Monatsreihe ist der GENESIS-Webservice mit Zeitraumfilter und Zugangskennung
  nötig; bis dahin zeigt die Seite die verfügbaren Monate.
* **Sondervermögen** des Bundes liegen nicht als frei maschinenlesbare Zeitreihe vor.
  Die Seite weist sie deshalb noch nicht separat aus.

## Stufe 5 – Haushaltspläne im Vergleich

* Haushaltspläne von Bundesregierung und Opposition als strukturierte Daten erfassen
  (Grundlage unter anderem Bundestagsdrucksache 21/073/2107301).
* Einheitliches Schema für Einnahmen und Ausgaben je Ressort, damit Pläne
  vergleichbar werden.
* Vergleichsseite mit Differenzen je Ressort.

## Offene Punkte

* Sollen die Rohdaten aus `data/raw/` zusätzlich versioniert werden? Bislang
  versioniert das Repository nur die Quellenbibliothek und die aufbereiteten Daten.
* Für die Insolvenzen ist eine längere Monatsreihe über den GENESIS-Webservice zu
  beschaffen (Zeitraumfilter, Zugangskennung).
* Für die Sondervermögen des Bundes fehlt eine frei zugängliche, maschinenlesbare
  Quelle.
* Für Russland liefert die OECD-Reihe nur Daten bis 2018; deshalb der Rückgriff auf
  die Tagesdaten der Bank of Russia (Monatsendwerte).
* Die theoretische Zinslast ist eine Modellrechnung (gesamter Schuldenstand zur
  aktuellen Rendite) und keine Prognose der tatsächlichen Zinsausgaben.
