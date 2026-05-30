---
name: vault-pdf-index
description: Pflegt und erweitert den Bildähnlichkeitsindex über PDFs im Reenactment-Vault (Arbman-Tafelband, Schwert-PDFs etc.). Wird ausgelöst, wenn der Nutzer "PDF X in den Index aufnehmen", "Tafelband indexieren", "PDF-Index erweitern", "Index neu bauen", "Index-Status prüfen", "welche PDFs sind im Index", "Tafel-/Buchseiten suchbar machen" sagt. Für reine Suche → siehe Skill `vault-bildsuche`. Für PDF-Textextraktion → siehe Skill `pdf-lesen`.
---

# vault-pdf-index

Pflegt den **bildbasierten** Suchindex über PDF-Seiten im Vault. Der Index liegt unter `~/.claude/cache/vault_image_index/index.db` und wird vom Tool `tools/vault_image_search.py` befüllt – dieser Skill beschreibt nur den **PDF-Teil** der Indexpflege (Auswahl, Aufnahme, Aktualisierung, Reset).

## Hintergrund: Warum nicht alle PDFs?

Der Vault enthält ca. 50 PDFs mit zusammen **~3.500 Seiten**. Jede Seite kostet beim Indexieren etwa **12 Sekunden** (VLM-Beschreibung + Text-Embedding via LM Studio). Ein Komplettlauf wäre rund 12 Stunden – und der größte Teil davon ist Rauschen: Text-PDFs (Abhandlungen, Bibliothekstexte, die Edda) liefern für eine **Bildähnlichkeitssuche** kaum Mehrwert.

Deshalb gilt: **PDFs werden im Index per Whitelist geführt.** Default ist „keine PDFs". Sinnvoll sind nur PDFs mit **Tafeln, Strichzeichnungen oder Foto-Plates** (also wo etwas zu *sehen* ist).

## Aktueller Indexstand (Pflege-Soll)

Stand 2026-05-30 sind diese PDFs indexiert (siehe `python tools/vault_image_search.py status`):

| PDF | Seiten | Begründung |
| --- | --- | --- |
| `Anhang/Buecher/Kalmring_2010_Hafen_Haithabu/kalmring_2010_hafen_haithabu.pdf` | 668 | Hafengrabungen Haithabu: Karten, Pläne, Bauphasen-Fotos, Schiffswrack-Aufnahmen |
| `Anhang/Buecher/Arbman_1943_Birka_Graeber/arbman_1943_birka_i_text.pdf` | 586 | Birka I Textband mit eingestreuten Fundskizzen (ergänzt den Tafelband) |
| `Anhang/Abhandlungen/toplak_2016_graeberfeld_kopparsvik.pdf` | 387 | Kopparsvik-Gräberfeld Gotland: Verteilungskarten, Tafeln |
| `Anhang/Abhandlungen/ingvardson_2025_hoarding_vikings.pdf` | 351 | Hortfund-Studie Bornholm mit Tafeln/Diagrammen |
| `Anhang/Buecher/Arbman_1943_Birka_Graeber/arbman_1943_birka_i_tafeln.pdf` | 310 | Birka I Tafelband – Hauptquelle für Birka-Funde |
| `Anhang/Buecher/Martens_2021_Swords_Telemark/martens_2021_swords_telemark.pdf` | 153 | Schwert-Typologie Telemark, viele Klingen-Zeichnungen |
| `Anhang/Abhandlungen/warming_2016_shields_hide.pdf` | 72 | Schild-Lederbespannung: Tabellen + Untersuchungsfotos |
| `Anhang/Buecher/Edberg_2022_Spelfoeremaal_Sigtuna/edberg_2022_spelfoeremaal_sigtuna.pdf` | 38 | Spielobjekte Sigtuna |
| `Anhang/Abhandlungen/hilberg_2014_detektorfunde.pdf` | 28 | Detektorfunde Haithabu (Fibeln, Beschläge) |
| `Anhang/Abhandlungen/pentz_2018_detector_finds.pdf` | 18 | Detektor-Funde |
| `Anhang/Abhandlungen/gustin_2016_birka_finnland.pdf` | 18 | Birka-Finnland Verbreitungskarten |
| `Anhang/Abhandlungen/habermann_2018_schwerter_hedendorf.pdf` | 12 | Schwert-Sammlung mit Fotos |

