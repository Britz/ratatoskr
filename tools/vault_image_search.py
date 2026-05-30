#!/usr/bin/env python3
"""Vault-Bildsuche via LM-Studio-VLM + Text-Embedding.

Indiziert Bilder und PDF-Seiten im Reenactment-Vault, indem ein Vision-LLM (Qwen3-VL)
eine streng deskriptive Beschreibung erzeugt, ein Text-Embedding-Modell (Qwen3-Embedding)
diese vektorisiert, und ein lokales SQLite-Cache die Vektoren speichert.

Suche per Text-Query oder per Beispielbild (Cosine-Similarity).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
import pypdfium2 as pdfium
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VAULT_ROOT = REPO_ROOT / "Reenactment"
CACHE_DIR = Path.home() / ".claude" / "cache" / "vault_image_index"
DB_PATH = CACHE_DIR / "index.db"
PDF_PAGE_CACHE = CACHE_DIR / "pdf_pages"

LM_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://host.docker.internal:1234/v1")
VLM_MODEL = os.environ.get("LMSTUDIO_VLM_MODEL", "qwen3-vl-8b-instruct-mlx")
EMBED_MODEL = os.environ.get("LMSTUDIO_EMBED_MODEL", "text-embedding-qwen3-embedding-0.6b")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
PDF_EXTS = {".pdf"}
EXCLUDE_DIR_NAMES = {".obsidian", ".tmp.drivedownload", ".tmp.driveupload", "Icon\r", "Icon"}

VLM_SYSTEM_PROMPT = (
    "Du erstellst rein deskriptive Bildbeschreibungen für einen wissenschaftlichen "
    "Reenactment-Vault. Strenge Regel: NIEMALS Datierungen, Inventarnummern, "
    "Materialien, Hersteller, Fundkontexte oder kulturelle Zuordnungen erfinden. "
    "Nur das wiedergeben, was tatsächlich sichtbar oder lesbar ist. "
    "Bei Unklarheit explizit 'unleserlich' oder 'nicht eindeutig erkennbar' schreiben. "
    "Antworte auf Deutsch."
)

VLM_USER_PROMPT = (
    "Beschreibe in 80–150 Wörtern, was tatsächlich auf dem Bild zu sehen ist.\n\n"
    "Behandle der Reihe nach:\n"
    "1. Objekt(e): Typ, Anzahl, sichtbare Form, Bestandteile, ungefähre Anordnung.\n"
    "2. Farben/Oberflächen (so wie sie erscheinen, ohne Materialaussage).\n"
    "3. Sichtbare Verzierungen, Inschriften, Texte – wörtlich zitieren, falls lesbar.\n"
    "4. Falls es eine Buchseite ist: lesbaren Text (Bildunterschriften, Seitenzahl, "
    "Maßstab) wörtlich wiedergeben.\n"
    "5. Umgebung/Hintergrund kurz erwähnen, falls relevant "
    "(z. B. Stoffauflage, Lineal, Museumsvitrine).\n\n"
    "Knappe, präzise Sprache. Keine Vermutungen, keine historische Einordnung, "
    "keine Materialhypothesen."
)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def db_connect() -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            key TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            source_path TEXT,
            page INTEGER,
            file_mtime REAL NOT NULL,
            file_hash TEXT NOT NULL,
            kind TEXT NOT NULL,
            description TEXT NOT NULL,
            embedding BLOB NOT NULL,
            embed_dim INTEGER NOT NULL,
            vlm_model TEXT NOT NULL,
            embed_model TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_kind ON items(kind)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_items_source ON items(source_path)")
    return con


def item_key(source_path: Path, page: int | None) -> str:
    rel = source_path.resolve().relative_to(REPO_ROOT)
    return f"{rel}#p{page}" if page is not None else str(rel)


def file_quick_hash(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        h.update(f.read(8192))
        f.seek(0, 2)
        h.update(str(f.tell()).encode())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# LM Studio clients
# ---------------------------------------------------------------------------

def _client() -> httpx.Client:
    return httpx.Client(base_url=LM_BASE_URL, timeout=180.0)


def vlm_describe(image_bytes: bytes, mime: str = "image/png") -> str:
    payload = {
        "model": VLM_MODEL,
        "messages": [
            {"role": "system", "content": VLM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VLM_USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
                        },
                    },
                ],
            },
        ],
        "temperature": 0.1,
        "max_tokens": 500,
    }
    with _client() as c:
        r = c.post("/chat/completions", json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


def text_embed(text: str) -> np.ndarray:
    with _client() as c:
        r = c.post("/embeddings", json={"model": EMBED_MODEL, "input": text})
        r.raise_for_status()
        data = r.json()["data"][0]["embedding"]
    return np.asarray(data, dtype=np.float32)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

@dataclass
class WorkItem:
    kind: str          # 'image' | 'pdf_page'
    path: Path         # actual image path (for pdf_page: cached PNG)
    source_path: Path  # original file path (image: same as path; pdf: the PDF)
    page: int | None
    mtime: float
    file_hash: str


def discover(
    root: Path,
    include_todo: bool,
    include_pdfs: bool,
    pdf_whitelist: list[Path] | None,
    max_pdf_pages: int,
) -> list[WorkItem]:
    items: list[WorkItem] = []
    wl_resolved = {p.resolve() for p in (pdf_whitelist or [])}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts_lower = {seg.lower() for seg in p.parts}
        if any(seg in EXCLUDE_DIR_NAMES for seg in p.parts):
            continue
        if not include_todo and "todo" in parts_lower:
            continue
        ext = p.suffix.lower()
        if ext in IMAGE_EXTS:
            items.append(
                WorkItem(
                    kind="image",
                    path=p,
                    source_path=p,
                    page=None,
                    mtime=p.stat().st_mtime,
                    file_hash=file_quick_hash(p),
                )
            )
        elif ext in PDF_EXTS:
            if wl_resolved:
                if p.resolve() not in wl_resolved:
                    continue
            elif not include_pdfs:
                continue
            try:
                pdf = pdfium.PdfDocument(p)
            except Exception as e:
                print(f"  [skip pdf] {p}: {e}", file=sys.stderr)
                continue
            n_pages = len(pdf)
            if max_pdf_pages > 0:
                n_pages = min(n_pages, max_pdf_pages)
            mtime = p.stat().st_mtime
            fh = file_quick_hash(p)
            for i in range(n_pages):
                items.append(
                    WorkItem(
                        kind="pdf_page",
                        path=p,
                        source_path=p,
                        page=i + 1,
                        mtime=mtime,
                        file_hash=fh,
                    )
                )
            pdf.close()
    return items


_PDF_RENDER_LOCK = threading.Lock()


def render_pdf_page(pdf_path: Path, page_1based: int, file_hash: str) -> bytes:
    """Rendert eine PDF-Seite in den Cache. pypdfium2 ist nicht thread-safe, daher Lock."""
    out_dir = PDF_PAGE_CACHE / file_hash
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"page_{page_1based:04d}.png"
    if not out_path.exists():
        with _PDF_RENDER_LOCK:
            if not out_path.exists():  # double-checked locking
                pdf = pdfium.PdfDocument(pdf_path)
                try:
                    page = pdf[page_1based - 1]
                    bitmap = page.render(scale=1.5)
                    pil = bitmap.to_pil()
                    pil.save(out_path, format="PNG", optimize=True)
                finally:
                    pdf.close()
    return out_path.read_bytes()


def image_bytes_capped(path: Path, max_side: int = 1600) -> tuple[bytes, str]:
    img = Image.open(path)
    img.load()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue(), "image/jpeg"


# ---------------------------------------------------------------------------
# Index / Search
# ---------------------------------------------------------------------------

def _describe_and_embed(it: "WorkItem") -> tuple["WorkItem", str, np.ndarray, float]:
    """Worker-Pfad ohne DB-Touch: rendert/lädt, beschreibt, embedded. Thread-safe."""
    t0 = time.time()
    if it.kind == "pdf_page":
        img_bytes = render_pdf_page(it.path, it.page, it.file_hash)
        mime = "image/png"
    else:
        img_bytes, mime = image_bytes_capped(it.path)
    desc = vlm_describe(img_bytes, mime=mime)
    emb = text_embed(desc)
    return it, desc, emb, time.time() - t0


def _persist(con: sqlite3.Connection, it: "WorkItem", desc: str, emb: np.ndarray) -> None:
    key = item_key(it.source_path, it.page)
    con.execute(
        """
        INSERT OR REPLACE INTO items
        (key, path, source_path, page, file_mtime, file_hash, kind,
         description, embedding, embed_dim, vlm_model, embed_model, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            str(it.path.resolve().relative_to(REPO_ROOT)),
            str(it.source_path.resolve().relative_to(REPO_ROOT)),
            it.page,
            it.mtime,
            it.file_hash,
            it.kind,
            desc,
            emb.tobytes(),
            int(emb.shape[0]),
            VLM_MODEL,
            EMBED_MODEL,
            time.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    con.commit()


def cmd_index(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root nicht gefunden: {root}", file=sys.stderr)
        return 2
    con = db_connect()
    pdf_whitelist = [Path(p).resolve() for p in (args.pdf or [])]
    items = discover(
        root,
        include_todo=args.include_todo,
        include_pdfs=args.include_pdfs,
        pdf_whitelist=pdf_whitelist,
        max_pdf_pages=args.max_pdf_pages,
    )
    print(f"Gefunden: {len(items)} Items (Bilder + PDF-Seiten) unter {root}")
    if args.limit:
        items = items[: args.limit]
        print(f"  beschränkt auf {len(items)} (--limit)")

    # Pre-Filter: schon indizierte Items im Main-Thread aussortieren
    todo: list[WorkItem] = []
    skipped = 0
    for it in items:
        key = item_key(it.source_path, it.page)
        cur = con.execute(
            "SELECT file_hash FROM items WHERE key=? AND vlm_model=? AND embed_model=?",
            (key, VLM_MODEL, EMBED_MODEL),
        ).fetchone()
        if cur and cur[0] == it.file_hash:
            skipped += 1
        else:
            todo.append(it)
    total = len(todo)
    workers = max(1, int(args.workers))
    print(f"  zu verarbeiten: {total} · übersprungen (schon im Index): {skipped} · Worker: {workers}")

    indexed, failed = 0, 0

    if workers == 1:
        # Seriell — bewährter Pfad, unverändertes Verhalten
        for idx, it in enumerate(todo, 1):
            try:
                _, desc, emb, dt = _describe_and_embed(it)
                _persist(con, it, desc, emb)
                indexed += 1
                label = f"{it.source_path.name}" + (f" S.{it.page}" if it.page else "")
                print(f"  [{idx}/{total}] {label} ({dt:.1f}s) {desc[:80]}…", flush=True)
            except httpx.HTTPError as e:
                failed += 1
                print(f"  [fail] {it.path}: {e}", file=sys.stderr, flush=True)
            except Exception as e:
                failed += 1
                print(f"  [fail] {it.path}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    else:
        # Parallel — VLM-Calls in N Threads, DB-Writes seriell im Main-Thread
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_describe_and_embed, it): it for it in todo}
            for fut in as_completed(futures):
                it_orig = futures[fut]
                done += 1
                try:
                    it, desc, emb, dt = fut.result()
                    _persist(con, it, desc, emb)
                    indexed += 1
                    label = f"{it.source_path.name}" + (f" S.{it.page}" if it.page else "")
                    print(f"  [{done}/{total}] {label} ({dt:.1f}s) {desc[:80]}…", flush=True)
                except httpx.HTTPError as e:
                    failed += 1
                    print(f"  [fail] {it_orig.path}: {e}", file=sys.stderr, flush=True)
                except Exception as e:
                    failed += 1
                    print(f"  [fail] {it_orig.path}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)

    print(f"\nFertig. Indiziert: {indexed}, übersprungen: {skipped}, fehlgeschlagen: {failed}.")
    return 0 if failed == 0 else 1


def _load_index(con: sqlite3.Connection, kind: str | None) -> tuple[list[dict], np.ndarray]:
    if kind:
        rows = con.execute(
            "SELECT key, path, source_path, page, kind, description, embedding, embed_dim "
            "FROM items WHERE kind=?",
            (kind,),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT key, path, source_path, page, kind, description, embedding, embed_dim "
            "FROM items"
        ).fetchall()
    if not rows:
        return [], np.zeros((0, 0), dtype=np.float32)
    embs = np.vstack(
        [np.frombuffer(r[6], dtype=np.float32).reshape(r[7]) for r in rows]
    )
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embs_n = embs / norms
    meta = [
        {
            "key": r[0],
            "path": r[1],
            "source_path": r[2],
            "page": r[3],
            "kind": r[4],
            "description": r[5],
        }
        for r in rows
    ]
    return meta, embs_n


def cmd_search(args: argparse.Namespace) -> int:
    con = db_connect()
    meta, embs = _load_index(con, args.kind)
    if not meta:
        print("Index ist leer. Erst `index` laufen lassen.", file=sys.stderr)
        return 2

    if args.text:
        q_emb = text_embed(args.text)
    elif args.like:
        p = Path(args.like).resolve()
        if not p.exists():
            print(f"Datei nicht gefunden: {p}", file=sys.stderr)
            return 2
        # Use stored embedding if already indexed; else describe+embed on the fly.
        try:
            rel = str(p.relative_to(REPO_ROOT))
        except ValueError:
            rel = None
        row = None
        if rel:
            row = con.execute(
                "SELECT description, embedding, embed_dim FROM items WHERE path=?",
                (rel,),
            ).fetchone()
        if row:
            q_emb = np.frombuffer(row[1], dtype=np.float32).reshape(row[2])
            print(f"(verwende gespeicherte Beschreibung: {row[0][:120]}…)")
        else:
            img_bytes, mime = image_bytes_capped(p)
            desc = vlm_describe(img_bytes, mime=mime)
            print(f"(neue Beschreibung: {desc[:120]}…)")
            q_emb = text_embed(desc)
    else:
        print("Bitte --text oder --like angeben.", file=sys.stderr)
        return 2

    q_norm = q_emb / (np.linalg.norm(q_emb) or 1.0)
    scores = embs @ q_norm
    order = np.argsort(-scores)[: args.top]
    print(f"\nTop {len(order)} Treffer:\n")
    for rank, i in enumerate(order, 1):
        m = meta[i]
        label = m["source_path"] + (f" (S. {m['page']})" if m["page"] else "")
        print(f"#{rank}  score={scores[i]:.3f}  {label}")
        print(f"      {m['description'][:200]}")
        print()
    return 0


def cmd_describe(args: argparse.Namespace) -> int:
    p = Path(args.path).resolve()
    if not p.exists():
        print(f"Datei nicht gefunden: {p}", file=sys.stderr)
        return 2
    ext = p.suffix.lower()
    if ext in PDF_EXTS:
        if args.page is None:
            print("Bei PDF bitte --page <n> angeben.", file=sys.stderr)
            return 2
        img_bytes = render_pdf_page(p, args.page, file_quick_hash(p))
        mime = "image/png"
    else:
        img_bytes, mime = image_bytes_capped(p)
    desc = vlm_describe(img_bytes, mime=mime)
    print(desc)
    return 0


def cmd_models(_: argparse.Namespace) -> int:
    try:
        with _client() as c:
            r = c.get("/models")
            r.raise_for_status()
            data = r.json().get("data", [])
    except httpx.HTTPError as e:
        print(f"LM Studio nicht erreichbar ({LM_BASE_URL}): {e}", file=sys.stderr)
        return 2
    print(f"In LM Studio geladen ({LM_BASE_URL}):")
    for m in data:
        print(f"  {m.get('id')}")
    print(f"\nAktuelle Defaults:\n  VLM:   {VLM_MODEL}\n  Embed: {EMBED_MODEL}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    if not DB_PATH.exists():
        print("Kein Index vorhanden.")
        return 0
    con = db_connect()
    total = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    by_kind = con.execute(
        "SELECT kind, COUNT(*) FROM items GROUP BY kind"
    ).fetchall()
    models = con.execute(
        "SELECT vlm_model, embed_model, COUNT(*) FROM items "
        "GROUP BY vlm_model, embed_model"
    ).fetchall()
    print(f"Index: {DB_PATH}")
    print(f"Gesamt: {total}")
    for kind, n in by_kind:
        print(f"  {kind}: {n}")
    print("Modelle:")
    for v, e, n in models:
        print(f"  VLM={v}  Embed={e}  ({n} Items)")
    print(f"\nLM Studio: {LM_BASE_URL}")
    print(f"  aktuelles VLM-Modell:   {VLM_MODEL}")
    print(f"  aktuelles Embed-Modell: {EMBED_MODEL}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_idx = sub.add_parser("index", help="Vault indizieren")
    p_idx.add_argument("--root", default=str(DEFAULT_VAULT_ROOT))
    p_idx.add_argument("--include-todo", action="store_true",
                       help="ToDo-Ordner mit-indexieren (default: ausgeschlossen)")
    p_idx.add_argument("--include-pdfs", action="store_true",
                       help="Alle PDF-Seiten unter --root mit-indexieren (default: PDFs aus)")
    p_idx.add_argument("--pdf", action="append",
                       help="Pfad einer gezielt zu indexierenden PDF (mehrfach erlaubt). "
                            "Wenn gesetzt, werden NUR diese PDFs verarbeitet (zusätzlich zu allen Bildern).")
    p_idx.add_argument("--max-pdf-pages", type=int, default=0,
                       help="Maximale Seitenzahl je PDF (0 = unlimited, default 0)")
    p_idx.add_argument("--limit", type=int, default=0)
    p_idx.add_argument("--workers", type=int, default=1,
                       help="Parallele Worker für VLM+Embed-Requests (default 1 = seriell). "
                            "Nur sinnvoll bei VLM-Backends mit Concurrency-Support (z. B. GGUF/llama.cpp).")
    p_idx.set_defaults(func=cmd_index)

    p_s = sub.add_parser("search", help="Suche per Text oder Beispielbild")
    g = p_s.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Textquery")
    g.add_argument("--like", help="Pfad zu Beispielbild")
    p_s.add_argument("--top", type=int, default=10)
    p_s.add_argument("--kind", choices=["image", "pdf_page"])
    p_s.set_defaults(func=cmd_search)

    p_d = sub.add_parser("describe", help="VLM-Beschreibung einer Datei (ohne Indexierung)")
    p_d.add_argument("path")
    p_d.add_argument("--page", type=int)
    p_d.set_defaults(func=cmd_describe)

    p_st = sub.add_parser("status", help="Index-Status anzeigen")
    p_st.set_defaults(func=cmd_status)

    p_m = sub.add_parser("models", help="In LM Studio geladene Modelle auflisten")
    p_m.set_defaults(func=cmd_models)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
