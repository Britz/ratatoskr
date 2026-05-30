---
name: bild-bearbeiten
description: Bearbeitet Bilder (JPEG/PNG/TIFF/PDF-Seiten) für den Vault — zuschneiden, drehen/entzerren, aufhellen/kontrastieren, Größe ändern, Format umwandeln, Metadaten lesen/setzen, mehrere Bilder zu PDF zusammenfügen. Enthält zusätzlich einen Helfer für Tafel-Verifikation gegen den Vault-Bildindex (Cache-Lookup, Preset-Crop, Beschreibungs-Grep). Wird ausgelöst, wenn der Nutzer "Bild zuschneiden", "Scan begradigen", "Scan aufhellen", "Bild verkleinern", "JPG zu PDF", "Tafel ausschneiden", "EXIF prüfen", "Tafelnummer ablesen", "Caption rauskratzen" oder ähnlich sagt. Output-Konvention: temporäre Zwischenstände nach `~/.claude/tmp/`, finale Vault-Versionen erst nach Bestätigung in den Anhang-Ordnern. Bei Bilddateien des Vaults arbeitet die Skill **nicht in-place** ohne ausdrückliche Erlaubnis, sondern legt eine neue Datei mit Suffix an.
---

# bild-bearbeiten

Werkzeugkasten für die typischen Bildoperationen am Vault: Buchscans aufbereiten (zuschneiden, entzerren, aufhellen), Fundzeichnungen auf Strichdarstellung trimmen, Bilder fürs Web kleinrechnen, JPEGs zu PDFs bündeln. Faktentreue gilt auch hier: **Inhalt nie verändern** (kein Inhalt hinzumalen, keine Watermarks aus dem Nichts) — nur das Originalbild aufbereiten.

## Werkzeuge im Container

- `magick` / `convert` (ImageMagick 7) — Schweizer Taschenmesser
- `img2pdf` — JPEGs/PNGs verlustfrei zu PDF
- `jpegoptim`, `optipng` — verlustfreie Größenoptimierung
- `exiftool` — Metadaten
- `pdftoppm` — PDF-Seite → PNG/JPEG (siehe auch [[pdf-lesen]])

## Ausgabe-Strategie

| Quelle | Zwischenstand | Endziel |
|---|---|---|
| Datei außerhalb des Vaults (`~/Downloads/`, …) | `~/.claude/tmp/<name>_step.ext` | Vault-Pfad nach Bestätigung (über [[buchscan-import]]) |
| Datei bereits im Vault (`Reenactment/Anhang/…`) | `~/.claude/tmp/<name>_edit.ext` | Originaldatei ersetzen **nur nach Auftrag** |

**Niemals** Zwischendateien in `/workspaces/ratatoskr/` (außer `Reenactment/Anhang/…`) ablegen — Google-Drive-Sync, siehe CLAUDE.md.

Bevor du eine Vault-Datei überschreibst: einmal nachfragen ("soll ich die Originaldatei `…/Anhang/Buecher/AROS/aros_seite_29.pdf` ersetzen oder eine `_v2`-Variante anlegen?"). Originalscan-Sicherung gewinnt.

## Operationen-Cheatsheet

### Größe ändern

```bash
magick "<in>" -resize 2000x "<out>"          # auf 2000 px Breite, Aspekt erhalten
magick "<in>" -resize 50% "<out>"            # halbieren
magick "<in>" -resize 2000x>  "<out>"        # nur verkleinern, falls größer
```

### Zuschneiden (Crop)

```bash
magick "<in>" -crop <B>x<H>+<X>+<Y> +repage "<out>"
# B/H = Zielmaße in px, X/Y = Offset von oben links
```

Wenn der Nutzer die Region anhand des Bildes zeigen will: erst Bild lesen (Read auf JPG/PNG), Koordinaten schätzen, dem Nutzer Vorschau-Box vorschlagen — niemals raten.

### Drehen / Entzerren

```bash
magick "<in>" -rotate 90 "<out>"             # exakt 90°
magick "<in>" -rotate -1.5 "<out>"           # leichte Schiefstellung korrigieren
magick "<in>" -deskew 40% "<out>"            # ImageMagick versucht Auto-Begradigung
```

### Aufhellen / Kontrast / Schwellwert

```bash
magick "<in>" -normalize "<out>"             # Histogramm auf vollen Bereich strecken
magick "<in>" -level 10%,90% "<out>"         # manueller Schwarz-/Weißpunkt
magick "<in>" -modulate 110,100 "<out>"      # Helligkeit +10%
magick "<in>" -threshold 60% "<out>"         # reines S/W für Strichzeichnungen
```

