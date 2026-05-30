---
name: vault-suche
description: Durchsucht den Reenactment-Vault nach Schlagworten, YAML-Frontmatter-Feldern, Tags oder Wikilink-Zielen, prüft auf kaputte Links und beschreibt Bildscans faktentreu. Holt außerdem referenzierte Tafeln/Abbildungen aus PDFs (Tafelband, Abhandlung) als Bilddatei in den Anhang, bindet sie im Fund-/Grab-Eintrag ein und pflegt Fundort/Grab/Fund-Kontext mit. Wird ausgelöst, wenn der Nutzer fragt "wo wird X erwähnt", "welche Einträge haben Tag Y", "gibt es schon einen Eintrag zu Z", "kaputte Links finden", "ähnliche Funde", "was ist auf dem Scan zu sehen", "Tafel X aus dem PDF einbinden / in den Anhang holen". Auch nützlich vor dem Anlegen eines neuen Eintrags, um Dubletten zu vermeiden.
---

# vault-suche

Operiert lesend über `Reenactment/`. Liefert immer Pfade (als klickbare Markdown-Links) und kurze Trefferauszüge — keine Interpretationen ohne Beleg.

## Suchmodi

### 1. Volltext (Inhalt + Frontmatter)

```bash
grep -rln --include='*.md' '<begriff>' Reenactment/
```

Bei vielen Treffern: knapp auflisten (Pfad + Match-Zeile), nicht den vollen Auszug zeigen. Bei < 5 Treffern: jeweils 1-2 Zeilen Kontext.

### 2. YAML-Frontmatter-Felder

Beispiel "alle Einträge mit `type: Fundbelegeintrag`":

```bash
grep -rln --include='*.md' '^type: Fundbelegeintrag' Reenactment/
```

Für Tag-Suche (`tags:`-Block):

```bash
grep -rB1 --include='*.md' '^  - <Tag>$' Reenactment/ | grep -E 'tags:|<Tag>' | ...
```

Wenn Logik komplex wird, einmaligen Python-Einzeiler mit `pathlib` + `re` über stdin verwenden — **nicht** ein Script ins Repo schreiben.

### 3. Wikilink-Rückwärtssuche

"Wer linkt auf [[X]]?":

```bash
grep -rln --include='*.md' '\[\[X' Reenactment/
```

Wikilinks können `[[Datei]]` oder `[[Datei|Alias]]` sein — beide Formen suchen.

### 4. Kaputte Wikilinks finden

Vorgehen:
1. Alle vorhandenen Dateinamen (ohne `.md`) sammeln:
   ```bash
   find Reenactment -name '*.md' -printf '%f\n' | sed 's/.md$//' | sort -u
   ```
2. Alle `[[Ziel]]`-Vorkommen sammeln:
   ```bash
   grep -roh --include='*.md' '\[\[[^]|]\+' Reenactment/ | sed 's/\[\[//' | sort -u
   ```
3. Differenz bilden: Ziele, die als Datei nicht existieren.

Bei jedem kaputten Link: Quelldatei nennen und Vorschlag (existiert ähnlicher Eintrag? Eintrag fehlt = anlegen über [[vault-eintrag]]?).

### 5. Bildscan faktentreu beschreiben

Wenn der Nutzer fragt "was ist auf `<bild>` zu sehen":

- Bei PDF → erst `pdftoppm` (siehe [[pdf-lesen]]) auf `~/.claude/tmp/`, dann Read auf die PNG.
- Bei JPEG/PNG direkt Read.
- Beschreibung: **nur Sichtbares**. Objektformen, Anzahl, Anordnung, Beschriftungen wörtlich übernehmen. Keine ergänzten Datierungen, Materialien, Stilzuschreibungen aus dem Bauch (siehe CLAUDE.md → Faktentreue).
- Bei unklaren Details: explizit "auf dem Bild nicht eindeutig erkennbar".

## Referenzierte Tafel/Abbildung in den Anhang holen + Kontext pflegen

