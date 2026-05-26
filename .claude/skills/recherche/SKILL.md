---
name: recherche
description: Recherchiert Themen aus der Wikingerzeit / dem historischen Reenactment im Web (WebSearch + WebFetch), prüft die Funde mit Blick auf wissenschaftliche Belastbarkeit und liefert Ergebnisse mit Quellennachweis, geeignet zur Übernahme als Webquelle-Eintrag im Vault. Wird ausgelöst, wenn der Nutzer "recherchiere X", "such mir Quellen zu Y", "was sagt das Netz über Z", "Museumsbestand prüfen" sagt. Strikt: nur belegen, was die Quelle wirklich sagt — keine Mischung aus Allgemeinwissen und Quellenangabe.
---

# recherche

Web-Recherche mit Faktentreue als oberster Regel. Die Skill ersetzt nicht den Bibliotheksbesuch — sie sammelt verlässliche Anhaltspunkte und kennzeichnet ihre Grenzen.

## Quellen-Hierarchie

Beim Vorschlagen / Zitieren in dieser Reihenfolge bevorzugen:

1. **Museumskataloge & Institute** (z.B. Statens Historiska Museum, Moesgaard, Stiftung Schleswig-Holsteinische Landesmuseen, Wikingermuseum Haithabu)
2. **Begutachtete Publikationen** (Antiquity, Acta Archaeologica, JSTOR, Open-Access-Journals)
3. **Universitäts-/Forschungsseiten** (.uni-*.de, .ac.uk, .edu)
4. **Reenactment-Communities mit Quellenarbeit** (Lazy Reenactor Girl, Hurstwic — Quellenlage stets gegenchecken)
5. Allgemein-Enzyklopädisches (Wikipedia) **nur als Einstiegspunkt**, nie als Beleg ohne Weiterverfolgung der Primärquelle.

## Workflow

1. **Suche formulieren**
   - Konkrete Suchbegriffe; bei archäologischen Themen Eigennamen plus Ort/Inventarnummer.
   - WebSearch nutzen, max. 2-3 Suchen pro Frage. Bei vager Anfrage erst klären (Zeitraum, Region, Objekttyp).

2. **Treffer scannen**
   - 3-5 vielversprechende URLs identifizieren, kurz erklären, warum.

3. **Inhalt holen mit WebFetch**
   - Pro URL kurzer Auftrag: "Extrahiere belegte Fakten zu <Frage>; ignoriere SEO/Werbung/Empfehlungs-Bausteine."
   - Bei PDFs / großen Files: nicht ins Workspace laden. Wenn ein Download nötig ist, nach `~/.claude/tmp/` (CLAUDE.md), nicht in den Vault.

4. **Ergebnis konsolidieren**
   - Pro Aussage eine konkrete Quelle (URL + Autor/Institution + Abrufdatum).
   - Widersprüche zwischen Quellen ausdrücklich nennen, nicht glattbügeln.
   - Lücken/Unbestätigtes als solches markieren ("nur in Reenactor-Blog erwähnt, keine Primärquelle gefunden").

5. **Bericht an Nutzer**
   - Zusammenfassung in 5-15 Zeilen mit nummerierten Quellen.
   - Vorschlag, ob das Ergebnis als Webquelle-Eintrag in den Vault übernommen werden soll (über [[vault-eintrag]] → Typ Webquelle).

## Was nicht passieren darf

- **Keine Synthese aus Allgemeinwissen + Quelle.** Wenn eine Quelle eine Datierung nicht enthält, darf sie auch nicht im Bericht erscheinen.
- **Keine Mehrfachzuordnung**: Aussage A stammt aus Quelle 1, Aussage B aus Quelle 2 — niemals quellenfremde Detailangaben unter eine andere URL packen.
- **Keine Übernahme reiner Sekundärzitate** (Quelle X zitiert Y) ohne Hinweis, dass Y nicht selbst eingesehen wurde.
- **Keine erfundenen URLs / DOIs / ISBNs.** Wenn der Nutzer um eine ISBN bittet und keine sicher belegt ist: explizit "nicht ermittelt".

## Temporäre Dateien

Heruntergeladene PDFs/Bilder/HTML-Schnipsel:

```bash
mkdir -p ~/.claude/tmp
curl -L -o ~/.claude/tmp/<name>.<ext> '<url>'
```

**Niemals** in `/workspaces/ratatoskr/` oder `/tmp/` innerhalb des Workspace. Workspace ist Google-Drive-synchronisiert (siehe CLAUDE.md).

Nur wenn die Datei explizit Teil des Vaults werden soll (z.B. ein Buchscan nach Konvention) → Übergabe an [[buchscan-import]].

## Beispiel-Ergebnisform

```
Frage: Aufbewahrungsort und Inv.-Nr. des Feuereisens aus Bj 644 (Birka)

Befund:
- Bj 644 ist im Bestand des Statens Historiska Museum (SHM), Stockholm. [1]
- Eine konkrete Inventarnummer für DAS Feuereisen ist im verfügbaren Online-
  Material nicht angegeben. Die Gesamtkollektion Bj 644 ist unter SHM 34000:Bj644
  recherchierbar — Einzelobjekt-IDs erfordern Konsultation der Druckausgabe von
  Arbman 1943 (Bd. 1, Tafel 183, Beschreibungsband). [2]
- Widerspruch: ein Reenactor-Blog datiert das Feuereisen "10. Jh.", ohne Quelle. [3]

Quellen:
[1] https://historiska.se/... — SHM, abgerufen 2026-05-26
[2] https://...arbman... — Bibliografische Übersicht, abgerufen 2026-05-26
[3] https://lazyreenactor.../bj644 — Reenactor-Blog, Quellenlage offen

Lücke: Inv.-Nr. des Einzelobjekts → nach Konsultation von Arbman 1943 nachtragen.
```
