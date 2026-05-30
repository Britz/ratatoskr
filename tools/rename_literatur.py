#!/usr/bin/env python3
"""Vault-weite Literatur-Umbenennung. Dry-Run by default; --apply zum echten Ausführen."""
import argparse, pathlib, re, sys, sqlite3, shutil

VAULT = pathlib.Path("/workspaces/ratatoskr/Reenactment")
DB = pathlib.Path.home() / ".claude" / "cache" / "vault_image_index" / "index.db"

# MD-Slugs (= Dateinamen ohne .md) ALT → NEU
RENAME = {
    # Buecher (15)
    "AROS_das_Aarhus_der_Wikinger": "Skov_2006_AROS_Aarhus",
    "Arbman_1943_Birka_I_Die_Graeber": "Arbman_1943_Birka_Graeber",
    "Asatru_Rueckkehr_der_Goetter": "Gundarsson_2026_Asatru_Rueckkehr",
    "Aufgeklaertes_Heidentum": "Mang_2015_Aufgeklaertes_Heidentum",
    "Die_Edda": "Simrock_1851_Edda",
    "Die_Wikingerschiffe_in_Oslo": "Sjoevold_1979_Wikingerschiffe_Oslo",
    "Kalmring_Hafen_von_Haithabu": "Kalmring_2010_Hafen_Haithabu",
    "Lexikon_der_germanischen_Mythologie": "Simek_2006_Lexikon_Mythologie",
    "Odin_Psychologischer_Streifzug": "Obleser_2015_Odin_Streifzug",
    "Odin_der_einaeugige_Gott": "Kershaw_2017_Odin_Maennerbuende",
    "Spurensuche_Haithabu": "Schietzel_2014_Spurensuche_Haithabu",
    "Viking_Age_Swords_Telemark": "Martens_2021_Swords_Telemark",
    "Viking_and_Slavic_Ornamental_Designs_Vol2": "Goerewicz_2017_Ornaments_Vol2",
    "Vorlagen_fuer_keltische_Muster": "Down_2003_Keltische_Muster",
    "Wikinger_Waraeger_Normannen": "Roesdahl_1992_Wikinger_Waraeger",
    # Abhandlungen (22)
    "Artikel_42635_2017": "Dobat_2017_Rez_Graeber_Haithabu",
    "Artikel_76641_2020": "Warming_2016_Shields_Hide",
    "Ausgrabungen_Flachgraberfeld_Haithabu": "Kalmring_2018_Flachgraeberfeld_Haithabu",
    "Buch_9781040133156": "Ingvardson_2025_Hoarding_Vikings",
    "Cambridge_Antiquity_2019": "Price_2019_Bj581_Warrior_Women",
    "FULLTEXT01": "Pentz_2018_Detector_Finds",
    "Gokstad_Schilde_Schiffsgrab": "Warming_2023_Gokstad_Schilde",
    "Great_Heathen_Army_Failure": "MacNeill_2019_Heathen_Army",
    "Gustin_2016_Finnish_Connection_Birka": "Gustin_2016_Birka_Finnland",
    "Habermann_Wikingerschwerter_Hedendorf": "Habermann_2018_Schwerter_Hedendorf",
    "Haneca_Dendrochronologie_Eiche": "Haneca_2005_Dendro_Eiche",
    "Horn_Die_Kinzig_2014": "Horn_2015_Kinzig",
    "IA_68_6": "Deckers_2025_Single_Ladies_Detector",
    "Jantzen_Metallverarbeitung_Bronzezeit": "Jantzen_2008_Metall_Bronzezeit",
    "Mitteilungen_GeschSH_83_2012": "Tummuscheit_2012_Danewerk_Rothenkrug",
    "Schjodt_Weltenbaum_RGA": "Schjoedt_2006_Weltenbaum",
    "Stalsberg_Vlfberht_Schwerter": "Stalsberg_2008_Vlfberht_Schwerter",
    "Steuer_Handel_Nord_Westeuropa": "Steuer_1987_Handel_Nord_Westeuropa",
    "Stolpe_1878_Birka_Grabungsdokumentation": "Stolpe_1878_Birka_Grabung",
    "Toplak_Graeberfeld_Kopparsvik": "Toplak_2016_Graeberfeld_Kopparsvik",
    "Vergessene_Hochburg_fruehes_Haithabu": "Kalmring_2014_Hochburg_Haithabu",
    "Viele_Funde_Grosse_Bedeutung": "Hilberg_2014_Detektorfunde",
    "Vike_Brynjevev_Ring_Weave": "Vike_2000_Brynjevev_Ring",
}

