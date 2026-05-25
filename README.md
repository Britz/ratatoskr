# Ratatöskr

A static website rendered from an [Obsidian](https://obsidian.md) vault using
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and deployed to
GitHub Pages.

## Layout

```
.
├── docs/              # Obsidian vault (markdown lives here)
│   ├── index.md       # site homepage
│   └── javascripts/   # MathJax config
├── mkdocs.yml         # site configuration
├── requirements.txt   # Python build dependencies
└── .github/workflows/deploy.yml   # CI build → GitHub Pages
```

The `docs/` folder *is* the Obsidian vault — open it in Obsidian and edit
notes directly. The build picks them up as-is.

## Local development

### Option A — Devcontainer (recommended)

If you have Docker + the VS Code **Dev Containers** extension (or open the repo
in a GitHub Codespace), the environment is fully described by
[`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json):

1. Open the folder in VS Code → *Reopen in Container*.
2. Wait for `pip install -r requirements.txt` to finish (one-time).
3. Run `mkdocs serve` — port `8000` is auto-forwarded to your host.

### Option B — Local Python venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdocs serve         # live preview at http://127.0.0.1:8000
mkdocs build         # produce static site in ./site
```

## Obsidian features supported

Translated automatically by the
[`mkdocs-obsidian-support-plugin`](https://github.com/ndy2/mkdocs-obsidian-support-plugin):

- `[[wikilinks]]` and `[[wikilinks|aliases]]`
- `![[image.png]]` and `![[note]]` embeds
- `> [!note]` / `> [!tip]` / `> [!warning]` callouts → Material admonitions
- Tags via the built-in MkDocs `tags` plugin
- Math (`$inline$`, `$$block$$`) via MathJax

## Deploying

1. Push to `main`.
2. In **Settings → Pages**, set **Source** to *GitHub Actions* (one-time).
3. The workflow at `.github/workflows/deploy.yml` builds and publishes the site
   on every push to `main`.

The site URL will be `https://britz.github.io/ratatoskr/`.
