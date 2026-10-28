"""Lossless storage and verification for Korean-only Bethesda base-game tables.

The local imported JSONL remains the authoritative input. This only packs it
into deterministic gzip members, preserving every original byte and string ID.
Metadata and full Korean text are separate files; no original English is
fabricated. Pack only user-provided, verified-local translation overrides.

Examples:
    python tools/package_base_patch.py pack --game fallout4 --input "D:/Codex_Trans/Morrowind mod/work/dictionaries/fallout4_base_staged" --output "D:/Codex_Trans/Morrowind mod/work/dictionaries/base_packed_stage/Fallout4"
    python tools/package_base_patch.py pack --game starfield --input "D:/Codex_Trans/Morrowind mod/work/dictionaries/starfield_base_staged" --output "D:/Codex_Trans/Morrowind mod/work/dictionaries/base_packed_stage/Starfield"
    python tools/package_base_patch.py verify --root "D:/Codex_Trans/Morrowind mod/work/dictionaries/base_packed_stage/Fallout4" --source "D:/Codex_Trans/Morrowind mod/work/dictionaries/fallout4_base_staged"
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

HANGUL = re.compile("[\uac00-\ud7a3\u3131-\u318e\u1100-\u11ff]")
MAX_GZ_BYTES = 48 * 1024 * 1024
GAMES = {
    "fallout4": {"report":"manifest.json", "count":"included_with_korean",
                 "file":"output_file", "sha":"output_sha256", "total":164201},
    "starfield": {"report":"starfield_base_report.json", "count":"ko_rows",
                  "file":"output", "sha":None, "total":182448},
}


def sha_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(2*1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def json_bytes(obj):
    return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")


def sources(game,src):
    config=GAMES[game]
    report=src/config["report"]
    if not report.is_file():
        raise FileNotFoundError(report)
    data=json.loads(report.read_text(encoding="utf-8"))
    if game=="fallout4":
        entries=data["entries"]
        expected=data.get("totals",{}).get("included_with_korean")
    else:
        entries=data["files"]
        expected=data.get("ko_rows")
    specs=[]
    for entry in entries:
        name=entry[config["file"]]
        if not name.endswith(".jsonl") or Path(name).name!=name:
            raise ValueError(f"Unexpected output name: {name}")
        specs.append({
            "filename":name,
            "rows":entry[config["count"]],
            "sha256":entry.get(config["sha"]) if config["sha"] else None,
        })
    if len({x["filename"].lower() for x in specs}) !=len(specs):
        raise ValueError("Source has duplicate stage filenames")
    if sum(x["rows"] for x in specs)!=config["total"]:
        raise ValueError("Stage count changed")
    if expected is not None and expected!=config["total"]:
        raise ValueError("Source report total changed")
    return report, specs


def verify_lines(raw, game, expected_rows):
    rows=0
    identities=set()
    for raw_line in raw:
        if not raw_line.endswith(b"\n"):
            raise ValueError("Missing JSONL trailing newline")
        item=json.loads(raw_line.decode("utf-8"))
        if not isinstance(item,dict) or not HANGUL.search(item.get("ko","")):
            raise ValueError("Missing Korean")
        if game=="fallout4":
            if item.get("game")!="fallout4" or item.get("content_language")!="ko":
                raise ValueError("Non-Fallout4 entry")
            if item.get("status")!="extracted_unreviewed":
                raise ValueError("Unexpected Fallout4 QA status")
            if item.get("type")=="string_table":
                identity=(item.get("deployed_path"),item.get("string_id"))
            else:
                identity=(item.get("deployed_path"),item.get("key"),item.get("occurrence"))
        else:
            if item.get("english_source") is not None or item.get("english_source_sha256") is not None:
                raise ValueError("Starfield English data should not be guessed")
            identity=(item.get("identity"),)
        if identity in identities:
            raise ValueError(f"Duplicate record identity in shard: {identity}")
        identities.add(identity)
        rows+=1
    if rows!=expected_rows:
        raise ValueError(f"Row count mismatch {rows} != {expected_rows}")
    return rows


def pack(game,source,dest):
    source=source.resolve()
    dest=dest.resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    report, specs=sources(game,source)
    if dest.exists() and list(dest.iterdir()):
        raise FileExistsError(f"Output destination must be new or empty: {dest}")
    dest.mkdir(parents=True,exist_ok=True)
    shards=[]
    raw_bytes=0
    for spec in specs:
        src=source/spec["filename"]
        digest=sha_file(src)
        if spec["sha256"] and digest!=spec["sha256"]:
            raise ValueError(f"Source SHA differs from importer manifest: {src}")
        with src.open("rb") as f:
            count=verify_lines(f,game,spec["rows"])
        tgt=dest/(spec["filename"]+".gz")
        if tgt.exists():
            raise FileExistsError(tgt)
        with src.open("rb") as inp, tgt.open("wb") as raw:
            with gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0,compresslevel=6) as gz:
                for block in iter(lambda:inp.read(2*1024*1024),b""):
                    gz.write(block)
        if tgt.stat().st_size>MAX_GZ_BYTES:
            raise ValueError(f"Too large for GitHub: {tgt}")
        shards.append({
            "file":tgt.name,"rows":count,
            "uncompressed_sha256":digest,
            "uncompressed_bytes":src.stat().st_size,
            "gzip_sha256":sha_file(tgt),
            "gzip_bytes":tgt.stat().st_size,
        })
        raw_bytes+=src.stat().st_size
        print(f"{game} {tgt.name}: {count:,} rows, {tgt.stat().st_size/1048576:.2f} MiB",flush=True)
    report_bytes=report.read_bytes()
    manifest={
        "schema":"korean_base_patch_jsonl_gzip_v1",
        "game":game,
        "source_report_name":report.name,
        "source_report_sha256":hashlib.sha256(report_bytes).hexdigest(),
        "compression":"RFC1952 gzip level 6 mtime=0",
        "status":"extracted_unreviewed",
        "source_english_text_included":False,
        "english_alignment_verified":False,
        "korean_rows":sum(x["rows"] for x in shards),
        "uncompressed_bytes":raw_bytes,
        "compressed_bytes":sum(x["gzip_bytes"] for x in shards),
        "shards":shards
    }
    (dest/"manifest.json").write_bytes(json_bytes(manifest))
    print(f"PASS pack {game}: {manifest['korean_rows']:,} rows, "
          f"{manifest['compressed_bytes']/1048576:.2f} MiB",flush=True)


def verify(root,source=None):
    data=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    game=data["game"]
    if game not in GAMES:
        raise ValueError(f"Unknown game: {game}")
    if sum(x["rows"] for x in data["shards"])!=data["korean_rows"]:
        raise ValueError("Manifest row total mismatch")
    if data["korean_rows"]!=GAMES[game]["total"]:
        raise ValueError("Game count mismatch")
    if source is not None:
        report_path=source/data["source_report_name"]
        if sha_file(report_path)!=data["source_report_sha256"]:
            raise ValueError("Original report mismatch")
        report,specs=sources(game,source)
        if {v["filename"]+".gz" for v in specs}!={r["file"] for r in data["shards"]}:
            raise ValueError("Original and archive file lists differ")
    overall=0
    for shard in data["shards"]:
        zipped=root/shard["file"]
        if zipped.stat().st_size!=shard["gzip_bytes"] or sha_file(zipped)!=shard["gzip_sha256"]:
            raise ValueError(f"Gzip mutated: {zipped}")
        hash_raw=hashlib.sha256()
        size_raw=0
        with gzip.open(zipped,"rb") as f:
            lines=[]
            for line in f:
                hash_raw.update(line)
                size_raw+=len(line)
                lines.append(line)
            verify_lines(lines,game,shard["rows"])
        if hash_raw.hexdigest()!=shard["uncompressed_sha256"] or size_raw!=shard["uncompressed_bytes"]:
            raise ValueError(f"Gzip cannot restore input exactly: {zipped}")
        if source:
            original=source/shard["file"][:-3]
            if sha_file(original)!=hash_raw.hexdigest():
                raise ValueError(f"Staged JSONL and archive differ: {original}")
        overall+=shard["rows"]
    if overall!=data["korean_rows"]:
        raise ValueError("Verified entry total mismatch")
    print(f"PASS {game}: {overall:,} rows, {len(data['shards'])} gzip members; "
          "identical source bytes; checksums OK",flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    subs=ap.add_subparsers(dest="action",required=True)
    p=subs.add_parser("pack")
    p.add_argument("--game",choices=GAMES,required=True)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p=subs.add_parser("verify")
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--source",type=Path)
    a=ap.parse_args()
    if a.action=="pack":
        pack(a.game,a.input,a.output)
    else:
        verify(a.root,a.source)


if __name__=="__main__":
    main()
