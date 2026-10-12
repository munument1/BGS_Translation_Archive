"""Index readable Fallout ESM records and keep the extracted English text local.

Usage: python tools/extract_fallout_esm.py --input "D:/.../폴아웃"
No third-party dependencies. Does not modify the source ESM/STRINGS files.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs/fallout/catalog.json"
WORK = ROOT / "work/fallout_esm"
GAME_FILES = {
    "fo3": ["Fallout3.esm", "Anchorage.esm", "ThePitt.esm", "BrokenSteel.esm", "PointLookout.esm", "Zeta.esm"],
    "fnv": ["FalloutNV.esm", "DeadMoney.esm", "HonestHearts.esm", "OldWorldBlues.esm", "LonesomeRoad.esm", "GunRunnersArsenal.esm", "CaravanPack.esm", "ClassicPack.esm", "MercenaryPack.esm", "TribalPack.esm"],
    "fo4": ["Fallout4.esm", "DLCRobot.esm", "DLCworkshop01.esm", "DLCworkshop02.esm", "DLCworkshop03.esm", "DLCCoast.esm", "DLCNukaWorld.esm"],
}
INTERESTING = {b"TERM", b"NOTE", b"BOOK"}
RECORD_HEADER = struct.Struct("<4s5I")
FIELD_HEADER = struct.Struct("<4sH")
LOCALIZED = {b"FULL", b"DESC", b"ITXT", b"RNAM", b"CNAM", b"DNAM", b"TNAM", b"BTXT", b"NAM1"}
TEXT_FIELDS = {b"DESC", b"ITXT", b"RNAM", b"CNAM", b"TNAM", b"BTXT", b"TEXT"}


def game_records(path: Path):
    """Sequentially walk GRUP headers and TES4 records (24-byte headers)."""
    end = path.stat().st_size
    with path.open("rb") as handle:
        pos = 0
        while pos < end:
            head = handle.read(24)
            if len(head) != 24:
                raise ValueError(f"Truncated record header: {path} @ {pos}")
            sig, size, flags, formid, revision, misc = RECORD_HEADER.unpack(head)
            pos += 24
            if sig == b"GRUP":
                if size < 24 or pos + size - 24 > end:
                    raise ValueError(f"Invalid GRUP: {path} @ {pos-24}")
                # GRUPs contain nested records, so step into them.
                continue
            if pos + size > end:
                raise ValueError(f"Invalid record size: {path} @ {pos-24}, {sig!r}")
            if sig in INTERESTING and not flags & 0x20:  # deleted record
                data = handle.read(size)
                if flags & 0x00040000:
                    if len(data) < 4:
                        raise ValueError(f"Compressed header missing: {path} @ {pos}")
                    uncompressed = struct.unpack_from("<I", data)[0]
                    data = zlib.decompress(data[4:])
                    if len(data) != uncompressed:
                        raise ValueError(f"Unexpected inflate size: {path} @ {pos}")
                yield sig.decode("ascii"), formid, data
            else:
                handle.seek(size, 1)
            pos += size


def fields(data: bytes):
    offset, extended = 0, 0
    while offset + 6 <= len(data):
        sig, size = FIELD_HEADER.unpack_from(data, offset)
        offset += 6
        if sig == b"XXXX":
            if size != 4 or offset + 4 > len(data):
                break
            extended = struct.unpack_from("<I", data, offset)[0]
            offset += 4
            continue
        size = extended or size
        extended = 0
        if offset + size > len(data):
            break
        yield sig, data[offset:offset + size]
        offset += size


def string_table(path: Path, encoding: str = "cp1252"):
    if not path.exists():
        return {}
    data = path.read_bytes()
    if len(data) < 8:
        return {}
    count, block_size = struct.unpack_from("<II", data)
    base = 8 + count * 8
    if base + block_size > len(data):
        raise ValueError(f"Invalid STRINGS table {path}")
    result = {}
    for i in range(count):
        key, offset = struct.unpack_from("<II", data, 8 + i * 8)
        idx = base + offset
        if idx >= len(data):
            continue
        if path.suffix.upper() == ".STRINGS":
            finish = data.find(b"\0", idx)
            raw = data[idx:finish if finish >= 0 else len(data)]
        else:
            if idx + 4 > len(data):
                continue
            length = struct.unpack_from("<I", data, idx)[0]
            if length > len(data) - idx - 4:
                continue
            raw = data[idx + 4:idx + 4 + length].rstrip(b"\0")
        result[key] = decode(raw, encoding)
    return result


def decode(raw: bytes, fallback: str = "cp1252") -> str:
    raw = raw.rstrip(b"\0")
    for encoding in ("utf-8", fallback):
        try:
            return raw.decode(encoding).strip()
        except UnicodeDecodeError:
            pass
    return ""


def get_text(sig: bytes, raw: bytes, strings: dict[str, dict[int, str]]) -> str:
    if len(raw) == 4 and sig in LOCALIZED:
        key = struct.unpack("<I", raw)[0]
        # Fallout 4 FULL is in STRINGS; descriptions/terminal entries usually in ILSTRINGS.
        kinds = ["STRINGS", "DLSTRINGS", "ILSTRINGS"] if sig == b"FULL" else ["ILSTRINGS", "DLSTRINGS", "STRINGS"]
        return next((strings[k][key] for k in kinds if key in strings[k]), "")
    if not raw or b"\0" in raw[:-1]:
        return ""
    text = decode(raw)
    if not text or sum(ch.isprintable() or ch in "\n\r\t" for ch in text) / len(text) < .97:
        return ""
    return text


def safe_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()[:160]


def readable(text: str) -> bool:
    return bool(text and any(ch.isalpha() for ch in text) and len(text) >= 3)


def extract_one(game: str, path: Path, string_dir: Path):
    prefix = path.stem
    tables = {kind: string_table(string_dir / f"{prefix}_en.{kind}", "cp949" if game == "fo4" else "cp1252") for kind in ("STRINGS", "DLSTRINGS", "ILSTRINGS")}
    # A few official packs have no localization; leave them as inline strings.
    counts: Counter = Counter()
    output = []
    for record, formid, blob in game_records(path):
        counts[record] += 1
        edid = ""
        full = ""
        main_text = ""
        items = []
        # TERM: ITXT menu caption, RNAM body; DESC welcome text.
        # FO3/FNV NOTE stores note text in TNAM. FO4 BOOK uses localized DESC.
        for sig, raw in fields(blob):
            if sig == b"EDID":
                edid = decode(raw)
            elif sig == b"FULL":
                full = get_text(sig, raw, tables)
            elif sig == b"DESC":
                text = get_text(sig, raw, tables)
                if readable(text):
                    if record == "TERM":
                        items.append(("welcome", "", text))
                    else:
                        main_text += ("\n\n" if main_text else "") + text
            elif record == "TERM" and sig == b"ITXT":
                caption = get_text(sig, raw, tables)
                items.append(("menu", caption, ""))
            elif record == "TERM" and sig == b"RNAM":
                text = get_text(sig, raw, tables)
                if readable(text):
                    if items and items[-1][0] == "menu" and not items[-1][2]:
                        kind, title, _ = items.pop()
                        items.append((kind, title, text))
                    else:
                        items.append(("entry", "", text))
            elif record != "TERM" and sig in ((b"TNAM", b"TEXT") if record == "NOTE" else (b"TEXT",)):
                text = get_text(sig, raw, tables)
                if readable(text):
                    main_text += ("\n\n" if main_text else "") + text

        candidates = []
        if record == "TERM":
            for n, (kind, caption, body) in enumerate(items):
                if readable(body):
                    candidates.append((f"{kind}-{n}", safe_title(caption or full or edid or f"Terminal {formid:08X}"), body, "terminal"))
        elif readable(main_text) and not (record == "BOOK" and main_text.strip() == full.strip()):
            kind = "holotape" if record == "NOTE" and game == "fo4" else "holodisk" if record == "NOTE" and re.search(r"holo(disk|tape)", (full + edid), re.I) else "note" if record == "NOTE" else "book"
            candidates.append(("body", safe_title(full or edid or f"{record} {formid:08X}"), main_text, kind))
        for part, title, body, kind in candidates:
            uid = f"esm-{game}-{prefix.lower()}-{record.lower()}-{formid:08x}-{part}"
            is_korean = bool(re.search(r"[가-힣]", title))
            entry = {
                "id": uid, "game": game, "type": kind, "level": "entry",
                "title_ko": title if is_korean else "", "title_en": edid if is_korean else title,
                "description": f"{prefix}.esm · {record} · FormID {formid:08X}",
                "source_name": "게임 원본 ESM", "source_url": "", "status": "extracted_untranslated",
                "body_ko": None, "plugin": path.name, "record_type": record,
                "editor_id": edid or None, "form_id": f"{formid:08X}", "field": part,
                "verification": "esm_direct", "usage_status": "unknown",
            }
            output.append((entry, body))
    return output, counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Folder containing official ESM and Strings directory")
    parser.add_argument("--probe", action="store_true", help="Print counts and representative text, do not write")
    args = parser.parse_args()
    string_dir = args.input / "Strings"
    all_rows = []
    stats = {}
    for game, names in GAME_FILES.items():
        for name in names:
            source = args.input / name
            if not source.exists():
                stats[name] = {"error": "missing ESM"}
                continue
            rows, counts = extract_one(game, source, string_dir)
            stats[name] = {"record_types": dict(counts), "entries": len(rows)}
            all_rows.extend(rows)
            print(f"{game} {name}: {len(rows)} entries / {dict(counts)}", flush=True)
    assert len({entry["id"] for entry, _ in all_rows}) == len(all_rows), "Duplicate IDs"
    print(f"TOTAL {len(all_rows)} entries")
    if args.probe:
        for row, body in all_rows[:8]:
            print(row["id"], repr(body[:180]))
        return
    WORK.mkdir(parents=True, exist_ok=True)
    source_path = WORK / "records.jsonl"
    with source_path.open("w", encoding="utf-8", newline="\n") as handle:
        for entry, body in all_rows:
            language = "ko" if re.search(r"[가-힣]", body) else "en"
            handle.write(json.dumps({**entry, "body_lang": language, "body_local": body}, ensure_ascii=False) + "\n")
    catalog = json.loads(TARGET.read_text(encoding="utf-8"))
    catalog["entries"] = [e for e in catalog["entries"] if not e["id"].startswith("esm-")] + [e for e, _ in all_rows]
    catalog["updated"] = date.today().isoformat()
    TARGET.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "source": "User-supplied local official ESM files", "extracted_at": date.today().isoformat(),
        "total_esm_entries": len(all_rows), "by_game": dict(Counter(e["game"] for e, _ in all_rows)),
        "files": stats, "local_body_file": "work/fallout_esm/records.jsonl",
        "note": "English text remains local; no translation or completeness claim. Audio-only holotapes and script-generated text are excluded.",
    }
    (ROOT / "docs/fallout/esm-import-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", source_path, TARGET, "esm-import-report.json", flush=True)


if __name__ == "__main__":
    main()
