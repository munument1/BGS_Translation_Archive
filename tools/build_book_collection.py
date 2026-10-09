#!/usr/bin/env python3
"""Build Korean book anthologies from user-maintained Elder Scrolls translation sources."""
import argparse
import csv
import hashlib
import html
import json
import re
import struct
import zipfile
from pathlib import Path
from collections import defaultdict

KOREAN = re.compile(r"[가-힣]")
GAMES = {"daggerfall":"II. Daggerfall", "morrowind":"III. Morrowind",
         "oblivion":"IV. Oblivion", "skyrim":"V. Skyrim"}
OBLIVION_PLUGINS = {x.lower() for x in (
 "Oblivion.esm","Knights.esp","DLCBattlehornCastle.esp","DLCFrostcrag.esp",
 "DLCThievesDen.esp","DLCSpellTomes.esp","DLCMehrunesRazor.esp","DLCVileLair.esp",
 "DLCOrrery.esp","DLCHorseArmor.esp","DLCShiveringIsles.esp")}
GH = "https://github.com/munument1/"

def norm(s):
    s=html.unescape(str(s)).replace("\x00","").replace("\r\n","\n")
    s=re.sub(r"<br\s*/?>","\n",s,flags=re.I)
    s=re.sub(r"</?(?:font|p|div|span|body|html)[^>]*>","",s,flags=re.I)
    s=re.sub(r"\[/?(?:center|left|right|font(?:=\d+)?)\]","",s,flags=re.I)
    return re.sub(r"\n{4,}","\n\n\n",s).strip()

def entry(game,book_id,title,body,url,**kw):
    return {"game":game,"record":"BOOK","field":"DESC","book_id":str(book_id),
            "title_ko":norm(title) or str(book_id),"ko":norm(body),
            "source_language":"en","content_language":"ko","status":"imported",
            "source_ref":url,**kw}

def daggerfall(folder):
    output=[]
    for p in sorted(folder.glob("BOK*-LOC.txt")):
        raw=p.read_text(encoding="utf-8-sig")
        match=re.search(r"(?m)^Content:\s*\n",raw)
        if match is None: raise ValueError("Missing Content: "+p.name)
        header,body=raw[:match.start()],raw[match.end():]
        fields=dict(re.findall(r"(?m)^([A-Za-z]+):[ \t]*(.*)$",header))
        if KOREAN.search(body):
            output.append(entry("daggerfall",p.stem.replace("-LOC",""),
                fields.get("Title",p.stem),body,
                GH+"-KR-Daggerfall_Unity/blob/main/text/Books/"+p.name,
                author_ko=fields.get("Author","").strip()))
    return output

def oblivion(file):
    allbooks={}
    with file.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        assert {"record_type","field","raw_formid","new_korean"}.issubset(r.fieldnames)
        for n,row in enumerate(r,2):
            if row.get("record_type","").upper()!="BOOK": continue
            plugin=(row.get("effective_source") or "").strip()
            if plugin.lower() not in OBLIVION_PLUGINS: continue
            field=row.get("field","").upper()
            if field not in ("FULL","DESC"): continue
            ko=(row.get("new_korean") or "").strip()
            if not ko: continue
            fid=(row.get("raw_formid") or "").upper()
            if not fid: raise ValueError("No FormID at line "+str(n))
            key=(plugin,fid)
            b=allbooks.setdefault(key,entry("oblivion",plugin+":"+fid,fid,"",
                GH+"-KR-Oblivion-Translation/blob/main/canonical_translation_v2.csv",
                plugin=plugin,form_id=fid))
            if field=="FULL": b["title_ko"]=norm(ko)
            if field=="DESC":
                try: idx=int(row.get("occurrence") or 0)
                except ValueError: idx=0
                b.setdefault("_parts",[]).append((idx,n,ko))
            if row.get("editor_id"): b["editor_id"]=row["editor_id"]
    books=[]
    for b in allbooks.values():
        b["ko"]=norm("\n".join(x[2] for x in sorted(b.pop("_parts",[]))))
        if KOREAN.search(b["ko"]):
            if not b["title_ko"] or b["title_ko"]==b["form_id"]:
                b["title_ko"]=b.get("editor_id") or b["form_id"]
            books.append(b)
    return books

def decode(raw):
    for enc in ("utf-8-sig","cp949","cp1252"):
        try: return raw.rstrip(b"\x00").decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode("utf-8","replace")

