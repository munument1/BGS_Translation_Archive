#!/usr/bin/env python3
"""Import a pinned OpenMW KR12.4 as NEW versioned source data; never overwrite KR9."""
import collections
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import urllib.request
import zipfile
import yaml

ROOT=Path(__file__).resolve().parents[1]
VERSION="KR12.4"
TAG="openmw-0.51.0-kr12.4"
RELEASE="https://github.com/munument1/Morrowind-OpenMW-KR/releases/download/"+TAG+"/"
FILENAME="Morrowind-Korean-OpenMW-0.51.0-KR12.4-Full.zip"
EXPECTED_ZIP_SHA="71fbbd1ae5506df4444fe47f31b29101f010a96fa5d73bb4b8699977cd211497"
EXPECTED_ESP_SHA="2276384ad93fd3e56bc0d401aacc45418ba38993ee798e0e1a7e09564a375d3a"
MOD_ROOT="payload/mods/Morrowind_Korean_ReTranslation/"
OUT=ROOT/"Morrowind/BaseGame/KR12.4"
KOREAN=re.compile(r"[가-힣]")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"TamrielArchive/1.0"})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()

def text_value(raw):
    raw=raw.rstrip(b"\x00")
    try: result=raw.decode("utf-8-sig")
    except UnicodeDecodeError: return None
    if not KOREAN.search(result): return None
    if any(ord(ch)<32 and ch not in "\r\n\t" for ch in result): return None
    return result

def base_row(member,raw):
    return {
        "game":"morrowind","mod":"Morrowind OpenMW Korean KR12.4","mod_version":VERSION,
        "source_archive_member":member,"source_archive_member_sha256":sha(raw),
        "content_language":"ko","source_language":"unknown","status":"imported",
        "note":"Pinned official KR12.4 source bytes; no independent English or in-game validation."
    }

def source_pairs():
    result=set()
    path=ROOT/"Morrowind/BaseGame/KR9/translation.jsonl"
    for ln in path.open(encoding="utf-8"):
        if ln.strip():
            row=json.loads(ln)
            if row.get("plugin") and row.get("record") and row.get("field"):
                result.add((row["record"],row["field"]))
    return result

def esp_rows(z,whitelist):
    member=MOD_ROOT+"Morrowind_Korean_ReTranslation.esp"
    raw=z.read(member)
    assert sha(raw)==EXPECTED_ESP_SHA,"Release ESP content hash mismatch"
    common=base_row(member,raw)
    pos=0
    i=0
    results=[]
    skipped_new_pairs=collections.Counter()
    active_topic=""
    while pos<len(raw):
        if pos+16>len(raw): raise ValueError("Invalid TES3 record header")
        kind,length,_,_=struct.unpack_from("<4sIII",raw,pos)
        end=pos+16+length
        if end>len(raw): raise ValueError("Record overflow")
        t=kind.decode("ascii")
        parts=[]
        subpos=pos+16
        while subpos<end:
            if subpos+8>end: raise ValueError("Subrecord overflow")
            field,n=struct.unpack_from("<4sI",raw,subpos)
            offset=subpos+8
            finish=offset+n
            if finish>end: raise ValueError("Subrecord data overflow")
            parts.append((field.decode("ascii"),raw[offset:finish],offset))
            subpos=finish
        if t=="DIAL":
            topic=next((x for f,x,_ in parts if f=="NAME"),b"")
            active_topic=topic.rstrip(b"\x00").decode("utf-8","replace")
        identifier=next((x for f,x,_ in parts if f==("INAM" if t=="INFO" else "NAME")),b"")
        rid=identifier.rstrip(b"\x00").decode("utf-8","replace")
        for index,(field,content,offset) in enumerate(parts):
            val=text_value(content)
            if val is None: continue
            if (t,field) not in whitelist:
                skipped_new_pairs[(t,field)]+=1
                continue
            row=dict(common)
            row.update({
                "plugin":"Morrowind_Korean_ReTranslation.esp",
                "record":t,"record_id":rid,"record_index":i,
                "field":field,"sub_index":index,
                "subrecord_data_offset":offset,
                "localized_subrecord_hash":sha(content),"dialogue_topic":active_topic if t=="INFO" else "",
                "ko":val
            })
            results.append(row)
        pos=end
        i+=1
    if pos!=len(raw): raise ValueError("Incomplete record stream")
    if len(results)<40000: raise ValueError("Unexpectedly few Korean ESP fields")
    return results,i,skipped_new_pairs

