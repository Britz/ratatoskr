#!/usr/bin/env python3
"""Prüft das YAML-Frontmatter aller Vault-Einträge.

Konventionen (siehe CLAUDE.md, Abschnitt "Konvention: YAML-Frontmatter"):
  1. Das Frontmatter zwischen den beiden `---` muss valides YAML sein.
  2. Listenfelder `tags` (und `aliases`) dürfen keine Einträge mit
     Leerzeichen / Whitespace enthalten — ein Tag ist genau ein Token.
  3. Kein Key darf doppelt vorkommen (sonst gewinnt still der letzte).

Aufruf:
    python3 tools/check_frontmatter.py            # prüft Reenactment/
    python3 tools/check_frontmatter.py PFAD ...    # prüft gezielt Dateien/Ordner

Exit-Code 0 = sauber, 1 = mindestens ein Problem gefunden.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML fehlt – `pip install pyyaml`")


class StrictLoader(yaml.SafeLoader):
    """SafeLoader, der doppelte Mapping-Keys als Fehler meldet.

    Der normale SafeLoader nimmt bei doppeltem Key still den letzten —
    so bleibt z.B. eine alte und eine neue `hersteller:`-Zeile unbemerkt
    beide stehen. Hier wird das als YAMLError gemeldet.
    """

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.YAMLError(f"doppelter Key '{key}' im Frontmatter")
            mapping[key] = True
        return super().construct_mapping(node, deep=deep)


# Felder, deren Listeneinträge keine Leerzeichen enthalten dürfen.
NO_SPACE_LIST_FIELDS = ("tags", "aliases")

VAULT_DEFAULT = Path(__file__).resolve().parent.parent / "Reenactment"


def iter_md(targets: list[Path]):
    for t in targets:
        if t.is_dir():
            for p in sorted(t.rglob("*.md")):
                # Obsidian-Interna und Papierkorb überspringen
                if any(part.startswith(".") for part in p.parts):
                    continue
                yield p
        elif t.suffix == ".md":
            yield t


def extract_frontmatter(text: str):
    """Liefert (yaml_text, startzeile) oder (None, None) wenn kein Frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), 1
    return None, None  # kein schließendes ---


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm, _ = extract_frontmatter(text)
    if fm is None:
        # Kein Frontmatter ist erlaubt (z.B. reine Notizen) -> kein Fehler,
        # aber wenn die Datei mit --- beginnt und nicht schließt, melden:
        if text.lstrip().startswith("---"):
            problems.append("Frontmatter-Block wird nicht mit '---' geschlossen")
        return problems

    try:
        data = yaml.load(fm, Loader=StrictLoader)
    except yaml.YAMLError as e:
        msg = str(e).replace("\n", " ")
        problems.append(f"ungültiges YAML: {msg}")
        return problems

    if not isinstance(data, dict):
        problems.append("Frontmatter ist kein YAML-Mapping (Key/Value)")
        return problems

    for field in NO_SPACE_LIST_FIELDS:
        if field not in data or data[field] is None:
            continue
        value = data[field]
        if not isinstance(value, list):
            problems.append(
                f"Feld '{field}' sollte eine YAML-Liste sein, ist aber {type(value).__name__}"
            )
            continue
        for item in value:
            if not isinstance(item, str):
                problems.append(f"{field}: Eintrag {item!r} ist kein String")
                continue
            if any(c.isspace() for c in item):
                problems.append(f"{field}: '{item}' enthält Leerzeichen/Whitespace")
    return problems


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv] or [VAULT_DEFAULT]
    files = list(iter_md(targets))
    total_problems = 0
    bad_files = 0
    for path in files:
        problems = check_file(path)
        if problems:
            bad_files += 1
            total_problems += len(problems)
            rel = path
            print(f"\n✗ {rel}")
            for p in problems:
                print(f"    - {p}")

    print(
        f"\n{'─' * 50}\n{len(files)} Dateien geprüft, "
        f"{bad_files} mit Problemen, {total_problems} Befunde gesamt."
    )
    return 1 if total_problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
