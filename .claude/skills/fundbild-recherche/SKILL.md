---
name: fundbild-recherche
description: Sucht online nach wissenschaftlich belegten, offiziell veröffentlichten Fund- und Ausstellungsbildern in Museumskatalogen und Sammlungsportalen (SHM/Historiska, Nationalmuseet, UNIMUS, British Museum, Europeana, DigitaltMuseum u.a.), prüft Provenienz (Inventarnummer, Institution) und Lizenz (CC0/CC BY/PDM/©) und bereitet sie zur Übernahme in den Vault auf. Wird ausgelöst, wenn der Nutzer "such mir ein Fundbild zu X", "offizielles Museumsfoto / Katalogbild beschaffen", "Bild aus dem Museumsbestand", "gibt es ein belegtes Foto von Objekt Y" sagt. Strikt faktentreu — nur Bilder mit nachweisbarer institutioneller Herkunft, niemals Reenactor-Fotos, Pinterest, Stockbilder oder KI-Bilder.
---

# fundbild-recherche

Findet **offiziell veröffentlichte, wissenschaftlich belegte** Bilder von Funden und Ausstellungsobjekten im Netz und bereitet sie samt Herkunfts- und Lizenznachweis für den Vault auf. Abgrenzung:

- **Textrecherche** zu einem Thema → [[recherche]]
- **Lokale Bildähnlichkeitssuche** im Vault → [[vault-bildsuche]]
- **Bild zuschneiden / entzerren / Tafel ausschneiden** → [[bild-bearbeiten]]
- **Eintrag anlegen** (Fund / Ausstellungsobjekt / Webquelle) → [[vault-eintrag]]
- **Buchseite einscannen/importieren** → [[buchscan-import]]

Diese Skill liefert das **belegte Bild + Metadaten + Lizenz**; das Ablegen im Vault übernehmen die obigen Skills.

## Quellen-Hierarchie (für Bilder)

Strikt von oben nach unten bevorzugen. **Je strukturierter das Sammlungsobjekt, desto besser** — ein Katalog-Objektdatensatz mit Inventarnummer, Datierung, Fundort und Lizenz schlägt jede bloße Dokument-/Post-Seite.

1. **Museums-Sammlungsportale mit Objektdatensatz** — die Goldquelle. Pro Objekt: Inventarnummer, Datierung, Fundort, Maße, Lizenz, herunterladbare Medien. Alle Domains unten geprüft (Stand 2026-05). Spalte „Bot" = WebFetch wird oft mit HTTP 403/429 abgewiesen → curl-Browser-UA-Fallback nutzen (siehe „Portale, die Bots blockieren").

   | Portal | Region | URL | Schwerpunkt / Lizenz | Bot |
   | --- | --- | --- | --- | --- |
   | **SHM / Historiska** | SE | `samlingar.shm.se` (Objekt `…/object/<UUID>`, Medien `media.samlingar.shm.se/item/<UUID>`); Wikinger-Teilportal `vikingar.historiska.se` | Größte Wikinger-Sammlung; Metadaten CC0, Bilder meist CC BY 4.0 / PDM | ok |
   | **Nationalmuseet** | DK | `samlinger.natmus.dk` | Dänische Vor-/Wikingerzeit | ok |
   | **UNIMUS / Universitetsmuseene** | NO | `unimus.no/portal/` (5 Universitätsmuseen, u.a. Kulturhistorisk museum Oslo) | Norwegische Archäologie inkl. Wikingerzeit | ok |
   | **Museum-digital** | DE | `museum-digital.de` (Regional-/Themenportale, exportiert nach DDB/Europeana) | Deutsche Museen, Archäologie | ok |
   | **Deutsche Digitale Bibliothek** | DE | `deutsche-digitale-bibliothek.de` | Aggregator dt. Institutionen | ok |
   | **Portable Antiquities Scheme (PAS)** | UK | `finds.org.uk/database` (JSON: URL + `/format/json`) | >1,4 Mio. Einzelfunde, Detektorfunde | 403 |
   | **British Museum** | UK | `britishmuseum.org/collection` | Große Sammlung, viele CC BY-NC-SA | 403 |
   | **The MET** | US | `metmuseum.org/art/collection` (Open-Access-API/CSV: `github.com/metmuseum/openaccess`) | Open Access, viele CC0 | 429 |
   | **Finna (Museovirasto)** | FI | `museovirasto.finna.fi/arkeologia`, allgemein `finna.fi` | Finnische Archäologie | ok |

   Weitere je nach Thema: Landesmuseum für Vorgeschichte Halle (`landesmuseum-vorgeschichte.de`), GNM Nürnberg, SMB-digital (Staatliche Museen Berlin), Vikingtidsmuseet/Museum of the Viking Age Oslo (`vikingtidsmuseet.no`).

