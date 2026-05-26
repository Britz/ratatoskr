# Vault-Skills

Projekt-lokale Claude-Skills für die Arbeit am Ratatoskr-Vault. Jeder Skill ist ein Ordner mit `SKILL.md`. Claude entscheidet anhand der `description`-Frontmatter selbst, wann ein Skill greift — sie steuern muss man sie nicht.

| Skill | Zweck | Typische Auslöser |
|---|---|---|
| [buchscan-import](buchscan-import/SKILL.md) | PDF/JPEG-Scan nach Anhang importieren, MD-Tabelle ergänzen | "Importier den Scan", "Seite X ins Buch übernehmen" |
| [pdf-lesen](pdf-lesen/SKILL.md) | PDF lesen (auch Scans ohne OCR), faktentreu zitieren | "Lies S. 26", "Was steht auf der Seite", "Zitiere aus dem PDF" |
| [vault-eintrag](vault-eintrag/SKILL.md) | Buch/Fund/Fundort/Grab/Webquelle als neue MD anlegen | "Neuer Eintrag", "Fund X dokumentieren" |
| [vault-suche](vault-suche/SKILL.md) | Volltext, Frontmatter, Wikilinks, kaputte Links, Bildbeschreibung | "Wo wird X erwähnt", "Kaputte Links finden" |
| [recherche](recherche/SKILL.md) | Web-Recherche mit Quellennachweis, faktentreu | "Recherchiere X", "Quellen zu Y suchen" |
| [bild-bearbeiten](bild-bearbeiten/SKILL.md) | Bilder zuschneiden, entzerren, aufhellen, Format/Größe, JPGs → PDF | "Scan begradigen", "Bild zuschneiden", "JPGs zu PDF" |

## Gemeinsame Regeln (CLAUDE.md → Faktentreue)

- Keine Fakten erfinden, raten oder durch Allgemeinwissen ergänzen.
- Unbekanntes explizit als `unbekannt` / `?` / "aus den vorliegenden Quellen nicht belegt" markieren.
- Temporäre Dateien nach `~/.claude/tmp/`, nicht in den Workspace (Google-Drive-Sync).
- Bildbeschreibungen: nur was sichtbar ist.
