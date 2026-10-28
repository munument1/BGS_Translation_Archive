"""Build/query a local multi-game Korean translation memory from this archive.

This does not alter SST, ESP, ESM or the tracked JSONL and gzip files.
The generated SQLite database belongs under ignored work/ (never commit it).

    python tools/translation_memory.py build
    python tools/translation_memory.py lookup --english "Slaughterfish"
    python tools/translation_memory.py lookup --english "Slaughterfish" --game oblivion
    python tools/translation_memory.py lookup --game morrowind --record-id BookSkill_Enchant1
    python tools/translation_memory.py lookup --korean "드웨머" --game morrowind --limit 10
    python tools/translation_memory.py report

Key rule: Only source_hash created from a *known English original* is used
for English matching. Korean hashes, unknown source hashes and numeric
StringIDs are not translated into imaginary English evidence. Same-English
different-Korean variants are review candidates, not automatic corrections.
"""
from collections import Counter
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/"work/translation_memory.sqlite3"
HEX=re.compile(r"^[0-9a-f]{64}$")
SST_GAMES=("Fallout4","FalloutNewVegas","Starfield")
KOREAN=re.compile("[\uac00-\ud7a3\u3131-\u318e\u1100-\u11ff]")
TABLE_SCHEMA_VERSION=1
CHUNK=12000
FIELDS="game dataset english_sha ko source_file source_dictionary record_type field record_id plugin ordinal identity status".split()


