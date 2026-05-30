# CLAUDE.md – Ratatoskr Vault

## Temporäre Downloads

Nur der Ordner `Reenactment/` wird mit Google Drive synchronisiert. Temporäre Dateien (Downloads via `curl`, `wget`, WebFetch-Zwischenablagen, Scratch-Dateien etc.) dürfen **niemals** unter `Reenactment/` landen.

Außerhalb von `Reenactment/` sind sie ok – bevorzugt unter `tmp/` im Workspace-Root oder in `~/.claude/tmp/` (persistentes Docker-Volume). Jeder Pfad, der für Temporäres im Workspace benutzt wird, muss in `.gitignore` stehen.

Nur Dateien, die explizit Teil des Vaults werden sollen (z. B. Buchscans nach Konvention), kommen unter `Reenactment/`.

## Git und Reenactment/

Der Ordner `Reenactment/` ist **nicht** Teil des Git-Repositories (er wird über Google Drive synchronisiert). Daher beim Umsortieren / Umbenennen innerhalb von `Reenactment/` **immer `mv`** verwenden — niemals `git mv`, das würde fehlschlagen, weil die Dateien nicht im Git-Index sind.

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

Die Struktur ist zweigeteilt: **Markdown-Einträge** (Text + Frontmatter) und der **Anhang** (Binärdateien wie Bildscans, PDFs, Fotos). Beide Hierarchien spiegeln einander.

```text
Reenactment/
├── Literatur/
│   ├── Buecher/                                   # ein .md pro Buch
│   ├── Abhandlungen/                              # ein .md pro Aufsatz/Artikel/Dissertation
│   ├── Webquellen/                                # ein .md pro Webseite/Video/Blog
│   └── Literatur-Uebersicht.md
├── Ausgrabungen/
│   ├── Fundorte/                                  # ein .md pro Ausgrabungsstätte
│   ├── Funde/                                     # ein .md pro Einzelfund
│   ├── Fundkomplexe/                              # ein .md pro geschlossenem Komplex: Grab (type: Grab) oder Hort/Depot (type: Fundkomplex)
│   └── Karte.md                                   # Dataview-Übersicht
├── Ausstellung/                                   # eigene Repliken, nach Kategorie sortiert
│   ├── Waffen/
│   ├── Schmuck/
│   ├── Taschen/
│   ├── Bekleidung/
│   └── Alltag/
├── Markt/                                         # kommerzieller Replik-Markt (KEIN Beleg, „laut Händler/Hersteller")
│   ├── Hersteller/                                # ein .md pro Hersteller/Marke
│   ├── Haendler/                                  # ein .md pro Webshop/Händler
│   └── Produkte/                                  # ein .md pro Produkt/Artikel
├── Projekte/                                      # geplante Bauprojekte (eigene Werkstücke)
├── Notizen/
├── ToDo/
└── Anhang/                                        # Binärdateien — spiegelt die MD-Struktur
    ├── Buecher/<BuchOrdner>/                      # Buchscans pro Buch
    ├── Abhandlungen/                              # PDFs der Aufsätze/Artikel
    ├── Webquellen/                                # optional, falls Webquellen-Anhänge
    ├── Fundkomplexe/<KomplexID>/                  # Bilder/Pläne + Inventarbilder pro Grab/Hort (spiegelt Ausgrabungen/Fundkomplexe/)
    ├── Funde/<Fundname>/                          # Bilder pro erfasstem Einzelfund (spiegelt Ausgrabungen/Funde/)
    ├── Fundebelege/                               # Rohscans/Fotos noch nicht erfasster Funde
    ├── Ausstellung/<Kategorie>/<Objekt>/          # Replikfotos pro Ausstellungsobjekt
    ├── Markt/<Subtyp>/<Name>/                     # optional; Produktbilder meist nur verlinkt (Markt = kommerziell/©)
    ├── Projekte/<ProjektOrdner>/                  # Bilder/Skizzen geplanter Werkstücke
    └── Bilder/
```

## Konvention: YAML-Frontmatter

Jeder Eintrag beginnt mit einem Frontmatter-Block zwischen zwei `---`. Dieser Block muss **valides YAML** sein, sonst zeigt Obsidian/Dataview ihn nicht korrekt an. Beim Anlegen oder Ändern von Frontmatter gilt:

