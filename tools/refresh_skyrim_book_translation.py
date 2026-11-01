#!/usr/bin/env python3
"""Build review-only Skyrim BOOK Korean refresh candidates from original plugins."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile
from extract_skyrim_books import run as extract

SOURCE="https://github.com/servaltullius/Skyrim_Translator_v6"
VARIABLE=re.compile(r"<(?:Alias|Global|Ref|Var|Actor|Pronoun|Text|Quest)=[^>]*>",re.I)

def key(r):
    return (str(r["plugin"]).casefold(),str(r["form_id"]).upper())

def load(folder):
    files=sorted(folder.glob("skyrim_books_*.jsonl"))
    if not files: raise ValueError("Missing archived Skyrim book shards")
    found={}
    for file in files:
        for line in file.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip(): continue
            row=json.loads(line); k=key(row)
            if k in found: raise ValueError(f"Duplicate archived BOOK {k}")
            if not row.get("ko") or not row.get("title_ko"): raise ValueError(f"Empty archived BOOK {k}")
            found[k]=row
    return found

def prepare(old,now,revision):
    if not re.fullmatch(r"[a-f0-9]{40}",revision): raise ValueError("Invalid revision SHA")
    out=dict(old); visited=set(); counts=Counter(); exceptions=[]; changes=[]
    for r in now:
        k=key(r)
        if k in visited: raise ValueError(f"Duplicate new BOOK {k}")
        visited.add(k)
        previous=old.get(k)
        reason=None
        if previous and previous.get("editor_id") and r.get("editor_id") and previous["editor_id"]!=r["editor_id"]:
            reason="editor_id_changed"
        if previous and Counter(VARIABLE.findall(previous["ko"]))!=Counter(VARIABLE.findall(r["ko"])):
            reason="runtime_tag_changed"
        if reason:
            counts["held"]+=1
            exceptions.append({"plugin":k[0],"form_id":k[1],"reason":reason})
            continue
        updated=dict(previous or {})
        updated.update(r)
        table=r.get("source_ref","").rsplit("/",1)[-1]
        updated["source_ref"]=f"{SOURCE}/blob/{revision}/Skyrim_Latest_Kor/01-main/strings/{table}"
        updated["translation_source_revision"]=revision
        updated["translation_source_name"]="Skyrim AE(SE) Korean patch 26.10.16 beta 6"
        updated["status"]="imported"
        out[k]=updated
        if previous is None: counts["new"]+=1; change="new"
        elif previous["ko"]!=r["ko"] or previous["title_ko"]!=r["title_ko"]:
            counts["changed"]+=1; change="changed"
        else: counts["same"]+=1; change=None
        if change: changes.append({"plugin":k[0],"form_id":k[1],"change":change,"title":r["title_ko"],
            "old_sha256":hashlib.sha256(previous["ko"].encode()).hexdigest() if previous else None,
            "new_sha256":hashlib.sha256(r["ko"].encode()).hexdigest()})
    counts.update({"old":len(old),"extracted":len(now),"result":len(out),
        "preserved_unmatched":len(set(old)-visited)})
    rows=sorted(out.values(),key=lambda r:(key(r)[0],r["title_ko"],key(r)[1]))
    return rows,{"counts":dict(counts),"exceptions":exceptions,"changes":changes,
        "source_revision":revision,"status":"review_required"}

def write_shards(rows,folder):
    folder.mkdir(parents=True,exist_ok=True)
    parts=[]; batch=[]; size=0
    def flush():
        nonlocal batch,size
        if batch:
            name=f"skyrim_books_{len(parts)+1:03d}.jsonl"
            (folder/name).write_text("".join(batch),encoding="utf-8",newline="\n")
            parts.append(name);batch=[];size=0
    for r in rows:
        line=json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n"
        length=len(line.encode("utf8"))
        if length>145000: raise ValueError(f"BOOK exceeds shard size: {key(r)}")
        if batch and size+length>145000:flush()
        batch.append(line);size+=length
    flush()
    return parts

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,default=Path("sources/skyrim_books"))
    p.add_argument("--patch-root",type=Path,required=True)
    p.add_argument("--plugins-dir",type=Path,required=True)
    p.add_argument("--source-revision",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if not (a.patch_root/"strings").is_dir():p.error("Korean strings/ missing")
    if not a.plugins_dir.is_dir():p.error("Original Skyrim Data directory unavailable")
    if a.output.resolve()==a.archive.resolve() or a.archive.resolve() in a.output.resolve().parents:
        p.error("Output must be outside the live archive")
    original=load(a.archive)
    with tempfile.TemporaryDirectory() as temp:
        file=Path(temp)/"fresh.jsonl"
        extract(a.patch_root,file,a.plugins_dir)
        fresh=[json.loads(s) for s in file.read_text(encoding="utf8").splitlines() if s]
    rows,report=prepare(original,fresh,a.source_revision)
    report["shards"]=write_shards(rows,a.output/"sources_skyrim_books")
    report["candidate_sha256"]=hashlib.sha256("".join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in rows).encode()).hexdigest()
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"review_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report["counts"],ensure_ascii=False,indent=2))
    print(f"REVIEW ONLY: {a.output}")

if __name__=="__main__":main()