DELETE_SLUGS = ["Wikingerschwerter_Hedendorf"]  # Dublette zu Habermann_…

# Frontmatter-Updates (slug → field-dict). Title für Buch_9781040133156 weil dort "Publikation ISBN …" steht.
META_UPDATES = {
    "Asatru_Rueckkehr_der_Goetter": {"erscheinungsjahr": "2026"},
    "Aufgeklaertes_Heidentum": {"erscheinungsjahr": "2015"},
    "Odin_Psychologischer_Streifzug": {"erscheinungsjahr": "2015"},
    "Odin_der_einaeugige_Gott": {"erscheinungsjahr": "2017"},
    "Artikel_42635_2017": {"autor": '"Andres S. Dobat"'},
    "Ausgrabungen_Flachgraberfeld_Haithabu": {"autor": '"Sven Kalmring"', "erscheinungsjahr": "2018"},
    "Buch_9781040133156": {"autor": '"Gitte T. Ingvardson"', "erscheinungsjahr": "2025",
                            "title": '"The Hoarding Vikings"'},
    "Gokstad_Schilde_Schiffsgrab": {"autor": '"Rolf Fabricius Warming"', "erscheinungsjahr": "2023"},
    "IA_68_6": {"autor": '"Pieterjan Deckers"', "erscheinungsjahr": "2025"},
    "Stalsberg_Vlfberht_Schwerter": {"erscheinungsjahr": "2008"},
    "Steuer_Handel_Nord_Westeuropa": {"erscheinungsjahr": "1987"},
    "Toplak_Graeberfeld_Kopparsvik": {"erscheinungsjahr": "2016"},
    "Vergessene_Hochburg_fruehes_Haithabu": {"autor": '"Sven Kalmring"', "erscheinungsjahr": "2014"},
    "Viele_Funde_Grosse_Bedeutung": {"autor": '"Volker Hilberg, Thorsten Lemm (Hrsg.)"', "erscheinungsjahr": "2014"},
    "Wikingerzeitliche_Graeber_Haithabu": {"autor": '"Silke Eisenschmidt"', "erscheinungsjahr": "2008"},
}

# Anhang-PDFs (in Anhang/Abhandlungen/) → neue Dateinamen
PDF_RENAME = {
    "artikel_42635_20171116.pdf": "dobat_2017_rez_graeber_haithabu.pdf",
    "artikel_76641_20201110.pdf": "warming_2016_shields_hide.pdf",
    "ausgrabungen_flachgraberfeld_haithabu.pdf": "kalmring_2018_flachgraeberfeld_haithabu.pdf",
    "buch_9781040133156.pdf": "ingvardson_2025_hoarding_vikings.pdf",
    "cambridge_antiquity_S0003598X18002582.pdf": "price_2019_bj581_warrior_women.pdf",
    "fulltext01.pdf": "pentz_2018_detector_finds.pdf",
    "great_heathen_army_failure.pdf": "macneill_2019_heathen_army.pdf",
    "horn_die_kinzig_2014.pdf": "horn_2015_kinzig.pdf",
    "ia_68_6.pdf": "deckers_2025_single_ladies_detector.pdf",
    "jantzen_metallverarbeitung_bronzezeit_2008.pdf": "jantzen_2008_metall_bronzezeit.pdf",
    "stalsberg_vlfberht_schwerter.pdf": "stalsberg_2008_vlfberht_schwerter.pdf",
    "steuer_handel_nord_westeuropa.pdf": "steuer_1987_handel_nord_westeuropa.pdf",
    "toplak_graeberfeld_kopparsvik.pdf": "toplak_2016_graeberfeld_kopparsvik.pdf",
    "vergessene_hochburg_fruehes_haithabu.pdf": "kalmring_2014_hochburg_haithabu.pdf",
    "viele_funde_grosse_bedeutung.pdf": "hilberg_2014_detektorfunde.pdf",
    "viking_age_swords.pdf": "martens_2021_swords_telemark.pdf",
    "wikingerschwerter_hedendorf.pdf": "habermann_2018_schwerter_hedendorf.pdf",
    "wikingerzeitliche_graeber_haithabu.pdf": "eisenschmidt_2008_graeber_haithabu.pdf",
    "gustin_2016_finnish_connection_birka.pdf": "gustin_2016_birka_finnland.pdf",
}

