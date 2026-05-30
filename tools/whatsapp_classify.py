#!/usr/bin/env python3
"""Klassifiziert Bilder im WhatsApp-Lagern-Ordner per LM-Studio-VLM in Unterordner.

Liest jedes .jpg im Quellordner, fragt Qwen3-VL nach genau einer Kategorie
aus einer festen Liste und verschiebt die Datei in den passenden Unterordner.
Macht selbst keine inhaltlichen Aussagen — die Klassifikation ist
nachvollziehbar im JSON-Log dokumentiert.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
import time
from pathlib import Path

import httpx
from PIL import Image
import io


LM_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://host.docker.internal:1234/v1")
VLM_MODEL = os.environ.get("LMSTUDIO_VLM_MODEL", "qwen3-vl-8b-instruct-mlx")

CATEGORIES = {
    "Lagerbilder": "Mittelalter-Reenactment-Lager im Freien: Zelte, Lagerfeuer, Kochstellen, Lagerausstattung in Outdoor-Umgebung, Lagerleben (auch wenn Personen drauf sind, aber das Lager-Setting deutlich dominiert)",
    "Events_Werbung": "Plakate, Flyer, Werbegrafiken, Veranstaltungs-Screenshots, Eintrittskarten, Marktwerbung, Programmankündigungen mit Text/Logo/Datum",
    "Werkstatt_Handwerk": "Werkstatt-Innenraum, eigene Bau-/Holzarbeiten in Arbeit, Schnitzen, Nähen, Schmieden, Werkzeug am Werkstück, Skizzen mit Werkstück, Bauprojekte im Entstehen",
    "Repliken_Ausstellung": "Fertige Repliken einzeln fotografiert (Trinkhorn, Tasche, Schmuck, Schwert, Axt etc.) auf Tisch oder neutralem Hintergrund, Indoor, ohne Werkstatt-Kontext",
    "Buchscans_Recherche": "Eingescannte oder abfotografierte Buchseiten, archäologische Tafeln, wissenschaftliche Abbildungen mit Bildunterschriften/Tafelnummern aus Fachliteratur",
    "Chat_Screenshots": "Screenshots von WhatsApp-/Messenger-/Facebook-/SMS-Konversationen mit erkennbarer Chat-UI (Sprechblasen, Eingabezeile, Profilbild)",
    "Logo_Designs": "Logos, Lineart-Zeichnungen, Vereinslogo Ratatöskr, Stickerei-Designs, Grafik-Entwürfe ohne Foto-Charakter",
    "Personen_Gruppenbilder": "Portraits oder Gruppenfotos von Personen in Mittelalter-Gewandung im Vordergrund, ohne dominantes Lager- oder Werkstatt-Setting",
    "Rezepte": "Rezeptbilder, Kochbuchseiten, schriftliche Zubereitungs-Anleitungen, Lebensmittel mit Rezept-Hinweisen",
    "Sonstiges": "Alles, was nicht in die anderen Kategorien passt — moderne Alltagsfotos, Memes, Schokolade, unklare Bilder, Privates",
}

PROMPT = (
    "Du klassifizierst ein Foto aus einer WhatsApp-Gruppe eines Wikinger-Reenactment-Vereins.\n\n"
    "Wähle GENAU EINE der folgenden Kategorien aus, die am besten zum Bild passt:\n\n"
    + "\n".join(f"- {name}: {desc}" for name, desc in CATEGORIES.items())
    + "\n\nAntworte mit GENAU einem JSON-Objekt: {\"kategorie\": \"<Kategoriename>\", \"begruendung\": \"<max 15 Wörter, was du im Bild siehst>\"}\n"
    "Nur die Kategorienamen aus der Liste sind erlaubt. Keine zusätzlichen Felder, kein Markdown, kein Text drumherum."
)


def encode_image(path: Path, max_side: int = 768) -> str:
    """Bild laden, runterskalieren, als base64-jpeg zurückgeben."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_side:
            scale = max_side / max(w, h)
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("ascii")


def classify(client: httpx.Client, path: Path) -> dict:
    """VLM einmal aufrufen, JSON parsen."""
    b64 = encode_image(path)
    payload = {
        "model": VLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 200,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "klassifikation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "kategorie": {"type": "string", "enum": list(CATEGORIES.keys())},
                        "begruendung": {"type": "string"},
                    },
                    "required": ["kategorie", "begruendung"],
                    "additionalProperties": False,
                },
            },
        },
    }
    r = client.post("/chat/completions", json=payload, timeout=120)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {"kategorie": "Sonstiges", "begruendung": f"JSON-Parse-Fehler: {content[:100]}"}
    kat = result.get("kategorie", "Sonstiges")
    if kat not in CATEGORIES:
        return {"kategorie": "Sonstiges", "begruendung": f"Unbekannte Kategorie '{kat}'"}
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path, help="Quellordner mit .jpg Dateien")
    ap.add_argument("--dry-run", action="store_true", help="Nur klassifizieren, nicht verschieben")
    ap.add_argument("--limit", type=int, default=0, help="Max Anzahl Bilder verarbeiten (0=alle)")
    ap.add_argument("--log", type=Path, default=None, help="JSON-Log-Datei")
    args = ap.parse_args()

    src = args.source.resolve()
    if not src.is_dir():
        print(f"Quelle nicht gefunden: {src}", file=sys.stderr)
        return 1

    jpgs = sorted(p for p in src.iterdir() if p.suffix.lower() in {".jpg", ".jpeg"} and p.is_file())
    if args.limit:
        jpgs = jpgs[: args.limit]

    print(f"Verarbeite {len(jpgs)} Bilder aus {src}", file=sys.stderr)
    if not args.dry_run:
        for cat in CATEGORIES:
            (src / cat).mkdir(exist_ok=True)

    log_path = args.log or (src / "_klassifikation_log.jsonl")
    log_path.touch(exist_ok=True)

    client = httpx.Client(base_url=LM_BASE_URL, timeout=120)
    counts: dict[str, int] = {}
    errors = 0

    with open(log_path, "a", encoding="utf-8") as logf:
        for i, p in enumerate(jpgs, 1):
            t0 = time.time()
            try:
                result = classify(client, p)
            except Exception as e:
                errors += 1
                result = {"kategorie": "Sonstiges", "begruendung": f"Fehler: {e}"}
            kat = result["kategorie"]
            counts[kat] = counts.get(kat, 0) + 1
            dt = time.time() - t0
            entry = {
                "file": p.name,
                "kategorie": kat,
                "begruendung": result.get("begruendung", ""),
                "dauer_s": round(dt, 2),
            }
            logf.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logf.flush()
            print(f"[{i:>3}/{len(jpgs)}] {dt:>4.1f}s  {kat:<25}  {p.name}", file=sys.stderr)
            if not args.dry_run:
                dest = src / kat / p.name
                shutil.move(str(p), str(dest))

    print(file=sys.stderr)
    print("=== Verteilung ===", file=sys.stderr)
    for k, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<25} {c:>4}", file=sys.stderr)
    if errors:
        print(f"Fehler: {errors}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