Wenn ein Literatureintrag (Buch/Tafelband/Abhandlung) eine **konkrete Tafel oder Abbildung** zu einem Fund oder Grab nennt (z. B. „Arbman 1943, Taf. 144:2" oder „Fig. 2 in Gustin 2016"), wird das referenzierte Bild **als echtes Bild aus dem PDF herausgezogen und eingebunden** — analog zur Bildbeschaffung aus Museumskatalogen über [[fundbild-recherche]], nur dass die Quelle ein PDF im Vault ist.

### Ablauf

1. **Referenz finden** (Volltextsuche, Modus 1/3): in welchem Fund-/Grab-Eintrag wird welche Tafel/Abbildung welcher PDF-Quelle genannt?
2. **Tafel-Seite lokalisieren & verifizieren** über [[bild-bearbeiten]] bzw. `tools/vault_pdf_detail.py`:
   - `lookup <pdf> --page <N>` → Cache-PNG-Pfad, dann `Read` zur Sichtprüfung.
   - `crop … --preset topleft|topright` (Tafelnummer) und `--preset caption` (Grab-/Inv.-Nrn.) → **bestätigen**, dass Tafelnummer und Beschriftung wirklich zum Fund/Grab passen. Erst dann weiter (Faktentreue: VLM-Index ist nicht belastbar).
3. **Tafel/Detail ausschneiden** (`crop --preset …` oder `--px`/`--pct`), Zwischenstand in `~/.claude/tmp/`.
4. **In den Anhang legen** (CLAUDE.md → „Fundbilder gehören in den Anhang"):
   - Einzelfund: `Reenactment/Anhang/Funde/<Fundname>/<quelle>_taf_<NR>_<thema>.jpg|png`
   - Grab-/Komplexfund: `Reenactment/Anhang/Fundkomplexe/<KomplexID>/<quelle>_<thema>.jpg|png`
   - Das Original-PDF bleibt zusätzlich als Buchscan/Abhandlung erhalten.
5. **Einbinden** im Eintrag mit relativem Pfad (`![Caption mit Tafel-/Inv.-Nr.](../../Anhang/…)`) und **Quellen-Caption** (Buch + Tafel/Seite). Bei urheberrechtlich geschützten Werken: nur einbinden, was als Zitat/eigener Scan vertretbar ist — im Zweifel nur verweisen.
6. **Kontext mitpflegen** — wie beim Web-Weg (CLAUDE.md → „Neuer Fund ⇒ Kontext mitpflegen"):
   - **Fundort** (`Ausgrabungen/Fundorte/<Ort>.md`): Fund unter „Verknüpfte Funde" verlinken.
   - **Grab/Fundkomplex** (`Ausgrabungen/Fundkomplexe/<KomplexID>.md`, `type: Grab` bzw. `type: Fundkomplex`): bei geschlossenem Komplex den Fund im Inventar verlinken und die Inventartafel dort einbinden. **Siedlungs-/Streufunde** gehören zu keinem Komplex — im `fundkontext`-Feld vermerken, keinen Komplex erfinden.
   - Fehlt der Fund-/Fundort-/Grab-Eintrag noch: über [[vault-eintrag]] anlegen.

Reine Beschreibung „was ist auf der Tafel zu sehen" ohne Übernahme → Modus 5 oben. Übernahme als eingebundenes Bild + Kontextpflege → dieser Ablauf.

## Ergebnisformat

Treffer als Liste mit klickbaren Pfaden:

```
3 Treffer für "Kleeblattfibel":
- [Skov_2006_AROS_Aarhus.md:75](Reenactment/Literatur/Buecher/Skov_2006_AROS_Aarhus.md#L75) — Tabellenzeile Scan
- [Birka.md:62](Reenactment/Ausgrabungen/Fundorte/Birka.md#L62) — "Kleeblattfibeln" als Beispiel
- ...
```

## Vor dem Anlegen eines neuen Eintrags

Wird oft im Verbund mit [[vault-eintrag]] genutzt: erst Volltext nach Titel/Kernbegriff suchen, um Dubletten zu vermeiden. Dem Nutzer Treffer zeigen, **bevor** eine neue Datei angelegt wird.
