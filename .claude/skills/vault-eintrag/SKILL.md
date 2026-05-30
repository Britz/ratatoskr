---
name: vault-eintrag
description: Legt einen neuen Vault-Eintrag an (Buch, Abhandlung, Webquelle, Fund, Fundort, Grab oder Ausstellungsobjekt) mit korrekter Ordnerstruktur, vault-konformem YAML-Frontmatter und Verlinkung. Wird ausgelöst, wenn der Nutzer "neuer Eintrag", "neues Buch anlegen", "Abhandlung importieren", "Fund X dokumentieren", "Fundort Y erfassen", "Webquelle speichern", "neue Replik / Ausstellungsobjekt anlegen" sagt. Strikt faktentreu — unbekannte Felder werden als `unbekannt` gekennzeichnet, niemals geraten oder durch Allgemeinwissen ersetzt.
---

# vault-eintrag

Legt strukturkonforme MD-Dateien im Vault an. Die Skill kennt acht Eintragstypen mit eigenen Templates:

| Typ | Zielordner | Template |
| --- | --- | --- |
| Buch | `Reenactment/Literatur/Buecher/` | `templates/buch.md` |
| Abhandlung | `Reenactment/Literatur/Abhandlungen/` | `templates/abhandlung.md` |
| Webquelle | `Reenactment/Literatur/Webquellen/` | `templates/webquelle.md` |
| Fundbeleg | `Reenactment/Ausgrabungen/Funde/` | `templates/fund.md` |
| Fundort | `Reenactment/Ausgrabungen/Fundorte/` | `templates/fundort.md` |
| Grab | `Reenactment/Ausgrabungen/Fundkomplexe/` (`type: Grab`) | `templates/grab.md` |
| Fundkomplex (Hort/Depot) | `Reenactment/Ausgrabungen/Fundkomplexe/` (`type: Fundkomplex`) | `templates/fundkomplex.md` |
| Ausstellungsobjekt | `Reenactment/Ausstellung/<Kategorie>/` | `templates/ausstellung.md` |

> **Grab und Fundkomplex teilen sich den Ordner `Fundkomplexe/`** und werden über `type:` unterschieden (ein Grab ist ein Sonderfall des geschlossenen Komplexes). Siehe CLAUDE.md → „Konvention: Fundkomplexe & Fundkontext".

## Arbeitsweise

1. **Typ klären.** Wenn aus dem Nutzerwunsch nicht eindeutig: einmal nachfragen ("Buch, Abhandlung, Webquelle, Fund, Fundort, Grab, Fundkomplex oder Ausstellungsobjekt?").

2. **Dateiname festlegen** nach Konvention der bestehenden Einträge:
   - **Buch / Abhandlung**: `<Autor>_<Jahr>_<Stichwort>.md`, Unterstriche, ASCII (`Arbman_1943_Birka_Graeber.md`, `Eisenschmidt_2008_Graeber_Haithabu.md`). Bei mehreren Autoren: nur Erstautor. Bei fehlendem Jahr ältere Konvention `<Autor>_<Stichwort>.md` zulässig (`Kalmring_Hafen_von_Haithabu.md`), aber neue Einträge bevorzugt mit Jahr.
   - **Webquelle**: bevorzugt ebenfalls `<Autor>_<Jahr>_<Stichwort>.md` (`Edberg_2022_Spelfoeremaal_Sigtuna.md`); falls kein klarer Autor/Jahr: `<Thema>_<Quelle>.md` (`Haithabu_Danewerk_UNESCO.md`). Bei Museumskatalogen das Werk nach Domain/Institution (`SHM_Samlingar.md`).
   - **Fund**: `<Objekt>_<Komplex/Fundort>.md` (`Feuereisen_Bj644_Birka.md`, `Stabwuerfel_Svarta_jorden_Birka.md`)
   - **Fundort**: kurzer Eigenname (`Birka.md`, `Haithabu.md`)
   - **Grab / Fundkomplex**: Komplex-ID + Ort, **ohne** `Grab_`/`Fundkomplex_`-Prefix (der `type:` unterscheidet) — `Bj644_Birka.md`, `Spillings_Hort_Gotland.md`. Liegt in `Ausgrabungen/Fundkomplexe/`.
   - **Ausstellungsobjekt**: `<Objekt>[_<Vorbild>].md`, **niemals `_Replik`-Suffix** (`Axt.md`, `Koenigsschwert_Haithabu.md`, `Walkuere_Anhaenger_Suffolk.md`)
   - **Hersteller / Händler**: Eigenname, ASCII, Unterstriche (`Pera_Peris.md`, `Battle_Merchant.md`, `Outfit4Events.md`)
   - **Produkt**: `<Objekt>[_<Hersteller>].md` (`Feuerstahl_Ulfberth.md`)

