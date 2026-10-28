"""Lossless, compact xTranslator translation-memory archive.

Input is the local, Korean-only validated JSONL export from SST source files.
Output is deterministic gzip JSONL shards, source metadata and a manifest.
Every source row is preserved exactly, including IDs, UTF-8 text, English
SHA-256, dictionary filename, item order and import status. No English source
prose or source SST binaries are written.

Examples:
  python tools/sst_tm.py pack --source "D:/Codex_Trans/Morrowind mod/work/dictionaries/sst_archive_exports" --output "D:/Codex_Trans/Morrowind mod/work/dictionaries/sst_packed_stage"
  python tools/sst_tm.py verify --root "D:/Codex_Trans/Morrowind mod/work/dictionaries/sst_packed_stage"
  python tools/sst_tm.py verify
  python tools/sst_tm.py find --game Fallout4 --hash <sha256>
  python tools/sst_tm.py find --game Starfield --dictionary SomeMod_en_ko.sst
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
GAME_FOLDERS = ("Fallout4", "FalloutNewVegas", "Starfield")
INPUT_SUBFOLDER = "Dictionaries/xTranslator"
TARGET_SUBFOLDER = "Dictionaries/xTranslator/archive"
MAX_INPUTS_PER_SHARD = 8
MAX_OUTPUT_SIZE = 48 * 1024 * 1024


def checksum(path):
    dig=hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda:inp.read(4*1024*1024),b""):
            dig.update(chunk)
    return dig.hexdigest()


def json_dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def input_record_count(file):
    n=0
    with file.open("rb") as f:
        for line in f:
            if not line.endswith(b"\n"):
                raise ValueError(f"Missing final newline: {file}")
            if not line.strip():
                raise ValueError(f"Empty JSONL line: {file}")
            n+=1
    return n


def pack(source_root,output_root):
    if source_root.resolve()==output_root.resolve():
        raise ValueError("Source and output must differ.")
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)
    games={}
    total_rows=0
    all_archive_files=[]
    for game in GAME_FOLDERS:
        src=source_root/game/INPUT_SUBFOLDER
        dest=output_root/game/TARGET_SUBFOLDER
        if not (src/"metadata.json").is_file():
            raise FileNotFoundError(src/"metadata.json")
        original_meta=json.loads((src/"metadata.json").read_text(encoding="utf-8"))
        files=sorted(src.glob("dictionary_*.jsonl"))
        expected=original_meta["chunk_names"]
        if sorted(x.name for x in files)!=sorted(expected):
            raise ValueError(f"{game}: input shard files differ from original SST import metadata")
        dest.mkdir(parents=True,exist_ok=True)
        meta_dest=dest/"source_metadata.json.gz"
        if meta_dest.exists():
            raise FileExistsError(meta_dest)
        meta_bytes=(src/"metadata.json").read_bytes()
        with meta_dest.open("wb") as target:
            target.write(gzip.compress(meta_bytes,compresslevel=6,mtime=0))
        shard_info=[]
        game_rows=0
        for start in range(0,len(files),MAX_INPUTS_PER_SHARD):
            group=files[start:start+MAX_INPUTS_PER_SHARD]
            index=start//MAX_INPUTS_PER_SHARD
            dest_file=dest/f"tm_{index:04d}.jsonl.gz"
            if dest_file.exists():
                raise FileExistsError(dest_file)
            digest=hashlib.sha256()
            shard_rows=0
            source_files=[]
            with dest_file.open("wb") as raw:
                with gzip.GzipFile(filename="",mode="wb",fileobj=raw,
                                   compresslevel=6,mtime=0) as zipped:
                    for path in group:
                        original_sha=hashlib.sha256()
                        current_count=0
                        with path.open("rb") as inp:
                            for line in inp:
                                if not line.endswith(b"\n") or not line.strip():
                                    raise ValueError(f"Invalid source JSONL: {path}")
                                # Preserve EVERY original line and all identity
                                # evidence, even if duplicate source English exists.
                                zipped.write(line)
                                digest.update(line)
                                original_sha.update(line)
                                current_count+=1
                        source_files.append({
                            "name":path.name,
                            "bytes":path.stat().st_size,
                            "sha256":original_sha.hexdigest(),
                            "rows":current_count,
                        })
                        shard_rows+=current_count
            packed_bytes=dest_file.stat().st_size
            if packed_bytes > MAX_OUTPUT_SIZE:
                raise ValueError(f"{dest_file}: {packed_bytes:,} > 48 MiB Git warning limit")
            shard_info.append({
                "file":dest_file.name,
                "bytes":packed_bytes,
                "sha256_compressed":checksum(dest_file),
                "sha256_uncompressed":digest.hexdigest(),
                "rows":shard_rows,
                "source_shards":source_files,
            })
            game_rows+=shard_rows
            print(f"{game} {dest_file.name}: {shard_rows:,} rows, {packed_bytes/1048576:.2f} MiB",flush=True)
        if game_rows != original_meta["counts"]["korean_entries_exported"]:
            raise ValueError(f"{game}: row sum {game_rows} differs from original import total")
        compressed_size=sum(x["bytes"] for x in shard_info)+meta_dest.stat().st_size
        game_manifest={
            "game":game,
            "format":"JSONL UTF-8 gzip",
            "lossless":True,
            "source_english_included":False,
            "compression":"RFC1952 gzip, level 6, mtime=0",
            "rows":game_rows,
            "original_source_sst_file_count":original_meta["source_files"],
            "original_jsonl_uncompressed_bytes":sum(f.stat().st_size for f in files),
            "total_compressed_bytes":compressed_size,
            "source_metadata":{
                "file":meta_dest.name,
                "bytes":meta_dest.stat().st_size,
                "sha256_compressed":checksum(meta_dest),
                "sha256_uncompressed":hashlib.sha256(meta_bytes).hexdigest(),
            },
            "shards":shard_info,
        }
        json_dump(dest/"manifest.json",game_manifest)
        total_rows+=game_rows
        games[game]={"rows":game_rows,"source_sst_files":original_meta["source_files"],
                     "compressed_bytes":compressed_size,
                     "archive_path":f"{game}/{TARGET_SUBFOLDER}"}
        all_archive_files.extend(dest.glob("*.gz"))
    summary={
        "schema":"sst_archive_gzip_lossless_v1",
        "games":games,
        "total_rows":total_rows,
        "total_source_sst_files":sum(g["source_sst_files"] for g in games.values()),
        "total_compressed_bytes":sum(g["compressed_bytes"] for g in games.values()),
        "no_original_english":True,
        "status":"unreviewed_import",
        "rights":"Retain dictionary-level provenance. Publication rights vary by contributor.",
    }
    json_dump(output_root/"sst_tm_summary.json",summary)
    print("Packed total:",f"{total_rows:,} Korean translation records,",
          f"{summary['total_compressed_bytes']/1048576:.2f} MiB",flush=True)


def verify(root, source=None):
    summary_path=root/"sst_tm_summary.json"
    if not summary_path.is_file():
        summary_path=root/"dictionaries/xTranslator/sst_tm_summary.json"
    summary=json.loads(summary_path.read_text(encoding="utf-8"))
    observed=0
    game_sums={}
    for game in GAME_FOLDERS:
        folder=root/game/TARGET_SUBFOLDER
        manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
        meta=manifest["source_metadata"]
        zipped=folder/meta["file"]
        if checksum(zipped)!=meta["sha256_compressed"]:
            raise ValueError(f"metadata compressed hash mismatch: {zipped}")
        metadata=gzip.decompress(zipped.read_bytes())
        if hashlib.sha256(metadata).hexdigest()!=meta["sha256_uncompressed"]:
            raise ValueError(f"metadata raw SHA mismatch: {zipped}")
        origin=json.loads(metadata)
        if origin["counts"]["korean_entries_exported"] != manifest["rows"]:
            raise ValueError(f"{game}: metadata output count mismatch")
        counts=Counter()
        rows=0
        for shard in manifest["shards"]:
            compressed=folder/shard["file"]
            if compressed.stat().st_size!=shard["bytes"] or checksum(compressed)!=shard["sha256_compressed"]:
                raise ValueError(f"Compressed shard differs: {compressed}")
            dig=hashlib.sha256()
            line_count=0
            with gzip.open(compressed,"rb") as inp:
                for line in inp:
                    dig.update(line)
                    line_count+=1
                    if not line.endswith(b"\n"):
                        raise ValueError(f"{compressed}: malformed JSONL line {line_count}")
                    obj=json.loads(line)
                    if obj.get("content_language")!="ko" or not obj.get("ko"):
                        raise ValueError(f"{compressed}: non-Korean translation row")
                    if "source_text" in obj or "original_text" in obj or "en" in obj:
                        raise ValueError(f"{compressed}: full original English exposed")
                    if obj.get("source_dictionary") not in origin["provenance"]:
                        raise ValueError(f"{compressed}: missing dictionary provenance")
                    counts[obj["source_dictionary"]]+=1
            if dig.hexdigest()!=shard["sha256_uncompressed"] or line_count!=shard["rows"]:
                raise ValueError(f"Decompressed SHA/rows mismatch: {compressed}")
            # Verify original split distribution and optional input shard bytes
            expected_count=sum(f["rows"] for f in shard["source_shards"])
            if expected_count!=line_count:
                raise ValueError(f"Input shard count mismatch: {compressed}")
            if source:
                original_dig=hashlib.sha256()
                for s in shard["source_shards"]:
                    original=source/game/INPUT_SUBFOLDER/s["name"]
                    if checksum(original)!=s["sha256"]:
                        raise ValueError(f"Original source SHA mismatch: {original}")
                    with original.open("rb") as f:
                        for data in iter(lambda:f.read(4*1024*1024),b""):
                            original_dig.update(data)
                if original_dig.hexdigest()!=dig.hexdigest():
                    raise ValueError(f"Decompressed bytes not identical to source: {compressed}")
            rows+=line_count
        if rows!=manifest["rows"] or rows!=summary["games"][game]["rows"]:
            raise ValueError(f"{game} total mismatch")
        seen_input=set(origin["provenance"])
        if set(counts)-seen_input:
            raise ValueError(f"{game}: unknown dictionaries")
        observed+=rows
        game_sums[game]=rows
        print(f"PASS {game}: {rows:,} rows and every gzip/source SHA",flush=True)
    if observed != summary["total_rows"]:
        raise ValueError(f"Global total changed: {observed}")
    print("PASS ALL:",f"{observed:,} source-equivalent rows",flush=True)


def find(root, game, value_hash, dictionary, korean, limit):
    if not any((value_hash,dictionary,korean)):
        raise ValueError("Supply --hash, --dictionary or --korean.")
    games=(game,) if game else GAME_FOLDERS
    found=0
    for g in games:
        folder=root/g/TARGET_SUBFOLDER
        manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
        for shard in manifest["shards"]:
            with gzip.open(folder/shard["file"],"rt",encoding="utf-8") as inp:
                for raw in inp:
                    rec=json.loads(raw)
                    if value_hash and rec.get("source_hash")!=value_hash:
                        continue
                    if dictionary and rec.get("source_dictionary")!=dictionary:
                        continue
                    if korean and korean not in rec.get("ko",""):
                        continue
                    print(json.dumps(rec,ensure_ascii=False))
                    found+=1
                    if found>=limit:
                        return
    print(f"Matches: {found}",file=sys.stderr)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="operation",required=True)
    p=sub.add_parser("pack")
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p=sub.add_parser("verify")
    p.add_argument("--root",type=Path,default=ARCHIVE_ROOT)
    p.add_argument("--source",type=Path)
    p=sub.add_parser("find")
    p.add_argument("--root",type=Path,default=ARCHIVE_ROOT)
    p.add_argument("--game",choices=GAME_FOLDERS)
    p.add_argument("--hash",dest="value_hash")
    p.add_argument("--dictionary")
    p.add_argument("--korean")
    p.add_argument("--limit",type=int,default=20)
    args=parser.parse_args()
    if args.operation=="pack":
        pack(args.source,args.output)
    elif args.operation=="verify":
        verify(args.root,args.source)
    else:
        find(args.root,args.game,args.value_hash,args.dictionary,args.korean,args.limit)


if __name__=="__main__":
    main()
