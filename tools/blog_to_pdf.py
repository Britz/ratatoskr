#!/usr/bin/env python3
"""Blog-Beitrag in lesbares PDF konvertieren (Reader-Mode + Browser-UA für Bilder).

Aufruf:
  python3 tools/blog_to_pdf.py <url> <ziel.pdf>
  python3 tools/blog_to_pdf.py <url> <ziel.pdf> --title "Manual Title" --author "..."

Workflow:
  1. URL fetchen mit Browser-User-Agent.
  2. Trafilatura extrahiert nur den Artikel-Body als HTML.
  3. HTML wird mit Kopfzeile (Titel, Autor, Datum, Quelle) eingebettet.
  4. weasyprint rendert als PDF mit eigenem url_fetcher (auch für Bilder UA).
"""
import argparse, datetime, html as html_lib, pathlib, re, sys
import requests, trafilatura, weasyprint
from readability import Document

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
}


def fetch(url: str) -> bytes:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    except requests.exceptions.SSLError:
        # Fallback bei abgelaufenen Zertifikaten / Konfigurationsfehlern
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True, verify=False)
    r.raise_for_status()
    return r.content


def decode_html(html_bytes: bytes) -> str:
    """Erkenne Charset aus Meta-Tag (oder fallback utf-8) und dekodiere."""
    # Roh-Scan auf <meta charset=...>
    head = html_bytes[:4096].decode("ascii", errors="replace")
    m = re.search(r'<meta[^>]+charset=["\']?([\w-]+)', head, re.I)
    enc = (m.group(1) if m else "utf-8").lower()
    if enc in ("utf8", "utf_8"):
        enc = "utf-8"
    try:
        return html_bytes.decode(enc)
    except (UnicodeDecodeError, LookupError):
        return html_bytes.decode("utf-8", errors="replace")