Für blasse Scans gut: `-normalize -level 5%,95% -sharpen 0x1`.

### Farbe → Graustufen / S/W

```bash
magick "<in>" -colorspace Gray "<out>"       # Graustufen
magick "<in>" -monochrome "<out>"            # reines 1-Bit S/W
```

### Format umwandeln

```bash
magick "<in>.tif" "<out>.png"
magick "<in>.png" -quality 90 "<out>.jpg"
```

JPEG für Fotos/Scans, PNG für Strichzeichnungen und Karten, TIFF nur wenn Vorlage es war.

### Mehrere Bilder zu PDF

```bash
img2pdf -o "<out>.pdf" <in1>.jpg <in2>.jpg <in3>.jpg
```

`img2pdf` ist verlustfrei (kein Re-Encoding). Für gemischte Quellen (mit PNG-Transparenz) ggf. `magick *.png "<out>.pdf"`.

### Größe optimieren (verlustfrei)

```bash
jpegoptim --strip-all --all-progressive "<datei>.jpg"
optipng -o5 "<datei>.png"
```

### Metadaten

```bash
exiftool "<datei>"                            # alles lesen
exiftool -EXIF:all= "<datei>"                 # alle EXIF-Tags entfernen
exiftool -Artist="…" -Copyright="…" "<datei>" # gezielt setzen
```

## Workflow für Buchscan-Aufbereitung

Häufigster Fall — frisch abgescannte Seite vor dem Import via [[buchscan-import]]:

1. Originalpfad lesen (z.B. `~/Downloads/scan001.jpg`).
2. Visuell prüfen (Read auf Bild): Schiefstellung? Ränder zu groß? Zu dunkel?
3. In `~/.claude/tmp/` arbeiten:
   ```bash
   IN=~/Downloads/scan001.jpg
   T=~/.claude/tmp
   magick "$IN" -deskew 40% -normalize -trim +repage "$T/scan001_step1.jpg"
   ```
4. Erneut visuell prüfen.
5. Wenn ok → an [[buchscan-import]] übergeben mit `$T/scan001_step1.jpg` als Quelle, Buchname, Seite, Thema.

## Workflow für Tafel/Detail aus Scan extrahieren

Für Funde, wo eine ganze Buchseite mehrere Tafeln zeigt:

1. PDF-Seite (oder JPG) öffnen, visuell die Tafel-Box identifizieren.
2. Mit `-crop` ausschneiden, evtl. `-trim` für sauberen Rand.
3. Eigene Datei nach `Reenactment/Anhang/Funde/<Fundname>/` (oder `Anhang/Fundkomplexe/<KomplexID>/` für Grab-/Hortfunde) — Konvention siehe CLAUDE.md (Buchscans liegen weiterhin im Buch-Anhang; Funddetails dürfen separat als `<fund>_<beschreibung>.jpg` im Fund-Anhang liegen).

## Tafel-Verifikations-Workflow (Helfer: `tools/vault_pdf_detail.py`)

Wenn man die Treffer der [[vault-bildsuche]] gegen den Tafelband prüfen will (Tafelnummer ablesen, Bildunterschriften lesen, Bj-/Grab-Zuordnung verifizieren), gibt es ein dediziertes Hilfsskript: `python3 tools/vault_pdf_detail.py`. Drei Subcommands:

### 1. `lookup` — PDF-Seite/Bild im Index nachschlagen

```bash
# Eine konkrete PDF-Seite (gibt Cache-Pfad + VLM-Beschreibung aus)
python3 tools/vault_pdf_detail.py lookup \
  Reenactment/Anhang/Buecher/Arbman_1943_Birka_I_Die_Graeber/arbman_1943_birka_i_tafeln.pdf \
  --page 182

# Alle indizierten Seiten/Items zu einer Quelle
python3 tools/vault_pdf_detail.py lookup \
  Reenactment/Anhang/Abhandlungen/wikingerschwerter_hedendorf.pdf
```

Output enthält den Pfad zur gerenderten PNG (`~/.claude/cache/vault_image_index/pdf_pages/<hash>/page_NNNN.png`) — den man dann direkt mit dem Read-Tool öffnen kann.

### 2. `crop` — Tafel-Region per Preset oder Koordinaten ausschneiden

Presets sind auf den typischen Birka/Tafel-Aufbau zugeschnitten (Tafelnummer oben, Caption unten):