Plus **244 normale Bilder** unter `Reenactment/`. Gesamt: **2885 Items**.

**Bewusst NICHT indexiert** (reine Text-PDFs ohne relevante Tafeln):

- `Anhang/Buecher/Obleser_2015_Odin_Streifzug/obleser_2015_odin_streifzug.pdf` (324 S., psychologische Abhandlung)
- `Anhang/Buecher/Kershaw_2017_Odin_Maennerbuende/kershaw_2000_one_eyed_god.pdf` (502 S., indogermanistische Dissertation)
- `Anhang/Buecher/Simrock_1851_Edda/Die_Edda.pdf` (Edda-Übersetzung, reiner Text)
- `Anhang/Abhandlungen/jantzen_2008_metall_bronzezeit.pdf` (607 S., Bronzezeit – nicht Wikingerzeit)
- `Anhang/Abhandlungen/horn_2015_kinzig.pdf` (173 S., Megalithgrab/vorgeschichtlich)
- `Anhang/Abhandlungen/macneill_2019_heathen_army.pdf` (133 S., reiner Text)
- Diverse Stalsberg/Eisenschmidt/Steuer-Abhandlungen sowie alle Webquellen-PDFs (textlastig oder klein)

## Wann erweitern?

Erweitern, sobald der Nutzer ein neues PDF mit **visuellem Inhalt** in den Vault einbringt:

- **Tafelbände** (Arbman, Birka II, Haithabu Bd. 4 etc.)
- **Foto-PDFs aus Museumskatalogen**
- **Buchseiten-Sammlungen mit Abbildungen** (Bildung der Webquellen-/Abhandlungen-Anhänge)
- **Polnische/dänische Werkstattlisten mit Produktfotos** (z.B. die Glasmacher-Preisliste war ein Grenzfall – wurde *nicht* indexiert, weil zu klein)

Nicht aufnehmen:

- reine Text-PDFs (Wikipedia-Exporte, Stalsberg-Abhandlung, Edda – auch wenn sie inhaltlich wichtig sind, helfen sie der **Bild**-Suche nicht)
- sehr große PDFs (>500 Seiten) ohne fokussierten Tafelteil – ggf. nur die Tafel-Seitenbereiche extrahieren

## Workflow: PDF zum Index hinzufügen

### 1. Kandidaten ermitteln

```bash
# Alle PDFs im Vault auflisten
find /workspaces/ratatoskr/Reenactment -name "*.pdf" -not -path "*/.obsidian/*" -not -path "*/ToDo/*" | sort

# Seitenzahl je PDF (inkl. Heuristik: nur PDFs >= 10 Seiten betrachten):
python3 - <<'PY'
import pypdfium2, pathlib
root = pathlib.Path("/workspaces/ratatoskr/Reenactment")
for p in sorted(root.rglob("*.pdf")):
    if any(seg in {".obsidian", "ToDo"} for seg in p.parts):
        continue
    try:
        d = pypdfium2.PdfDocument(p)
        print(f"{len(d):4d}  {p.relative_to(root)}")
        d.close()
    except Exception as e:
        print(f"  !!  {p}: {e}")
PY
```

### 2. PDF-Inhalt visuell prüfen (Bildanteil?)

```bash
# Erste paar Seiten ansehen, ob es ein Tafelband ist:
python3 - <<'PY'
import pypdfium2, pathlib
src = pathlib.Path("PFAD/ZUM/PDF.pdf")
out = pathlib.Path.home() / ".claude" / "tmp" / "view"
out.mkdir(parents=True, exist_ok=True)
pdf = pypdfium2.PdfDocument(src)
for i in [0, len(pdf)//2, len(pdf)-1]:
    pdf[i].render(scale=1.2).to_pil().save(out/f"check_p{i+1}.png", optimize=True)
pdf.close()
PY
# Dann die check_p*.png-Dateien öffnen
```

Entscheidung:

- Überwiegend Tafeln/Fotos → **aufnehmen**
- Überwiegend Text → **nicht aufnehmen**
- Gemischt → ggf. `--max-pdf-pages N` setzen, oder die relevanten Seiten als Buchscan-PDFs einzeln importieren (siehe Skill `buchscan-import`)

