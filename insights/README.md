# Insights

Datengeschichten zum Haushaltssimulator als Präsentationen. Jede Präsentation liegt in
einem eigenen Unterordner und ist eine einzelne HTML-Datei mit
[Reveal.js](https://revealjs.com/) (per CDN eingebunden, keine Installation nötig).

Die Folien sind im **Hochformat 9:16 (1080 × 1920)** gestaltet: auf dem Smartphone gut
lesbar und als Bildschirmaufnahme direkt für YouTube Shorts, Instagram oder Facebook
nutzbar.

| Foliensatz | Thema | Online |
| --- | --- | --- |
| [zinslast/index.html](zinslast/index.html) | Fast 100 Milliarden Euro Zinsen – woher kommt das? (13 Folien) | [Öffnen](https://cirrus18m.github.io/Haushaltssimulator/zinslast/) |
| [zinslast/kurz.html](zinslast/kurz.html) | Kurzfassung: Haushaltslücke, Kosten der Schulden, Vergleich, Verzögerung, Frankreich und Italien (5 Folien) | [Öffnen](https://cirrus18m.github.io/Haushaltssimulator/zinslast/kurz.html) |

Varianten eines Themas liegen im selben Ordner und teilen sich `stil.css`, `bilder/` und
`kennzahlen.json`.

## GitHub Pages

Der Workflow [.github/workflows/insights-pages.yml](../.github/workflows/insights-pages.yml)
veröffentlicht den Ordner `insights/` bei jedem Push auf `main`, der `insights/` ändert,
unter <https://cirrus18m.github.io/Haushaltssimulator/>. Die Startseite
[index.html](index.html) verlinkt alle Foliensätze.

Einmalig im Repository einstellen: **Settings → Pages → Build and deployment → Source:
GitHub Actions**. Danach läuft die Veröffentlichung automatisch; von Hand startet sie unter
**Actions → Insights auf GitHub Pages → Run workflow**.

## Ansehen

`index.html` im Browser öffnen. Blättern mit Pfeiltasten, Leertaste oder Wischen.
Weitere Tasten: `F` Vollbild, `O` Übersicht.

* **Als PDF:** `index.html?print-pdf` im Chrome öffnen und als PDF drucken.
* **Als Video:** Folie im Vollbild auf dem Smartphone oder in einem 1080 × 1920
  großen Browserfenster aufnehmen.

## Regeln

Es gelten die Projektregeln aus
[.github/copilot-instructions.md](../.github/copilot-instructions.md): deutsche Sprache,
jede Zahl mit Quelle, Modellrechnungen als solche gekennzeichnet.

* Diagramme und Kennzahlen entstehen per Skript **aus `data/processed/`** – nie von
  Hand. Je Präsentation erzeugt `diagramme.py` die SVG-Dateien in `bilder/` und
  schreibt alle im Text genannten Zahlen nach `kennzahlen.json`.
* Zahlen, die nicht in `data/processed/` liegen (z. B. aus dem Finanzplan des Bundes),
  stehen mit Fundstelle als Konstante im Skript.
* Nach einem Datenupdate: Skript neu ausführen und die Zahlen im Foliensatz mit
  `kennzahlen.json` abgleichen.

```bash
uv run python insights/zinslast/diagramme.py
```