2. **Aggregatoren** (mehrere Institutionen, aber **immer zur Originalinstitution durchklicken** und dort Inventarnr./Lizenz verifizieren):
   - **K-samsök / SOCH** (Schweden, maschinenlesbar) — siehe „K-samsök-API" unten.
   - **Europeana** `europeana.eu` (eigene API mit Lizenzfilter), **DigitaltMuseum** `digitaltmuseum.org` (NO/SE), **Deutsche Digitale Bibliothek**, **Kulturpool** (AT).
3. **Offizielle Dokumente / Berichte** (UNESCO WHC, Grabungsberichte, Open-Access-Tafelbände) — Bilder mit klarer Bildunterschrift und Abbildungsnummer.
4. **Wissenschaftliche Open-Access-Publikationen** mit Tafel-/Figurenteil (Acta Archaeologica, Antiquity, Uni-Repositorien).

**Niemals als Bildquelle:** Pinterest, Reenactor-/Hobby-Blogs ohne Beleg, Stockfoto-Seiten, Etsy/Shops, generische Bildersuche-Treffer ohne Institutionsbezug, KI-generierte Bilder. Ein Bild ohne nachweisbare Institution + Inventar-/Abbildungsnummer ist **kein** Fundbild im Sinne dieses Vaults.

## Workflow

1. **Auftrag klären.** Welches Objekt? Wenn vorhanden: Fundort, Grab-/Inventarnummer, Objekttyp, Datierung mitnehmen — das macht die Suche treffsicher. Bei vager Anfrage einmal nachfragen.

2. **Suchen.** WebSearch mit Eigenname + Ort + Inventarnummer, oder direkt auf einem Portal (z.B. `samlingar.shm.se` Stichwort). Max. 2–3 Suchen. Reenactor-/Shop-Domains ggf. über `blocked_domains` ausschließen.

3. **Objektdatensatz holen** (WebFetch auf die Objekt-URL). Extrahieren:
   - Inventarnummer / Objekt-ID, Institution
   - Objekttyp, Datierung, Fundort, Maße, Material — **nur was dort steht**
   - **Bild-URLs** (Download-/IIIF-Link), Anzahl Ansichten
   - **Lizenz** pro Bild (CC0 / CC BY 4.0 / PDM / © / unklar) + Attribution

4. **Provenienz prüfen.** Gehört das Bild wirklich zum gesuchten Fund? Inventarnummer/Fundort müssen passen. Bei Aggregator-Treffern zur **Originalinstitution** durchklicken und dort verifizieren. Bei Zweifel: dem Nutzer den Treffer zeigen, nicht raten.

