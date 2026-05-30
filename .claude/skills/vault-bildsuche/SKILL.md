---
name: vault-bildsuche
description: Visuelle Ähnlichkeitssuche im Reenactment-Vault über VLM-Beschreibungen + Text-Embeddings (Qwen3-VL + Qwen3-Embedding via LM Studio). Wird ausgelöst, wenn der Nutzer "ähnliche Funde finden", "vergleichbare Bilder suchen", "wo gibt es ähnliche Äxte/Fibeln/Schwerter", "Bildsuche" oder "vault index aktualisieren" sagt.
---

# vault-bildsuche

Indiziert Bilder + PDF-Seiten unter `Reenactment/` und ermöglicht semantische Suche per Textquery oder Beispielbild.

## Voraussetzungen

- LM Studio läuft auf dem Host und ist unter `http://host.docker.internal:1234` erreichbar.
- In LM Studio geladen:
  - **VLM**: `qwen3-vl-8b-instruct` (oder beliebiges anderes, das man dann per `LMSTUDIO_VLM_MODEL` setzt)
  - **Embedding**: `text-embedding-qwen3-embedding-0.6b` (Default; **das 4B-Modell ist aktuell in LM Studio defekt — "Failed to decode batch"-Fehler**). Modell-Name per `LMSTUDIO_EMBED_MODEL` setzen, falls abweichend.
  - Mit `python tools/vault_image_search.py models` die aktuell geladenen Modell-IDs auflisten.
- Python-Deps installiert: `pip install -r tools/requirements.txt`

## Kommandos

Aus dem Repo-Root:

```bash
# Initial-Index (kann je nach Vaultgröße dauern; nur was sich geändert hat wird neu beschrieben)
python tools/vault_image_search.py index

# Statusübersicht (Anzahl Items, Modelle, DB-Pfad)
python tools/vault_image_search.py status

# Textquery
python tools/vault_image_search.py search --text "wikingerzeitliche Bartaxt mit Stielwicklung"

# Beispielbildsuche (z.B. eine Replik gegen Funde halten)
python tools/vault_image_search.py search --like Reenactment/Anhang/Ausstellung/Waffen/Axt/axt_ansicht_1.jpeg

# Nur Buchseiten durchsuchen
python tools/vault_image_search.py search --text "Axt" --kind pdf_page --top 20

# Einzelbeschreibung ohne Index (zum Ausprobieren des VLM-Prompts)
python tools/vault_image_search.py describe Reenactment/Anhang/Ausstellung/Waffen/Axt/axt_ansicht_1.jpeg
python tools/vault_image_search.py describe Reenactment/Anhang/Buecher/Spurensuche_Haithabu/haithabu_seite_232_klappmesser.png
```

## Was indiziert wird

- **Default:** alle `.jpg/.jpeg/.png/.webp/.gif/.bmp` unter `Reenactment/`. **Keine PDFs**, weil Text-PDFs (Abhandlungen, Edda etc.) viel Rauschen wären.
- `--include-pdfs` aktiviert alle PDF-Seiten unter `--root`.
- `--pdf <pfad>` (mehrfach erlaubt) indiziert nur gezielt ausgewählte PDFs (z.B. die Arbman-Tafeln). Andere PDFs bleiben aussen vor; Bilder werden trotzdem indiziert.
- `--max-pdf-pages N` begrenzt die Seitenzahl je PDF (0 = unbegrenzt).
- Ausgenommen: `.obsidian/`, `.tmp.drive*/`, `Icon`-Hilfsdateien, `ToDo/` (sofern nicht `--include-todo`).

## Beispiele für PDF-Auswahl

```bash
# Nur die Arbman-Tafeln zusätzlich zu allen Bildern:
python tools/vault_image_search.py index \
  --pdf Reenactment/Anhang/Buecher/Arbman_1943_Birka_I_Die_Graeber/arbman_1943_birka_i_tafeln.pdf

# Alle PDFs, aber nur erste 50 Seiten je PDF (Schnelltest):
python tools/vault_image_search.py index --include-pdfs --max-pdf-pages 50
```

## Caches

- Index-DB: `~/.claude/cache/vault_image_index/index.db`
- PDF-Seiten-Rendering: `~/.claude/cache/vault_image_index/pdf_pages/<file-hash>/page_NNNN.png`

Beide Pfade liegen außerhalb des Vaults (CLAUDE.md: nichts Temporäres unter `Reenactment/`).

## Faktentreue (sehr wichtig)

Der VLM erzeugt streng deskriptive Beschreibungen (System-Prompt verbietet Datierungs-/Material-/Fundkontext-Erfindung). Trotzdem gilt:

**VLM-Beschreibungen sind maschinell und ungeprüft.** Sie dürfen NIE direkt als Fakt in einen Vault-Eintrag übernommen werden. Sie sind nur Suchindex. Bei der Erstellung von Funde-/Ausstellungs-Einträgen weiterhin: nur belegte Aussagen, Unbekanntes als `unbekannt` markieren (siehe CLAUDE.md).

## Konfiguration über Umgebungsvariablen

| Variable | Default | Zweck |
| --- | --- | --- |
| `LMSTUDIO_BASE_URL` | `http://host.docker.internal:1234/v1` | LM-Studio-API-Endpunkt |
| `LMSTUDIO_VLM_MODEL` | `qwen3-vl-8b-instruct` | VLM-Modell-Name (so wie in LM Studio geladen) |
| `LMSTUDIO_EMBED_MODEL` | `text-embedding-qwen3-embedding-0.6b` | Text-Embedding-Modell (4B aktuell defekt in LM Studio) |

Nach Modell-Wechsel den Index neu bauen lassen (alte Einträge mit anderem Embedding sind nicht vergleichbar mit neuen).
