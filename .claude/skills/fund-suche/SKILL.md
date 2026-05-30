---
name: fund-suche
description: Sucht einen Fund/ein Objekt mehrgleisig und parallel — gleichzeitig lokal im Reenactment-Vault (Text via vault-suche, Bildähnlichkeit via vault-bildsuche), online in offiziellen Museumskatalogen (fundbild-recherche) und kommerziell am Markt (produkt-recherche: Hersteller/Webshops) — wobei die VLM-Bildbeschreibung sowohl die Museums- als auch die Markt-Suche schärft, und führt die Befunde zu einem gegenvalidierten Gesamtbild zusammen (was ist schon erfasst, was gibt es belegt im Netz, wo ist es käuflich, wo sind Lücken). Wird ausgelöst, wenn der Nutzer "such mir alles zu Fund X", "gibt es Fund Y schon im Vault und sonst belegt", "recherchiere Objekt Z im Vault und online", "Fundsuche zu …" sagt. Orchestriert vault-suche (lokal Text), vault-bildsuche (lokal Bild), fundbild-recherche (online belegt) und produkt-recherche (Markt/kommerziell); legt selbst nichts an, sondern bündelt die Treffer und schlägt die nächsten Schritte vor. Strikt faktentreu — Markt-Angaben sind kommerziell ("laut Händler/Hersteller") und kein Beleg.
---

# fund-suche

Findet einen Fund oder ein Objekt **mehrgleisig und parallel** und stellt das Ergebnis als ein Gesamtbild dar. Die Skill macht selbst keine neue Recherche-Mechanik auf, sondern **orchestriert bestehende Skills**:

- **lokal im Vault (Text)** → [[vault-suche]] (Volltext, Frontmatter, Tags, Wikilinks, Bildscans)
- **lokal im Vault (Bild)** → [[vault-bildsuche]] (visuelle Ähnlichkeit über VLM-Beschreibungen + Embeddings)
- **online, belegt** → [[fundbild-recherche]] (Museumskataloge/Sammlungsportale, Provenienz + Lizenz)
- **Markt, kommerziell** → [[produkt-recherche]] (Hersteller-Seiten + Webshops/Händler) — **kein Beleg**, nur Bezugsquelle/Replik-Markt; jede Angabe „laut Händler"/„laut Hersteller"

Alle Stränge sind **unabhängige Quellen** und laufen **gleichzeitig** — keiner wartet auf den anderen. Je mehr validierte Fund-Infos zusammenkommen, desto besser; der Wert dieser Skill liegt im **Abgleich/Gegenvalidieren** der Befunde, nicht in einer festen Reihenfolge. **Zuverlässigkeit:** belegt sind nur Vault-Einträge, Museumskataloge und wissenschaftliche Literatur; **Markt-Angaben (und Blogs/Webquellen)** sind kommerziell bzw. ungeprüft und zählen **nicht** als Beleg für Datierung/Provenienz/Historizität.

**Bildsuche speist die Online-Suche.** Liegt zum Objekt ein Bild vor (eigenes Replik-Foto, Anhang-Scan, Web-Treffer), liefert der VLM von [[vault-bildsuche]] eine rein deskriptive Merkmalsbeschreibung (Objektform, Anzahl, Ornament, Konstruktion, Beschriftung). Diese **konkreten Sichtmerkmale werden zu zusätzlichen Suchtermen** — sowohl für die Museumskatalog-Suche in [[fundbild-recherche]] als auch für die Markt-Suche in [[produkt-recherche]] (Hersteller/Webshop ohne bekannten Produktnamen) — oft treffsicherer als der bloße Objektname. Gleichzeitig findet die Bildsuche lokal vergleichbare Funde/Tafeln im Vault. **Faktentreue:** VLM-Beschreibungen sind maschinell und ungeprüft — nur als **Suchinput** verwenden, niemals als Fakt in einen Eintrag übernehmen (siehe [[vault-bildsuche]]).

Sie legt **nichts selbst an**. Übernahme eines Treffers läuft danach über:

