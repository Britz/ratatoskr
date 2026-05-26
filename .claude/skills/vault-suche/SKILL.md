---
name: vault-suche
description: Durchsucht den Reenactment-Vault nach Schlagworten, YAML-Frontmatter-Feldern, Tags oder Wikilink-Zielen, prüft auf kaputte Links und beschreibt Bildscans faktentreu. Wird ausgelöst, wenn der Nutzer fragt "wo wird X erwähnt", "welche Einträge haben Tag Y", "gibt es schon einen Eintrag zu Z", "kaputte Links finden", "ähnliche Funde", "was ist auf dem Scan zu sehen". Auch nützlich vor dem Anlegen eines neuen Eintrags, um Dubletten zu vermeiden.
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

## Ergebnisformat

Treffer als Liste mit klickbaren Pfaden:

```
3 Treffer für "Kleeblattfibel":
- [AROS_das_Aarhus_der_Wikinger.md:75](Reenactment/Literatur/Buecher/AROS_das_Aarhus_der_Wikinger.md#L75) — Tabellenzeile Scan
- [Birka.md:62](Reenactment/Ausgrabungen/Fundorte/Birka.md#L62) — "Kleeblattfibeln" als Beispiel
- ...
```

## Vor dem Anlegen eines neuen Eintrags

Wird oft im Verbund mit [[vault-eintrag]] genutzt: erst Volltext nach Titel/Kernbegriff suchen, um Dubletten zu vermeiden. Dem Nutzer Treffer zeigen, **bevor** eine neue Datei angelegt wird.
