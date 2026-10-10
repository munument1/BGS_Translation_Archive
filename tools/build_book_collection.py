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

def book_filename(book):
    """Only the translated title appears in the filename (no ID/hash suffix)."""
    import unicodedata
    name=unicodedata.normalize("NFC",str(book.get("title_ko") or book["title_en"])).strip()
    name=re.sub(r'[<>:"/\\|?*#%\x00-\x1f]'," ",name)
    name=re.sub(r"\s+"," ",name).strip(" .")
    if not name:
        name="제목 미확인"
    if name.upper().split(".")[0] in {"CON","PRN","AUX","NUL","COM1","COM2","LPT1","LPT2"}:
        name="서적 "+name
    # Keep the UTF-8 basename under the 255-byte file-system limit.
    while len((name+".md").encode("utf-8"))>245:
        name=name[:-1].rstrip(" .")
    return name+".md"


def safe_segment(value):
    value=re.sub(r'[^A-Za-z0-9가-힣._-]',"_",str(value)).strip("._")
    # Never let .esp/.esm/.esl-like directory names match repository ignore patterns.
    return (value.replace(".", "_")[:80] or "unknown")


def render(book):
    title=(book.get("title_ko") or book["title_en"]).replace("\n"," ").replace("#",r"\#")
    details=["ID: "+book["book_id"]]
    if book.get("author_ko"): details.append("저자: "+book["author_ko"])
    if book.get("plugin"): details.append("플러그인: "+book["plugin"])
    source=book["source_ref"]
    credit="[출처]("+source+")" if source.startswith("https://") else "출처: "+source
    body=book.get("ko") or book.get("en","")
    return "## "+title+"\n\n"+" / ".join(details)+"\n\n"+body.replace("\n","  \n")+"\n\n"+credit+"\n\n---\n\n"