- **Werte mit YAML-Sonderzeichen in Anführungszeichen setzen.** Sobald ein Wert eines der Zeichen `:` (Doppelpunkt+Leerzeichen), `#`, `"`, `'`, `[`, `]`, `{`, `}`, `,`, `&`, `*`, `?`, `|`, `>`, `%`, `@`, `` ` `` enthält oder mit `-` beginnt, gehört er in **doppelte Anführungszeichen**. Beispiele: `title: "Birka I – Die Gräber"`, `reihe: "Birka. Untersuchungen…"`. Einfache Wörter/Zahlen/Datümer (`type: Buch`, `erscheinungsjahr: 1943`, `datum: 2026-05-30`) brauchen keine.
- **Werte, die ein `"` enthalten, komplett in _einfache_ Anführungszeichen `'…'` setzen** (so macht es auch Obsidian selbst). Der **ganze Wert** kommt zwischen ein Paar `'…'` — es wird _nicht_ das innere `"` einzeln umquotet/escapt. In `'…'` sind `"` dann völlig egal; nur ein echtes `'` im Text muss als `''` verdoppelt werden.

  ```yaml
  # richtig: ganzer Wert in '…', inneres " bleibt unangetastet
  masse: '29 × 16 × 21 mm (L × B × H); Typkort: „Längd 3 cm"'
  # falsch: in "…" schließt das innere " den String vorzeitig …
  masse: "29 × 16 × 21 mm (L × B × H); Typkort: „Längd 3 cm""
  # falsch: nicht das innere " einzeln umquoten
  masse: "29 × 16 × 21 mm (L × B × H); Typkort: „Längd 3 cm"'"'"
  ```

  (Nur als Notlösung: in `"…"` jedes innere `"` als `\"` escapen — umständlicher und fehleranfällig.)
- **ISBN, Telefonnummern, Inventarnummern** immer quoten (`isbn: "978-3-8289-2451-2"`), sonst interpretiert YAML sie als Zahl/Datum.
- **Listen** (z. B. `tags`, `aliases`, `baende`) als Block-Liste schreiben, je Eintrag eine eigene Zeile mit `-` davor.

### Tags: ein Tag = ein Token, **keine Leerzeichen**

Tags (und `aliases`) sind Obsidian-Tags und dürfen **niemals Leerzeichen** enthalten — ein Leerzeichen zerlegt das Tag bzw. macht den YAML-Wert mehrdeutig. Mehrwortbegriffe zusammenziehen oder mit `-`/`_` verbinden, ASCII bevorzugen:

```yaml
# falsch
tags:
  - Pera Peris
  - CC BY
# richtig
tags:
  - PeraPeris            # zusammengezogen
  - CC-BY                # oder mit Bindestrich verbinden
```

### Vor dem Commit prüfen (Tool statt Handarbeit)

Nicht alle Einträge manuell durchsehen — der Validator [tools/check_frontmatter.py](tools/check_frontmatter.py) prüft das gesamte Vault auf ungültiges YAML, doppelte Keys und auf Tags/Aliases mit Leerzeichen:

```bash
python3 tools/check_frontmatter.py            # ganzes Reenactment/
python3 tools/check_frontmatter.py Reenactment/Literatur/Buecher/Neu.md   # gezielt
```

Exit-Code 0 = sauber, 1 = Befunde. In VSCode ist zusätzlich `redhat.vscode-yaml` (Devcontainer) aktiv, das reine `.yml`-Dateien live prüft; Markdown-Frontmatter deckt es aber nicht ab — dafür ist der Validator zuständig.

## Konvention: Literatureinträge

Drei MD-Typen unter `Reenactment/Literatur/`. Naming durchgängig **`<Autor>_<Jahr>_<Stichwort>.md`** mit Unterstrichen, ASCII (`ae/oe/ue/ss`), keine Sonderzeichen.

| Unterordner | Inhalt | Beispiel-Dateiname |
| --- | --- | --- |
| `Buecher/` | Selbstständige Monografien, Tafelbände, Sammelbände | `Arbman_1943_Birka_Graeber.md` |
| `Abhandlungen/` | Aufsätze, Buchkapitel, Dissertationen, Zeitschriftenartikel | `Eisenschmidt_2008_Graeber_Haithabu.md` |
| `Webquellen/` | Webseiten, Videos, Blog-Beiträge, Museumsdatenbanken | `Edberg_2022_Spelfoeremaal_Sigtuna.md`, `Moren_LazyReenactorGirl_Blog.md` |

