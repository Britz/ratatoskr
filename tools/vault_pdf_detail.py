#!/usr/bin/env python3
"""Companion-Tool zu `vault_image_search.py`.

Drei Aufgaben:

1. `lookup`   – PDF-Seite (oder Bild) → Cache-Pfad der gerenderten PNG plus die
                im Index gespeicherte VLM-Beschreibung.
2. `crop`     – Bild zuschneiden, entweder über benannte Region-Presets oder
                über freie Koordinaten (Prozent oder Pixel).
3. `grep`     – Volltext-LIKE-Suche über die `description`-Spalte der Index-DB.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import textwrap
from pathlib import Path
from typing import Iterable

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path.home() / ".claude" / "cache" / "vault_image_index"
DB_PATH = CACHE_DIR / "index.db"
PDF_PAGE_CACHE = CACHE_DIR / "pdf_pages"
TMP_DIR = Path.home() / ".claude" / "tmp"


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def db_open() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit(
            f"Index-DB nicht gefunden: {DB_PATH}\n"
            "Erst `python3 tools/vault_image_search.py index` ausführen."
        )
    return sqlite3.connect(DB_PATH)


def _normalize_source(source: str) -> str:
    p = Path(source)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(REPO_ROOT)
        except ValueError:
            pass
    return str(p)


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def cmd_lookup(args: argparse.Namespace) -> int:
    src = _normalize_source(args.source)
    con = db_open()
    cur = con.cursor()
    if args.page is None:
        rows = cur.execute(
            "SELECT key, kind, page, file_hash, description, indexed_at, vlm_model "
            "FROM items WHERE source_path=? OR path=? ORDER BY page",
            (src, src),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT key, kind, page, file_hash, description, indexed_at, vlm_model "
            "FROM items WHERE source_path=? AND page=?",
            (src, args.page),
        ).fetchall()

    if not rows:
        print(f"Kein Index-Eintrag für source_path={src} page={args.page}", file=sys.stderr)
        return 1

    for key, kind, page, file_hash, description, indexed_at, vlm_model in rows:
        if kind == "pdf_page":
            cache_path = PDF_PAGE_CACHE / file_hash / f"page_{page:04d}.png"
        else:
            cache_path = Path(REPO_ROOT) / src
        exists = "✓" if cache_path.exists() else "✗ (fehlt)"
        print(f"=== {key} ===")
        print(f"  kind         : {kind}")
        if page is not None:
            print(f"  page         : {page}")
        print(f"  file_hash    : {file_hash}")
        print(f"  cache_path   : {cache_path}  [{exists}]")
        print(f"  vlm_model    : {vlm_model}")
        print(f"  indexed_at   : {indexed_at}")
        print(f"  description  :")
        for line in textwrap.wrap(description, width=100):
            print(f"    {line}")
        print()
    return 0


# ---------------------------------------------------------------------------
# crop
# ---------------------------------------------------------------------------

# Region-Presets als (x, y, w, h) in Prozent (0..1)
PRESETS = {
    "caption":     (0.00, 0.85, 1.00, 0.15),   # untere 15% – Tafelbeschriftung
    "header":      (0.00, 0.00, 1.00, 0.15),   # obere 15% – Tafelnummer
    "topleft":     (0.00, 0.00, 0.40, 0.30),
    "topright":    (0.60, 0.00, 0.40, 0.20),   # für „Taf. NNN" oben rechts
    "bottomleft":  (0.00, 0.70, 0.40, 0.30),
    "bottomright": (0.60, 0.70, 0.40, 0.30),
    "center":      (0.25, 0.25, 0.50, 0.50),
    "top":         (0.00, 0.00, 1.00, 0.50),
    "bottom":      (0.00, 0.50, 1.00, 0.50),
    "left":        (0.00, 0.00, 0.50, 1.00),
    "right":       (0.50, 0.00, 0.50, 1.00),
}


def _parse_box(spec: str, mode: str, w: int, h: int) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 4:
        raise SystemExit(f"--{mode} braucht vier Werte X,Y,W,H — bekommen: {spec!r}")
    try:
        vals = [float(p) for p in parts]
    except ValueError as e:
        raise SystemExit(f"--{mode}: numerischer Wert erwartet: {e}")
    if mode == "pct":
        # Akzeptiere sowohl 0–1 als auch 0–100
        if any(v > 1.5 for v in vals):
            vals = [v / 100.0 for v in vals]
        x, y, bw, bh = vals
        box = (int(x * w), int(y * h), int(bw * w), int(bh * h))
    else:  # px
        box = tuple(int(v) for v in vals)  # type: ignore[assignment]
    return box  # type: ignore[return-value]


def _clip(box: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
    x, y, bw, bh = box
    x = max(0, min(w, x))
    y = max(0, min(h, y))
    bw = max(1, min(w - x, bw))
    bh = max(1, min(h - y, bh))
    return (x, y, bw, bh)


def cmd_crop(args: argparse.Namespace) -> int:
    in_path = Path(args.input).expanduser()
    if not in_path.exists():
        raise SystemExit(f"Eingabedatei nicht gefunden: {in_path}")

    img = Image.open(in_path)
    w, h = img.size

    chosen = sum(1 for v in (args.preset, args.pct, args.px) if v)
    if chosen != 1:
        raise SystemExit("Genau eine Region wählen: --preset XOR --pct XOR --px")

    if args.preset:
        if args.preset not in PRESETS:
            raise SystemExit(f"Unbekanntes Preset: {args.preset}. Erlaubt: {', '.join(PRESETS)}")
        x_pct, y_pct, w_pct, h_pct = PRESETS[args.preset]
        box = (int(x_pct * w), int(y_pct * h), int(w_pct * w), int(h_pct * h))
    elif args.pct:
        box = _parse_box(args.pct, "pct", w, h)
    else:
        box = _parse_box(args.px, "px", w, h)

    box = _clip(box, w, h)
    x, y, bw, bh = box
    cropped = img.crop((x, y, x + bw, y + bh))

    if args.output:
        out_path = Path(args.output).expanduser()
    else:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        tag = args.preset or "crop"
        out_path = TMP_DIR / f"{in_path.stem}_{tag}{in_path.suffix or '.png'}"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {}
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs["quality"] = 92
        if cropped.mode != "RGB":
            cropped = cropped.convert("RGB")
    cropped.save(out_path, **save_kwargs)
    print(f"Crop: {in_path.name}  ({w}x{h}) → {out_path}  ({bw}x{bh} bei {x},{y})")
    return 0


# ---------------------------------------------------------------------------
# grep
# ---------------------------------------------------------------------------

def _highlight(text: str, needle: str, ctx: int = 60) -> Iterable[str]:
    """Yield short snippets around each case-insensitive match of needle."""
    if not needle:
        yield text[:200]
        return
    lower = text.lower()
    n = needle.lower()
    start = 0
    while True:
        idx = lower.find(n, start)
        if idx < 0:
            break
        a = max(0, idx - ctx)
        b = min(len(text), idx + len(needle) + ctx)
        prefix = "…" if a > 0 else ""
        suffix = "…" if b < len(text) else ""
        yield f"{prefix}{text[a:b]}{suffix}"
        start = idx + len(needle)


def cmd_grep(args: argparse.Namespace) -> int:
    con = db_open()
    cur = con.cursor()
    where = ["description LIKE ?"]
    params: list[object] = [f"%{args.pattern}%"]
    if args.kind:
        where.append("kind=?")
        params.append(args.kind)
    if args.source:
        where.append("source_path LIKE ?")
        params.append(f"%{_normalize_source(args.source)}%")
    sql = (
        "SELECT source_path, page, kind, description "
        f"FROM items WHERE {' AND '.join(where)} "
        "ORDER BY source_path, page LIMIT ?"
    )
    params.append(args.limit)
    rows = cur.execute(sql, params).fetchall()
    if not rows:
        print(f"Kein Treffer für: {args.pattern!r}")
        return 1
    print(f"{len(rows)} Treffer für {args.pattern!r}:")
    for source_path, page, kind, description in rows:
        loc = f"{source_path}" + (f" (S. {page})" if page is not None else "")
        snippets = list(_highlight(description, args.pattern))
        print(f"\n• [{kind}] {loc}")
        for s in snippets[:3]:
            for line in textwrap.wrap(s, width=100):
                print(f"    {line}")
    return 0


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="DB-Lookup, Crop und Beschreibungs-Grep für den Vault-Bildindex."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("lookup", help="PDF-Seite/Bild im Index nachschlagen")
    pl.add_argument("source", help="Pfad zur PDF (oder zum Bild), relativ zum Repo oder absolut")
    pl.add_argument("--page", type=int, help="PDF-Seitennummer (1-basiert); ohne --page: alle Seiten der Quelle")
    pl.set_defaults(func=cmd_lookup)

    pc = sub.add_parser("crop", help="Bild zuschneiden")
    pc.add_argument("input", help="Eingabe-Bild (PNG/JPEG)")
    pc.add_argument("--preset", choices=list(PRESETS), help="Benanntes Region-Preset")
    pc.add_argument("--pct", help="Region in Prozent: X,Y,W,H (0–1 oder 0–100)")
    pc.add_argument("--px", help="Region in Pixel: X,Y,W,H")
    pc.add_argument("--output", "-o", help="Zieldatei (Default: ~/.claude/tmp/<stem>_<tag><ext>)")
    pc.set_defaults(func=cmd_crop)

    pg = sub.add_parser("grep", help="Volltextsuche in den VLM-Beschreibungen")
    pg.add_argument("pattern", help="Substring (case-insensitiv)")
    pg.add_argument("--kind", choices=["image", "pdf_page"])
    pg.add_argument("--source", help="Quell-Pfad-Filter (LIKE, Substring genügt)")
    pg.add_argument("--limit", type=int, default=20)
    pg.set_defaults(func=cmd_grep)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
