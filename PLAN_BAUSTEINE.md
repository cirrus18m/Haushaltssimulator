# Plan: Bausteine, Einfach-/Expertenansicht und Berichtsexport

Status: Stufen 7.1–7.3 und Teile von 7.4 an der Pilotseite **Insolvenzen** umgesetzt (siehe
„Umsetzungsstand“). Ergänzt [PLAN.md](PLAN.md) als Stufe 7.

Getroffene Entscheidungen: Ansicht **global** (Schalter in der Seitenleiste,
`?ansicht=experte`), Export-Diagramme standardmäßig **interaktiv**, Reveal.js und plotly.js
per **CDN**, Pilotseite **Insolvenzen**.

## Ziel

1. **Zwei Ansichten je Seite**: eine *einfache* Ansicht (Kernaussage, wenige Diagramme,
   Erklärung in Alltagssprache) und eine *Expertenansicht* (alle Diagramme, Tabellen,
   Parameter, Methodik, Abgrenzungen). Umschaltbar auf jeder Seite.
2. **Eigener Bericht**: In der App einzelne Diagramme, Kennzahlen oder ganze Abschnitte
   anhaken, auf einer Seite **Bericht** sortieren und ohne KI als eigenständige
   Reveal.js-HTML-Datei exportieren – wahlweise im **Querformat** (Rechner, Beamer) oder
   **Hochformat** (Smartphone, wie die bestehenden Insights).
3. **Grundstruktur „React + LaTeX“**: Inhalte liegen einmal als gleichartige
   **Bausteine** vor (Diagramm + Erklärung + Quellen + Metadaten). Seiten der App,
   Ansichten und Berichte sind nur noch **Zusammenstellungen** dieser Bausteine – wie
   Komponenten in React oder `\input{}` in LaTeX. Inhalt und Darstellung sind getrennt.

## Ausgangslage

* 15 Seiten unter `app/pages/` mit zusammen rund 53 `ui.plot(...)`-Aufrufen. Die
  Diagramme werden direkt im Seitencode gebaut (Daten laden → Figure → `ui.plot`),
  Erklärtexte und Quellen-Captions stehen als `st.markdown`/`st.caption` dazwischen.
* `ui.style()` legt Layout und Farben für die App fest; `insights/<thema>/diagramme.py`
  baut dieselben Diagramme ein zweites Mal mit eigenem Layout für das Hochformat
  (1080 × 1920, Mindestschrift 30 px).
* Folge: Ein Diagramm existiert heute teils doppelt, und es gibt keine Stelle, an der
  „dieses Diagramm mit Titel, Erklärung und Quellen“ als Objekt greifbar wäre. Genau
  dieses Objekt braucht man für Ansichten und Export.

## Kernidee: der Baustein

Ein Baustein ist eine Python-Dataclass in einem neuen Modul
`src/haushaltssimulator/bausteine/` – **ohne Streamlit**, damit App, Export, Insights und
Tests ihn gleichermaßen nutzen.

```python
@dataclass(frozen=True)
class Baustein:
    id: str                      # eindeutig, stabil, z. B. "insolvenzen.langreihe"
    titel: str                   # Diagrammtitel / Folienüberschrift
    art: Art                     # DIAGRAMM | KENNZAHLEN | TABELLE | TEXT
    ebene: Ebene                 # EINFACH | EXPERTE  (EINFACH erscheint in beiden Ansichten)
    quellen: tuple[str, ...]     # Schlüssel aus data/sources.json (Pflicht, per Test geprüft)
    kernaussage: str             # ein Satz, für einfache Ansicht und Folie
    erklaerung: str              # Markdown, Alltagssprache
    methodik: str = ""           # Markdown, nur Expertenansicht (Abgrenzung, Formeln)
    parameter: tuple[Parameter, ...] = ()   # z. B. Zeitraum, Länderauswahl, Szenariowerte
    erzeuge: Callable[[Kontext], Inhalt]    # reine Funktion: Daten + Parameter → Inhalt
    schlagworte: tuple[str, ...] = ()
```

* `erzeuge` liefert **inhaltliche** Ergebnisse (Plotly-Figure ohne Endlayout, Kennzahlen
  als Liste, DataFrame) – **kein** Styling. Das Layout setzt erst das Ausgabeziel.
* `Kontext` enthält die geladenen Daten (über `dataset.load_*`) und die Parameterwerte.
* `Parameter` beschreibt ein Bedienelement abstrakt (Typ, Standardwert, Wertebereich,
  Beschriftung). Die App macht daraus ein Widget; der Export friert den aktuellen Wert ein.
