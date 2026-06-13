# Ratatöskr — Webseite

Die öffentliche Webseite des Wikingerzeit-Reenactment-Projekts **Ratatöskr**
(lebendige Geschichte & kleines Museum).

🌐 **[britz.github.io/ratatoskr](https://britz.github.io/ratatoskr/)**

## Was ist dieses Repo?

Hier liegt **ausschließlich die fertig gebaute Webseite** — statisches HTML im
Repo-Root, das GitHub Pages direkt ausliefert.

> **Nicht von Hand bearbeiten.** Der Inhalt ist ein Build-Ergebnis.

Quelle der Wahrheit ist ein **privater** Obsidian-Vault (Repo `ratatoskr-private`).
Daraus wird die Seite gefiltert generiert und hierher gepusht — öffentlich wird
nur, was ausdrücklich freigegeben ist:

- nur Seiten mit `publish: true` im Frontmatter (default-deny),
- nur lizenzkonforme Bilder (Prüfung über einen Anhang-Index),
- private Inhalte (Kaufdaten, Anbieter, ©-Scans) bleiben im privaten Vault.

## Deployment

GitHub Pages, **Deploy from a branch** → `main` / `(root)`. Die Datei `.nojekyll`
schaltet die Jekyll-Verarbeitung ab, sodass das HTML unverändert serviert wird.
Ein Build-Workflow ist nicht nötig: neue Stände werden bereits gebaut committet.
