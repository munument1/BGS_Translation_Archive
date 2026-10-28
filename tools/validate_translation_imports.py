"""Check imported Korean-only JSONL reference bundles without external programs.

Usage: python tools/validate_translation_imports.py
"""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    ("morrowind", ROOT/"Morrowind/BaseGame/KR9/translation.jsonl", 53896),
    ("oblivion", ROOT/"Oblivion/BaseGame/Oblivion.esm/canonical_v2.jsonl", 46225),
    ("oblivion", ROOT/"Oblivion/DLC/canonical_v2.jsonl", 1734),
    ("oblivion", ROOT/"Oblivion/Mods/canonical_v2.jsonl", 3185),
    ("fallout4", ROOT/"Fallout4/MCM/SimpleMcmJsonTranslator/translation.jsonl", 10893),
]
SHA = re.compile(r"[0-9a-f]{64}")
HANGUL = re.compile("[가-힣ㄱ-ㅎㅏ-ㅣ]")
FORBIDDEN = {"old_english", "source_text", "original_text", "english_original", "en"}


def main():
    if list((ROOT/"Morrowind"/"BaseGame").rglob("*kr6*")):
        raise ValueError("Obsolete KR6 files found; KR9 is the only accepted Morrowind baseline")
    seen_all = set()
    total = 0
    for game, path, expected in INPUTS:
        count = 0
        with path.open(encoding="utf-8", newline="") as f:
            for line_no,line in enumerate(f, 1):
                row = json.loads(line)
                if row.get("game") != game or row.get("content_language") != "ko":
                    raise ValueError(f"{path}:{line_no}: game or content_language mismatch")
                if row.get("status") != "imported":
                    raise ValueError(f"{path}:{line_no}: non-imported draft claimed")
                if not isinstance(row.get("ko"),str) or not HANGUL.search(row["ko"]):
                    raise ValueError(f"{path}:{line_no}: missing Korean")
                if FORBIDDEN.intersection(row):
                    raise ValueError(f"{path}:{line_no}: full English source field present")
                if game=="morrowind":
                    if row.get("mod_version")!="KR9":
                        raise ValueError(f"{path}:{line_no}: obsolete Morrowind source")
                    if row.get("record")=="L10N":
                        key_field="localized_value_sha256"
                        unique=(row.get("source_archive_member"),row.get("record_id"))
                    elif row.get("record")=="OPENMW_TEXT_MAP":
                        key_field="original_key_hash"
                        unique=(row.get("source_archive_member"),row.get("record_id"))
                    else:
                        key_field="localized_subrecord_hash"
                        unique=(row.get("source_archive_member"),row.get("subrecord_data_offset"))
                elif game=="oblivion":
                    key_field="source_hash"
                    unique=(row.get("plugin"),row.get("record"),row.get("form_id"),
                            row.get("field"),row.get("sub_index"))
                else:
                    key_field="source_hash"
                    unique=(row.get("source_dictionary"),row.get("dictionary_record_index"))
                if not SHA.fullmatch(row.get(key_field,"")):
                    raise ValueError(f"{path}:{line_no}: invalid SHA")
                # File/record identity scope must be intact even if same English
                # has different Korean across contexts.
                identity=(game,*unique)
                if identity in seen_all:
                    raise ValueError(f"{path}:{line_no}: duplicated record identity")
                seen_all.add(identity)
                count+=1
        if count != expected:
            raise ValueError(f"{path}: {count} != expected {expected}")
        total += count
        print(f"PASS {game}: {path.relative_to(ROOT)} = {count:,} rows")
    print(f"PASS total {total:,} Korean-only imported rows; no original English fields")


if __name__=="__main__":
    main()
