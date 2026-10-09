#!/usr/bin/env python3
"""Extract Korean BOOK texts from locally owned Skyrim plugin + STRINGS files.

Input example:
  Skyrim.esm / Dawnguard.esm / HearthFires.esm / Dragonborn.esm / Update.esm
  strings/Skyrim_english.STRINGS, Skyrim_english.DLSTRINGS, ...
Output: normalized JSONL for tools/build_book_collection.py

The plugin binaries are read-only and are never redistributed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zlib
from collections import Counter
from pathlib import Path

HAN = re.compile(r"[가-힣]")
MAX_TABLE_ITEMS = 500_000


def read_table(path: Path) -> dict[int, str]:
    data = path.read_bytes()
    if len(data) < 8:
        raise ValueError(f"Bad STRINGS header: {path}")
    count, size = struct.unpack_from("<II", data)
    if count > MAX_TABLE_ITEMS or count * 8 > len(data) - 8:
        raise ValueError(f"Bad STRINGS directory: {path}")
    start = 8 + 8 * count
    end = start + size
    if end > len(data):
        raise ValueError(f"STRINGS data goes past file end: {path}")
    length_prefixed = path.suffix.lower() in (".dlstrings", ".ilstrings")
    table = {}
    for i in range(count):
        sid, rel = struct.unpack_from("<II", data, 8 + 8 * i)
        pos = start + rel
        if not (start <= pos < end):
            raise ValueError(f"Invalid STRINGS offset in {path}: {sid}")
        if length_prefixed:
            if pos + 4 > end:
                raise ValueError(f"Truncated length prefix for {sid}")
            length = struct.unpack_from("<I", data, pos)[0]
            if length > end - pos - 4:
                raise ValueError(f"Invalid string length for {sid}")
            raw = data[pos + 4:pos + 4 + length].rstrip(b"\x00")
        else:
            terminator = data.find(b"\x00", pos, end)
            if terminator < 0:
                raise ValueError(f"Unterminated string {sid} in {path}")
            raw = data[pos:terminator]
        for codec in ("utf-8-sig", "cp949", "cp1252"):
            try:
                value = raw.decode(codec)
                break
            except UnicodeDecodeError:
                continue
        table[sid] = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return table


def fields(payload: bytes):
    p = 0
    extra_size = None
    while p + 6 <= len(payload):
        name, length = struct.unpack_from("<4sH", payload, p)
        p += 6
        if name == b"XXXX":
            if length != 4 or p + 4 > len(payload):
                raise ValueError("Invalid XXXX extended subrecord")
            extra_size = struct.unpack_from("<I", payload, p)[0]
            p += 4
            continue
        if extra_size is not None:
            length = extra_size
            extra_size = None
        if p + length > len(payload):
            raise ValueError("Subrecord exceeds record boundary")
        yield name, payload[p:p + length]
        p += length
    if p != len(payload):
        raise ValueError("Trailing partial subrecord")


def book_records(plugin: Path):
    data = plugin.read_bytes()
    size = len(data)
    p = 0
    seen_master = False
    localized = False
    while p + 24 <= size:
        kind, length, flags, formid = struct.unpack_from("<4sIII", data, p)
        if kind == b"GRUP":
            if length < 24 or length > size - p:
                raise ValueError(f"Invalid GRUP in {plugin.name} at {p}")
            p += 24
            continue
        if length > size - p - 24:
            raise ValueError(f"Invalid record in {plugin.name} at {p}")
        start = p + 24
        end = start + length
        if kind == b"TES4":
            seen_master = True
            localized = bool(flags & 0x80)
        if kind == b"BOOK":
            raw = data[start:end]
            if flags & 0x00040000:
                if len(raw) < 4:
                    raise ValueError("Truncated zlib BOOK")
                expected = struct.unpack_from("<I", raw)[0]
                raw = zlib.decompress(raw[4:])
                if len(raw) != expected:
                    raise ValueError(f"Wrong decompressed size for BOOK {formid:08X}")
            record = {"form_id":f"{formid:08X}"}
            for field, value in fields(raw):
                if field == b"EDID":
                    record["editor_id"] = value.rstrip(b"\x00").decode("cp1252", "replace")
                elif field in (b"FULL", b"DESC") and len(value) == 4:
                    record[field.decode()] = struct.unpack("<I", value)[0]
                elif field in (b"FULL", b"DESC") and not localized:
                    record[field.decode()] = value.rstrip(b"\x00").decode("utf-8", "replace")
            yield record
        p = end
    if p != size or not seen_master:
        raise ValueError(f"Malformed or incomplete Skyrim plugin: {plugin}")


def run(input_dir: Path, output: Path, plugins_dir: Path | None = None):
    strings_dir = input_dir / "strings"
    if not strings_dir.is_dir():
        raise ValueError(f"Missing strings directory: {strings_dir}")
    all_tables = {p.name.lower():p for p in strings_dir.iterdir() if p.is_file()}
    plugin_root = plugins_dir or input_dir
    plugin_paths = sorted(p for p in plugin_root.iterdir()
                          if p.is_file() and p.suffix.lower() in (".esm", ".esp", ".esl"))
    if not plugin_paths:
        raise ValueError(
            "No Skyrim .esm/.esp/.esl files next to strings/. "
            "STRINGS alone cannot identify BOOK records.")
    records, problems, counts = [], [], Counter()
    for plugin in plugin_paths:
        basename = plugin.stem.lower()
        table_paths = {suffix:all_tables.get(f"{basename}_english.{suffix}")
                       for suffix in ("strings", "dlstrings", "ilstrings")}
        if not table_paths["strings"] or not table_paths["dlstrings"]:
            problems.append({"plugin":plugin.name,"reason":"missing localized STRINGS/DLSTRINGS"})
            continue
        names = read_table(table_paths["strings"])
        descriptions = read_table(table_paths["dlstrings"])
        counts["plugins_read"] += 1
        for book in book_records(plugin):
            counts["book_records"] += 1
            title_sid, body_sid = book.get("FULL"), book.get("DESC")
            if not isinstance(body_sid, int):
                counts["missing_desc_id"] += 1
                continue
            title = names.get(title_sid, "") if isinstance(title_sid, int) else str(title_sid or "")
            text = descriptions.get(body_sid, "")
            if not text:
                counts["missing_text"] += 1
                continue
            if not HAN.search(title + text):
                counts["no_hangul"] += 1
                continue
            record = {
                "game":"skyrim","record":"BOOK","field":"DESC",
                "form_id":book["form_id"],"book_id":book["form_id"],
                "editor_id":book.get("editor_id",""),
                "plugin":plugin.name,"title_ko":title or book.get("editor_id") or book["form_id"],
                "ko":text,"source_language":"en","content_language":"ko",
                "status":"imported",
                "source_ref":f"local:{plugin.name}+strings/{table_paths['dlstrings'].name}",
                "text_string_id":body_sid,"title_string_id":title_sid,
            }
            records.append(record)
            counts["exported"] += 1
    if not records:
        raise ValueError(f"No Korean BOOK records extracted. Counts: {dict(counts)}; problems: {problems}")
    records.sort(key=lambda r:(r["plugin"].lower(),r["title_ko"],r["form_id"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w",encoding="utf-8",newline="\n") as f:
        for record in records:
            f.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
    report={"counts":dict(counts),"source_files":[p.name for p in plugin_paths],
            "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"warnings":problems,
            "note":"Do not publish or copy original ESM/ESP/ESL into the archive"}
    output.with_suffix(".report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


def main():
    a=argparse.ArgumentParser()
    a.add_argument("input_dir",type=Path,help="Local folder containing ESM/ESP/ESL and strings/")
    a.add_argument("--output",type=Path,default=Path("sources/skyrim_books/skyrim_book_records.jsonl"))
    a.add_argument("--plugins-dir",type=Path,help="Optional separate Skyrim Data directory containing ESM/ESL")
    args=a.parse_args()
    run(args.input_dir,args.output,args.plugins_dir)


if __name__=="__main__":
    main()
