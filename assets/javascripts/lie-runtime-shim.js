/**
 * lie-runtime.js (Obsidian-Plugin "Live Image Editor", vendored) referenziert
 * an mehreren Stellen die Obsidian-eigene Global `activeDocument` — im Browser
 * existiert die nicht, daher wirft der Runtime beim ersten Bild mit `.lie`
 * oder Transform-Attribut "ReferenceError: activeDocument is not defined".
 *
 * UEBERGANGS-Workaround, bis der Bug upstream (Britz/obsidian-live-image-editor)
 * behoben und ein neues Release draussen ist — dann diese Datei ersatzlos
 * entfernen (und den Eintrag in properdocs.yml).
 */
window.activeDocument = window.activeDocument || document;