| Preset | Wozu |
|---|---|
| `header` | obere 15% — Tafelnummer „Taf. NNN" |
| `topleft` / `topright` | obere Ecken (Tafelnummer steht je nach Seite links oder rechts) |
| `caption` | untere 15% — Bildunterschrift mit Grab-/Inv.-Nrn. |
| `top` / `bottom` / `left` / `right` | halbe Tafel |
| `center` | mittlere 50% |

```bash
# Beschriftung am unteren Rand ausschneiden (z.B. "1. Gr. 944 — 2. Gr. 644 …")
python3 tools/vault_pdf_detail.py crop \
  ~/.claude/cache/vault_image_index/pdf_pages/<hash>/page_0182.png \
  --preset caption

# Tafelnummer oben links
python3 tools/vault_pdf_detail.py crop \
  ~/.claude/cache/vault_image_index/pdf_pages/<hash>/page_0182.png \
  --preset topleft

# Freier Crop in Prozent (akzeptiert 0–1 oder 0–100)
python3 tools/vault_pdf_detail.py crop <bild> --pct 0,85,100,15

# Freier Crop in Pixeln (X,Y,W,H)
python3 tools/vault_pdf_detail.py crop <bild> --px 0,1037,956,183
```

Default-Output: `~/.claude/tmp/<stem>_<tag><ext>` — JPEG-Qualität 92, sonst PNG. Mit `-o <pfad>` explizit setzen.

### 3. `grep` — Volltextsuche über die VLM-Beschreibungen

Komplementär zur Embedding-Suche (die Embeddings finden semantisch ähnliches, `grep` findet wörtliche Zeichenketten):

```bash
# Alle Tafeln mit "Taf. 162" in der Beschreibung
python3 tools/vault_pdf_detail.py grep "Taf. 162"

# Auf PDF-Seiten einschränken
python3 tools/vault_pdf_detail.py grep "Knochenkamm" --kind pdf_page

# Nur in einer bestimmten Quelle suchen
python3 tools/vault_pdf_detail.py grep "Pferdekamm" --source arbman_1943
```

### Workflow Bildähnlichkeitssuche → Tafelnummer ablesen

```text
1. vault_image_search.py search --like <replik-foto>       # liefert PDF-Seiten-Treffer mit Score
2. vault_pdf_detail.py lookup <pdf> --page <seite>         # holt Cache-Pfad
3. Read auf den Cache-PNG-Pfad                             # visuelle Sichtung
4. vault_pdf_detail.py crop … --preset topleft|topright   # Tafelnummer freischneiden
5. vault_pdf_detail.py crop … --preset caption            # Grab-/Inv.-Nrn. ablesen
6. Erst wenn Tafelnummer + Beschriftung bestätigt: in Vault-Eintrag eintragen
```

**Wichtig (Faktentreue):** Die VLM-Beschreibung im Index ist nicht belastbar. Die Tafelnummer immer per `crop --preset topleft/topright` aus dem Originalscan verifizieren, bevor sie in einen Vault-Eintrag wandert.

## Wichtige Regeln

- **Nie Inhalt verändern.** Keine Pinselstriche, Retuschen, Fake-Schärfungen, die Details "erfinden". Erlaubt: Belichtung, Kontrast, Geometrie, Größe, Format.
- **Originaldatei nicht überschreiben ohne Auftrag.** Wenn die Eingabe schon im Vault liegt, default ist `_v2`-Variante. Originalscan ist die Belegquelle.
- **Output mit höchster sinnvoller Qualität.** JPEG-Qualität ≥ 90 für Scans, PNG für alles mit harten Kanten. Verlustbehaftete Wiederholungen vermeiden.
- **Vorher/Nachher zeigen.** Bei nicht-trivialen Bearbeitungen das Ergebnis kurz visuell prüfen (Read auf Output) und dem Nutzer mit Pfad melden, bevor weitergeht.
- **EXIF-Stripping nur auf Auftrag.** Kann Quelleninformation enthalten (Aufnahmedatum, Gerät) — kein automatisches Entfernen.

## Beispiel

Eingabe: "Hellt diesen Scan auf, gerade ist er ein bisschen schief — `~/Downloads/IMG_9821.jpg`"

```
~/Downloads/IMG_9821.jpg
  → magick … -deskew 40% -normalize -level 5%,95%
  → ~/.claude/tmp/IMG_9821_step1.jpg
```

Antwort an Nutzer: Pfad, Vorher/Nachher (kurze Bildbeschreibung), Frage ob Import per [[buchscan-import]].