### 3. PDF indexieren

```bash
# Einzelne PDF zusätzlich zu allen bereits indizierten Bildern aufnehmen
# (Bilder werden übersprungen, wenn Hash unverändert)
python tools/vault_image_search.py index \
  --pdf Reenactment/Anhang/Buecher/<BuchOrdner>/<datei>.pdf

# Mehrere PDFs in einem Lauf
python tools/vault_image_search.py index \
  --pdf Reenactment/Anhang/Buecher/Arbman/arbman_tafeln.pdf \
  --pdf Reenactment/Anhang/Abhandlungen/viking_age_swords.pdf

# Mit Seitenbegrenzung (sinnvoll für gemischte PDFs):
python tools/vault_image_search.py index \
  --pdf Reenactment/Anhang/...pdf --max-pdf-pages 50

# Parallel mit 2-4 Workers (nur sinnvoll, wenn das LM-Studio-Backend parallele Requests verarbeiten kann)
python tools/vault_image_search.py index \
  --pdf Reenactment/Anhang/...pdf --workers 2

# Im Hintergrund starten, wenn groß (run_in_background=True bei Bash-Aufruf)
```

**Faustregel Laufzeit:**
- `--workers 1` (default, seriell, MLX-Backend): ~12 s/Seite. 310 Seiten ≈ 60 min.
- `--workers 2` (MLX-Backend): ~8 s/Seite effektiv (~40 % Speedup durch HTTP/Overhead-Überlappung).
- `--workers 4` mit GGUF-Backend + mmproj (theoretisch): ~3 s/Seite effektiv. ⚠️ aktuell nicht aktiviert, weil Qwen3-VL-GGUF in LM Studio (Stand 0.4.15) das mmproj nicht zuverlässig anbindet → HTTP 400 „Model does not support images". Bei späteren Runtime-Updates erneut prüfen.

Bei großen Läufen `run_in_background` einsetzen und Fortschritt per SQLite-DB statt Log überwachen — die Log-Ausgabe ist block-buffered (8 KB) und zeigt das echte Tempo nicht.

**Status aus DB statt Log (block-buffered):**
```python
import sqlite3, pathlib
db = pathlib.Path.home() / ".claude" / "cache" / "vault_image_index" / "index.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
print(con.execute("SELECT COUNT(*) FROM items WHERE source_path LIKE '%<pdf>%'").fetchone()[0])
```

### 4. Status verifizieren

```bash
python tools/vault_image_search.py status
```

Ausgabe enthält: Gesamtanzahl, Aufteilung `image`/`pdf_page`, verwendete Modelle.

### 5. Stichprobensuche

```bash
# Themenkern testen (etwas, das auf den neuen Tafeln zu sehen sein sollte):
python tools/vault_image_search.py search --text "Knochenkamm Doppelreihe" --kind pdf_page --top 10

# Beispielbildsuche gegen eine eigene Replik halten:
python tools/vault_image_search.py search --like Reenactment/Anhang/Ausstellung/...
```

## Workflow: Index aktualisieren bei geändertem PDF

`tools/vault_image_search.py` führt einen SHA1-Hash-Vergleich der ersten 8 KB + Dateigröße. Wenn ein PDF ersetzt wird (z.B. neu eingescannt, anderer Inhalt), wird es beim nächsten `index --pdf <pfad>` automatisch neu beschrieben. Nichts weiter zu tun.

## Workflow: Index nach Modell-Wechsel neu bauen

Wenn `LMSTUDIO_VLM_MODEL` oder `LMSTUDIO_EMBED_MODEL` geändert wird (z.B. Wechsel auf `text-embedding-qwen3-embedding-4b`, sobald der MLX-Bug behoben ist):

```bash
# Alten Index löschen
rm ~/.claude/cache/vault_image_index/index.db

# PDF-Page-Renderings können bleiben (sind nur Cache, kein Modell-spezifischer Inhalt)
# Bei Bedarf:  rm -rf ~/.claude/cache/vault_image_index/pdf_pages/

# Voll-Indexierung starten – Bilder + die früher indexierten PDFs neu aufnehmen
python tools/vault_image_search.py index \
  --pdf Reenactment/Anhang/Buecher/Arbman_1943_Birka_I_Die_Graeber/arbman_1943_birka_i_tafeln.pdf \
  --pdf Reenactment/Anhang/Abhandlungen/viking_age_swords.pdf \
  --pdf Reenactment/Anhang/Abhandlungen/wikingerschwerter_hedendorf.pdf
```

