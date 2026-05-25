# Getting started

Ratatöskr renders an [Obsidian](https://obsidian.md) vault into a static site
using [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and the
[`obsidian-support`](https://github.com/ndy2/mkdocs-obsidian-support-plugin)
plugin.

## Authoring

Drop your Obsidian markdown files into the `docs/` folder. The build pipeline
translates Obsidian-flavored syntax into MkDocs / Material equivalents:

- `[[wikilinks]]` → standard markdown links
- `![[image.png]]` → image embeds
- `> [!note]` style callouts → Material admonitions
- `==highlight==` and `~~strike~~`
- Inline `\( e^{i\pi} + 1 = 0 \)` and block math via MathJax

### Example callout

> [!tip] Obsidian callouts work
> This block uses Obsidian's callout syntax. The `obsidian-support` plugin
> rewrites it to a Material admonition at build time.

## Local preview

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

Open <http://127.0.0.1:8000> — edits hot-reload as you save in Obsidian.

## Deploying

1. Push to `main`.
2. In **Settings → Pages**, set **Source** to *GitHub Actions* (one-time).
3. The workflow at `.github/workflows/deploy.yml` builds and publishes on every
   push to `main`.

The site URL will be `https://britz.github.io/ratatoskr/`.