Bei Webquellen kann sich das Schema lockern, wenn kein klarer Autor/Jahr vorliegt — dann **`<Thema>_<Quelle>.md`** (z. B. `Haithabu_Danewerk_UNESCO.md`). **Mehrere Einträge derselben Seite/Quelle werden zu _einer_ Webquelle zusammengefasst** (siehe „Konvention: Webquellen als Werk" unten).

### Anhänge

- **Buchscans**: `Reenactment/Anhang/Buecher/<BuchOrdner>/` (siehe Abschnitt „Konvention: Buchscans" unten)
- **Abhandlungs-PDFs**: `Reenactment/Anhang/Abhandlungen/<dateiname>.pdf`
- **Webquellen-Anhänge** (selten): `Reenactment/Anhang/Webquellen/`

## Konvention: Webquellen als Werk (wie Buch)

Eine **Webquelle = eine Seite/Quelle = ein Eintrag** wird **wie ein Buch** behandelt: die Seite/Domain ist das „Werk", die einzelnen Unterseiten/Beiträge sind die „Seiten" bzw. – bei viel Inhalt – die „Kapitel" (analog zu eingescannten Buchseiten). Das gilt für **alle** Quellen mit mehreren abgerufenen Unterseiten, insbesondere:

- **Blogs** (z. B. `lazyreenactorgirl.wordpress.com` → `Moren_LazyReenactorGirl_Blog.md`): das Blog ist das Werk, die Blog-Beiträge sind die „Seiten/Kapitel" (je ein `## Beitrag: …`-Abschnitt mit unverändert übernommenem Inhalt).
- **Mehrseitige Webseiten** (z. B. `haithabu.de` → `Wikinger_Museum_Haithabu.md`): je ein `## Seite: …`-Abschnitt.
- **Museums-/Sammlungskataloge** (z. B. `samlingar.shm.se` → `SHM_Samlingar.md`, `subtype: Museumskatalog`): je Objektseite eine Tabellenzeile (Sonderfall, siehe unten).

Aufbau jeder Werk-Webquelle:

- **Eine MD-Datei** unter `Reenactment/Literatur/Webquellen/` pro Werk (Name nach Domain/Autor, ASCII, Unterstriche), `type: Webquelle`. Das Frontmatter beschreibt das Werk (Blog/Webseite/Katalog), nicht den Einzelbeitrag.
- **Eine Übersichtstabelle** der Seiten/Beiträge (Titel als interner Anker `[[#…]]`, Datum, URL, Archiv-PDF).
- **Je Unterseite ein `##`-Abschnitt** mit dem Inhalt (faktentreu, wörtlich aus der Quelle; nichts ergänzen).
- **Archivierte PDF-Schnappschüsse** in **einem Ordner pro Werk**: `Reenactment/Anhang/Webquellen/<Werk>/…pdf`, gelistet in einem `## Anhang – Dokumente`-Abschnitt.
- **Deep-Links** aus anderen Einträgen zeigen auf den Kapitel-Anker: `[[<Werk>#<Überschrift>|Alias]]`. Überschriften ankerfreundlich halten (kein `# | ^ [ ]`; `:`, `–`, `()` sind ok).

### Nachrüsten: neuer Beitrag derselben Seite ⇒ bestehende Webquelle umbauen

Kommt ein **weiterer Beitrag/Unterseite einer bereits erfassten Quelle** hinzu, wird **kein zweiter Einzel-Eintrag** angelegt. Stattdessen:

1. Falls die Quelle bisher als **einzelner** Eintrag (eine Seite) vorliegt, diesen **in die Werk-Struktur oben umbauen** (Frontmatter aufs Werk umstellen, bisherigen Inhalt zu `## Beitrag/Seite: …` machen) — genau wie bei `Moren_LazyReenactorGirl_Blog.md` und `Wikinger_Museum_Haithabu.md` geschehen.
2. Den neuen Beitrag als weiteren `##`-Abschnitt + Tabellenzeile ergänzen, sein PDF in den Werk-Ordner unter `Anhang/Webquellen/<Werk>/` legen.
3. **Backlinks umbiegen** (`grep -rn` im Vault nach dem alten Notiznamen) und die Zähler/Tabelle in `Literatur/Literatur-Uebersicht.md` aktualisieren.
4. Beim Umbenennen/Verschieben innerhalb von `Reenactment/` `mv` verwenden (nicht `git mv`, s. o.).

### Museumskatalog (Sonderfall)

Beim Museums-/Sammlungskatalog (`subtype: Museumskatalog`) heißt der Seiten-Abschnitt `## Anhang – Aufgerufene Objektseiten` (je Zeile: Objektseiten-URL, Inventarnummer **wörtlich wie im Katalog**, Wikilink auf den Fund-Eintrag). Lizenzangaben (Metadaten + Medien) gehören ins Frontmatter und in einen `## Lizenz / Nutzung`-Abschnitt. **Die fachlichen Fund-Informationen stehen NICHT in der Webquelle**, sondern in einem eigenen Eintrag unter `Reenactment/Ausgrabungen/Funde/` (`type: Fundbelegeintrag`), der per Wikilink `[[<Katalog-Webquelle>]]` auf die Objektseite verweist — genau wie ein Fund auf ein Buch + Tafel verweist.

### Fundbilder gehören in den Anhang

Referenzierte Fund-/Objektbilder werden **nicht nur verlinkt, sondern als Bilddatei in den Anhang geholt und im Eintrag eingebunden** (`![…](../../Anhang/…)`). Das gilt für **beide** Bezugswege:

- **Webquelle / Museumskatalog:** Objektfotos der Objektseite herunterladen (Lizenz pro Bild prüfen, siehe unten) → ablegen unter:
  - Einzelfund: `Reenactment/Anhang/Funde/<Fundname>/<datei>.jpg`
  - Fund aus Grab/Komplex: `Reenactment/Anhang/Fundkomplexe/<KomplexID>/<datei>.jpg`
- **Literatur / PDF (Tafelband, Abhandlung):** die referenzierte **Tafel/Abbildung aus dem PDF herausschneiden** (über [vault-suche](.claude/skills/vault-suche/SKILL.md) → [bild-bearbeiten](.claude/skills/bild-bearbeiten/SKILL.md) bzw. `tools/vault_pdf_detail.py crop`) und als Bilddatei in denselben Anhang-Ordner legen. Das Original-PDF bleibt zusätzlich als Buchscan/Abhandlung erhalten.
- **Lizenz/Attribution** ist Pflicht: CC0/PDM → frei (Quelle nennen); CC BY → Namensnennung (Institution/Fotograf) als Bild-Caption im Eintrag; © / unklar → **nicht** in den Anhang, nur verlinken.
- **Grab-/Komplex-Inventare:** auch die Inventartafeln/Übersichtsbilder eines Grabes oder Hortes gehören in `Anhang/Fundkomplexe/<KomplexID>/` und werden im Komplex-Eintrag eingebunden.

### Neuer Fund ⇒ Kontext mitpflegen

Wird ein Fundobjekt neu angelegt (egal ob aus Webquelle oder Literatur/PDF), **immer** die zugehörigen Kontext-Einträge aktualisieren — nach Fundkontext (siehe „Konvention: Fundkomplexe & Fundkontext" unten):

- **Fundort** (`Ausgrabungen/Fundorte/<Ort>.md`): **immer** unter „Verknüpfte Funde" (und ggf. beim passenden Befund/Schicht) verlinken.
- **Fundkomplex** (`Ausgrabungen/Fundkomplexe/<KomplexID>.md`): nur bei geschlossenem Komplex — den Fund im Inventar des **Grabes** (`type: Grab`) bzw. **Hortes/Depots** (`type: Fundkomplex`) verlinken. **Siedlungs-/Streufunde** (z. B. Svarta jorden) gehören zu **keinem** Komplex; das im `fundkontext`-Feld vermerken, keinen Komplex/kein Grab erfinden.

## Konvention: Fundkomplexe & Fundkontext

Ein **Grab ist ein Sonderfall des geschlossenen Fundkomplexes** (versiegelter, assoziierter Fundverband). Beide werden als **Bündel-Einträge** geführt, die Einzelfunde zusammenfassen, und liegen **im selben Ordner** `Reenactment/Ausgrabungen/Fundkomplexe/` — unterschieden über `type:`, **nicht** über den Ordner (so erzwingt eine Umklassifizierung nie eine Dateiverschiebung):

| `type:` | Was | Beispiel-Dateiname |
| --- | --- | --- |
| `Grab` | Bestattung (mit Anthropologie-/Bestattungsfeldern) | `Bj644_Birka.md` |
| `Fundkomplex` | geschlossener Komplex ohne Bestattung: Hort, Depot, Opfer-/Moorfund | `Spillings_Hort_Gotland.md` |

- **Dateinamen ohne `Grab_`/`Fundkomplex_`-Prefix** — der `type:`-Eintrag unterscheidet. So bleiben Wikilinks (`[[Bj644_Birka]]`) stabil, weil Obsidian über den Dateinamen auflöst.
- Anhang spiegelt: `Reenactment/Anhang/Fundkomplexe/<KomplexID>/`.

### Einzelfunde: das `fundkontext`-Feld

Einzelfunde (`Ausgrabungen/Funde/`, `type: Fundbelegeintrag`) tragen statt eines überladenen `grab:`-Feldes ein **`fundkontext:`**-Feld mit kontrolliertem Vokabular:

`Grab | Siedlung | Hort/Depot | Opferfund | Lösfund/Streufund | Hafen | Werkstatt | unbekannt`

- Bei **geschlossenem Komplex** (Grab/Hort) zusätzlich `komplex: "[[<Komplex-Eintrag>]]"` (z. B. `[[Bj644_Birka]]`) und dort im Inventar verlinken.
- Bei **Siedlungs-/Streufund** kein `komplex`/`grab`; Anker ist der **Fundort** plus Ortsnummer.
- **Ortsnummer** (das Site-Analog zur Grabnummer) im Eintrag festhalten, wenn belegt: Fornlämning/RAÄ (SE, z. B. `L2017:1568`), Askeladden-ID (NO), `sb.`-Nr (DK). Der eindeutige Objekt-Handle bleibt die **Museums-/Inventarnummer** (`museum_nr`), z. B. SHM-, C-/B-/T-/Ts- (NO), Danefæ/NM- (DK), PAS-ID (UK).
- Faktentreue: grabungsinterne Fund-/Befundnummern (Fnr, Kontext/SE) nur eintragen, wenn aus der Quelle belegt — sonst `unbekannt`.

## Konvention: Ausstellungseinträge

Eigene Repliken werden in `Reenactment/Ausstellung/<Kategorie>/<Objekt>.md` erfasst, mit fünf festen Kategorie-Ordnern:

| Kategorie | Typische Objekte |
| --- | --- |
| `Waffen/` | Schwerter, Äxte, Saxe, Lanzen |
| `Schmuck/` | Fibeln, Anhänger, Halsketten, Ringe |
| `Taschen/` | Gürteltaschen (Tarsoly), Schultertaschen |
| `Bekleidung/` | Gürtel, Tunika-/Schuh-Repliken |
| `Alltag/` | Feuereisen, Klappmesser, Kämme, Würfel, Trinkgefäße, Spielsteine |

### Naming

`<Objekt>[_<Vorbild>].md`, Unterstriche, ASCII. **Niemals `_Replik`-Suffix** — der `type: Ausstellungsobjekt`-Eintrag im Frontmatter macht das klar. Beispiele:

- `Axt.md` (kein konkretes Vorbild)
- `Koenigsschwert_Haithabu.md` (Vorbild = Haithabu)
- `Walkuere_Anhaenger_Suffolk.md` (Vorbild = Suffolk SF-9305)

### Anhang spiegelt die Kategorie-Struktur

```text
Reenactment/Anhang/Ausstellung/<Kategorie>/<Objekt>/<datei>.jpeg
```

Beispiel: zu [Ausstellung/Waffen/Ulfberht_Gnezdovo.md](Reenactment/Ausstellung/Waffen/Ulfberht_Gnezdovo.md) gehört [Anhang/Ausstellung/Waffen/Ulfberht_Gnezdovo/](Reenactment/Anhang/Ausstellung/Waffen/Ulfberht_Gnezdovo/).

### Relative Pfade

Da MD-Dateien zwei Ebenen tief liegen (`Ausstellung/<Kat>/<X>.md`), sind alle Anhang-Pfade `../../Anhang/...`:

```markdown
![Foto](../../Anhang/Ausstellung/Waffen/Ulfberht_Gnezdovo/ulfberht_eigenes_foto.jpeg)
```

Dieselbe `../../`-Tiefe gilt auch für Verweise auf Buchscans, Abhandlungs-PDFs etc. aus Ausstellungseinträgen heraus.

### Frontmatter (Pflichtfelder)

`title, type: Ausstellungsobjekt, kategorie, objekt_nr, vorbild, datierung_vorbild, material_replik, hersteller, status, tags` — `unbekannt` ist erlaubt und erwartet, wenn die Quelle nichts hergibt (siehe Faktentreue).

## Konvention: Markt (Hersteller / Händler / Produkte)

Die kommerzielle Bezugs-Seite (wo bekomme ich ein Stück, wer macht es) liegt unter `Reenactment/Markt/` — analog zu `Ausgrabungen/`, mit drei Subtypen, unterschieden über `type:`:

| `type:` | Was | Ordner | Beispiel-Dateiname |
| --- | --- | --- | --- |
| `Hersteller` | Hersteller/Marke | `Markt/Hersteller/` | `Pera_Peris.md` |
| `Haendler` | Webshop/Zwischenhändler | `Markt/Haendler/` | `Battle_Merchant.md` |
| `Produkt` | konkreter Artikel | `Markt/Produkte/` | `Feuerstahl_Ulfberth.md` |

- **Naming:** Hersteller/Händler = Eigenname (ASCII, Unterstriche). Produkt = `<Objekt>[_<Hersteller>].md`.
- **Anhang spiegelt:** `Reenactment/Anhang/Markt/<Subtyp>/<Name>/`.
- **Hersteller vs. Händler:** klären, ob der Shop **selbst Hersteller** ist (z. B. Mytholon; „Ulfberth" = Eigenmarke von Battle-Merchant) oder nur **Zwischenhändler**. Ein Zwischenhändler kann mehr Produktinfos zeigen als der Hersteller — verwenden, aber „laut Händler" und trotzdem die Marke benennen.

### Zuverlässigkeit (wichtig)

Markt-Angaben sind **durchweg kommerziell** und **kein Beleg für historische/archäologische Fakten** — weder Händler **noch** Hersteller:

- **Händlerangaben** mit **„laut Händler"** kennzeichnen, **Herstellerangaben** mit **„laut Hersteller"**. Marketing-Claims („originalgetreu", „nach Birka-Fund") **nicht** als belegt behandeln.
- **Belegt** sind nur **Museumskataloge** und **wissenschaftliche Literatur** (Bücher/Abhandlungen). Einschränkung „i. d. R.": in der Literatur gelistete **Webquellen/Blogs** können ähnlich unzuverlässig sein wie Markt-Infos und gelten nicht automatisch als Beleg.
- Datierung/Provenienz/Historizität daher nie aus Markt-Quellen übernehmen, sondern über Museum/Literatur belegen.
- **Preise** mit Währung + Datum erfassen („laut Händler"); unbekannte Felder = `unbekannt`.

### Ähnliche Artikel

Ist der **Hersteller nicht klar bestimmbar** oder gibt es **sehr ähnliche Produkte anderer Anbieter**, diese als **„ähnliche Artikel"** auflisten (Anbieter, URL, worin ähnlich) statt sich auf einen unsicheren Treffer festzulegen.

### Produktbilder

**Nicht herunterladen, nur verlinken** (kommerziell/©). **Ausnahme:** gibt es noch kein eigenes schönes Ausstellungsfoto, darf ein Produktbild als **Platzhalter** dienen (Lizenz beachten) — und der Fall wird in [ToDo.md](Reenactment/ToDo.md) als „eigenes Ausstellungsfoto nachholen / Platzhalter austauschen" notiert.

### Quer-Verlinkung

Ein `Produkt` verlinkt — soweit vorhanden — auf das **historische Vorbild** (`Ausgrabungen/Funde/`, Beleg über Museum/Literatur, **nicht** über den Shop) und auf die **eigene Replik** (`Ausstellung/<Kategorie>/`). Recherche der Markt-Daten läuft über die Skill [produkt-recherche](.claude/skills/produkt-recherche/SKILL.md); Hersteller-Hypothesen bei unklarer Herkunft (z. B. Pera Peris zuerst) stehen in [ToDo.md](Reenactment/ToDo.md) → „Hersteller-Hypothesen".

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

Da die MD-Dateien in `Literatur/Buecher/` (bzw. `Literatur/Abhandlungen/`, `Ausstellung/<Kat>/`) liegen, ist der relative Pfad nach `Anhang/Buecher/` immer `../../Anhang/Buecher/`.
