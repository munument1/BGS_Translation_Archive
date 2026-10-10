#!/usr/bin/env python3
"""Build BIBLIOGRAPHIC (not copyrighted full-text) game-book references.

No books or journals are redistributed from Imperial Library or EPUB files.
The EPUB input's NCX/TOC labels are read; chapter XHTML bodies are never opened.
"""
import argparse
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT_URL="https://www.imperial-library.info/game-books/"
ESO_LIST=ROOT_URL+"elder-scrolls-online-books"
MIN_ESO=2000

def key(s):
    return re.sub(r"[^a-z0-9]+","",unicodedata.normalize("NFKC",s).casefold())

def epub_titles(epub_path):
    with zipfile.ZipFile(epub_path) as z:
        toc_files=[name for name in z.namelist() if name.casefold().endswith(".ncx")]
        if not toc_files: raise ValueError("No NCX title-only table of contents in EPUB")
        tree=ET.fromstring(z.read(toc_files[0]))
        rows=[]
        for node in tree.iter():
            if node.tag.rsplit("}",1)[-1]!="navPoint":continue
            title=""
            for child in node.iter():
                if child.tag.rsplit("}",1)[-1]=="text" and (child.text or "").strip():
                    title=child.text.strip()
                    break
            if not title or title.casefold() in {"title page","cover"}:continue
            rows.append(title)
        if len(rows)<MIN_ESO: raise ValueError(f"ESO title index incomplete: {len(rows)}")
        return rows

def make_record(game,title,index,source_url,source_description,title_ko="",direct_url=None):
    uid=hashlib.sha256(f"{game}\x00{index}\x00{title}".encode()).hexdigest()[:20]
    return {
        "uid":"ext-"+uid,
        "game":game,
        "title_en":title,
        "title_ko":title_ko,
        "source_url":direct_url or source_url,
        "collection_url":source_url,
        "direct_link":bool(direct_url),
        "source_description":source_description,
        "status":"bibliography_only",
        "translation_status":"untranslated",
        "translation_complete":False,
        "rights_reviewed":False,
        "full_text_included":False,
        "body_en":None,
        "body_ko":None,
        "source_text_access":"external_link_only",
    }

def build(epub,curated,known_refs):
    refs=json.loads(curated.read_text(encoding="utf-8"))
    previous=json.loads(known_refs.read_text(encoding="utf-8"))
    known={key(x["title_en"]):x for x in previous["items"] if x["game"]=="eso"}
    rows=[]
    for i,title in enumerate(epub_titles(epub),1):
        k=known.get(key(title),{})
        rows.append(make_record("eso",title,i,ESO_LIST,
            "The Elder Scrolls Tomes EPUB NCX (bibliographic titles only)",
            title_ko=k.get("title_ko",""),direct_url=k.get("url")))
    counts={"eso":len(rows)}
    for game,collection in refs["groups"].items():
        listing=collection.get("items",[])
        if not listing:
            listing=[{"title_en":title} for title in collection.get("titles",[])]
        source_url=collection.get("source_url") or collection.get("url")
        seen_urls=set()
        for i,item in enumerate(listing,1):
            title=item.get("title_en") or item.get("title")
            url=item.get("url")
            if url and url in seen_urls:
                raise ValueError(f"Repeated source URL in {game}: {url}")
            if url: seen_urls.add(url)
            rows.append(make_record(game,title,i,source_url,
                "The Imperial Library Game Books public category index",
                direct_url=url))
        counts[game]=len(listing)
    return {
        "schema_version":1,
        "title":"The Imperial Library — additional game books bibliography",
        "notice_ko":"서지 색인입니다. ESO 일반 서적은 공개 EPUB 목차, 나머지 네 게임/문서 분류는 The Imperial Library 원문 목록 페이지의 제목과 개별 링크입니다. 본문은 포함하지 않습니다.",
        "original_sources":{
            "battlespire":ROOT_URL+"tesl-battlespire-books",
            "redguard":ROOT_URL+"tesa-redguard-books",
            "shadowkey":ROOT_URL+"tes-travels-shadowkey-books",
            "eso":ESO_LIST,
            "eso_journals":ROOT_URL+"elder-scrolls-online-books-journals-notes-and-letters"
        },
        "counts":counts,"total":len(rows),"entries":rows
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--eso-epub",type=Path,required=True)
    ap.add_argument("--curated",type=Path,default=Path("sources/imperial_library/live_indexes.json"))
    ap.add_argument("--known",type=Path,default=Path("docs/books/external_candidates.json"))
    ap.add_argument("--output",type=Path,default=Path("docs/books/imperial_game_books_catalog.json"))
    args=ap.parse_args()
    doc=build(args.eso_epub,args.curated,args.known)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"total":doc["total"],"counts":doc["counts"],
        "direct_urls":sum(x["direct_link"] for x in doc["entries"])},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
