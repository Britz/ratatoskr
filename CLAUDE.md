# CLAUDE.md – Ratatoskr Vault

## Temporäre Downloads

Nur der Ordner `Reenactment/` wird mit Google Drive synchronisiert. Temporäre Dateien (Downloads via `curl`, `wget`, WebFetch-Zwischenablagen, Scratch-Dateien etc.) dürfen **niemals** unter `Reenactment/` landen.

Außerhalb von `Reenactment/` sind sie ok – bevorzugt unter `tmp/` im Workspace-Root oder in `~/.claude/tmp/` (persistentes Docker-Volume). Jeder Pfad, der für Temporäres im Workspace benutzt wird, muss in `.gitignore` stehen.

Nur Dateien, die explizit Teil des Vaults werden sollen (z. B. Buchscans nach Konvention), kommen unter `Reenactment/`.

## Faktentreue (sehr wichtig)

Dieser Vault ist eine **wissenschaftliche Faktensammlung** für historisches Reenactment. Daraus folgt eine harte Regel:

- **NIEMALS Fakten erfinden, raten oder plausibel klingende Details halluzinieren.** Auch nicht „zur Vervollständigung", nicht zur Glättung des Textes und nicht aus Allgemeinwissen, das nicht durch eine konkrete Quelle gedeckt ist.
- Das gilt insbesondere für: Inventarnummern, Datierungen, Maße, Materialien, Autorinnen/Autoren, Verlagsangaben, Seitenzahlen, Tafel-/Abbildungsnummern, Fundkontexte und Ortsangaben.
- **Unbekanntes wird explizit markiert**, z. B.:
  - `unbekannt` im YAML-Feld
  - `?` in Tabellen
  - Formulierungen wie „bislang nicht im Vault erfasst", „aus der Quelle nicht eindeutig hervorgehend", „nach Bibliotheksbesuch nachzutragen"
- **Quellenbasiert schreiben**: Jede Aussage muss aus einer im Vault verlinkten oder im Tool-Aufruf nachweisbaren Quelle stammen. Wenn die Quelle eine Aussage nicht enthält, darf die Aussage nicht im Eintrag erscheinen.
- **Bildbeschreibungen** dürfen nur das wiedergeben, was tatsächlich auf dem Bild zu sehen ist – keine ergänzenden Stilzuschreibungen, Materialien oder Datierungen aus dem Bauch heraus.
- **Bei Unsicherheit lieber knapper, dafür korrekt.** Lieber eine Lücke offenlassen als sie zu füllen.

## Vault-Struktur

Der Obsidian-Vault liegt unter `Reenactment/`. Die `.obsidian/`-Konfiguration befindet sich in `Reenactment/.obsidian/`.

Wichtige Ordner:

- `Reenactment/Literatur/Buecher/` – Literatureinträge als Markdown-Dateien (eine pro Buch)
- `Reenactment/Anhang/Buecher/` – Eingescannte Buchseiten, pro Buch ein Unterordner
- `Reenactment/Ausgrabungen/` – Alles rund um Ausgrabungen und Funde
  - `Fundorte/` – Ausgrabungsstätten (eine MD-Datei pro Ort)
  - `Funde/` – Einzelne Fundbelegeinträge (eine MD-Datei pro Fund)
  - `Karte.md` – Dataview-Übersicht aller Fundorte und Funde
- `Reenactment/Anhang/Fundebelege/` – Rohscans/Fotos von Funden, die noch nicht in Markdown erfasst sind

## Konvention: Buchscans

Eingescannte Seiten aus Büchern werden nach folgendem Schema verwaltet:

### Benennung (Kopien in Anhang)

```text
buch_seite_NR_thema.pdf   (oder .jpeg)
```

- **buch**: Kurzname des Buches, kurz und sprechend (z. B. `haithabu`, `aros`, `keltisch`)
- **NR**: Seitenzahl(en), bei Seitenbereich mit `-` verbunden (z. B. `192-193`)
- **thema**: Inhalt in Kleinbuchstaben, Leerzeichen als `_`, Umlaute als ASCII (`ae`, `oe`, `ue`)

### Speicherort

Kopien der Scans liegen unter:

```text
Reenactment/Anhang/Buecher/<BuchOrdner>/
```

Pro Buch wird ein eigener Unterordner angelegt, benannt nach dem Buch (z. B. `Haithabu`, `AROS`, `KeltischeMuster`). Bestehende Ordner sind in `Reenactment/Anhang/Buecher/` einsehbar.

Die Original-PDFs/JPEGs werden nach dem Kopieren mit dem Präfix `moved_` versehen, Leerzeichen durch `_` ersetzt, Umlaute als ASCII kodiert.

### Verlinkung in Literatureinträgen

Jede Buch-MD-Datei enthält einen Abschnitt `## Anhang – Eingescannte Buchseiten` mit einer Tabelle. Pfade sind relativ zur MD-Datei:

```markdown
| [dateiname.pdf](../../Anhang/Buecher/<BuchOrdner>/dateiname.pdf) | NR | Thema |
```

Da die MD-Dateien in `Literatur/Buecher/` liegen, ist der relative Pfad nach `Anhang/Buecher/` immer `../../Anhang/Buecher/`.
