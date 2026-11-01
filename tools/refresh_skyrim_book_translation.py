#!/usr/bin/env python3
"""Stage a Skyrim BOOK refresh from the Tullius Translator embedded game dictionary.

No local ESM/ESL is needed to refresh *existing* identified BOOK records.
New books that lack a full FormID/EDID in our archive are review candidates only.
The upstream dictionary contains an English fingerprint, not the English text.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re

UPSTREAM = "https://github.com/servaltullius/Skyrim_Translator_v6"
DICT_PATH = "src/XTranslatorAi.App/Assets/GameStrings/game-strings-skyrim.gz"
HEADER = "XTranslatorAi-GameStrings-v2"
IDENTITY = re.compile(r"^BOOK/([^/:]+):([0-9A-Fa-f]{6})/(FULL|DESC)/", re.I)
EN_HASH = re.compile(r"^[0-9a-fA-F]{32}$")
VARIABLE = re.compile(r"<(?:Alias|Global|Ref|Var|Actor|Pronoun|Text|Quest)=[^>]*>", re.I)


def old_key(row):
    return (str(row["plugin"]).casefold(), str(row["form_id"])[-6:].upper())


def load_archive(directory):
    shards = sorted(directory.glob("skyrim_books_*.jsonl"))
    if not shards:
        raise ValueError(f"No old Skyrim shards: {directory}")
    old = {}
    for path in shards:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("ko") or not row.get("plugin") or not row.get("form_id"):
                raise ValueError(f"Invalid old BOOK row in {path}")
            key = old_key(row)
            if key in old:
                raise ValueError(f"Duplicate archive key: {key}")
            old[key] = row
    return old


def unescape(text):
    # Match GameStringDictionary.Unescape in the upstream C# implementation.
    return re.sub(r"\\(.)", lambda m: {
        "t": "\t", "r": "\r", "n": "\n"
    }.get(m.group(1), m.group(1)), text)


def read_dictionary(path):
    groups = defaultdict(lambda: defaultdict(list))
    records = Counter()
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        if stream.readline().rstrip("\r\n") != HEADER:
            raise ValueError("Unrecognized game dictionary header")
        for lineno, line in enumerate(stream, 2):
            if not line.startswith("F\t"):
                continue
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) != 5:
                raise ValueError(f"Invalid F dictionary row at line {lineno}")
            _, identity, english_hash, escaped_ko, source_plugin = parts
            m = IDENTITY.match(identity)
            if m is None:
                continue
            if not EN_HASH.fullmatch(english_hash):
                raise ValueError(f"Invalid English fingerprint at line {lineno}")
            owner, local_id, field = m.groups()
            key = (owner.casefold(), local_id.upper())
            groups[key][field.upper()].append((unescape(escaped_ko), english_hash.upper(), source_plugin))
            records[field.upper()] += 1
    if not groups or not records["DESC"]:
        raise ValueError("Dictionary has no BOOK:DESC fields; refusing empty migration")
    return groups, dict(records)


def unique_field(rows):
    variants = {(korean, english_hash) for korean, english_hash, _ in rows}
    if len(variants) != 1:
        return None
    value = next(iter(variants))
    return value[0], value[1], sorted({r[2] for r in rows})


def prepare(old, dictionary, revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source revision must be full lowercase SHA")
    rows = []
    counts = Counter()
    review = []
    for k, previous in sorted(old.items()):
        group = dictionary.get(k)
        if not group or not group.get("DESC"):
            rows.append(previous)
            counts["unmatched_preserved"] += 1
            continue
        desc = unique_field(group["DESC"])
        full = unique_field(group["FULL"]) if group.get("FULL") else None
        if desc is None:
            rows.append(previous)
            counts["ambiguous_held"] += 1
            review.append({"plugin": previous["plugin"], "form_id": previous["form_id"],
                           "reason": "multiple_DESC_variants"})
            continue
        new_text, en_hash, origins = desc
        if not new_text.strip():
            rows.append(previous)
            counts["empty_held"] += 1
            continue
        if Counter(VARIABLE.findall(previous["ko"])) != Counter(VARIABLE.findall(new_text)):
            rows.append(previous)
            counts["tag_mismatch_held"] += 1
            review.append({"plugin": previous["plugin"], "form_id": previous["form_id"],
                           "reason": "dynamic_tag_mismatch"})
            continue
        updated = dict(previous)
        updated["ko"] = new_text
        if full and full[0].strip():
            updated["title_ko"] = full[0]
        updated.update({
            "source_ref": f"{UPSTREAM}/blob/{revision}/{DICT_PATH}",
            "translation_source_revision": revision,
            "translation_source_name": "Tullius Translator game-strings-skyrim",
            "english_hash128": en_hash,
            "translation_source_plugins": origins,
            "status": "review_required",
        })
        rows.append(updated)
        if updated["ko"] != previous["ko"] or updated["title_ko"] != previous["title_ko"]:
            counts["changed"] += 1
            review.append({"plugin": previous["plugin"], "form_id": previous["form_id"],
                           "reason": "changed", "title": updated["title_ko"],
                           "prior_ko_sha256": hashlib.sha256(previous["ko"].encode()).hexdigest(),
                           "candidate_ko_sha256": hashlib.sha256(updated["ko"].encode()).hexdigest()})
        else:
            counts["unchanged"] += 1
    counts["original_books"] = len(old)
    counts["candidate_books"] = len(rows)
    counts["dictionary_book_keys"] = len(dictionary)
    unmatched_new = sorted(set(dictionary) - set(old))
    counts["new_identity_candidates"] = len(unmatched_new)
    # A six-digit local ID is NOT a full FormID. Do not invent new book records.
    for plugin, local_id in unmatched_new:
        review.append({"plugin_owner": plugin, "local_form_id": local_id,
                       "reason": "new_identity_requires_full_form_id_and_edid"})
    return rows, {"counts": dict(counts), "review": review,
                  "revision": revision, "dictionary": f"{UPSTREAM}/blob/{revision}/{DICT_PATH}",
                  "status": "candidate_only_not_published"}


def write_shards(rows, folder, max_bytes=145000):
    folder.mkdir(parents=True, exist_ok=True)
    pieces, lines, size = [], [], 0
    def flush():
        nonlocal lines, size
        if lines:
            name = f"skyrim_books_{len(pieces)+1:03d}.jsonl"
            (folder / name).write_text("".join(lines), encoding="utf-8", newline="\n")
            pieces.append(name)
            lines, size = [], 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        length = len(line.encode("utf-8"))
        if length > max_bytes:
            raise ValueError(f"Oversized row: {old_key(row)}")
        if lines and size + length > max_bytes:
            flush()
        lines.append(line); size += length
    flush()
    return pieces


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, default=Path("sources/skyrim_books"))
    p.add_argument("--dictionary", type=Path, required=True,
                   help="game-strings-skyrim.gz from the pinned Tullius repository")
    p.add_argument("--source-revision", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    old = load_archive(a.archive)
    fields, field_counts = read_dictionary(a.dictionary)
    rows, report = prepare(old, fields, a.source_revision)
    if a.output.resolve() == a.archive.resolve() or a.archive.resolve() in a.output.resolve().parents:
        p.error("--output must not overwrite the archived source folder")
    report["field_counts"] = field_counts
    report["shards"] = write_shards(rows, a.output / "sources_skyrim_books")
    report["candidate_sha256"] = hashlib.sha256("".join(
        json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows
    ).encode()).hexdigest()
    (a.output / "review_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": report["counts"], "field_counts": field_counts,
                      "status": report["status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