def morrowind(file):
    result={}
    with zipfile.ZipFile(file) as z:
        plugins=sorted((i for i in z.infolist() if i.filename.lower().endswith((".esp",".esm"))),
                       key=lambda x:("morrowind_korean_retranslation.esp" not in x.filename.lower(),x.filename))
        if not plugins: raise ValueError("No TES3 ESP in Korean OpenMW package")
        for info in plugins:
            raw=z.read(info)
            off=0
            while off+16<=len(raw):
                tag,size,_,_=struct.unpack_from("<4sIII",raw,off)
                off+=16
                if off+size>len(raw): raise ValueError("Invalid TES3 record size")
                if tag==b"BOOK":
                    sub={}
                    pos=off
                    while pos+8<=off+size:
                        t,length=struct.unpack_from("<4sI",raw,pos)
                        pos+=8
                        if pos+length>off+size: raise ValueError("Invalid TES3 subrecord")
                        sub[t]=raw[pos:pos+length]
                        pos+=length
                    bid=decode(sub.get(b"NAME",b""))
                    title=decode(sub.get(b"FNAM",b""))
                    body=decode(sub.get(b"TEXT",b""))
                    if bid and body and KOREAN.search(title+body):
                        result.setdefault(bid.lower(),entry("morrowind",bid,title,body,
                            GH+"-KR-openmw/releases/tag/openmw-0.51.0-kr4",
                            plugin=Path(info.filename).name))
                off+=size
    return list(result.values())

def skyrim(folder):
    output={}
    if not folder.exists(): return []
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower()==".jsonl":
            with p.open(encoding="utf-8-sig") as f: rows=[json.loads(x) for x in f if x.strip()]
        elif p.suffix.lower()==".csv":
            with p.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
        else: continue
        for row in rows:
            if str(row.get("record",row.get("record_type",""))).upper()!="BOOK": continue
            if str(row.get("field","DESC")).upper() not in ("DESC","TEXT",""): continue
            fid=row.get("form_id") or row.get("raw_formid") or row.get("book_id")
            body=row.get("ko") or row.get("new_korean")
            if fid and body and KOREAN.search(str(body)):
                plugin=row.get("plugin","Skyrim.esm")
                output[(plugin,str(fid))]=entry("skyrim",fid,
                    row.get("title_ko") or row.get("title") or fid,body,
                    row.get("source_ref") or str(p),
                    plugin=plugin,form_id=str(fid),editor_id=row.get("editor_id",""))
    return list(output.values())

def render(book):
    title=book["title_ko"].replace("\n"," ").replace("#",r"\#")
    details=["ID: "+book["book_id"]]
    if book.get("author_ko"): details.append("저자: "+book["author_ko"])
    if book.get("plugin"): details.append("플러그인: "+book["plugin"])
    source=book["source_ref"]
    credit="[출처]("+source+")" if source.startswith("https://") else "출처: "+source
    return "## "+title+"\n\n"+" / ".join(details)+"\n\n"+book["ko"].replace("\n","  \n")+"\n\n"+credit+"\n\n---\n\n"


def file_name(book):
    """Stable and collision-resistant, compatible with Windows filenames."""
    key="/".join((book["game"],book.get("plugin",""),book["book_id"]))
    safe_id=re.sub(r"[^A-Za-z0-9가-힣._-]+","-",book["book_id"]).strip("-.")[:52]
    safe_title=re.sub(r"[^A-Za-z0-9가-힣._-]+","-",book["title_ko"]).strip("-.")[:54]
    identifier=hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"{safe_id or 'book'}-{safe_title or 'untitled'}-{identifier}.md"