* Registrierung über einen Dekorator, z. B.

  ```python
  @baustein(id="insolvenzen.langreihe", titel="Unternehmensinsolvenzen seit 2003",
            art=Art.DIAGRAMM, ebene=Ebene.EINFACH, quellen=("destatis_insolvenzen",), ...)
  def langreihe(k: Kontext) -> go.Figure: ...
  ```

  Ein Modul je Thema (`bausteine/insolvenzen.py`, `bausteine/zinsen.py` …) – analog zu
  den Quellmodulen. `REGISTRY: dict[str, Baustein]` sammelt alle.

### Seiten als Zusammenstellung

```python
SEITE_INSOLVENZEN = Seite(
    titel="Insolvenzen",
    einleitung="…",
    abschnitte=(
        Abschnitt("Überblick", ("insolvenzen.kennzahlen", "insolvenzen.langreihe")),
        Abschnitt("Verfahrensausgang", ("insolvenzen.ausgang",)),
        Abschnitt("Aktuelles Berichtsjahr", ("insolvenzen.aktuell", "insolvenzen.tabelle")),
    ),
)
```

Die Seitendatei unter `app/pages/` schrumpft auf `ui.zeige_seite(SEITE_INSOLVENZEN)`.
Seiten mit stark verschachtelter Interaktion (Szenario-Rechner) dürfen Bausteine auch
einzeln mit `ui.zeige_baustein(...)` einbinden und eigenen Code behalten (Hybridbetrieb).

### Ausgabeziele (Trennung von Inhalt und Darstellung)

```
            Baustein.erzeuge(Kontext)  →  Inhalt (Figure ohne Layout, Kennzahlen, Tabelle)
                         │
        ┌────────────────┼──────────────────────┐
        ▼                ▼                      ▼
  Ziel APP          Ziel QUERFORMAT        Ziel HOCHFORMAT
  ui.style()        1920 × 1080, Folie     1080 × 1920, Mindestschrift 30 px
  ui.plot()         Reveal.js-Abschnitt    Reveal.js-Abschnitt (wie insights/)
```

Ein Modul `layout.py` bündelt die drei Profile (Schriftgrößen, Ränder, Legendenposition,
Breite/Höhe). `ui.style()` wird zum Profil „App“; die Layoutfunktion aus
`insights/zinslast/diagramme.py` wird zum Profil „Hochformat“.

## Funktion 1: Einfache und Expertenansicht

* **Umschalter global** in der Seitenleiste von `app/main.py`
  (`st.segmented_control("Ansicht", ["Einfach", "Experte"])`), gespeichert in
  `st.session_state["ansicht"]` und gespiegelt in `st.query_params["ansicht"]`, damit ein
  Link die Ansicht mitnimmt. Global statt je Seite, weil man beim Seitenwechsel sonst
  ständig neu umschalten müsste; eine Seite kann die Wahl lokal überschreiben.
* **Was sich unterscheidet**

  | | Einfach | Experte |
  | --- | --- | --- |
  | Bausteine | nur `ebene=EINFACH` | alle |
  | Text | `kernaussage` + `erklaerung` | zusätzlich `methodik`, Abgrenzungen |
  | Parameter | feste, sinnvolle Standardwerte | alle Widgets sichtbar |
  | Tabellen | ausgeblendet | sichtbar, mit CSV-Download |
  | Downloads SVG/HTML | ja | ja |

* Die Einteilung erfolgt **am Baustein**, nicht im Seitencode – eine Seite muss dafür
  nichts wissen.
* Startansicht: *Einfach* (für neue Besucher). Offen: Soll die Wahl über Sitzungen
  hinweg erhalten bleiben? Streamlit kennt keinen Browserspeicher ohne Zusatzpaket;
  der Query-Parameter reicht für Lesezeichen.

## Funktion 2: Bericht zusammenstellen und exportieren

### In der App

* Jeder Baustein erhält neben SVG/HTML einen Knopf **„+ Bericht“** (Häkchen-Zustand).
  Jeder Abschnitt erhält **„Abschnitt zum Bericht“**.
* Der **Berichtskorb** liegt in `st.session_state["bericht"]` als Liste von
  Einträgen `{"id": …, "parameter": {…}}` – die eingefrorenen Parameterwerte sorgen
  dafür, dass genau das Diagramm exportiert wird, das man gesehen hat (z. B. gewählte
  Länder).
* Seitenleiste: „Bericht: 5 Bausteine →“ als Link zur neuen Seite **Bericht**.

### Seite „Bericht“

1. Liste der gewählten Bausteine mit Vorschau, Reihenfolge ändern (▲/▼ oder
   `st.data_editor` mit Spalte „Position“), entfernen.