def sha256(file):
    digest=hashlib.sha256()
    with file.open("rb") as inp:
        for block in iter(lambda: inp.read(4*1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def content(file):
    if file.suffix==".gz":
        return gzip.open(file,"rt",encoding="utf-8",newline="")
    return file.open("rt",encoding="utf-8",newline="")


def iter_sources():
    """Yield each archive shard and its expected record count/checksum."""
    for game in SST_GAMES:
        folder=ROOT/game/"Dictionaries/xTranslator/archive"
        manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["shards"]:
            path=folder/entry["file"]
            yield game.lower(), "sst", path, entry["rows"], entry["sha256_compressed"]

    folders={
        "fallout4":ROOT/"Fallout4/BaseGame/KoreanPatch-20260819/archive",
        "starfield":ROOT/"Starfield/BaseGame/KoreanPatch-260914/archive",
    }
    for game,folder in folders.items():
        manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
        for item in manifest["shards"]:
            yield game,"base",folder/item["file"],item["rows"],item["gzip_sha256"]

    sources=[
        ("morrowind","kr9",ROOT/"Morrowind/BaseGame/KR9/translation.jsonl",53896),
        ("oblivion","oblivion",ROOT/"Oblivion/BaseGame/Oblivion.esm/canonical_v2.jsonl",46225),
        ("oblivion","oblivion",ROOT/"Oblivion/DLC/canonical_v2.jsonl",1734),
        ("oblivion","oblivion",ROOT/"Oblivion/Mods/canonical_v2.jsonl",3185),
        ("fallout4","mcm",ROOT/"Fallout4/MCM/SimpleMcmJsonTranslator/translation.jsonl",10893),
    ]
    for game,dataset,path,rows in sources:
        yield game,dataset,path,rows,None


def strval(value):
    return "" if value is None else str(value)


def stable_identity(row,game,dataset):
    if dataset=="sst":
        return f"{row.get('source_dictionary','')}#{row['dictionary_record_index']}"
    if dataset=="mcm":
        return f"{row.get('source_dictionary','')}#{row['dictionary_record_index']}"
    if dataset=="kr9":
        src=row.get("source_archive_member","")
        if "subrecord_data_offset" in row:
            return f"{src}@{row['subrecord_data_offset']}"
        return f"{src}@{row.get('record_id','')}"
    if dataset=="oblivion":
        return "|".join(strval(row.get(k)) for k in
                        ("plugin","record","form_id","field","sub_index"))
    if game=="fallout4":
        if row.get("type")=="string_table":
            return f"{row.get('deployed_path','')}@{row['string_id']}"
        return "|".join(strval(row.get(k)) for k in
                        ("deployed_path","key","occurrence"))
    return strval(row["identity"])


def normalized(row,game,dataset,source_file):
    ko=row["ko"]
    if not isinstance(ko,str) or not KOREAN.search(ko):
        raise ValueError("Missing Hangul text")
    source_lang=row.get("source_language")
    if dataset=="kr9" and row.get("mod_version")!="KR9":
        raise ValueError("Non-KR9 Morrowind localization is forbidden")
    if dataset=="base" and game=="starfield":
        if row.get("english_source_sha256") is not None:
            raise ValueError("English source should be absent in Starfield stage")
    # 'source_hash' is meaningful ONLY when archive includes that exact
    # field on a trusted bilingual SST, Oblivion or MCM importer record.
    en=row.get("source_hash") if dataset in ("sst","oblivion","mcm") else None
    if en is not None and (not isinstance(en,str) or not HEX.fullmatch(en)):
        raise ValueError("Invalid English source SHA256")
    if dataset=="sst":
        source_dict=strval(row["source_dictionary"])
        record_type=strval(row.get("record"))
        field=strval(row.get("field"))
        record_id=strval(row.get("form_id") or row.get("string_id"))
        plugin=source_dict
        ordinal=int(row["dictionary_record_index"])
        status=strval(row.get("status"))
    elif dataset=="mcm":
        source_dict=strval(row["source_dictionary"])
        record_type="MCM"
        field="translated"
        record_id=strval(row.get("dictionary_record_index"))
        plugin=strval(row.get("mod"))
        ordinal=int(row["dictionary_record_index"])
        status=strval(row.get("status"))
    elif dataset=="kr9":
        source_dict=strval(row.get("source_archive_member"))
        record_type=strval(row.get("record"))
        field=strval(row.get("field"))
        record_id=strval(row.get("record_id"))
        plugin=strval(row.get("plugin") or "OpenMW_KR9")
        ordinal=int(row.get("subrecord_data_offset",0))
        status=strval(row.get("status"))
    elif dataset=="oblivion":
        source_dict=strval(row.get("source_dictionary"))
        record_type=strval(row.get("record"))
        field=strval(row.get("field"))
        record_id=strval(row.get("form_id"))
        plugin=strval(row.get("plugin"))
        ordinal=int(row.get("sub_index",0))
        status=strval(row.get("status"))
    else:
        source_dict=strval(row.get("source_file") or row.get("table"))
        record_type=strval(row.get("type") or row.get("kind"))
        field=strval(row.get("deployed_path") or row.get("table"))
        record_id=strval(row.get("string_id") if row.get("string_id") is not None
                         else row.get("key") or row.get("ui_key"))
        plugin=strval(row.get("plugin_hint"))
        ordinal=int(row.get("index",row.get("physical_line",row.get("source_line_number",0))))
        status=strval(row.get("status") or "extracted_unreviewed")
    identity=stable_identity(row,game,dataset)
    if not identity:
        raise ValueError("Empty original record identity")
    return (game,dataset,en,ko,str(source_file),source_dict,
            record_type,field,record_id,plugin,ordinal,identity,status)


def init(con):
    con.executescript("""
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=NORMAL;
        PRAGMA cache_size=-65536;
        CREATE TABLE entry (
            id INTEGER PRIMARY KEY, game TEXT NOT NULL,
            dataset TEXT NOT NULL, english_sha TEXT, ko TEXT NOT NULL,
            source_file TEXT NOT NULL, source_dictionary TEXT NOT NULL,
            record_type TEXT, field TEXT, record_id TEXT, plugin TEXT,
            ordinal INTEGER, identity TEXT NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE import_file (
            source_file TEXT PRIMARY KEY, game TEXT, dataset TEXT,
            expected_rows INTEGER, imported_rows INTEGER,
            sha256 TEXT NOT NULL
        );
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    con.execute("INSERT INTO meta VALUES ('schema_version', ?)", (str(TABLE_SCHEMA_VERSION),))
    con.execute("INSERT INTO meta VALUES ('baseline', 'Morrowind KR9 only; no KR6 imports')")


def build(db):
    db.parent.mkdir(parents=True,exist_ok=True)
    if db.exists():
        raise FileExistsError(f"Refusing to replace database: {db} (move/rename it first)")
    partial=db.with_suffix(db.suffix+".partial")
    if partial.exists():
        raise FileExistsError(f"Incomplete prior build exists: {partial}")
    con=sqlite3.connect(partial)
    counts=Counter()
    filecount=0
    started=time.monotonic()
    try:
        init(con)
        for game,dataset,path,expected,expected_digest in iter_sources():
            if not path.is_file():
                raise FileNotFoundError(path)
            if expected_digest is not None and sha256(path)!=expected_digest:
                raise ValueError(f"Archive input compressed SHA mismatch: {path}")
            relative=path.relative_to(ROOT).as_posix()
            batch=[]
            actual=0
            with content(path) as handle:
                for lineno,line in enumerate(handle,1):
                    row=json.loads(line)
                    batch.append(normalized(row,game,dataset,relative))
                    actual+=1
                    if len(batch)>=CHUNK:
                        con.executemany(
                            "INSERT INTO entry(game,dataset,english_sha,ko,source_file,"
                            "source_dictionary,record_type,field,record_id,plugin,ordinal,identity,status)"
                            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                        batch.clear()
                if batch:
                    con.executemany(
                        "INSERT INTO entry(game,dataset,english_sha,ko,source_file,"
                        "source_dictionary,record_type,field,record_id,plugin,ordinal,identity,status)"
                        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            if actual!=expected:
                raise ValueError(f"File count mismatch {relative}: {actual} != {expected}")
            con.execute("INSERT INTO import_file VALUES(?,?,?,?,?,?)",
                        (relative,game,dataset,expected,actual,sha256(path)))
            con.commit()
            counts[dataset]+=actual
            filecount+=1
            print(f"{filecount:3d} {game}/{dataset}: {actual:,} imported, "
                  f"total {sum(counts.values()):,}",flush=True)

        print("Building lookup indexes...",flush=True)
        con.executescript("""
            CREATE INDEX idx_english_sha ON entry (english_sha, game);
            CREATE INDEX idx_identity ON entry (game, dataset, identity);
            CREATE INDEX idx_game_record ON entry (game, record_id);
            CREATE INDEX idx_game_source ON entry (game, source_dictionary);
            ANALYZE;
        """)
        con.execute("INSERT INTO meta VALUES ('total_rows', ?)", (str(sum(counts.values())),))
        con.execute("INSERT INTO meta VALUES ('dataset_rows', ?)",
                    (json.dumps(dict(counts),sort_keys=True),))
        con.execute("INSERT INTO meta VALUES ('source_count', ?)", (str(filecount),))
        con.commit()
        integrity=con.execute("PRAGMA quick_check").fetchone()[0]
        if integrity!="ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        con.close()
        partial.replace(db)
    except BaseException:
        con.close()
        print(f"Import failed; partial file left at {partial}, never published.",file=sys.stderr)
        raise
    print(f"PASS local indexed translation memory: {sum(counts.values()):,} rows, "
          f"{db.stat().st_size/1048576:.2f}MiB, {time.monotonic()-started:.1f}s",flush=True)


def lookup(db,english,korean,record_id,game,limit,full):
    if not any([english,korean,record_id]):
        raise ValueError("Provide --english, --korean, or --record-id.")
    if not db.is_file():
        raise FileNotFoundError(f"Build local database first: python tools/translation_memory.py build")
    if limit<1 or limit>200:
        raise ValueError("--limit must be between 1 and 200")
    con=sqlite3.connect(f"file:{db.as_posix()}?mode=ro",uri=True)
    try:
        where=[]
        params=[]
        if english:
            where.append("english_sha=?")
            params.append(hashlib.sha256(english.encode("utf-8")).hexdigest())
        if korean:
            where.append("ko LIKE ? ESCAPE '\\'")
            params.append("%"+korean.replace("%","\\%").replace("_","\\_")+"%")
        if record_id:
            where.append("record_id=?")
            params.append(record_id)
        if game:
            where.append("game=?")
            params.append(game)
        where_sql=" AND ".join(where)
        count=con.execute("SELECT COUNT(*) FROM entry WHERE "+where_sql,params).fetchone()[0]
        rows=con.execute(
            "SELECT game,dataset,english_sha,ko,source_dictionary,record_type,field,"
            " record_id,plugin,ordinal,identity,status,source_file FROM entry WHERE "
            +where_sql+" ORDER BY dataset,game,ko LIMIT ?",params+[limit]).fetchall()
        variants=[]
        for row in rows:
            item=dict(zip(
                ("game","dataset","english_sha","ko","source_dictionary",
                 "record_type","field","record_id","plugin","ordinal",
                 "identity","status","archive_file"),row))
            if not full and len(item["ko"])>240:
                item["ko_length"]=len(item["ko"])
                item["ko"]=item["ko"][:240]+"… [preview; use --full for full text]"
            variants.append(item)
        output={"total_hits":count,"returned":len(rows),
                "caution":"Alternatives require contextual review; not automatically approved.",
                "entries":variants}
        if english:
            output["source_english"]=english
            output["source_sha256"]=hashlib.sha256(english.encode("utf-8")).hexdigest()
            output["same_english_korean_variants"]=con.execute(
                "SELECT COUNT(DISTINCT ko) FROM entry WHERE english_sha=?"
                +(" AND game=?" if game else ""),
                [output["source_sha256"]]+([game] if game else [])).fetchone()[0]
        print(json.dumps(output,ensure_ascii=False,indent=2))
    finally:
        con.close()


def report(db, out):
    if not db.is_file():
        raise FileNotFoundError(db)
    con=sqlite3.connect(f"file:{db.as_posix()}?mode=ro",uri=True)
    try:
        c=con.cursor()
        datasets={f"{a}/{b}":n for a,b,n in c.execute(
            "SELECT game,dataset,COUNT(*) FROM entry GROUP BY game,dataset ORDER BY game,dataset")}
        total=sum(datasets.values())
        aligned=c.execute("SELECT COUNT(*) FROM entry WHERE english_sha IS NOT NULL").fetchone()[0]
        distinct_hash=c.execute("SELECT COUNT(DISTINCT english_sha) FROM entry").fetchone()[0]
        by_game={}
        for game,total_rows,hash_rows in c.execute(
            "SELECT game,COUNT(*),COUNT(english_sha) FROM entry GROUP BY game"):
            by_game[game]={"rows":total_rows,"english_hash_rows":hash_rows}
        result={
            "schema":"bethesda_translation_memory_report_v1",
            "baseline":"Morrowind KR9 only",
            "indexed_total_rows":total,
            "source_english_hash_rows":aligned,
            "identity_only_or_localized_hash_rows":total-aligned,
            "distinct_known_english_hashes":distinct_hash,
            "datasets":datasets,
            "games":by_game,
            "status":"not editorially validated",
            "limits":[
                "English source text is absent from archive; exact SHA matching only where source_hash was recorded from actual English.",
                "Morrowind KR9 hashes are localized Korean bytes, NOT English original hashes.",
                "Fallout4/Starfield base string IDs are not portable FormIDs and have no known English source SHA.",
                "Distinct Korean translations of same English can be valid in different contexts; they are flagged, never overwritten.",
                "Cross-game reuse is an editorial suggestion, not a proven in-game replacement.",
            ]
        }
        # Group only by *verified* English hash; a hash alone doesn't carry
        # plaintext, but it is consistent across games for identical English.
        conflicts=c.execute("""
            SELECT COUNT(*) FROM (
                SELECT english_sha FROM entry WHERE english_sha IS NOT NULL
                GROUP BY english_sha HAVING COUNT(DISTINCT ko)>1
            )
        """).fetchone()[0]
        result["english_hashes_with_multiple_korean_variants"]=conflicts
        exact_repeat=c.execute("""
            SELECT SUM(n-1) FROM (
                SELECT COUNT(*) AS n FROM entry
                WHERE english_sha IS NOT NULL
                GROUP BY game,english_sha,ko HAVING COUNT(*)>1
            )
        """).fetchone()[0]
        result["repeated_same_game_english_sha_plus_identical_ko_rows"]=exact_repeat or 0
        if out:
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:
        con.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db",type=Path,default=DEFAULT_DB)
    sub=ap.add_subparsers(dest="action",required=True)
    sub.add_parser("build")
    p=sub.add_parser("lookup")
    p.add_argument("--english")
    p.add_argument("--korean")
    p.add_argument("--record-id")
    p.add_argument("--game",choices=("fallout4","falloutnewvegas","starfield","oblivion","morrowind"))
    p.add_argument("--limit",type=int,default=10)
    p.add_argument("--full",action="store_true",help="Show entire Korean texts, including very long books")
    p=sub.add_parser("report")
    p.add_argument("--output",type=Path,default=ROOT/"dictionaries/analysis/translation_memory_summary.json")
    a=ap.parse_args()
    if a.action=="build":
        build(a.db)
    elif a.action=="lookup":
        lookup(a.db,a.english,a.korean,a.record_id,a.game,a.limit,a.full)
    else:
        report(a.db,a.output)


if __name__=="__main__":
    main()