def map_rows(z):
    result=[]
    counts={}
    for ext in ("cel","jrn","mrk","top"):
        member=MOD_ROOT+"Morrowind_Korean_ReTranslation."+ext
        raw=z.read(member)
        common=base_row(member,raw)
        kind=ext.upper()
        nonempty=0
        for line in raw.decode("utf-8-sig").splitlines():
            if "\t" not in line: continue
            old,translated=line.split("\t",1)
            val=translated.strip()
            if not val or not KOREAN.search(val): continue
            nonempty+=1
            row=dict(common)
            row.update({
                "record":"OPENMW_TEXT_MAP","field":kind,"record_id":str(nonempty),
                "original_key_hash":sha(old.encode("utf-8")),"ko":val
            })
            result.append(row)
        counts[kind]=nonempty
    return result,counts

def flatten_yaml(obj,prefix=""):
    if isinstance(obj,dict):
        for key,value in obj.items():
            k=(prefix+"." if prefix else "")+str(key)
            yield from flatten_yaml(value,k)
    elif isinstance(obj,str):
        yield prefix,obj

def l10n_rows(z):
    result=[]
    counts={}
    for member in z.namelist():
        if not member.startswith(MOD_ROOT+"l10n/") or not member.endswith("/ko.yaml"):
            continue
        raw=z.read(member)
        data=yaml.safe_load(raw.decode("utf-8-sig"))
        field=member[len(MOD_ROOT):]
        common=base_row(member,raw)
        count=0
        for key,val in flatten_yaml(data):
            if not KOREAN.search(val): continue
            count+=1
            row=dict(common)
            row.update({
                "source_language":"key","record":"L10N","field":field,
                "record_id":key,"localized_value_sha256":sha(val.encode("utf-8")),"ko":val
            })
            result.append(row)
        counts[field]=count
    return result,counts

def main():
    raw=get(RELEASE+FILENAME)
    assert sha(raw)==EXPECTED_ZIP_SHA,"Release ZIP changed since audited source"
    checksum=get(RELEASE+FILENAME+".sha256").decode("utf-8-sig").split()[0].lower()
    assert checksum==sha(raw),"Official published SHA256 mismatch"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        esp,records,new_pairs=esp_rows(z,source_pairs())
        maps,mapcounts=map_rows(z)
        l10n,l10ncounts=l10n_rows(z)
    allrows=esp+maps+l10n
    assert all(row.get("ko") and KOREAN.search(row["ko"]) for row in allrows)
    assert len(allrows)>45000,"Suspicious corpus size"
    # Identity: physical byte positions for ESP, key hashes for maps, keys for YAML.
    identities=set()
    for row in allrows:
        if row["record"]=="L10N":
            identity=(row["source_archive_member"],row["record_id"])
        elif row["record"]=="OPENMW_TEXT_MAP":
            identity=(row["source_archive_member"],row["record_id"])
        else:
            identity=(row["source_archive_member"],row["subrecord_data_offset"])
        if identity in identities: raise ValueError("Duplicate archive key: "+repr(identity))
        identities.add(identity)
    OUT.mkdir(parents=True,exist_ok=True)
    dest=OUT/"translation.jsonl"
    dest.write_text("".join(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n" for row in allrows),encoding="utf-8")
    baseline=json.loads((ROOT/"Morrowind/BaseGame/KR9/metadata.json").read_text("utf-8"))
    manifest={
        "game":"morrowind","release":TAG,"source_release_zip":RELEASE+FILENAME,
        "source_release_zip_sha256":sha(raw),"source_esp_sha256":EXPECTED_ESP_SHA,
        "status":"imported_not_game_verified",
        "source_english_included":False,"english_source_hash_available":False,
        "korean_esp_fields":len(esp),"korean_text_map_fields":len(maps),
        "korean_openmw_l10n_fields":len(l10n),"korean_archive_rows_total":len(allrows),
        "source_record_count":records,"text_map_breakdown":mapcounts,
        "l10n_breakdown":l10ncounts,
        "new_record_field_pairs_with_hangul_not_imported":[
            {"record":k[0],"field":k[1],"count":v} for k,v in new_pairs.most_common()
        ],
        "version_policy":"KR9 kept as historical snapshot; KR12.4 is separate current source.",
        "previous_kr9_rows_retained":baseline["korean_archive_rows_total"],
        "source_english_alignment":False,
        "hash_semantics":"Localized field hashes refer to Korean source bytes, not English originals."
    }
    (OUT/"metadata.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