# Buchordner unter Anhang/Buecher/ folgen dem MD-Buchslug
BUCHORDNER_RENAME = {old: new for old, new in RENAME.items()
                      if (VAULT / "Anhang" / "Buecher" / old).is_dir()}


def update_yaml_field(text: str, field: str, value: str) -> str:
    """Setze field: value im YAML-Frontmatter; lege das Feld an wenn nicht vorhanden."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end < 0:
        return text
    fm, rest = text[3:end], text[end:]
    pat = re.compile(rf"^({re.escape(field)}):\s*.*$", re.M)
    if pat.search(fm):
        fm = pat.sub(f"{field}: {value}", fm)
    else:
        fm = fm.rstrip() + f"\n{field}: {value}\n"
    return "---" + fm + rest


def patch_link_paths(text: str, name_map: dict, kind: str) -> str:
    """Ersetzt Pfad-Substrings (Anhang/Buecher/ALT/ → /NEU/ usw.)."""
    for old, new in name_map.items():
        if kind == "buchordner":
            text = text.replace(f"Anhang/Buecher/{old}/", f"Anhang/Buecher/{new}/")
        elif kind == "pdf":
            text = text.replace(f"Anhang/Abhandlungen/{old}", f"Anhang/Abhandlungen/{new}")
    return text


def patch_wikilinks(text: str, slug_map: dict) -> str:
    """[[ALT]], [[ALT|alias]], [[ALT#sec]] → [[NEU…]]"""
    for old, new in slug_map.items():
        # Wikilink: [[ALT(|...)?(#...)?]]
        pat = re.compile(rf"\[\[{re.escape(old)}((?:\|[^\]]+)?(?:#[^\]]+)?)\]\]")
        text = pat.sub(rf"[[{new}\1]]", text)
        # Auch normale .md-Referenzen (selten)
        text = text.replace(f"{old}.md", f"{new}.md")
    return text


def patch_anhang_ordner_field(text: str, ordner_map: dict) -> str:
    """Frontmatter-Feld anhang_ordner: ALT → NEU"""
    for old, new in ordner_map.items():
        text = re.sub(rf"(^anhang_ordner:\s*){re.escape(old)}\s*$",
                      rf"\g<1>{new}", text, flags=re.M)
    return text


def patch_dateiname_field(text: str, pdf_map: dict) -> str:
    """Frontmatter-Feld dateiname: ALT.pdf → NEU.pdf"""
    for old, new in pdf_map.items():
        text = re.sub(rf'(^dateiname:\s*"?){re.escape(old)}("?\s*)$',
                      rf"\g<1>{new}\g<2>", text, flags=re.M)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Tatsächlich ausführen. Sonst Dry-Run.")
    args = parser.parse_args()
    dry = not args.apply
    tag = "[DRY-RUN]" if dry else "[APPLY] "

    print(f"=== Vault-Literatur-Umbenennung {tag} ===\n")
    print(f"Vault: {VAULT}")
    print(f"Mappings:  {len(RENAME)} MD-Umbenennungen, {len(DELETE_SLUGS)} Löschung(en),")
    print(f"           {len(PDF_RENAME)} PDF-Umbenennungen, {len(BUCHORDNER_RENAME)} Buchordner-Umbenennungen.\n")

    # 1) Frontmatter-Updates an aktuellen Einträgen
    print("--- 1) Frontmatter-Updates ---")
    for slug, updates in META_UPDATES.items():
        candidates = list(VAULT.glob(f"Literatur/**/{slug}.md"))
        if not candidates:
            print(f"  !! {slug}.md nicht gefunden")
            continue
        p = candidates[0]
        txt = p.read_text(encoding="utf-8")
        new = txt
        for field, value in updates.items():
            new = update_yaml_field(new, field, value)
        if new != txt:
            print(f"  ✓ {p.relative_to(VAULT)}  ({', '.join(updates.keys())})")
            if not dry:
                p.write_text(new, encoding="utf-8")
        else:
            print(f"  =  {p.relative_to(VAULT)}  (keine Änderung)")

    # 2) Body-Pfade in MDs ersetzen (Buchordner & PDFs) UND anhang_ordner-Feld
    print("\n--- 2) Pfad-/anhang_ordner-Replacements in allen Vault-MDs ---")
    for md in sorted(VAULT.rglob("*.md")):
        txt = md.read_text(encoding="utf-8")
        new = txt
        new = patch_link_paths(new, BUCHORDNER_RENAME, "buchordner")
        new = patch_link_paths(new, PDF_RENAME, "pdf")
        new = patch_anhang_ordner_field(new, BUCHORDNER_RENAME)
        new = patch_dateiname_field(new, PDF_RENAME)
        if new != txt:
            print(f"  ✓ {md.relative_to(VAULT)}")
            if not dry:
                md.write_text(new, encoding="utf-8")

    # 3) Wikilink-Replacements (alle Vault-MDs + Repo)
    print("\n--- 3) Wikilink-Replacements ---")
    slug_map = RENAME.copy()
    for md in sorted(VAULT.rglob("*.md")):
        txt = md.read_text(encoding="utf-8")
        new = patch_wikilinks(txt, slug_map)
        if new != txt:
            print(f"  ✓ {md.relative_to(VAULT)}")
            if not dry:
                md.write_text(new, encoding="utf-8")

    # 4) Anhang/Buecher Ordner umbenennen
    print("\n--- 4) Anhang/Buecher Ordner umbenennen ---")
    for old, new in BUCHORDNER_RENAME.items():
        src = VAULT / "Anhang" / "Buecher" / old
        dst = VAULT / "Anhang" / "Buecher" / new
        if src.is_dir():
            if dst.exists():
                print(f"  !! {new} existiert schon, skip")
                continue
            print(f"  ✓ {old}/ → {new}/")
            if not dry:
                src.rename(dst)
        else:
            print(f"  -- {old}/ nicht gefunden")

    # 5) Anhang/Abhandlungen PDFs umbenennen
    print("\n--- 5) Anhang/Abhandlungen PDFs umbenennen ---")
    for old, new in PDF_RENAME.items():
        src = VAULT / "Anhang" / "Abhandlungen" / old
        dst = VAULT / "Anhang" / "Abhandlungen" / new
        if src.is_file():
            if dst.exists():
                print(f"  !! {new} existiert schon, skip")
                continue
            print(f"  ✓ {old} → {new}")
            if not dry:
                src.rename(dst)
        else:
            print(f"  -- {old} nicht gefunden")

    # 6) MD-Dateien umbenennen
    print("\n--- 6) MD-Dateien umbenennen ---")
    for slug, new_slug in RENAME.items():
        candidates = list(VAULT.glob(f"Literatur/**/{slug}.md"))
        if not candidates:
            print(f"  !! {slug}.md nicht gefunden")
            continue
        src = candidates[0]
        dst = src.with_name(f"{new_slug}.md")
        if dst.exists():
            print(f"  !! {dst.name} existiert schon, skip")
            continue
        print(f"  ✓ {src.relative_to(VAULT)} → {dst.name}")
        if not dry:
            src.rename(dst)

    # 7) Zu löschende Einträge
    print("\n--- 7) Löschungen ---")
    for slug in DELETE_SLUGS:
        candidates = list(VAULT.glob(f"Literatur/**/{slug}.md"))
        for c in candidates:
            print(f"  ✗ {c.relative_to(VAULT)}")
            if not dry:
                c.unlink()

    # 8) Bild-Index: source_path UPDATE (per Substring-Replace, dedupliziert)
    print("\n--- 8) Bild-Index source_path UPDATE ---")
    if not DB.exists():
        print(f"  !! Bild-Index {DB} nicht vorhanden, skip")
    else:
        con = sqlite3.connect(DB)
        path_subs = []
        for old, new in BUCHORDNER_RENAME.items():
            path_subs.append((f"Anhang/Buecher/{old}/", f"Anhang/Buecher/{new}/"))
        for old, new in PDF_RENAME.items():
            path_subs.append((f"Anhang/Abhandlungen/{old}", f"Anhang/Abhandlungen/{new}"))
        for old, new in path_subs:
            n = con.execute(
                "SELECT COUNT(*) FROM items WHERE source_path LIKE ?",
                (f"%{old}%",)
            ).fetchone()[0]
            if n == 0:
                continue
            print(f"  ✓ {old}  → {new}  ({n} Zeilen)")
            if not dry:
                con.execute(
                    "UPDATE items SET source_path = REPLACE(source_path, ?, ?) "
                    "WHERE source_path LIKE ?",
                    (old, new, f"%{old}%"),
                )
        if not dry:
            con.commit()
        con.close()

    print(f"\n=== {tag} Fertig ===\n")
    if dry:
        print("Zum tatsächlichen Ausführen: python3 ~/.claude/tmp/rename_literatur.py --apply")


if __name__ == "__main__":
    main()