- **Eintrag anlegen** (Fund / Fundort / Grab / Webquelle) → [[vault-eintrag]]
- **Tafel/Abbildung aus PDF in den Anhang holen** → [[vault-suche]] (Tafel-Ablauf) bzw. [[bild-bearbeiten]]
- **Online-Bild aufbereiten/zuschneiden** → [[bild-bearbeiten]]

Abgrenzung: reine **Textrecherche** zu einem Thema → [[recherche]]. (Die **lokale Bildähnlichkeit** [[vault-bildsuche]] ist hier als dritter Strang eingebunden, siehe unten — als eigenständige Suche aber auch direkt nutzbar.)

## Workflow

1. **Auftrag klären.** Welcher Fund/Objekttyp? Wenn vorhanden Fundort, Grab-/Inventarnummer, Datierung, Material mitnehmen — schärft beide Suchen. Bei vager Anfrage einmal nachfragen.

2. **Beide Stränge parallel anstoßen** — gleicher Suchbegriff, unabhängige Quellen, keine Reihenfolge-Abhängigkeit:

   - **lokal** (→ [[vault-suche]]), um Dubletten zu vermeiden und vorhandenen Kontext zu finden:
     - Volltext nach Eigenname/Kernbegriff, Fundort, Inventarnummer.
     - Frontmatter/Tag-Suche (`type: Fundbelegeintrag`, `museum_nr`, `fundkontext`).
     - Wikilink-Rückwärtssuche: linkt schon ein Grab/Fundort/Buch auf den Fund?
     - Festhalten: existiert ein Eintrag? Welcher Fundort/Komplex? Welche Tafel-/Buchreferenz ist schon vermerkt?
   - **lokal Bild** (→ [[vault-bildsuche]]), wenn ein Bild des Objekts vorliegt:
     - `describe <bild>` für eine deskriptive Merkmalsbeschreibung; `search --like <bild>` bzw. `search --text "<merkmale>"` für ähnliche Funde/Tafeln im Vault.
     - Die Sichtmerkmale (Form, Ornamentstil, Konstruktion, Beschriftung) **als zusätzliche Suchterme an den Online-Strang weitergeben**.
     - Ist LM Studio nicht erreichbar (Voraussetzung der Skill), diesen Strang überspringen und das vermerken — die anderen laufen weiter.
   - **online** (→ [[fundbild-recherche]]), zeitgleich:
     - Belegte Objektdatensätze in Museumskatalogen (SHM/Historiska, Nationalmuseet, UNIMUS …).
     - Suche mit Objektname **plus** den vom VLM gelieferten Sichtmerkmalen schärfen.
     - Provenienz prüfen (Inventarnummer/Fundort müssen zum gesuchten Fund passen) und Lizenz pro Bild notieren.
     - **Faktentreue:** nur institutionell belegte Treffer; keine Reenactor-/Shop-/Pinterest-/KI-Bilder.
   - **Markt** (→ [[produkt-recherche]]), zeitgleich, **nur als Bezugsquelle/Replik-Markt — kein Beleg**:
     - Hersteller-Seite und Webshops zum Objekt (mit Objektname **plus** VLM-Sichtmerkmalen).
     - Hersteller vs. Zwischenhändler trennen; bei unklarem Hersteller „ähnliche Artikel" sammeln.
     - **Jede Angabe „laut Händler"/„laut Hersteller" kennzeichnen**; Historisierungs-Claims der Shops nicht als Fakt übernehmen.

   Wenn ein Strang früh Eckdaten liefert (z. B. lokal eine Inventarnr. oder ein markantes VLM-Sichtmerkmal), die den anderen schärfen, gern in einer zweiten gezielten Suche nachfassen — aber **nicht** den ersten Strang dafür blockieren.

