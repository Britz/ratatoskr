---
name: pdf-lesen
description: Liest ein PDF (auch Buchscan ohne OCR) und liefert daraus Textstellen, Zitate oder visuelle Beschreibungen einzelner Seiten — ohne dass jedes Mal pdftotext-Code neu geschrieben werden muss. Wird ausgelöst, wenn der Nutzer "lies das PDF", "was steht auf Seite X", "zitiere aus …", "schau dir Seite N an" sagt oder ein PDF/Scan in den Anhang-Ordnern referenziert. Liefert immer Quellenangabe (Datei + Seite) und markiert Unlesbares explizit als unleserlich.
---

# pdf-lesen

Dreistufiger Lese-Workflow für PDFs im Vault. Faktentreu — wörtlich zitieren oder klar als Paraphrase kennzeichnen, niemals "ergänzen".

## Stufe 1: Metadaten & Textextraktion

Erst Übersicht holen:

```bash
pdfinfo "<pfad>"          # Seitenanzahl, Erstellung, Format
```

Dann Text extrahieren (Layout erhalten):

```bash
pdftotext -layout -f <von> -l <bis> "<pfad>" -
```

- `-f`/`-l` (from/last page) eingrenzen, wenn der Nutzer eine konkrete Seite/Range nennt — sonst läuft das gesamte PDF.
- Stdout direkt lesen (kein temporäres File anlegen).
- Bei sehr großem Output: in Häppchen pro Seitenrange ausgeben.

Wenn nichts oder fast nichts zurückkommt → Stufe 2.

## Stufe 2a: OCR per `ocrmypdf` (bevorzugt für reine Scans)

Wenn Stufe 1 leer bleibt, **erst OCR versuchen** — das ist meistens schneller und exakter als visuelles Lesen:

```bash
ocrmypdf -l deu+eng --skip-text \
    "<pfad>" ~/.claude/tmp/<basename>_ocr.pdf
```

- `-l deu+eng` Sprachen (mehrere mit `+`). Verfügbar im Container: `deu`, `eng`, `dan`, `swe`, `nor`, `fra`, `lat`. Für AROS/Birka oft `-l deu+dan+swe+eng`.
- `--skip-text` lässt bereits vorhandene Textebenen unangetastet.
- Output landet in `~/.claude/tmp/` (Google-Drive-sicher, siehe CLAUDE.md). **Nie** ins Workspace.
- Anschließend wieder `pdftotext -layout` auf das OCR-PDF.

Bei einzelnen Seiten:

```bash
ocrmypdf -l deu+eng --pages <von>-<bis> --skip-text \
    "<pfad>" ~/.claude/tmp/<basename>_p<von>-<bis>_ocr.pdf
```

## Stufe 2b: Visuell lesen (Fallback / Tafeln / Karten)

Für Bildinhalte, Tabellen, Karten oder wenn OCR fehlschlägt — pro Seite ein PNG rendern und mit Read als Bild lesen:

```bash
pdftoppm -r 200 -f <seite> -l <seite> -png "<pfad>" ~/.claude/tmp/<basename>_p<seite>
```

- `-r 200` reicht meistens; bei feiner Schrift `-r 300`.
- Anschließend `Read <pfad>` auf die erzeugte PNG.

Bei mehreren Seiten: einzeln rendern und einzeln lesen, nicht in eine Riesendatei zusammenführen.

## Stufe 3: Aussage aus dem Inhalt formulieren

Beim Zitieren / Zusammenfassen für den Nutzer oder für einen Vault-Eintrag:

- **Wörtliches Zitat** in `> Blockquote` oder Anführungszeichen mit Quelle: `(Pfad, S. NR)`.
- **Paraphrase** klar gekennzeichnet, ohne hinzugefügte Details.
- **Unleserlich / nicht eindeutig** → ausdrücklich so schreiben (`unleserlich`, `auf Seite nicht eindeutig erkennbar`), nicht überbrücken.
- **Bildinhalte** (Tafeln, Karten, Zeichnungen): nur beschreiben, was tatsächlich zu sehen ist — keine ergänzten Stilzuschreibungen, Datierungen oder Materialien aus dem Bauch heraus.

## Wenn das PDF zu einem Buch im Vault gehört

Ist der PDF-Pfad unter `Reenactment/Anhang/Buecher/<Ordner>/` → prüfe in `Reenactment/Literatur/Buecher/`, ob es eine passende Buch-MD gibt, und nenne sie in der Antwort als Wikilink (`[[<Dateiname-ohne-md>]]`). So bleibt der Querverweis nutzbar.

## Aufräumen

Temporäre PNGs in `~/.claude/tmp/` sind unkritisch (persistentes Docker-Volume), aber am Sessionende ruhig `rm` löschen. **Nichts** ins Workspace schreiben.

## Beispiel-Antwortform

```
Quelle: Reenactment/Anhang/Buecher/AROS/aros_seite_29_handelkarte.pdf, S. 29

Auf der Karte sind eingezeichnet: Aros (Aarhus), Hedeby, Birka, Kaupang, Dublin, York,
sowie Routen nach Nowgorod und Kiew. Die Legende ist auf Dänisch.

Maßstab und Quelle der Karte sind auf der Seite nicht erkennbar.
```