Mischen alter und neuer Embeddings ist **sinnlos** – Cosine-Vergleiche zwischen verschiedenen Modellen sind nicht vergleichbar. Deshalb immer kompletter Reset.

## Workflow: Index-Selektion (welche PDFs sind drin)

```bash
# Pro PDF: wie viele Seiten sind im Index?
python3 - <<'PY'
import sqlite3, pathlib
db = pathlib.Path.home() / ".claude" / "cache" / "vault_image_index" / "index.db"
con = sqlite3.connect(db)
rows = con.execute(
    "SELECT source_path, COUNT(*) FROM items WHERE kind='pdf_page' "
    "GROUP BY source_path ORDER BY source_path"
).fetchall()
for path, n in rows:
    print(f"{n:4d}  {path}")
con.close()
PY
```

Daraus ableiten: welche PDFs sind aufgenommen, welche fehlen vom Soll (Pflege-Tabelle oben im Vault).

## Performance & Tuning

- **Geschwindigkeit hängt am VLM** (~12 s/Seite). Embedding ist vernachlässigbar (<200 ms).
- **Größere Modelle** (z.B. Qwen3-VL-32B) sind genauer aber langsamer – nicht für Massenindex sinnvoll.
- **Render-Auflösung**: aktuell `scale=1.5`. Erhöhen verlangsamt nur, erhöht die Beschreibungsqualität meist nicht.
- **Page-Cache**: gerenderte PDF-Seiten landen in `~/.claude/cache/vault_image_index/pdf_pages/<hash>/page_NNNN.png`. Nicht ohne Grund löschen – bei Reindex spart das viele Sekunden je Seite.

## Erweiterungs-Strategie

Wenn der Vault wächst, regelmäßig prüfen:

1. **Neue Tafelbände** (Birka II, Haithabu Bd. 4, AROS-Tafelteil) → einzeln aufnehmen, siehe Workflow oben.
2. **Webquellen-PDFs** (z.B. Sippe-Guntursson-Export, Vlasaty-Artikel) → nur indexieren, wenn sie eigene Tafeln/Fotos enthalten; sonst nicht.
3. **Markt-/Hersteller-Preislisten** → in der Regel nicht indexieren (zu klein, zu spezifisch); stattdessen den relevanten Eintrag direkt mit dem PDF verlinken.
4. **Reenactment-Eigenproduktion** (Strichzeichnungen, KI-Renderings) → falls als PDF im Vault, indexieren (Beispiel: KI-Zeichnungen des Feuereisens).

Den **Pflege-Soll-Block** oben in diesem Skill aktualisieren, sobald ein neues PDF dauerhaft im Index ist – damit künftige Sessions den Soll-Stand kennen.

## Beziehung zu anderen Skills

- **`buchscan-import`** – Importiert eine einzelne Buchseite (PDF/JPG) als sprechend benannte Datei in den Buch-Anhang und verlinkt sie in der Buch-MD. Dort liegende Buchscan-PDFs werden vom PDF-Index **nicht automatisch** aufgenommen (sie sind klein und einzeln – per Bildsuche bereits abgedeckt durch die importierte Bilddatei).
- **`vault-bildsuche`** – Liefert die Suchschnittstelle gegen den Index, den dieser Skill pflegt.
- **`pdf-lesen`** – Liest Text aus PDFs (Volltext / Seiteninhalt), unabhängig vom Bildindex.

## Faktentreue-Erinnerung

Der VLM erzeugt rein deskriptive Beschreibungen für den Index. Diese sind **maschinell erzeugt** und **dürfen nicht** ungeprüft als Fakt in Vault-Einträge übernommen werden. Sie sind ausschließlich Such-Hilfe. Für inhaltliche Quellenarbeit immer den Originaltext (Tafelbeschreibung, Bildunterschrift, Bibliografie) prüfen – per `pdf-lesen` oder direkt im Buch.
