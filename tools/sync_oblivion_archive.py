#!/usr/bin/env python3
"""Synchronize source-verified Oblivion canonical records, preserving unrelated rows."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = {
    "basegame": ROOT / "Oblivion/BaseGame/Oblivion.esm/canonical_v2.jsonl",
    "dlc": ROOT / "Oblivion/DLC/canonical_v2.jsonl",
    "mods": ROOT / "Oblivion/Mods/canonical_v2.jsonl",
}
BASE_URL = "https://raw.githubusercontent.com/munument1/Oblivion-KR-Translation/main/"
EXPECTED_SOURCE_SHA = "57306d322a0cca7d18b452ecb5d0f38bc594d23ed2e6b6040a3eee828c96ca23"
EXPECTED_LOCATIONS_SHA = "fecabf0c18db08756ebb98a5a066689fa1322f7b6f252a30ef67359a1538ae78"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def download(name):
    req = urllib.request.Request(BASE_URL + name, headers={"User-Agent": "TamrielArchiveSync/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def norm(v):
    return str(v or "").strip().lower()

def ident(p, r, f, field, index):
    return (norm(p), norm(r), norm(f).removeprefix("0x"), norm(field), str(index or 0))

def main():
    source = download("canonical_translation_v2.csv")
    locations = download("canonical_locations_v2.csv")
    assert sha(source) == EXPECTED_SOURCE_SHA, "Canonical source changed since review; stop"
    assert sha(locations) == EXPECTED_LOCATIONS_SHA, "Canonical location source changed since review; stop"
    # Retain the original order/bytes for every unchanged record; only approved matches are rewritten.
    lookup = {}
    lines = {}
    counts = {}
    for part, path in ARCHIVE.items():
        orig = path.read_bytes()
        raw_lines = orig.splitlines(keepends=True)
        count = 0
        for i, raw in enumerate(raw_lines):
            if not raw.strip():
                continue
            row = json.loads(raw)
            key = ident(row.get("plugin"), row.get("record"), row.get("form_id"), row.get("field"), row.get("sub_index"))
            if key in lookup:
                raise ValueError("Duplicate identity in archive: " + repr(key))
            lookup[key] = (part, i, row)
            count += 1
        lines[part] = raw_lines
        counts[part] = count
    modifications = collections.Counter()
    unmatched = []
    seen = set()
    number = 0
    checked = 0
    for csv_line, row in enumerate(csv.DictReader(io.StringIO(source.decode("utf-8-sig"), newline="")), 2):
        ko = row["new_korean"]
        if not ko:
            continue
        number += 1
        key = ident(row["effective_source"], row["record_type"], row["raw_formid"], row["field"], row["occurrence"])
        if key in seen:
            raise ValueError("Duplicate current source identity: " + repr(key))
        seen.add(key)
        if key not in lookup:
            unmatched.append({
                "plugin": row["effective_source"], "record": row["record_type"], "form_id": row["raw_formid"],
                "field": row["field"], "sub_index": int(row["occurrence"] or 0), "ko": ko,
                "source_hash": sha(row["old_english"].encode("utf-8")), "source_line": csv_line,
                "status": "unmatched_review_needed", "source_dictionary": "canonical_translation_v2.csv"})
            continue
        part, index, old = lookup[key]
        original_sha = old.get("source_hash")
        current_sha = sha(row["old_english"].encode("utf-8"))
        if original_sha != current_sha:
            raise ValueError("English original changed; manual review needed: " + repr(key))
        checked += 1
        if old["ko"] == ko:
            continue
        changed = dict(old)
        changed["ko"] = ko
        changed["source_line"] = csv_line
        changed["note"] = "Source-confirmed canonical v1.2.0 update (2026-11-01); no independent in-game test."
        # No global terminology replacement, no change to metadata/status of other records.
        ending = b"\r\n" if lines[part][index].endswith(b"\r\n") else b"\n"
        lines[part][index] = json.dumps(changed, ensure_ascii=False, sort_keys=True).encode("utf-8") + ending
        modifications[part] += 1
    assert checked == 47215 and sum(modifications.values()) == 1197, (
        f"Unexpected comparison: checked {checked}, changes {dict(modifications)}")
    assert len(unmatched) == 12 and number == 47227, "Missing/new source row count changed"
    for part, path in ARCHIVE.items():
        updated = b"".join(lines[part])
        assert sum(bool(line.strip()) for line in updated.splitlines()) == counts[part], part
        if modifications[part]:
            path.write_bytes(updated)
    out = ROOT / "Oblivion"
    candidates = out / "review_candidates_v1.2.0_20261101.jsonl"
    candidates.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in unmatched), encoding="utf-8")
    meta_path = out / "import_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["sources"]["canonical_translation_v2.csv"] = sha(source)
    meta["sources"]["canonical_locations_v2.csv"] = sha(locations)
    meta["latest_sync_date"] = "2026-11-01"
    meta["latest_sync_reference"] = "Oblivion-KR-Translation v1.2.0 canonical CSV"
    meta["latest_sync_changed_existing"] = dict(modifications)
    meta["latest_sync_unmatched_review_candidates"] = len(unmatched)
    meta["original_import_version_preserved"] = True
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema": "tamriel_oblivion_canonical_sync_v1",
        "baseline_original_import_date": meta.get("import_date"),
        "new_source_sha256": sha(source),
        "latest_version": "v1.2.0", "checked_identical_source_identities": checked,
        "updated_entries": dict(modifications), "total_updated_entries": sum(modifications.values()),
        "unmatched_candidates_kept_separate": len(unmatched),
        "unchanged_existing_entries_retained": sum(counts.values()) - sum(modifications.values()),
        "archive_rows": counts,
        "source_english_sha_guard": "all matched entries verified",
        "in_game_verified": False}
    report_path = ROOT / "dictionaries/analysis/tamriel_oblivion_sync_20261101.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
