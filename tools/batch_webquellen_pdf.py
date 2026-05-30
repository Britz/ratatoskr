#!/usr/bin/env python3
"""Batch-Erzeugung von Reader-PDFs für alle Webquellen-Einträge ohne PDF.

Für jeden Webquellen-MD-Eintrag mit Subtype in PDF_SUBTYPES und ohne vorhandenes PDF:
1. Reader-Mode-PDF via tools/blog_to_pdf.py erzeugen (Anhang/Webquellen/<Slug>/<slug>.pdf)
2. Frontmatter `dateiname:` setzen (relativer Pfad)
3. Im Body `## Anhang – Dokument` einfügen (falls nicht vorhanden)

Aufruf:
  python3 tools/batch_webquellen_pdf.py            # Dry-Run
  python3 tools/batch_webquellen_pdf.py --apply    # tatsächlich ausführen
  python3 tools/batch_webquellen_pdf.py --apply --only Schildbau_Heydenwall
"""
import argparse, pathlib, subprocess, sys, yaml, re

VAULT = pathlib.Path("/workspaces/ratatoskr/Reenactment")
WQ = VAULT / "Literatur" / "Webquellen"
ATTACH = VAULT / "Anhang" / "Webquellen"
TOOL = pathlib.Path("/workspaces/ratatoskr/tools/blog_to_pdf.py")

PDF_SUBTYPES = {
    "Blog", "Reenactor-Blog", "News-Artikel", "Museums-Webseite",
    "Reenactor-Webseite", "Hobby-Webseite", "Handwerks-Tutorial",
    "UNESCO-Eintrag",
}


def parse_fm(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    try:
        fm = yaml.safe_load(text[3:end]) or {}
    except Exception:
        fm = {}
    return fm, text[end + 4:].lstrip("\n")


def has_existing_pdf(slug, fm, body):
    """Prüft, ob der Eintrag bereits ein PDF verlinkt."""
    if fm.get("dateiname"):
        return True
    folder = ATTACH / slug
    if folder.is_dir() and any(folder.glob("*.pdf")):
        return True
    # Falls im Body ein Pfad nach Anhang/Webquellen/.../*.pdf steht
    if re.search(r"Anhang/Webquellen/[^)]+\.pdf", body):
        return True
    return False


def set_frontmatter_field(text, key, value):
    """key: value-Feld setzen (vor tags wenn möglich)."""
    pat = re.compile(rf"^({re.escape(key)}):\s*.*$", re.M)
    if pat.search(text):
        return pat.sub(f"{key}: {value}", text, count=1)
    # Vor `tags:` einfügen, sonst am Ende des Frontmatters
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    fm_body = parts[1]
    if "\ntags:" in fm_body:
        fm_body = fm_body.replace("\ntags:", f"\n{key}: {value}\ntags:", 1)
    else:
        fm_body = fm_body.rstrip() + f"\n{key}: {value}\n"
    return parts[0] + "---" + fm_body + "---" + parts[2]


def ensure_anhang_section(body, pdf_rel_path, pdf_filename):
    """Stellt einen Abschnitt `## Anhang – Dokument` sicher."""
    if "## Anhang" in body:
        # Wenn schon vorhanden, kein Duplikat hinzufügen
        return body, False
    # Vor "## Weiterführende Links" einfügen, sonst am Ende
    block = (
        "## Anhang – Dokument\n\n"
        "| Datei | Beschreibung |\n"
        "| --- | --- |\n"
        f"| [{pdf_filename}]({pdf_rel_path}) | Reader-Snapshot der Webseite (PDF) |\n\n"
    )
    if "## Weiterführende Links" in body:
        body = body.replace("## Weiterführende Links", block + "## Weiterführende Links", 1)
    else:
        body = body.rstrip() + "\n\n" + block
    return body, True


def process(p: pathlib.Path, dry: bool):
    raw = p.read_text(encoding="utf-8")
    fm, body = parse_fm(raw)
    slug = p.stem
    subtype = fm.get("subtype")
    url = fm.get("url")
    if subtype not in PDF_SUBTYPES:
        return f"  -- {slug} ({subtype or 'kein Subtype'}) — übersprungen"
    if has_existing_pdf(slug, fm, body):
        return f"  =  {slug} — hat schon PDF"
    if not url:
        return f"  !! {slug} — keine URL"
    # Output-Pfad
    pdf_name = slug.lower() + ".pdf"
    pdf_abs = ATTACH / slug / pdf_name
    pdf_rel = f"../../Anhang/Webquellen/{slug}/{pdf_name}"
    if dry:
        return f"  ▸ {slug} — würde erzeugen: {pdf_rel}  (URL: {url})"

    # Erzeuge PDF
    pdf_abs.parent.mkdir(parents=True, exist_ok=True)
    autor = fm.get("autor")
    cmd = ["python3", str(TOOL), url, str(pdf_abs)]
    if autor and autor != "unbekannt":
        cmd += ["--author", autor]
    pub = fm.get("erscheinungsjahr") or fm.get("exportiert")
    if pub:
        cmd += ["--published", str(pub)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not pdf_abs.exists() or pdf_abs.stat().st_size < 1024:
        msg = (proc.stdout + proc.stderr).strip().splitlines()
        return f"  !! {slug} — Extraktion fehlgeschlagen: {msg[-1] if msg else 'unbekannt'}"

    # Frontmatter dateiname + Body Anhang-Tabelle
    new_raw = set_frontmatter_field(raw, "dateiname", pdf_rel)
    fm2, body2 = parse_fm(new_raw)
    body2, _ = ensure_anhang_section(body2, pdf_rel, pdf_name)
    # Frontmatter aus new_raw extrahieren
    parts = new_raw.split("---", 2)
    final = parts[0] + "---" + parts[1] + "---\n\n" + body2
    p.write_text(final, encoding="utf-8")
    return f"  ✓ {slug} — PDF {pdf_abs.stat().st_size//1024} KB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="nur diesen Slug verarbeiten")
    args = ap.parse_args()
    dry = not args.apply
    print(f"=== Batch-Webquellen-PDF {'[DRY-RUN]' if dry else '[APPLY]'} ===\n")
    for p in sorted(WQ.glob("*.md")):
        if args.only and p.stem != args.only:
            continue
        print(process(p, dry))
    print("\n=== Fertig ===")


if __name__ == "__main__":
    main()
