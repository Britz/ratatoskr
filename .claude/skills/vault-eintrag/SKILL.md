---
name: vault-eintrag
description: Legt einen neuen Vault-Eintrag an (Buch, Fund, Fundort, Grab oder Webquelle) mit korrekter Ordnerstruktur, vault-konformem YAML-Frontmatter und Verlinkung. Wird ausgelöst, wenn der Nutzer "neuer Eintrag", "neues Buch anlegen", "Fund X dokumentieren", "Fundort Y erfassen", "Webquelle speichern" sagt. Strikt faktentreu — unbekannte Felder werden als `unbekannt` gekennzeichnet, niemals geraten oder durch Allgemeinwissen ersetzt.
---

# vault-eintrag

Legt strukturkonforme MD-Dateien im Vault an. Die Skill kennt vier Eintragstypen mit eigenen Templates:

| Typ | Zielordner | Template |
|---|---|---|
| Buch | `Reenactment/Literatur/Buecher/` | `templates/buch.md` |
| Fundbeleg | `Reenactment/Ausgrabungen/Funde/` | `templates/fund.md` |
| Fundort | `Reenactment/Ausgrabungen/Fundorte/` | `templates/fundort.md` |
| Grab | `Reenactment/Ausgrabungen/Graeber/` | `templates/grab.md` |
| Webquelle | `Reenactment/Literatur/Webquellen/` | `templates/webquelle.md` |

## Arbeitsweise

1. **Typ klären.** Wenn aus dem Nutzerwunsch nicht eindeutig: einmal nachfragen ("Buch, Fund, Fundort, Grab oder Webquelle?").

2. **Dateiname festlegen** nach Konvention der bestehenden Einträge:
   - **Buch**: `<Titel_Schlagworte>.md` mit Unterstrichen, Umlaute als ASCII (`Kalmring_Hafen_von_Haithabu.md`)
   - **Fund**: `<Objekt>_<Grab/Fundort>.md` (`Feuereisen_Bj644_Birka.md`)
   - **Fundort**: kurzer Eigenname (`Birka.md`, `Haithabu.md`)
   - **Grab**: Grabungs-ID + Ort (`Bj644_Birka.md`)
   - **Webquelle**: `<Thema>_<Quelle>.md` (`Schildbau_Kite_Shield_YouTube.md`)

3. **Template laden** (`Read .claude/skills/vault-eintrag/templates/<typ>.md`) und mit den bekannten Werten füllen.

4. **Unbekannte Felder als `unbekannt` lassen** — niemals plausibel klingende Defaults eintragen (siehe CLAUDE.md → Faktentreue).

5. **Bei Buch zusätzlich**:
   - Anhang-Ordner `Reenactment/Anhang/Buecher/<BuchOrdner>/` anlegen, wenn Buchscans erwartet werden. Der Buchordner-Name kommt vom Nutzer (CamelCase, vgl. `AROS`, `Haithabu`).

6. **Bei Fund/Grab zusätzlich**:
   - Wikilinks zum Fundort (`[[Fundortname]]`) prüfen — wenn die Fundort-MD fehlt, dem Nutzer das anbieten ("Soll ich den Fundort gleich mit anlegen?").

7. **Bericht**: Pfad der neuen Datei, welche Felder noch auf `unbekannt` stehen und welche Quelle zur Verifikation zu konsultieren ist.

## Goldene Regel

> Lieber ein knapper, korrekter Eintrag mit vielen `unbekannt`-Feldern als ein voller Eintrag, in dem Details halluziniert sind.

Wenn der Nutzer eine konkrete Quelle (Buch/PDF/URL) nennt: erst über [[pdf-lesen]] oder die URL prüfen und nur eintragen, was in der Quelle steht. Bei URL-basierten Einträgen über [[recherche]] arbeiten.

## Beispiel

Eingabe: "Neuer Fund: Lanzenspitze aus Grab X in Haithabu, ich habe noch keine Quelle dazu"

→ Datei: `Reenactment/Ausgrabungen/Funde/Lanzenspitze_X_Haithabu.md` (Name mit Nutzer abstimmen)
→ Template `fund.md`, gefüllt mit Titel/Fundort/Grab; alle übrigen Felder: `unbekannt`
→ Abschnitt "Offene Aufgaben / nachzutragen" listet die fehlenden Belege auf