2. Berichtsangaben: Titel, Untertitel, Autor (optional), Datum.
3. Optionen:
   * Format: **Querformat 16:9** oder **Hochformat 9:16**
   * Diagramme: **interaktiv** (Plotly im Browser) oder **statisch** (SVG)
   * Text je Folie: Kernaussage / + Erklärung / + Methodik
   * Abschlussfolie **„Quellen“** (automatisch, aus `data/sources.json` mit Lizenz und
     Abrufzeitpunkt – erfüllt die Quellenpflicht ohne Handarbeit)
4. **Export** → Download `bericht_<datum>.html` (eine Datei).
5. **Konfiguration speichern/laden** als kleine JSON-Datei (Bausteine + Parameter +
   Optionen). Damit geht beim Neuladen der Seite nichts verloren, und ein Bericht lässt
   sich nach einem Datenupdate mit neuen Zahlen neu erzeugen.

### Erzeugung (rein, testbar)

Neues Modul `bericht.py` ohne Streamlit:

```python
def erzeuge_bericht(konfiguration: BerichtKonfiguration) -> str:  # fertiges HTML
```

* HTML-Vorlage mit `string.Template` (keine neue Abhängigkeit) oder Jinja2, abgelegt
  unter `src/haushaltssimulator/vorlagen/`.
* Je Baustein ein `<section>`: Kicker (Seite/Abschnitt), Überschrift, Diagramm,
  Kernaussage, Quellzeile – dieselben CSS-Klassen wie `insights/zinslast/stil.css`
  (`kicker`, `kern`, `quelle`), damit Berichte und Insights gleich aussehen.
* **Interaktive Diagramme ohne Serverrendering**: Die Figure wird als JSON eingebettet
  und im Browser mit plotly.js gezeichnet. Das umgeht Kaleido/Chrome, das auf Streamlit
  Community Cloud unsicher ist (heute fällt `ui._svg_bytes` dort ggf. auf
  `SVG_NICHT_VERFUEGBAR` zurück). Die statische SVG-Variante bleibt als Option für
  lokale Nutzung und Druck.
* **Offline-Fähigkeit**: Reveal.js (MIT) und plotly.js wahlweise per CDN
  (Datei ~ 100 kB) oder eingebettet (Datei ~ 5 MB, funktioniert ohne Netz, z. B. im
  Vortragsraum). Für die eingebettete Variante werden die minifizierten Dateien
  versioniert unter `vorlagen/` abgelegt.
* PDF entsteht wie bei den Insights über `?print-pdf` im Chrome – kein eigener Export
  nötig.

## Verhältnis zu den Insights

* Kurzfristig bleiben die handgeschriebenen Foliensätze unverändert (viel Erzähltext,
  eigene Gestaltung).
* Mittelfristig kann `insights/<thema>/diagramme.py` die Diagramme aus der Registry
  holen statt sie neu zu bauen (Profil „Hochformat“) – damit gibt es jedes Diagramm nur
  noch einmal.
* Langfristig lässt sich ein Insight als **versionierte Berichtskonfiguration** plus
  eigene Textfolien beschreiben (`insights/<thema>/bericht.json`) – also genau das, was
  ein Nutzer in der App zusammenklickt, nur im Repository gepflegt.

## Umsetzungsstand

| Stufe | Stand |
| --- | --- |
| 7.1 Grundgerüst + Pilotseite | ✅ `bausteine/kern.py`, `bausteine/insolvenzen.py` (6 Bausteine), `ui.zeige_seite`/`ui.zeige_baustein`, `format.py` |
| 7.2 Ansichten | ✅ Schalter „Expertenansicht“ in `app/main.py`; Parameter-Widgets, Tabellen und Methodik nur in der Expertenansicht |
| 7.3 Bericht | ✅ Knöpfe „Zum Bericht“/„Abschnitt zum Bericht“, Seite **Bericht** (ordnen, Optionen, Vorschau, JSON speichern/laden), `bericht.py` |
| 7.4 Hochformat, statisch, offline | 🟡 Hochformat ✅, statische SVG mit Rückfall ✅, Offline-Variante (eingebettete Bibliotheken) ⬜ |
| 7.5 Übrige Seiten | ⬜ |
| 7.6 Insights aus der Registry | ⬜ |

Abweichungen vom Entwurf: Die Tabelle auf Folien zeigt im Querformat höchstens 8, im
Hochformat 14 Zeilen; Diagramme werden auf der Folie flacher, wenn die Methodik mit
ausgegeben wird. Markdown in Texten wird für den Export mit einem kleinen eigenen
Umsetzer (Absätze, Listen, fett, Code) übertragen, ohne neue Abhängigkeit.

## Umsetzung in Stufen

Jede Stufe endet lauffähig, mit grünen Tests und einem Commit.

