#!/usr/bin/env python3
"""Webquellen-Einträge im Vault einheitlich normalisieren.

Schritte je Eintrag:
1. URL aus dem Body (Quellen & Links / Quelle / Markdown-Link) extrahieren und ins Frontmatter heben.
2. Frontmatter-Felder einheitlich (Reihenfolge, fehlende Felder als unbekannt).
3. Subtype aus Domain-Heuristik setzen, falls leer.
4. URL als Markdown-Link unter der H1 einfügen (sofern noch nicht da).
5. Bekannte Section-Headings vereinheitlichen.

Dry-Run by default; --apply zum echten Schreiben."""
import argparse, pathlib, re, sys, yaml

VAULT = pathlib.Path("/workspaces/ratatoskr/Reenactment")
WQ = VAULT / "Literatur" / "Webquellen"

# Subtype-Map: per Eintragsname (slug). Fallback: per Domain.
SUBTYPE_PER_SLUG = {
    "Birka_Stavtaerning_SHM_5208_1709": "Museumskatalog",
    "Bj644_Doppelgrab_Birka_LazyReenactor": "Reenactor-Blog",
    "Bj644_Viking_Age_Beads_LazyReenactor": "Reenactor-Blog",
    "Bj644_Visby_Shopping_Haul_LazyReenactor": "Reenactor-Blog",
    "Edberg_2022_Spelfoeremaal_Sigtuna": "Forschungs-Repository",
    "Faerben_Pflanzenfarben_Rete_Amicorum": "Reenactor-Webseite",
    "Faerber_Berufe_Taetigkeiten": "Hobby-Webseite",
    "Faerberwaid_Kulturpflanze": "Hobby-Webseite",
    "Gokstad_Holzschilde_Nahkampf": "News-Artikel",
    "Haithabu_Danewerk_UNESCO": "UNESCO-Eintrag",
    "Haithabu_Museum_Dauerausstellung": "Museums-Webseite",
    "Haithabu_Museum_Siedlungsausschnitt": "Museums-Webseite",
    "Handel_Skandinavien_Fernhandel": "Forschungs-Repository",
    "Interview_John_Gwynne_Shadow_of_Gods": "Blog",
    "Naturfarbstoffe_Farben_Geschichte": "Forschungs-Repository",
    "Oseberg_Chieftain_Red_White": "Museums-Webseite",
    "Schildbau_Gratleiste_Anleitung": "Handwerks-Tutorial",
    "Schildbau_Heydenwall": "Reenactor-Webseite",
    "Schildbau_Kite_Shield_YouTube": "YouTube-Video",
    "Schildbau_Schildbuckel_Vlasaty": "Forschungs-Repository",
    "Schoenfaerberey_Historische_Faerberei": "Reenactor-Webseite",
    "Sippe_Guntursson_Birka_Belt_Pouch": "Reenactor-Blog",
    "Trelleborg_Schild_Ausgrabung": "UNESCO-Eintrag",
    "Viking_Shield_Research_YouTube": "YouTube-Video",
    "Vikings_History_Interesting_Bits": "Blog",
}

# Section-Header-Umbenennungen
SECTION_MAP = {
    "Kurzzusammenfassung": "Quellenübersicht",
    "Bedeutung für das Reenactment": "Relevanz für das Reenactment",
    "Verknüpfte Einträge": "Verknüpfte Vault-Einträge",
    "PDF im Vault": "Anhang – Dokument",
    "Quellen & Links": "Weiterführende Links",
}

# Feld-Reihenfolge im Frontmatter
FIELD_ORDER = [
    "title", "type", "subtype", "autor", "erscheinungsjahr", "sprache",
    "url", "quelle", "exportiert", "dateiname", "blog", "kanal", "tags",
]


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text, ""
    end = text.find("\n---", 3)
    if end < 0:
        return None, text, ""
    raw = text[3:end]
    body = text[end + 4:].lstrip("\n")
    try:
        fm = yaml.safe_load(raw) or {}
    except Exception:
        fm = None
    return fm, body, raw


def dump_frontmatter(fm: dict) -> str:
    """Frontmatter in fester Feld-Reihenfolge ausgeben."""
    lines = ["---"]
    seen = set()
    for key in FIELD_ORDER:
        if key in fm and fm[key] not in (None, ""):
            seen.add(key)
            lines.append(dump_yaml_pair(key, fm[key]))
    for key, val in fm.items():
        if key in seen or val in (None, ""):
            continue
        lines.append(dump_yaml_pair(key, val))
    lines.append("---")
    return "\n".join(lines) + "\n"


def dump_yaml_pair(key, val):
    if isinstance(val, list):
        out = [f"{key}:"]
        for item in val:
            out.append(f"  - {item}")
        return "\n".join(out)
    if isinstance(val, (int, float, bool)):
        return f"{key}: {val}"
    s = str(val)
    # quoten, wenn Leerzeichen / Doppelpunkt / Sonderzeichen / führendes Zeichen
    needs_quote = (
        any(c in s for c in [":", "#", "'", '"', "[", "]", "{", "}", "&", "*", "|"])
        or s.strip() != s
        or s.startswith(("@", "!", "?", "-", "%"))
        or re.search(r"[äöüÄÖÜß]", s)  # konservativ quoten
    )
    if needs_quote:
        s = '"' + s.replace('"', '\\"') + '"'
    return f"{key}: {s}"