def _extract_balanced_block(html_text: str, start_re: str) -> str | None:
    """Findet einen Tag-Block, der zum start_re passt, und gibt das HTML inkl. Wrapper zurück
    (mit korrektem schließenden Tag, depth-balanced)."""
    m = re.search(start_re, html_text, re.I)
    if not m:
        return None
    # Tag-Name aus dem Match holen
    tag_m = re.match(r"<([a-z][a-z0-9]*)", m.group(0), re.I)
    if not tag_m:
        return None
    open_tag = tag_m.group(1)
    pos = m.end()
    depth = 1
    while depth > 0 and pos < len(html_text):
        next_open = html_text.find(f"<{open_tag}", pos)
        next_close = html_text.find(f"</{open_tag}", pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 1
        else:
            depth -= 1
            pos = next_close + len(open_tag) + 3
    return html_text[m.start():pos]


def extract_itemprop_articlebody(html_text: str) -> str | None:
    """Suche schema.org itemprop="articleBody"."""
    return _extract_balanced_block(html_text, r'<[a-z][a-z0-9]*[^>]+itemprop="articleBody"[^>]*>')


def extract_main_block(html_text: str) -> str | None:
    """Fallback: <main>...</main>, mit Cleanup von Navigation/Asides/Related-Articles."""
    block = _extract_balanced_block(html_text, r"<main\b[^>]*>")
    if not block:
        return None
    # nav, aside, footer-typische Inhalte raus
    block = re.sub(r"<nav\b.*?</nav>", "", block, flags=re.S | re.I)
    block = re.sub(r"<aside\b.*?</aside>", "", block, flags=re.S | re.I)
    block = re.sub(
        r'<div\b[^>]*class="[^"]*(?:breadcrumb|sidebar|related|share|teaser|social)[^"]*"[^>]*>.*?</div>',
        "", block, flags=re.S | re.I,
    )
    # Inner <article>-Vorschau-Karten (z.B. UNESCO "Mehr Welterbe") raus
    block = re.sub(r"<article\b.*?</article>", "", block, flags=re.S | re.I)
    # Sektionen, die im Klassennamen "more", "weitere", "empfehl" tragen
    block = re.sub(
        r'<(section|div)\b[^>]*class="[^"]*(?:more|weitere|empfehl|stations?-list|teaser-list)[^"]*"[^>]*>.*?</\1>',
        "", block, flags=re.S | re.I,
    )
    return block


def upgrade_lazy_images(html_text: str) -> str:
    """Bilder mit nur lazy-/srcset-Attributen so umschreiben, dass weasyprint sie sieht.
    Falls kein normales src= existiert, wird die erste URL aus dem ersten gefundenen
    *-srcset/*-src-Attribut nach src= übernommen.
    Falls bereits ein src= existiert, das aber auf ein data:-Placeholder zeigt,
    wird es ebenfalls überschrieben."""
    LAZY_ATTRS = (
        "data-orig-file", "data-lazy-src", "data-src", "data-original",
        "data-lazy-srcset", "data-srcset", "srcset",
    )
    def fix_img(m):
        tag = m.group(0)
        real = None
        for attr in LAZY_ATTRS:
            mm = re.search(rf'\b{attr}="([^"]+)"', tag)
            if mm:
                real = mm.group(1).split(",")[0].strip().split(" ")[0]
                if real and not real.startswith("data:"):
                    break
                real = None
        if not real:
            return tag
        src_m = re.search(r'\bsrc="([^"]*)"', tag)
        if src_m and not src_m.group(1).startswith("data:"):
            return tag  # echtes src= bleibt
        if src_m:
            return re.sub(r'\bsrc="[^"]*"', f'src="{real}"', tag, count=1)
        return tag.replace("<img", f'<img src="{real}"', 1)
    return re.sub(r"<img\b[^>]+>", fix_img, html_text, flags=re.I)


def url_fetcher(url: str) -> dict:
    """Eigener fetcher für weasyprint — Browser-UA. Accept-Header je nach Asset-Typ."""
    # Bilder/Stylesheets brauchen einen passenden Accept-Header, sonst antworten
    # manche Server (WordPress!) mit HTML statt mit Asset.
    is_image = re.search(r"\.(?:png|jpe?g|webp|gif|svg|avif|bmp)(?:\?|$)", url, re.I)
    is_css = re.search(r"\.css(?:\?|$)", url, re.I)
    headers = dict(HEADERS)
    if is_image:
        headers["Accept"] = "image/avif,image/webp,image/apng,image/*;q=0.9,*/*;q=0.5"
    elif is_css:
        headers["Accept"] = "text/css,*/*;q=0.1"
    try:
        r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    except requests.exceptions.SSLError:
        r = requests.get(url, headers=headers, timeout=30, allow_redirects=True, verify=False)
    return {
        "string": r.content,
        "mime_type": r.headers.get("Content-Type", "").split(";")[0].strip() or None,
        "redirected_url": r.url,
    }


CSS = """
@page { size: A4; margin: 2.5cm 2.2cm; }
body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 11pt;
       line-height: 1.55; color: #222; max-width: 16cm; margin: 0 auto;
       orphans: 3; widows: 3; }
p, li { orphans: 3; widows: 3; }

h1.beitrag-titel { font-size: 20pt; line-height: 1.2; margin: 0 0 0.3em 0; color: #1a1a1a;
                   break-after: avoid; page-break-after: avoid; }
.meta { font-size: 9.5pt; color: #666; margin-bottom: 0.2em;
        break-after: avoid; page-break-after: avoid; }
.meta-url { font-size: 9pt; color: #666;
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.8em; margin-bottom: 1.6em;
            overflow-wrap: anywhere; word-break: break-all;
            break-after: avoid; page-break-after: avoid; }
.meta-url a { color: #1a4a73;
              overflow-wrap: anywhere; word-break: break-all; }

/* Überschriften kleben am nächsten Block */
h1, h2 { font-size: 14pt; margin-top: 1.4em;
         break-after: avoid; page-break-after: avoid; }
h3 { font-size: 12pt; margin-top: 1.2em;
     break-after: avoid; page-break-after: avoid; }

/* Abschnitte zusammenhalten, sofern sie nicht zu lang sind */
section { break-inside: avoid-page; page-break-inside: avoid; }

p { margin: 0.6em 0; }
img { max-width: 100%; max-height: 16cm;
      width: auto; height: auto; object-fit: contain;
      margin: 1em auto; display: block; }
figure { margin: 1.2em 0; text-align: center;
         break-inside: avoid; page-break-inside: avoid; }
figure img { max-height: 14cm; }
figcaption { font-size: 9pt; color: #666; text-align: center; font-style: italic;
             margin-top: 0.3em; }
table { break-inside: avoid; page-break-inside: avoid; }
blockquote { border-left: 3px solid #cbcbcb; margin-left: 0; padding-left: 1em; color: #444;
             break-inside: avoid; page-break-inside: avoid; }
a { color: #1a4a73; }
"""


JUNK_URL = re.compile(
    r"/(flags?|icons?|logo|sprite|button|emoji|favicon|smili?ey?)s?/|"
    r"(\?|\.)(?:wpcf7|jetpack|plugin)|"
    r"-(?:icon|logo|flag)\.(?:png|svg|gif|jpg|jpeg)",
    re.I,
)


def fix_typography(text: str) -> str:
    """Typografische Korrekturen, die WordPress-Blogs oft falsch machen:
    - Acute Accent (´, U+00B4) statt Apostroph → typografisch korrekter Apostroph (', U+2019).
      Wirkt sich auch auf Zeilenumbruch aus, da weasyprint ´ als Bruchstelle erkennt.
    """
    return text.replace("´", "’")


def clean_article_html(article_html: str) -> str:
    """Räumt das Reader-Output auf:
    - <img>-Tags mit Junk-URLs (Flaggen, Icons, Logos) entfernen
    - <a>-Wrapper, die nur ein Junk-<img> umschlossen, ebenfalls entfernen
    - Leere <p>-Container entfernen
    - <img> mit alt-Text in <figure>+<figcaption> wrappen (für unsere CSS)
    - Typografische Fehler im Body korrigieren (´ → ')
    """
    article_html = fix_typography(article_html)
    # 1) <a> die nur Junk-<img> enthalten ganz raus
    article_html = re.sub(
        r'<a\b[^>]*>\s*<img\b[^>]*?src="([^"]+)"[^>]*?>\s*</a>',
        lambda m: "" if JUNK_URL.search(m.group(1)) else m.group(0),
        article_html, flags=re.I | re.S,
    )
    # 2) standalone Junk-<img> raus
    article_html = re.sub(
        r'<img\b[^>]*?src="([^"]+)"[^>]*?/?>',
        lambda m: "" if JUNK_URL.search(m.group(1)) else m.group(0),
        article_html, flags=re.I,
    )
    # 3) leere Paragraphen
    article_html = re.sub(r"<p\b[^>]*>\s*</p>", "", article_html, flags=re.I)
    # 4) <img> in <figure> wrappen — aber NUR wenn nicht direkt schon eine Caption folgt
    def img_to_figure(m):
        attrs = m.group(0)
        suffix = article_html[m.end():m.end()+200]
        # Falls direkt ein <figcaption> oder ein Caption-Paragraph folgt: kein Wrap
        if re.match(r"\s*<(?:figcaption|p)\b", suffix, re.I):
            return attrs
        alt_m = re.search(r'alt="([^"]+)"', attrs)
        if not alt_m or not alt_m.group(1).strip():
            return attrs
        alt = alt_m.group(1)
        return f'<figure>{attrs}<figcaption>{html_lib.escape(alt)}</figcaption></figure>'
    article_html = re.sub(r'<img\b[^>]+/?>', img_to_figure, article_html, flags=re.I)
    return article_html


def wrap_sections(html: str) -> str:
    """Gruppiere <h2>…bis nächste <h2>…</h2> in <section>-Tags,
    damit weasyprint sie als Einheit umbrechen kann."""
    import re
    if not re.search(r"<h[23][>\s]", html, re.I):
        return html
    parts = re.split(r"(?=<h2[>\s])", html, flags=re.I)
    if len(parts) <= 1:
        return html
    out = [parts[0]]
    for block in parts[1:]:
        out.append(f"<section>{block}</section>")
    return "".join(out)


def build_html(article_html: str, *, url: str, title: str, author: str | None,
               published: str | None, hero_image: str | None = None) -> str:
    today = datetime.date.today().isoformat()
    meta_bits = []
    if author:
        meta_bits.append(html_lib.escape(author))
    if published:
        meta_bits.append(html_lib.escape(published))
    meta_bits.append(f"gespeichert am {today}")
    meta_line = " · ".join(meta_bits)
    hero_block = ""
    if hero_image and "<img" not in article_html:
        # Nur wenn der Article-Body selbst keine Bilder enthält
        hero_block = f'<figure><img src="{html_lib.escape(hero_image)}" alt=""/></figure>\n'
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html_lib.escape(title)}</title>
<style>{CSS}</style></head><body>
<h1 class="beitrag-titel">{html_lib.escape(title)}</h1>
<div class="meta">{meta_line}</div>
<div class="meta-url"><a href="{html_lib.escape(url)}">{html_lib.escape(url)}</a></div>
{hero_block}{article_html}
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out_pdf")
    ap.add_argument("--title", help="Beitragstitel (Fallback: aus HTML extrahiert)")
    ap.add_argument("--author", help="Autor")
    ap.add_argument("--published", help="Datum (frei formatiert)")
    ap.add_argument("--cut-after", help="Alles im Article-HTML nach diesem Text-Marker abschneiden (Werbung/Quiz/Footer-Boilerplate)")
    args = ap.parse_args()

    print(f"Fetch {args.url} ...")
    html_bytes = fetch(args.url)
    print(f"  HTML: {len(html_bytes)} bytes")

    # Hauptcontent: readability-lxml ist konservativer und behält footer-nahe Links
    html_text = decode_html(html_bytes)
    html_text = upgrade_lazy_images(html_text)
    doc = Document(html_text)
    article_html = doc.summary(html_partial=True)

    # Fallback-Kette: wenn readability zu wenig liefert,
    # nacheinander itemprop="articleBody" und <main>-Container probieren.
    if not article_html or len(article_html) < 5000:
        for fallback_name, fn in [
            ("itemprop articleBody", extract_itemprop_articlebody),
            ("<main>", extract_main_block),
        ]:
            cand = fn(html_text)
            if cand and len(cand) > len(article_html or ""):
                article_html = cand
                print(f"  Article ({fallback_name} fallback): {len(article_html)} chars")
                break
        else:
            print(f"  Article (readability): {len(article_html or '')} chars")
    else:
        print(f"  Article (readability): {len(article_html)} chars")

    if not article_html or len(article_html) < 200:
        print("FAIL: keine Reader-Extraktion möglich.")
        sys.exit(1)

    # Metadaten: trafilatura ist hier präziser
    meta = trafilatura.extract_metadata(html_bytes)
    title = args.title or (meta.title if meta and meta.title else doc.short_title())
    author = args.author or (meta.author if meta and meta.author else None)
    published = args.published or (meta.date if meta and meta.date else None)
    # Typografie auch in Metadaten reparieren
    title = fix_typography(title or "")
    if author:
        author = fix_typography(author)

    article_html = clean_article_html(article_html)
    # Cut-after: alles ab dem Marker abschneiden
    if args.cut_after:
        idx = article_html.find(args.cut_after)
        if idx != -1:
            # Auf den nächsten </p> zurück, damit der Cut sauber ist
            cut = article_html.rfind("</p>", 0, idx)
            if cut != -1:
                article_html = article_html[:cut + 4]
            else:
                article_html = article_html[:idx]
            print(f"  Cut-after '{args.cut_after}': {len(article_html)} chars verbleibend")
    article_html = wrap_sections(article_html)
    # og:image als Hero-Image, falls Article-Body keine Bilder hat
    hero = None
    m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html_text)
    if m:
        hero = m.group(1)
    full = build_html(article_html, url=args.url, title=title, author=author,
                      published=published, hero_image=hero)
    out = pathlib.Path(args.out_pdf)
    out.parent.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=full, base_url=args.url, url_fetcher=url_fetcher).write_pdf(str(out))
    print(f"  PDF: {out}  ({out.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