| Stufe | Inhalt | Ergebnis |
| --- | --- | --- |
| 7.1 | `bausteine/`-Paket: `Baustein`, `Parameter`, `Kontext`, Registry, `layout.py` mit Profil „App“; `ui.zeige_baustein`/`ui.zeige_seite`. **Pilot: Seite Insolvenzen** (3 Diagramme, Kennzahlen, Tabelle) vollständig umstellen. | Gleiche Seite wie vorher, aber aus Bausteinen. Bewertungsgrundlage für alles Weitere. |
| 7.2 | Ansichtsumschalter in `main.py`, `ebene` + `methodik` für die Pilotseite. | Einfach/Experte auf Insolvenzen erlebbar. |
| 7.3 | Berichtskorb, Seite **Bericht**, `bericht.py` mit Querformat + interaktiven Diagrammen + Quellenfolie; JSON speichern/laden. | Erster Export aus der Pilotseite. |
| 7.4 | Profil Hochformat (aus Insights übernommen), statische SVG-Option, Offline-Variante. | Handy- und Rechnersicht im Export. |
| 7.5 | Übrige Seiten migrieren, klein nach groß: Zeitreihe, Ebenen, Bundesländer, Analysen, Geld & Kaufkraft, Preisniveau, Bund & Schuldendienst, Überblick, Energiepreise, Wirtschaft, Zinsvergleich, **Haushalt & Zinsen** (1082 Zeilen) zuletzt, Szenario-Rechner im Hybridbetrieb. | Alle Diagramme exportierbar, beide Ansichten überall. |
| 7.6 | Insights holen Diagramme aus der Registry; optional Berichtskonfigurationen im Repo. | Keine doppelten Diagramme mehr. |

Bis eine Seite migriert ist, läuft sie unverändert weiter – alte und neue Seiten können
nebeneinander existieren.

## Tests

* **Registry**: IDs eindeutig; jeder Baustein hat Titel, Kernaussage und mindestens eine
  Quelle, und jede Quelle existiert in `data/sources.json`.
* **Erzeugung**: Jeder Baustein läuft mit den Standardparametern auf `data/processed/`
  fehlerfrei; Diagramme haben Achsentitel (Projektregel 2) – wird so erstmals
  automatisch geprüft statt nur per Review.
* **Ansichten**: `test_streamlit_pages_run_without_exception` zusätzlich über
  `ansicht ∈ {einfach, experte}` parametrisieren.
* **Bericht**: `erzeuge_bericht` liefert gültiges HTML mit genau n + Titel + Quellen
  `<section>`s; Mindestschrift im Hochformat wie in `tests/test_insights.py`;
  JSON-Konfiguration übersteht Hin- und Rückweg.
* `test_app_does_not_import_api_clients` gilt unverändert auch für `bausteine/`.

## Risiken und offene Fragen

* **Aufwand der Migration**: ~53 Diagramme umzuziehen ist der Großteil der Arbeit.
  Deshalb zuerst eine Pilotseite und danach eine bewusste Entscheidung.
* **Abhängige Diagramme**: Manche Diagramme teilen sich berechnete Zwischenergebnisse
  oder Widgets (z. B. Zeitraumregler für mehrere Diagramme). Lösung: gemeinsame
  Parameter auf Abschnittsebene, Berechnungen nach `analysis.py`.
* **Widget-Schlüssel**: Bausteine kommen mehrfach vor (Seite und Berichtsvorschau);
  Schlüssel daher aus `baustein.id` + Ort ableiten.
* **Streamlit-Zustand** ist pro Browsersitzung; ohne gespeicherte JSON-Datei ist der
  Berichtskorb nach einem Neuladen leer.
* **Einfache Ansicht braucht Redaktion**: Kernaussagen und Alltagssprache müssen
  geschrieben werden – das ist inhaltliche, keine technische Arbeit. Kernaussagen mit
  Zahlen dürfen keine festen Zahlen enthalten, sondern werden aus den Daten gefüllt
  (wie `kennzahlen.json` bei den Insights), sonst veralten sie.
* **Dateigröße**: Ein eingebetteter Bericht mit plotly.js ist ~ 5 MB – für E-Mail
  grenzwertig, daher CDN als Standard.

## Zu entscheidende Punkte

1. Ansicht **global** (Vorschlag) oder je Seite getrennt umschaltbar?
2. Export-Diagramme standardmäßig **interaktiv** (Vorschlag, läuft auch in der Cloud)
   oder statisch SVG?
3. Reveal.js/plotly.js im Export per **CDN** (Vorschlag) oder eingebettet als Standard?
4. Pilotseite **Insolvenzen** (klein, Vorschlag) oder gleich eine zentrale Seite wie
   Haushalt & Zinsen?
5. Sollen Insights langfristig auf Berichtskonfigurationen umgestellt werden (7.6)?