def extract_url_from_body(body: str, domain: str = None) -> str | None:
    """Findet die erste Markdown-Link-URL im Body, vorzugsweise mit der genannten Domain."""
    # 1) Im Abschnitt "Quellen & Links" / "Quelle" / "Weiterführende Links"
    section = re.search(
        r"##\s+(?:Quellen\s*&?\s*Links|Quelle|Weiterführende\s*Links)\s*\n(.+?)(?=\n## |\Z)",
        body, re.S | re.I,
    )
    candidates = []
    if section:
        for m in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", section.group(1)):
            candidates.append(m.group(2))
    # 2) Fallback: alle Markdown-Links im Body
    if not candidates:
        for m in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", body):
            candidates.append(m.group(2))
    if not candidates:
        return None
    # Priorisiere Links mit der bekannten Domain
    if domain:
        bare = domain.replace("https://", "").replace("http://", "").strip("/")
        for u in candidates:
            if bare in u:
                return u
    return candidates[0]


def rename_sections(body: str) -> str:
    for old, new in SECTION_MAP.items():
        body = re.sub(rf"^##\s+{re.escape(old)}\s*$", f"## {new}", body, flags=re.M)
    return body


def ensure_h1_link(body: str, title: str, url: str) -> str:
    """Stelle sicher: H1 (`# {title}`) am Anfang, darunter klickbarer URL-Link (nur wenn URL da)."""
    if not title and not url:
        return body
    body = body.lstrip("\n")
    lines = body.split("\n")
    # Existierende H1 finden
    h1_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("# ") and not ln.startswith("## "):
            h1_idx = i
            break
        if ln.strip().startswith("## "):
            break
    if h1_idx is None:
        # H1 vor allem einfügen, Link nur wenn URL da
        if url:
            new_lines = [f"# {title}", "", f"[{title}]({url})", ""] + lines
        else:
            new_lines = [f"# {title}", ""] + lines
        return "\n".join(new_lines)
    # H1 vorhanden — prüfen ob URL-Link direkt darunter steht
    title_in_h1 = lines[h1_idx][2:].strip()
    if not url:
        return body  # nur H1, kein Link einfügen
    for j in range(h1_idx + 1, len(lines)):
        if lines[j].strip() == "":
            continue
        if lines[j].startswith("[") and url in lines[j]:
            return body  # bereits vorhanden
        # leere Link-Stubs `[...]()` zuerst entfernen
        if re.match(r"^\[[^\]]+\]\(\)\s*$", lines[j]):
            new_lines = lines[: h1_idx + 1] + ["", f"[{title_in_h1}]({url})", ""] + lines[j + 1:]
            return "\n".join(new_lines)
        new_lines = lines[: h1_idx + 1] + ["", f"[{title_in_h1}]({url})", ""] + lines[j:]
        return "\n".join(new_lines)
    return body


def process(p: pathlib.Path, dry: bool) -> list[str]:
    txt = p.read_text(encoding="utf-8")
    fm, body, _raw = parse_frontmatter(txt)
    if fm is None:
        return [f"  !! {p.name}: kein parsbares Frontmatter"]
    changes = []
    # 1) Subtype setzen
    target_subtype = SUBTYPE_PER_SLUG.get(p.stem)
    if target_subtype and fm.get("subtype") != target_subtype:
        old = fm.get("subtype")
        fm["subtype"] = target_subtype
        changes.append(f"subtype: {old!r} → {target_subtype!r}")
    # 2) URL aus Body extrahieren wenn noch nicht im Frontmatter
    if not fm.get("url"):
        url = extract_url_from_body(body, fm.get("quelle"))
        if url:
            fm["url"] = url
            changes.append(f"url ergänzt: {url}")
    # 3) H1 + URL-Link
    url = fm.get("url")
    title = str(fm.get("title", "") or "")
    if url or title:
        new_body = ensure_h1_link(body, title, url or "")
        if new_body != body:
            changes.append("H1/URL-Link eingefügt")
            body = new_body
    # 4) Section-Umbenennungen
    new_body = rename_sections(body)
    if new_body != body:
        diffs = [old for old in SECTION_MAP if re.search(rf"^##\s+{re.escape(old)}", body, re.M)]
        if diffs:
            changes.append("Sections umbenannt: " + ", ".join(diffs))
        body = new_body
    # 5) Frontmatter neu rendern; sauber genau eine Leerzeile zwischen --- und Body
    new_fm_text = dump_frontmatter(fm).rstrip("\n")
    body_stripped = body.lstrip("\n")
    new_txt = new_fm_text + "\n\n" + body_stripped
    # Mehrfache Leerzeilen auf max. 1 reduzieren
    new_txt = re.sub(r"\n{3,}", "\n\n", new_txt)
    if new_txt != txt:
        if not changes:
            changes.append("Frontmatter neu sortiert")
        if not dry:
            p.write_text(new_txt, encoding="utf-8")
    return [f"  ✓ {p.name}  ▸ " + " | ".join(changes)] if changes else [f"  =  {p.name}  (unverändert)"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry = not args.apply
    print(f"=== Webquellen-Normalisierung {'[DRY-RUN]' if dry else '[APPLY]'} ===\n")
    for p in sorted(WQ.glob("*.md")):
        for line in process(p, dry):
            print(line)
    print(f"\n=== Fertig {'[DRY-RUN]' if dry else '[APPLY]'} ===")
    if dry:
        print("Zum Schreiben: python3 tools/normalize_webquellen.py --apply")


if __name__ == "__main__":
    main()
