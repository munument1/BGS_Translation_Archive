#!/usr/bin/env python3
"""Store unofficial Oblivion translation memory as a distinct, versioned dataset."""
import collections, csv, hashlib, io, json, re, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC="https://raw.githubusercontent.com/munument1/Oblivion-KR-Translation/main/canonical_unofficial_translation_v2.csv"
SHA="f3a41105ec44a52de6b20ac9b21865f047673aa8d83abd80d66686b4eb7b39c4"
OUT=ROOT/"Oblivion/Mods/UnofficialPatches"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    req=urllib.request.Request(SRC,headers={"User-Agent":"TamrielArchive/1.0"})
    with urllib.request.urlopen(req,timeout=120) as response:
        raw=response.read()
    assert digest(raw)==SHA, "Unreviewed source revision"
    records=[]
    seen=set()
    counts=collections.Counter()
    nonhangul=0
    hash_mismatch=0
    for line,row in enumerate(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline="")),2):
        ko=row["new_korean"]
        if not ko: continue
        identity=tuple((row.get(k) or "").casefold() for k in ("effective_source","record_type","raw_formid","field","occurrence","subrecord_index"))
        if identity in seen: raise ValueError("Repeated identity: "+repr(identity))
        seen.add(identity)
        if not re.search("[가-힣]",ko): nonhangul+=1
        english_hash=digest(row["old_english"].encode("utf-8"))
        if re.fullmatch("[0-9a-f]{64}",row.get("source_sha256","").lower()) and row["source_sha256"].lower()!=english_hash:
            hash_mismatch+=1
        item={
            "game":"oblivion","type":"plugin","source_language":"en","content_language":"ko",
            "plugin":row["effective_source"],"record":row["record_type"],"form_id":row["raw_formid"],
            "field":row["field"],"sub_index":int(row.get("occurrence") or 0),
            "source_subrecord_index":int(row.get("subrecord_index") or 0),
            "editor_id":row.get("editor_id") or "","ko":ko,"source_hash":english_hash,
            "source_dictionary":"canonical_unofficial_translation_v2.csv",
            "source_line":line,"status":"imported",
            "source_encoding_check":row.get("obcjk_conversion_status") or "",
            "note":"Unofficial mod translation, not verified in game."
        }
        counts[item["plugin"]]+=1
        records.append(item)
    assert len(records)>=5000, "Unexpectedly few data rows"
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"canonical_unofficial_v1.2.0.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in records),encoding="utf-8")
    meta={
        "game":"oblivion","dataset":"UnofficialPatches","source_version":"v1.2.0-unofficial-sync",
        "source_csv_sha256":SHA,"source_repo":"https://github.com/munument1/Oblivion-KR-Translation",
        "records":len(records),"by_plugin":dict(sorted(counts.items())),
        "non_hangul_values_retained":nonhangul,
        "upstream_source_sha256_not_equal_english_hash_count":hash_mismatch,
        "source_hash":"SHA256 of old_english UTF8 in same canonical CSV row",
        "status":"imported_not_game_verified",
        "mixed_with_base_game":False,
        "source_english_republished":False
    }
    (OUT/"metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