def export(root,game,books):
    d=root/game
    d.mkdir(parents=True,exist_ok=True)
    books.sort(key=lambda b:(b.get("plugin",""),b["title_ko"],b["book_id"]))
    intro="# The Elder Scrolls "+GAMES[game]+" 한국어 서적 합본\n\n"
    if not books:
        (d/"index.md").write_text(intro+"현재 사용 가능한 한국어 서적 본문 자료가 없어 보류 중입니다.\n",encoding="utf-8")
        return {"game":game,"books":0,"individual_files":0,"available":False}
    intro+=f"수록 서적: {len(books):,}건. 기존 번역 데이터를 추출한 상태이며 인게임 전수 검수를 의미하지 않습니다.\n\n---\n\n"
    full=intro+"".join(map(render,books))
    (d/"complete.md").write_text(full,encoding="utf-8")
    with (d/"books.jsonl").open("w",encoding="utf-8",newline="\n") as f:
        for b in books: f.write(json.dumps(b,ensure_ascii=False,sort_keys=True)+"\n")

    # Every book has a directly-linkable file in addition to complete/part collections.
    individual=d/"books"
    individual.mkdir(exist_ok=True)
    index_rows=[]
    filenames=set()
    for book in books:
        name=file_name(book)
        normalized=name.casefold()
        if normalized in filenames:
            raise ValueError("Duplicate individual book filename: "+name)
        filenames.add(normalized)
        single=render(book).replace("## ","# ",1)
        single=single.rsplit("\n---\n",1)[0].rstrip()+"\n"
        (individual/name).write_text(single,encoding="utf-8")
        title=book["title_ko"].replace("\n"," ").replace("[",r"\[").replace("]",r"\]")
        index_rows.append(f"- [{title}](books/{name}) — {book['book_id']}")

    parts=[]
    for i in range(0,len(books),40):
        name=f"part-{i//40+1:02d}.md"
        (d/name).write_text(intro+"".join(map(render,books[i:i+40])),encoding="utf-8")
        parts.append(f"- [{i+1}~{min(len(books),i+40)}권]({name})")
    (d/"index.md").write_text(intro+
        "[전체 합본](complete.md) · [JSONL](books.jsonl)\n\n"+
        "### 개별 서적 파일\n\n"+
        f"총 {len(books):,}개의 독립 Markdown 파일 (books/). 제목을 선택하면 해당 책만 열립니다.\n\n"+
        "\n".join(index_rows)+"\n\n"+
        "### 40권 단위 분할 열람\n\n"+"\n".join(parts)+"\n",encoding="utf-8")
    return {"game":game,"books":len(books),"individual_files":len(filenames),"available":True,
            "sha256":hashlib.sha256(full.encode()).hexdigest()}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--daggerfall",type=Path,required=True)
    ap.add_argument("--morrowind-zip",type=Path,required=True)
    ap.add_argument("--oblivion",type=Path,required=True)
    ap.add_argument("--root",type=Path,default=Path("."))
    a=ap.parse_args()
    source={"daggerfall":daggerfall(a.daggerfall),"morrowind":morrowind(a.morrowind_zip),
            "oblivion":oblivion(a.oblivion),"skyrim":skyrim(a.root/"sources"/"skyrim_books")}
    for g in ("daggerfall","morrowind","oblivion"):
        if not source[g]: raise ValueError("Source extraction produced zero books: "+g)
    root=a.root/"docs"/"books"
    root.mkdir(parents=True,exist_ok=True)
    results=[export(root,g,source[g]) for g in GAMES]
    manifest={"schema_version":1,"games":results,
        "sources":{"daggerfall":GH+"-KR-Daggerfall_Unity","morrowind":GH+"-KR-openmw/releases/tag/openmw-0.51.0-kr4",
          "oblivion":GH+"-KR-Oblivion-Translation","skyrim":"sources/skyrim_books (not supplied)"}}
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# 엘더 스크롤 한국어 서적 아카이브","","각 작품의 한국어 서적 본문을 합본 Markdown과 JSONL로 정리합니다.","",
           "| 게임 | 수록 | 열람 |","|---|---:|---|"]
    for item in results:
        g=item["game"]; count=f'{item["books"]:,}권' if item["available"] else "자료 미확보"
        lines.append(f"| {GAMES[g]} | {count} | [열기]({g}/index.md) |")
    lines.extend(["","각 게임의 books/ 폴더에 서적 1권당 Markdown 1개를 보관하며 index.md에서 개별로 찾아볼 수 있습니다.",
      "complete.md가 전체 합본이고, part-XX.md는 40권 단위 분할본입니다.",
      "스카이림 한국어 STRINGS는 로컬에서 확인했지만 해당 문자열을 BOOK FormID와 연결할 게임 플러그인(ESM/ESL)은 아직 확보되지 않았습니다.",
      "tools/extract_skyrim_books.py로 게임 플러그인과 번역 STRINGS를 대조해 sources/skyrim_books에 BOOK JSONL을 가져오면 자동 반영됩니다.",
      "","번역 데이터의 원본 출처와 재배포 조건을 존중해야 합니다. 영어 서적 본문 전문은 포함하지 않습니다.",""])
    (root/"README.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False))

if __name__=="__main__": main()
