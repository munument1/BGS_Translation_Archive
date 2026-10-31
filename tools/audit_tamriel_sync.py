#!/usr/bin/env python3
"""Read-only source/identity comparison for Tamriel translation archive."""
import collections
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TAG = "openmw-0.51.0-kr12.4"
MW_URL = (
    "https://github.com/munument1/Morrowind-OpenMW-KR/releases/download/"
    + TAG + "/Morrowind-Korean-OpenMW-0.51.0-KR12.4-Full.zip"
)
OB_URL = "https://raw.githubusercontent.com/munument1/Oblivion-KR-Translation/main/"
OUT = ROOT / "dictionaries/analysis/tamriel_sync_audit_20261101.json"
SOURCES = (
    ("basegame", ROOT / "Oblivion/BaseGame/Oblivion.esm/canonical_v2.jsonl"),
    ("dlc", ROOT / "Oblivion/DLC/canonical_v2.jsonl"),
    ("mods", ROOT / "Oblivion/Mods/canonical_v2.jsonl"),
)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "TamrielTranslationArchiveSync/1.0"})
    with urllib.request.urlopen(request, timeout=120) as resp:
        return resp.read()

def archive_oblivion():
    index = collections.defaultdict(list)
    file_info = {}
    for kind, path in SOURCES:
        count = 0
        sample = None
        for line in path.open("r", encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if sample is None:
                sample = {k: str(v)[:100] for k, v in r.items() if k != "ko"}
            k = identity(r.get("plugin"), r.get("record"), r.get("form_id"), r.get("field"), r.get("sub_index"))
            index[k].append((kind, r.get("ko"), r.get("source_hash")))
            count += 1
        file_info[kind] = {"rows": count, "sample_no_korean": sample, "path": str(path.relative_to(ROOT))}
    return index, file_info

def identity(plugin, record, formid, field, index):
    def norm(x):
        return str(x or "").strip().lower()
    return (norm(plugin), norm(record), norm(formid).removeprefix("0x"), norm(field), str(index or 0))

def compare_csv(data, archive_index):
    f = io.StringIO(data.decode("utf-8-sig"), newline="")
    reader = csv.DictReader(f)
    required = {"effective_source", "record_type", "raw_formid", "field", "occurrence", "new_korean"}
    assert required <= set(reader.fieldnames), f"Missing columns {required - set(reader.fieldnames)}"
    total = 0
    matched = 0
    exact = 0
    changed = 0
    mismatched_source_hash = 0
    no_match = 0
    ambiguous = 0
    counts = collections.Counter()
    samples = []
    new_keys = set()
    for r in reader:
        if not r["new_korean"]:
            continue
        total += 1
        k = identity(r["effective_source"], r["record_type"], r["raw_formid"], r["field"], r["occurrence"])
        new_keys.add(k)
        old = archive_index.get(k, [])
        if not old:
            no_match += 1
            continue
        if len(old) != 1:
            ambiguous += 1
            continue
        matched += 1
        kind, ko, oldhash = old[0]
        counts[kind] += 1
        if ko == r["new_korean"]:
            exact += 1
        else:
            changed += 1
            if len(samples) < 12:
                samples.append({"plugin": k[0], "record": k[1], "form_id": k[2],
                                "field": k[3], "sub_index": k[4], "part": kind,
                                "old_ko_sha256": sha(str(ko).encode("utf-8")),
                                "new_ko_sha256": sha(r["new_korean"].encode("utf-8"))})
        oldhash = oldhash or ""
        source = r.get("old_english", r.get("old_text", ""))
        if oldhash and source and sha(source.encode("utf-8")) != oldhash:
            mismatched_source_hash += 1
    return {"csv_fields": reader.fieldnames, "new_nonempty_rows": total,
            "archive_exact_id_hits": matched, "exact_same_korean": exact,
            "changed_same_id": changed, "unmatched": no_match,
            "ambiguous_archive_ids": ambiguous, "match_by_part": dict(counts),
            "matched_but_source_hash_mismatch_if_available": mismatched_source_hash,
            "existing_archive_keys_not_in_csv": len(set(archive_index) - new_keys),
            "changed_samples_hash_only": samples}

def morrowind_audit(data):
    members = []
    esp_list = []
    interesting_members = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.lower().endswith((".yaml", ".yml", ".top", ".cel", ".mrk", ".jrn", ".txt", ".json")):
                interesting_members.append({"name": name, "size": z.getinfo(name).file_size})
            if name.lower().endswith((".esp", ".esm")):
                raw = z.read(name)
                esp_list.append({"member": name, "sha256": sha(raw), "bytes": len(raw)})
            if "Morrowind_Korean_ReTranslation.esp".lower() in name.lower():
                members.append(name)
    baseline = json.loads((ROOT / "Morrowind/BaseGame/KR9/metadata.json").read_text("utf-8"))
    kr9_path = ROOT / "Morrowind/BaseGame/KR9/translation.jsonl"
    old_lines = 0
    kr9_sample = []
    kr9_kinds = collections.Counter()
    kr9_samples_by_type = {}
    for ln in kr9_path.open("r", encoding="utf-8"):
        if not ln.strip():
            continue
        row = json.loads(ln)
        if len(kr9_sample) < 8:
            kr9_sample.append({k: str(v)[:120] for k, v in row.items()
                               if k not in ("ko", "source_english", "en")})
        kr9_kinds[(row.get("record"), row.get("field"))] += 1
        rt = row.get("record")
        if rt in ("INFO", "DIAL", "OPENMW_TEXT_MAP", "L10N", "MGEF") and rt not in kr9_samples_by_type:
            kr9_samples_by_type[rt] = {k: str(v)[:120] for k, v in row.items() if k not in ("ko", "source_english", "en")}
        old_lines += 1
    web_manifest = json.loads((ROOT / "docs/books/manifest.json").read_text("utf-8"))
    return {"current_release_tag": TAG, "latest_zip_sha256": sha(data),
            "latest_esp_members": esp_list, "korean_target_members": members,
            "archive_baseline_release": baseline.get("release"),
            "archive_baseline_rows": old_lines,
            "archive_baseline_sample_no_korean": kr9_sample,
            "archive_special_samples": kr9_samples_by_type,
            "latest_zip_nonplugin_text_members": interesting_members[:250],
            "archive_record_field_counts": [{"record": k[0], "field": k[1], "rows": n} for k, n in kr9_kinds.most_common(40)],
            "archive_stored_source_esp_sha256": baseline.get("source_esp_sha256"),
            "web_book_source": web_manifest["sources"].get("morrowind"),
            "action": "Preserve KR9 baseline; generate new versioned KR12.4 source dataset after identity/schema verification."}

def main():
    old, files = archive_oblivion()
    ob = download(OB_URL + "canonical_translation_v2.csv")
    locations = download(OB_URL + "canonical_locations_v2.csv")
    obmeta = json.loads((ROOT / "Oblivion/import_metadata.json").read_text("utf-8"))
    oc = compare_csv(ob, old)
    unofficial = download(OB_URL + "canonical_unofficial_translation_v2.csv")
    with io.StringIO(unofficial.decode("utf-8-sig"), newline="") as inp:
        rdr = csv.DictReader(inp)
        uc = {"sha256": sha(unofficial), "csv_fields": rdr.fieldnames,
              "data_rows": sum(1 for _ in rdr)}
    mw = download(MW_URL)
    result = {
        "schema": "tamriel_source_archive_sync_audit_v1",
        "status": "read_only_review_required",
        "inputs": {"oblivion_csv_sha256": sha(ob),
                   "oblivion_locations_sha256": sha(locations),
                   "previous_oblivion_csv_sha256": obmeta["sources"].get("canonical_translation_v2.csv"),
                   "previous_oblivion_locations_sha256": obmeta["sources"].get("canonical_locations_v2.csv")},
        "oblivion": {"archive_files": files, "record_identity_comparison": oc,
                     "unofficial_source": uc},
        "morrowind": morrowind_audit(mw),
        "patch_for_purists": {
            "separate_archive_exists": (ROOT / "Morrowind/Mods/Patch-for-Purists").exists(),
            "note": "PFP is a separate mod and must never be automatically merged into base-game KR data."},
        "notes": ["Only same stable identities can be candidates for a translation update.",
                  "Changed source hash or mismatched translation context must be reviewed before updates.",
                  "The web books are a distinct generated output, not a replacement for versioned full translation memory."]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "oblivion_source_changed": result["inputs"]["oblivion_csv_sha256"] != result["inputs"]["previous_oblivion_csv_sha256"],
        "oblivion": oc,
        "morrowind": result["morrowind"],
        "unofficial": uc,
        "report": str(OUT.relative_to(ROOT))}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