3. **Template laden** (`Read .claude/skills/vault-eintrag/templates/<typ>.md`) und mit den bekannten Werten füllen.

4. **Unbekannte Felder als `unbekannt` lassen** — niemals plausibel klingende Defaults eintragen (siehe CLAUDE.md → Faktentreue).

5. **Bei Buch zusätzlich**:
   - Anhang-Ordner `Reenactment/Anhang/Buecher/<BuchOrdner>/` anlegen, wenn Buchscans erwartet werden. Der Buchordner-Name kommt vom Nutzer (CamelCase, vgl. `AROS`, `Haithabu`).
   - **Cover-Bild beschaffen** (siehe Abschnitt „Cover-Beschaffung" unten). Wenn erfolgreich, im MD als `![[Anhang/Buecher/<BuchOrdner>/cover.jpg|float-right small]]` direkt unter der `# Titel`-Zeile einbinden.

6. **Bei Abhandlung zusätzlich**:
   - Falls eine PDF mit übergeben wurde: nach `Reenactment/Anhang/Abhandlungen/<dateiname>.pdf` ablegen (ASCII, Unterstriche) und im Frontmatter-Feld `dateiname` referenzieren.

7. **Bei Webquelle zusätzlich** (siehe CLAUDE.md → „Konvention: Webquellen als Werk"):
   - **Erst prüfen, ob die Seite/Quelle (Domain/Blog/Autor) schon als Webquelle existiert** — `grep -rn` in `Reenactment/Literatur/Webquellen/` nach Domain/`quelle:`/`blog:`. Wenn ja: **keinen zweiten Einzel-Eintrag anlegen**, sondern den neuen Beitrag als weiteren `## Beitrag/Seite: …`-Abschnitt (+ Tabellenzeile + PDF in `Anhang/Webquellen/<Werk>/`) in die bestehende Werk-Webquelle einhängen.
   - Liegt die Quelle bisher als **einzelner** Eintrag (eine Seite) vor, diesen **in die Werk-Struktur umbauen** (Frontmatter aufs Werk, bisheriger Inhalt → `## Beitrag/Seite: …`), dann Backlinks per `grep` umbiegen und `Literatur/Literatur-Uebersicht.md` aktualisieren. Vorbilder: `Moren_LazyReenactorGirl_Blog.md`, `Wikinger_Museum_Haithabu.md`, `SHM_Samlingar.md`.
   - Falls eine PDF/Snapshot übergeben wurde: nach `Reenactment/Anhang/Webquellen/<Werk>/<dateiname>.pdf` ablegen und im `## Anhang – Dokumente`-Abschnitt verlinken.

8. **Bei Ausstellungsobjekt zusätzlich**:
   - **Kategorie wählen** aus den fünf festen Ordnern (`Waffen`, `Schmuck`, `Taschen`, `Bekleidung`, `Alltag`) — siehe CLAUDE.md → „Konvention: Ausstellungseinträge". Wenn unklar: einmal nachfragen mit den fünf Optionen.
   - Anhang-Ordner `Reenactment/Anhang/Ausstellung/<Kategorie>/<Objekt>/` anlegen.
   - Bilder mit sprechenden ASCII-Namen ablegen (`<objekt>_<thema>.<ext>`, snake_case).
   - Relative Pfade im MD: `../../Anhang/Ausstellung/<Kategorie>/<Objekt>/...` (zwei Ebenen hoch wegen Kategorie-Unterordner).

9. **Bei Fund/Grab/Fundkomplex zusätzlich** (siehe CLAUDE.md → „Konvention: Fundkomplexe & Fundkontext" + „Neuer Fund ⇒ Kontext mitpflegen"):
   - **Fund:** `fundkontext:` setzen (Grab/Siedlung/Hort/Lösfund/…). Bei geschlossenem Komplex zusätzlich `komplex: "[[…]]"` und im Komplex-Eintrag im Inventar verlinken; bei Siedlungs-/Streufund kein Komplex. `ortsnummer` (Fornlämning/RAÄ/…) und `museum_nr` eintragen, wenn belegt.
   - **Fundort immer mitpflegen:** Wikilink prüfen (`[[Fundortname]]`) und den Fund dort unter „Verknüpfte Funde" ergänzen. Fehlt die Fundort-MD: anbieten, sie gleich mit anzulegen.
   - **Grab/Fundkomplex:** liegt in `Ausgrabungen/Fundkomplexe/` (`type: Grab` bzw. `type: Fundkomplex`); Bilder/Inventartafeln in `Anhang/Fundkomplexe/<KomplexID>/`.
   - **Bilder in den Anhang** (CLAUDE.md → „Fundbilder gehören in den Anhang"): Objektfotos aus Museumskatalogen bzw. referenzierte Tafeln aus PDFs als Bilddatei ablegen und einbinden — Einzelfund nach `Anhang/Funde/<Fundname>/`, Komplex nach `Anhang/Fundkomplexe/<KomplexID>/`; Lizenz/Attribution beachten.

10. **Bericht**: Pfad der neuen Datei, welche Felder noch auf `unbekannt` stehen und welche Quelle zur Verifikation zu konsultieren ist.

## Cover-Beschaffung (nur bei Typ Buch)

Beim Anlegen eines Buch-Eintrags wird zusätzlich versucht, ein Cover lokal in den Anhang-Ordner zu legen. Strikt nach Faktentreue: niemals erfundene Bilder, immer visuell prüfen, dass Cover Autor und Titel zeigt.

**Reihenfolge der Versuche:**

1. **PDF im Vault vorhanden** (z. B. antiquarischer Scan, Open-Access-Werk): Mit Ghostscript Seite 1 (oder erste textbare Titelseite) extrahieren:
   ```bash
   gs -dNOPAUSE -dBATCH -sDEVICE=jpeg -r200 -dJPEGQ=90 \
      -dFirstPage=1 -dLastPage=1 \
      -sOutputFile=/tmp/cover_p1.jpg \
      <pfad-zur-pdf>
   ```
   Erste 3–5 Seiten extrahieren und visuell die geeignetste wählen (oft ist Seite 1 leeres Vorblatt — dann Seite 2 oder 3 nehmen).

2. **ISBN bekannt**: `https://buch.isbn.de/cover/<ISBN-ohne-Bindestriche>.jpg` versuchen (funktioniert für deutsche Titel deutlich besser als OpenLibrary). Mit `curl -o` herunterladen, dann `file <pfad>` prüfen, dass es ein gültiges JPEG ist.

3. **ISBN bekannt, isbn.de leer**: Fallback auf `https://covers.openlibrary.org/b/isbn/<ISBN>-L.jpg?default=false`. Bei `?default=false` liefert OpenLibrary einen Fehler, wenn kein Cover existiert (statt eines Platzhalters).

4. **Keine ISBN, kein PDF**: WebSearch nach „<Autor> '<Titel>' Buch ISBN", aus den Treffern eine ISBN ableiten und dann Schritt 2 versuchen. Wenn das Buch eine Sammelwerks-/Lexikon-Komponente ist (kein eigenständiges Werk), kein Cover anlegen und das im Eintrag vermerken.

**Speichern:**
- Pfad: `Reenactment/Anhang/Buecher/<BuchOrdner>/cover.jpg` (oder `.png`, je nach Quelle).
- **Vor dem Endgültigen** Bild lesen (`Read`-Tool auf die heruntergeladene Datei) und prüfen, dass Autor + Titel zur Vault-MD passen. Wenn nicht eindeutig: dem Nutzer das Bild zeigen und nachfragen.
- Zwischendateien unter `~/.claude/tmp/covers/` ablegen, niemals unter `Reenactment/` (siehe CLAUDE.md → Temporäre Downloads).

**Was nicht tun:**
- Niemals ein nicht passendes Cover „einigermaßen passend" akzeptieren — lieber kein Cover als das falsche.
- Bei Mehrfach-Editionen ohne bekannte ISBN nicht raten — Nutzer fragen, welche Auflage er besitzt.
- Externe URLs (`covers.openlibrary.org/...`) nicht als Cover-Quelle im Frontmatter speichern — der Vault soll lokal autark sein.

## Goldene Regel

> Lieber ein knapper, korrekter Eintrag mit vielen `unbekannt`-Feldern als ein voller Eintrag, in dem Details halluziniert sind.

Wenn der Nutzer eine konkrete Quelle (Buch/PDF/URL) nennt: erst über [[pdf-lesen]] oder die URL prüfen und nur eintragen, was in der Quelle steht. Bei URL-basierten Einträgen über [[recherche]] arbeiten.

## Beispiel

Eingabe: "Neuer Fund: Lanzenspitze aus Grab X in Haithabu, ich habe noch keine Quelle dazu"

→ Datei: `Reenactment/Ausgrabungen/Funde/Lanzenspitze_X_Haithabu.md` (Name mit Nutzer abstimmen)
→ Template `fund.md`, gefüllt mit Titel/Fundort/Grab; alle übrigen Felder: `unbekannt`
→ Abschnitt "Offene Aufgaben / nachzutragen" listet die fehlenden Belege auf