def export(root,game,books,language_label="한국어",game_label=None,source_note=None):
    import shutil
    from collections import Counter
    from urllib.parse import quote
    d=root/game
    d.mkdir(parents=True,exist_ok=True)
    books.sort(key=lambda b:(b.get("plugin",""),b.get("title_ko") or b["title_en"],b["book_id"]))
    intro="# The Elder Scrolls "+(game_label or GAMES[game])+" "+language_label+" 서적 합본\n\n"
    if not books:
        (d/"index.md").write_text(intro+"현재 사용 가능한 한국어 서적 본문 자료가 없어 보류 중입니다.\n",encoding="utf-8")
        return {"game":game,"books":0,"individual_files":0,"duplicate_titles":0,"available":False}
    intro+=f"수록 서적: {len(books):,}건. "+(source_note or "기존 번역 데이터를 추출한 상태이며 인게임 전수 검수를 의미하지 않습니다.")+"\n\n---\n\n"
    full=intro+"".join(map(render,books))
    (d/"complete.md").write_text(full,encoding="utf-8")

    names=[book_filename(b) for b in books]
    duplicates=Counter(name.casefold() for name in names)
    # Clean only generated per-book files, never source material or shared docs.
    individual=d/"books"
    if individual.exists():
        shutil.rmtree(individual)
    individual.mkdir()
    index_rows=[]
    paths=set()
    for book,name in zip(books,names):
        if duplicates[name.casefold()]>1:
            # Conflicting book titles keep the SAME clean filename; only the
            # containing directory distinguishes the two distinct records.
            rel=Path("books")/"동명이서적"/safe_segment(book.get("plugin","game"))/safe_segment(book["book_id"])/name
        else:
            rel=Path("books")/name
        key=rel.as_posix().casefold()
        if key in paths: raise ValueError("Book file path collision: "+str(rel))
        paths.add(key)
        filepath=d/rel
        filepath.parent.mkdir(parents=True,exist_ok=True)
        single=render(book).replace("## ","# ",1)
        filepath.write_text(single.rsplit("\n---\n",1)[0].rstrip()+"\n",encoding="utf-8")
        book["file_path"]=rel.as_posix()
        title=(book.get("title_ko") or book["title_en"]).replace("\n"," ").replace("[",r"\[").replace("]",r"\]")
        index_rows.append(f"- [{title}]({quote(rel.as_posix(),safe='/')}) — {book['book_id']}")
    with (d/"books.jsonl").open("w",encoding="utf-8",newline="\n") as f:
        for book in books:
            f.write(json.dumps(book,ensure_ascii=False,sort_keys=True)+"\n")
    parts=[]
    for i in range(0,len(books),40):
        name=f"part-{i//40+1:02d}.md"
        (d/name).write_text(intro+"".join(map(render,books[i:i+40])),encoding="utf-8")
        parts.append(f"- [{i+1}~{min(len(books),i+40)}권]({name})")
    (d/"index.md").write_text(intro+
        "[웹 도서관](../../index.html) · [전체 합본](complete.md) · [JSONL](books.jsonl)\n\n"+
        "### 개별 서적 파일\n\n"+
        f"총 {len(books):,}개의 독립 Markdown 파일. 파일명은 책 제목만 사용합니다.\n"+
        "같은 제목의 서로 다른 책은 동명이서적 하위 폴더에서 구분합니다.\n\n"+
        "\n".join(index_rows)+"\n\n"+
        "### 40권 단위 분할 열람\n\n"+"\n".join(parts)+"\n",encoding="utf-8")
    return {"game":game,"books":len(books),"individual_files":len(paths),
            "duplicate_titles":sum(v for v in duplicates.values() if v>1),"available":True,
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
    # Small fast catalog for navigation; body text is indexed separately to
    # keep the first web page load light. Reader fetches one Markdown file.
    metadata=[]
    fulltext=[]
    for game in GAMES:
        for b in source[game]:
            uid=hashlib.sha256((game+"\x1f"+b.get("plugin","")+"\x1f"+b["book_id"]).encode("utf-8")).hexdigest()[:20]
            metadata.append({
                "uid":uid,"game":game,"title":b["title_ko"],
                "author":b.get("author_ko",""),
                "plugin":b.get("plugin",""),
                "record_id":b["book_id"],
                "path":game+"/"+b["file_path"],
                "source":b["source_ref"],
                "preview":" ".join(b["ko"].split())[:185],
                "length":len(b["ko"])
            })
            fulltext.append({"uid":uid,"text":b["ko"]})
    metadata.sort(key=lambda x:(list(GAMES).index(x["game"]),x["title"],x["record_id"]))
    (root/"catalog.json").write_text(json.dumps({
        "schema_version":1,"books":metadata,"counts":{r["game"]:r["books"] for r in results}
    },ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    (root/"fulltext-index.json").write_text(
        json.dumps(fulltext,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    manifest={"schema_version":1,"games":results,
        "sources":{"daggerfall":GH+"-KR-Daggerfall_Unity","morrowind":GH+"-KR-openmw/releases/tag/openmw-0.51.0-kr4",
          "oblivion":GH+"-KR-Oblivion-Translation","skyrim":"sources/skyrim_books (localized BOOK JSONL)"}}
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# 엘더 스크롤 한국어 서적 아카이브","","각 작품의 한국어 서적 본문을 합본 Markdown과 JSONL로 정리합니다.","",
           "| 게임 | 수록 | 열람 |","|---|---:|---|"]
    for item in results:
        g=item["game"]; count=f'{item["books"]:,}권' if item["available"] else "자료 미확보"
        lines.append(f"| {GAMES[g]} | {count} | [열기]({g}/index.md) |")
    lines.extend(["","[검색과 서적 읽기 기능이 있는 GitHub Pages](../index.html)",
      "각 게임의 books/ 폴더에 번역된 서적 제목만 사용한 Markdown 파일 1개씩 보관합니다.",
      "complete.md가 전체 합본이고, part-XX.md는 40권 단위 분할본입니다.",
      "스카이림은 사용자가 제공한 ESM/ESL과 한국어 STRINGS를 대조해 BOOK 레코드를 JSONL로 수록했습니다.",
      "tools/extract_skyrim_books_node.cjs에서 추출한 한국어 서적 레코드는 sources/skyrim_books/에서 확인할 수 있습니다.",
      "[The Imperial Library의 추가 서적 출처와 후보](../imperial-library.html) — 외부 참조 링크만 포함하며 번역 본문에는 합산하지 않습니다.",
      "[확장 및 저작권 검토 정책](EXTERNAL_SOURCES.md)",
      "","번역 데이터의 원본 출처와 재배포 조건을 존중해야 합니다. 영어 서적 본문 전문은 포함하지 않습니다.",""])
    (root/"README.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(results,ensure_ascii=False))

if __name__=="__main__": main()
