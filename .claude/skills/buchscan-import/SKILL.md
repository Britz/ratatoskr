---
name: buchscan-import
description: Importiert eine eingescannte Buchseite (PDF/JPEG/PNG) in den Vault — kopiert sie nach `Reenactment/Anhang/Buecher/<BuchOrdner>/` mit normalisiertem Namen `buch_seite_NR_thema.ext`, präfixt das Original mit `moved_`, und fügt den Link als Tabellenzeile in den Abschnitt "## Anhang – Eingescannte Buchseiten" der zugehörigen Buch-MD ein. Wird ausgelöst, wenn der Nutzer eine Seite/Datei "ins Vault übernehmen", "in den Anhang kopieren", "als Scan einbinden" möchte.
---

# buchscan-import

Importiert Buchscans nach der Vault-Konvention. Strikt: keine Fakten erfinden — Seitenzahl und Thema kommen vom Nutzer oder werden nachgefragt.

## Inputs erwartet

- **Quelldatei(en)**: absoluter Pfad zu PDF/JPEG/PNG (z.B. `~/Downloads/Scan 2026-05-20.pdf`)
- **Buch**: Kurzname (`aros`, `haithabu`, ...) ODER Pfad/Dateiname der Buch-MD ODER eindeutiger Titel-Substring
- **Seite(n)**: Seitenzahl als Zahl oder Range (`192-193`)
- **Thema**: kurze Inhaltsbeschreibung (Kleinbuchstaben, ASCII)

Fehlt etwas → einmal sammeln nachfragen, nicht raten.

## Schritte

1. **Buch-MD auflösen**
   - In `Reenactment/Literatur/Buecher/` per `find` + Grep nach Kurzname/Substring suchen.
   - Mehrere Treffer → Nutzer wählen lassen.

2. **Anhang-Ordnernamen ermitteln** (in dieser Reihenfolge, erste Quelle gewinnt):
   1. YAML-Frontmatter-Feld `anhang_ordner` der Buch-MD (`grep '^anhang_ordner:' <md>` und Wert lesen).
   2. Bestehende Tabellen-Links: aus dem Abschnitt "Anhang – Eingescannte Buchseiten" das Muster `../../Anhang/Buecher/<X>/` extrahieren.
   3. Heuristik-Vorschlag aus der Buch-MD: CamelCase aus dem ersten markanten Substantiv des `title` (Eigenname > Thema > Autor; Umlaute ASCII; ohne Sonderzeichen). Beispiele:
      - "AROS – das Aarhus der Wikinger" → `AROS` (Akronym im Titel)
      - "Kalmring – Der Hafen von Haithabu" → `Haithabu` (Ortsname im Titel)
      - "Vorlagen für keltische Muster" → `KeltischeMuster` (Themenname)
      - "Die Wikingerschiffe in Oslo" → `Oslo` (Ortsname)
      Den Vorschlag dem Nutzer **einmal** zur Bestätigung zeigen, alternative annehmen.
   4. Sobald der Name bestätigt ist: in das YAML-Frontmatter der Buch-MD als `anhang_ordner: <Name>` schreiben — beim nächsten Mal ist es ableitbar.

3. **Zielordner sicherstellen**
   - `Reenactment/Anhang/Buecher/<BuchOrdner>/` anlegen, falls nicht vorhanden.

4. **Zieldateiname bilden**
   - Schema: `<buch>_seite_<NR>_<thema>.<ext>`
   - Normalisierung: Kleinbuchstaben, Leerzeichen → `_`, Umlaute → ASCII (`ä→ae, ö→oe, ü→ue, ß→ss`), keine sonstigen Sonderzeichen.
   - Existiert die Zieldatei bereits → mit dem Nutzer abklären (überschreiben? Suffix `_v2`?).

5. **Kopieren statt verschieben**
   - `cp` vom Originalpfad nach Zielpfad. Originaldatei bleibt erhalten.

6. **Original mit `moved_` präfixen**
   - Im Originalordner: Datei umbenennen zu `moved_<originalname_normalisiert>`.
   - Normalisierung des Originalnamens: Leerzeichen → `_`, Umlaute → ASCII. Extension bleibt.
   - Wenn das Original auf einem Read-only-Pfad liegt (z.B. eingehängte Quelle), überspringen und Nutzer informieren.

7. **Tabelle in der Buch-MD aktualisieren**
   - Abschnitt `## Anhang – Eingescannte Buchseiten` finden.
   - Fehlt der Abschnitt → vor `## Behandelte Fundorte` / `## Quellen` / am Ende der Datei anhängen, mit Header:
     ```
     ## Anhang – Eingescannte Buchseiten

     | Datei | Seite | Thema |
     | --- | --- | --- |
     ```
   - Neue Zeile einfügen:
     ```
     | [<dateiname>](../../Anhang/Buecher/<BuchOrdner>/<dateiname>) | <NR> | <Thema lesbar> |
     ```
   - **Thema lesbar**: Originaleingabe des Nutzers (mit Umlauten/Großschreibung), nicht die normalisierte Form.
   - Zeile an passender Stelle einsortieren: aufsteigend nach Seitenzahl, falls Tabelle existiert.

8. **Bericht**
   - Eine knappe Zusammenfassung: Quelldatei → Ziel, Original umbenannt zu, MD-Zeile eingefügt. Keine zusätzlichen Vermutungen über Buchinhalt.

## Wichtige Regeln

- **Niemals Thema oder Seitenzahl raten.** Wenn der Nutzer "die Seite mit dem Schwert" sagt, aber keine Zahl liefert: nachfragen.
- Temporäre Hilfsdateien gehören nach `~/.claude/tmp/`, nicht in den Workspace (siehe CLAUDE.md).
- Bei mehreren Scans im selben Aufruf: alle in einem Batch, eine Tabellen-Bearbeitung am Ende.
- Vorhandene Tabellenzeilen NIE umsortieren ohne Auftrag — nur die neue Zeile einsortieren.

## Beispiel

Eingabe: "Importier `~/Downloads/Scan 2026-05-20.pdf` ins AROS-Buch, Seite 45, Kämme"

Ergebnis:
- Kopie: `Reenactment/Anhang/Buecher/AROS/aros_seite_45_kaemme.pdf`
- Original: `~/Downloads/moved_Scan_2026-05-20.pdf`
- Neue Zeile in `Reenactment/Literatur/Buecher/Skov_2006_AROS_Aarhus.md`:
  `| [aros_seite_45_kaemme.pdf](../../Anhang/Buecher/AROS/aros_seite_45_kaemme.pdf) | 45 | Kämme |`
