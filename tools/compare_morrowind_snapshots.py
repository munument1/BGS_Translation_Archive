#!/usr/bin/env python3
"""Compare KR9 and KR12.4 on stable field identities without deleting either snapshot."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES={
    "KR9":ROOT/"Morrowind/BaseGame/KR9/translation.jsonl",
    "KR12.4":ROOT/"Morrowind/BaseGame/KR12.4/translation.jsonl",
}
OUT=ROOT/"dictionaries/analysis/tamriel_morrowind_kr9_to_kr124_diff_20261101.json"

def sha(v):
    return hashlib.sha256(v.encode("utf-8")).hexdigest()

def identity(row):
    typ=row["record"]
    if typ=="OPENMW_TEXT_MAP":
        return ("map",row["field"],row.get("original_key_hash"),row.get("record_id"))
    if typ=="L10N":
        return ("l10n",row["field"],row["record_id"])
    return ("esp",row["record_index"],row["record"],row["field"],row["sub_index"])

def load(path):
    data={}
    counts=collections.Counter()
    dup=[]
    for line in path.open(encoding="utf-8"):
        if not line.strip(): continue
        row=json.loads(line)
        key=identity(row)
        if key in data:
            dup.append(str(key))
            continue
        data[key]=row
        counts[key[0]]+=1
    if dup: raise ValueError(f"Duplicate identity in {path}: {len(dup)}, samples {dup[:5]}")
    return data,dict(counts)

def main():
    prev,pc=load(FILES["KR9"])
    current,cc=load(FILES["KR12.4"])
    oldkeys=set(prev);newkeys=set(current)
    shared=oldkeys&newkeys
    changed=collections.Counter()
    same=collections.Counter()
    textdiff=[]
    record_id_differences=[]
    for key in sorted(shared,key=str):
        old,new=prev[key],current[key]
        cat=key[0]
        if old["ko"]==new["ko"]:
            same[cat]+=1
        else:
            changed[cat]+=1
            if len(textdiff)<35:
                textdiff.append({
                    "category":cat,"identity":[str(x) for x in key],
                    "old_sha256":sha(old["ko"]),"new_sha256":sha(new["ko"])
                })
        if cat=="esp" and old.get("record_id")!=new.get("record_id"):
            record_id_differences.append({"identity":[str(x) for x in key],
                                          "old_id":str(old.get("record_id"))[:110],
                                          "new_id":str(new.get("record_id"))[:110]})
    added=collections.Counter(key[0] for key in newkeys-oldkeys)
    removed=collections.Counter(key[0] for key in oldkeys-newkeys)
    result={
        "schema":"openmw_korean_kr9_kr124_identity_diff_v1",
        "comparison":"Versioned Korean archive snapshots, no verified English originals",
        "source_versions":["KR9","KR12.4"],
        "previous_rows":len(prev),"current_rows":len(current),
        "rows_by_source":{"KR9":pc,"KR12.4":cc},
        "stable_identity_shared":len(shared),
        "same_korean":dict(same),"changed_korean":dict(changed),
        "new_only":dict(added),"old_only":dict(removed),
        "record_id_changed_at_matching_esp_slot":len(record_id_differences),
        "record_id_samples":record_id_differences[:15],
        "changed_samples_hash_only":textdiff,
        "source_english_alignment":False,"in_game_tested":False,
        "policy":"KR9 preserved; KR12.4 current source; no cross-version automatic substitution."
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