3. **Zusammenführen & gegenvalidieren** (der Kern dieser Skill). Die Befunde in **einem** Bericht gegenüberstellen:
   - **Im Vault:** Eintrag(e), Fundkontext, schon eingebundene Bilder/Tafeln.
   - **Online belegt:** Katalogtreffer mit Inventarnr., Institution, Lizenz, ob Bild ladbar.
   - **Markt (kommerziell):** Hersteller/Webshops, „laut Händler"/„laut Hersteller" — klar als **kein Beleg** ausweisen; nur Bezugsquelle/Replik-Bezug.
   - **Abgleich / Lücken:** stimmen Inventarnummer/Datierung/Fundort zwischen Vault und Katalog überein? Bestätigen sich die belegten Quellen gegenseitig? Was fehlt im Vault noch (Bild, Tafel, Fundort-Verknüpfung)? **Markt-Claims zählen nicht als Beleg** für Datierung/Provenienz. Widersprüche **benennen, nicht glätten**.

4. **Nächste Schritte vorschlagen** (nicht ungefragt ausführen):
   - Kein Vault-Eintrag, aber belegter Katalogtreffer → über [[vault-eintrag]] anlegen (Bild nach Anhang, Lizenz dokumentieren).
   - Eintrag vorhanden, aber ohne Bild → Online-Bild (→ [[fundbild-recherche]]/[[bild-bearbeiten]]) oder Tafel aus PDF (→ [[vault-suche]]) nachrüsten.
   - Fund vorhanden, aber Fundort/Grab-Kontext fehlt → Kontext mitpflegen (CLAUDE.md → „Neuer Fund ⇒ Kontext mitpflegen").

## Ergebnisformat

Beide Stränge klar getrennt, mit klickbaren Pfaden (Vault) und Quellen-Fußnoten (online):

```
Auftrag: Kleeblattfibel aus Birka

Im Vault (vault-suche):
- [Birka.md:62](Reenactment/Ausgrabungen/Fundorte/Birka.md#L62) — als Beispiel genannt
- Kein eigener Fund-Eintrag (type: Fundbelegeintrag) vorhanden.

Online belegt (fundbild-recherche):
- SHM/Historiska, Inv. <Nr.>, Björkö/Birka, Dat. 800–1100 — Bild CC BY 4.0. [1]

Markt / kommerziell (produkt-recherche) — KEIN Beleg:
- Battle-Merchant „Kleeblattfibel Bronze", 24,90 € (Stand 2026-05-30, laut Händler). [2]
- Hersteller unklar → ähnliche Artikel bei 2 weiteren Shops gelistet.

Abgleich / Lücken:
- Fund noch nicht als eigener Eintrag erfasst; Katalogbeleg vorhanden.
- Inventarnr. passt zum Fundort Birka.
- Markt-Datierung „wikingerzeitlich" NICHT belegt — gilt nur [1] (Museum).

Vorschlag: Fund-Eintrag über [[vault-eintrag]] anlegen, Bild nach
Anhang/Funde/<Fundname>/, Lizenz/Attribution dokumentieren. OK?

Quellen:
[1] https://samlingar.shm.se/object/… — SHM, abgerufen 2026-05-30
[2] https://www.battlemerchant.com/… — Händler, abgerufen 2026-05-30
```

## Faktentreue (CLAUDE.md)

- Vault-, Online- und Markt-Befund **nicht vermischen**: jede Aussage trägt ihre Herkunft (Vault-Pfad, Katalog-URL oder Shop/Hersteller-URL).
- Inventarnummern, Datierungen, Fundorte nur übernehmen, wenn sie in Vault-Eintrag oder Objektdatensatz wirklich stehen — sonst `unbekannt`.
- **Markt-Angaben sind kein Beleg:** Hersteller/Händler-Claims (Datierung, „originalgetreu", Provenienz) niemals als Fakt übernehmen — nur als „laut Händler"/„laut Hersteller" und nur als Bezugsquelle/Replik-Bezug. Belegt wird über Museum/Literatur.
- Kein belegter Treffer? Das **so sagen**; kein Ersatz aus unbelegter Quelle.
- Widersprüche zwischen Vault und Katalog offen benennen, nicht stillschweigend angleichen.
