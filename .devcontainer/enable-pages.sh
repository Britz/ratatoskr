#!/usr/bin/env bash
# Enable GitHub Pages with GitHub Actions as the build source, then trigger
# the deploy workflow. Idempotent — safe to re-run.
#
# Usage:
#   bash .devcontainer/enable-pages.sh
#
# Requires: gh CLI (installed by the devcontainer feature), an authenticated
# session (run `gh auth login` first if needed).

set -euo pipefail

WORKFLOW="${WORKFLOW:-Deploy MkDocs site to GitHub Pages}"

if ! command -v gh >/dev/null 2>&1; then
  echo "✗ gh CLI is not installed in this environment."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "→ gh is not authenticated. Launching: gh auth login"
  gh auth login
fi

REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)}"
if [[ -z "${REPO}" ]]; then
  echo "✗ Could not determine repo. Run from inside the cloned repo, or set REPO=owner/name."
  exit 1
fi

echo "→ Repo: ${REPO}"

if gh api "repos/${REPO}/pages" >/dev/null 2>&1; then
  echo "→ Pages already enabled — ensuring build_type=workflow..."
  gh api "repos/${REPO}/pages" -X PUT -f build_type=workflow >/dev/null
else
  echo "→ Enabling Pages with build_type=workflow..."
  gh api "repos/${REPO}/pages" -X POST -f build_type=workflow >/dev/null
fi

echo "→ Triggering workflow: ${WORKFLOW}"
gh workflow run "${WORKFLOW}"

echo
echo "✓ Done. Follow the run:"
echo "    gh run watch"
echo "Or open: $(gh repo view --json url -q .url)/actions"