5. **Lizenz entscheiden** (siehe „Lizenz & Bildrechte"). Das bestimmt, **ob** das Bild in den Vault darf oder nur verlinkt wird.

6. **Bild laden** (nur wenn Lizenz es erlaubt) nach `~/.claude/tmp/` (siehe „Temporäre Dateien"), dann **mit `Read` öffnen und visuell prüfen**, dass es das richtige Objekt zeigt und brauchbar ist.

7. **Bericht an Nutzer**: gefundene Bilder mit Quelle, Inventarnummer, Lizenz + Attributionspflicht, und Vorschlag zur Übernahme (welcher Eintragstyp, welcher Anhang-Ordner). Erst nach Bestätigung in den Vault übergeben (→ [[vault-eintrag]] / [[bild-bearbeiten]] / [[buchscan-import]]).

## Lizenz & Bildrechte (sehr wichtig)

Anders als bei reiner Textrecherche werden hier **Dateien** in den Vault übernommen. Daher zwingend die Lizenz prüfen, **bevor** ein Bild lokal abgelegt wird:

| Lizenz | In den Vault? | Pflicht |
| --- | --- | --- |
| **CC0 / Public Domain (PDM)** | ja | Quelle/Inventarnr. trotzdem notieren |
| **CC BY / CC BY-SA / CC BY-NC** | ja | **Attribution** (Institution, Fotograf, Lizenzname, URL) im Eintrag pflichtig |
| **© / „all rights reserved" / unklar** | **nein** | nur URL verlinken + im Eintrag vermerken „Bild urheberrechtlich geschützt, nur als Verweis" |

- Die **Lizenz immer mitschreiben** und im Vault-Eintrag dokumentieren — der Vault ist eine wissenschaftliche Sammlung, Bildnachweise gehören dazu.
- Im Zweifel über die Lizenz: **nicht herunterladen**, sondern Nutzer fragen / nur verlinken. Lieber ein Verweis als eine Rechteverletzung.
- Lizenzangaben **nicht erfinden**: wenn auf der Seite keine Lizenz steht, ist sie `unbekannt`, nicht „vermutlich frei".

## SHM / Historiska — konkret

Beispiel-Objekt: `https://samlingar.shm.se/object/5BF4B031-90C9-4862-9C83-9390B7F936D2`
(Stavtärning Bj, Inv. 270230_HST:1709, Björkö/Birka, 800–1100, Metadaten CC0, Bilder CC BY 4.0 / PDM).

- Objektseite per WebFetch holen → Inventarnummer, Fundort, Datierung, Maße, **Medien-Links** (`media.samlingar.shm.se/item/<UUID>`) und Lizenz pro Bild.
- Bild herunterladen (siehe Snippet unten), dann mit `Read` prüfen.

### K-samsök-API (maschinenlesbar, optional)

Für strukturierte/Massenabfragen bietet das Riksantikvarieämbetet die **K-samsök (SOCH)**-Web-API; sie liefert SHM-Objekte als XML/JSON. Für Entwicklung ist der API-Key `test` nutzbar (produktiv: Key beim Riksantikvarieämbetet anfragen). Nur einsetzen, wenn die normale Objektseiten-Recherche nicht reicht — und Felder weiterhin nur übernehmen, wenn sie wirklich im Datensatz stehen.

## Portale, die Bots blockieren

Manche offiziellen Seiten (z.B. `whc.unesco.org`-Dokumente) liefern WebFetch ein **HTTP 403**. Dann:

1. Per Browser-User-Agent mit `curl` nach `~/.claude/tmp/` laden und lokal ansehen (PDF → [[pdf-lesen]], Bild → `Read`):
   ```bash
   curl -L -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
     -o ~/.claude/tmp/<name>.<ext> '<url>'
   file ~/.claude/tmp/<name>.<ext>   # Format verifizieren
   ```
2. Klappt das nicht (Login/JS-Wall): die URL nur **als Verweis** im Eintrag festhalten und dem Nutzer sagen, dass das Bild manuell zu beschaffen ist. **Nicht** ersatzweise ein „ähnliches" Bild aus anderer Quelle einsetzen.

## Temporäre Dateien

Heruntergeladene Bilder/PDFs zuerst nach `~/.claude/tmp/` (persistentes Docker-Volume):

```bash
mkdir -p ~/.claude/tmp
curl -L -o ~/.claude/tmp/<objekt>_<quelle>.jpg '<bild-url>'
file ~/.claude/tmp/<objekt>_<quelle>.jpg   # ist es wirklich ein Bild?
```

**Niemals** direkt unter `Reenactment/` oder im Workspace-Root ablegen (CLAUDE.md → Temporäre Downloads, Google-Drive-Sync). Endgültig in den Vault kommt das Bild erst nach Bestätigung über [[vault-eintrag]] (Anhang-Ordner-Konvention) bzw. nach Aufbereitung über [[bild-bearbeiten]].

## Faktentreue (CLAUDE.md)

- **Bildbeschreibungen**: nur was tatsächlich zu sehen ist — keine ergänzten Datierungen/Materialien/Stilzuschreibungen.
- **Metadaten** (Inventarnr., Datierung, Fundort, Maße) nur aus dem Objektdatensatz übernehmen; was dort fehlt, bleibt `unbekannt`.
- Keine Mischung aus Allgemeinwissen und Quelle; keine erfundenen Inventar-/Abbildungsnummern oder URLs.
- Wenn kein belegtes Bild gefunden wird: das **so sagen** — kein Ersatzbild aus unbelegter Quelle einsetzen.

## Beispiel-Ergebnisform

```
Auftrag: Foto der Stavtärning aus Birka (Bj-Würfel), für Ausstellungseintrag

Befund:
- SHM/Historiska, Inv. 270230_HST:1709, Björkö/Adelsö (Birka), Dat. 800–1100. [1]
- 10 Ansichten verfügbar; Metadaten CC0, Bilder CC BY 4.0 (1 Bild PDM).
- Heruntergeladen: ~/.claude/tmp/stavtaerning_shm.jpg (geprüft: Knochenwürfel
  mit Punkt-Kreis-Ornament, 29×16×21 mm) — passt zum Datensatz.

Lizenz/Attribution (pflichtig bei Übernahme):
  Foto: Historiska museet / SHM, CC BY 4.0, [1]

Quelle:
[1] https://samlingar.shm.se/object/5BF4B031-… — SHM, abgerufen 2026-05-30

Vorschlag: Übernahme als Fund-/Webquelle-Eintrag über [[vault-eintrag]];
Bild nach Anhang, Attribution im Eintrag dokumentieren. OK?
```
