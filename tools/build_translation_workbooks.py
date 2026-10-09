#!/usr/bin/env python3
"""Create per-book translation workspaces from public bibliographic records.

Never fetches external bodies. Never publishes game text. Existing translations
are not overwritten; the source catalog remains authoritative for references.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import quote

SHELVES = {
    "battlespire": "Battlespire / 배틀스파이어",
    "redguard": "Redguard / 레드가드",
    "shadowkey": "Shadowkey / 섀도키",
    "eso": "The Elder Scrolls Online / ESO 일반 서적",
    "eso_journals": "ESO Journals, Notes & Letters / ESO 일지·쪽지·편지",
}
WINDOWS_RESERVED = {"CON","PRN","AUX","NUL", *{f"COM{i}" for i in range(1,10)}, *{f"LPT{i}" for i in range(1,10)}}
INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

def title_filename(title: str) -> str:
    """Use the book's title alone; no serial numbers or hashes in the basename."""
    title = unicodedata.normalize("NFC", str(title)).strip()
    title = re.sub(r"\s+", " ", INVALID.sub(" ", title)).strip(" .")
    if not title:
        title = "Untitled"
    if title.split(".")[0].upper() in WINDOWS_RESERVED:
        title = "Book " + title
    while len((title + ".md").encode("utf-8")) > 230:
        title = title[:-1].rstrip(" .")
    return title + ".md"

def escape_md(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")

def create_workbooks(catalog: dict, root: Path) -> dict:
    entries = catalog["entries"]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in entries:
        game = item["game"]
        if game not in SHELVES:
            raise ValueError(f"Unknown game: {game}")
        if item.get("translation_status") != "untranslated":
            raise ValueError(f"Non-untranslated item: {item['uid']}")
        if item.get("body_en") is not None or item.get("body_ko") is not None:
            raise ValueError("Source or translation bodies must not be present in metadata catalog")
        grouped[game].append(item)
    all_ids = set()
    manifest = {"schema_version":1, "total":0, "games":{}}
    for game, title in SHELVES.items():
        books = sorted(grouped[game], key=lambda e:(e["title_en"].casefold(),e["uid"]))
        counter = Counter(title_filename(b["title_ko"] or b["title_en"]).casefold() for b in books)
        seen_paths = set()
        index = [f"# {title}", "", f"총 {len(books):,}건 · 미번역 작업 목록", "",
                 "[외부 출처 검색](../../imperial-library.html) · [메인 도서관](../../index.html)", "",
                 "> 이 폴더는 서지 정보와 번역 작업 틀만 포함합니다. 원문 전문을 저장하지 않습니다.", ""]
        created = 0
        for b in books:
            uid = b["uid"]
            if uid in all_ids:
                raise ValueError("Duplicated record UID: " + uid)
            all_ids.add(uid)
            fn = title_filename(b["title_ko"] or b["title_en"])
            # Same-titled distinct books get the same clean filename under
            # separate short UID folders, avoiding destructive overwrites.
            rel = Path("books") / fn if counter[fn.casefold()] == 1 \
                else Path("books") / "동명서적" / uid / fn
            lower = rel.as_posix().casefold()
            if lower in seen_paths:
                raise ValueError("Case-folded path collision: "+str(rel))
            seen_paths.add(lower)
            target = root / game / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            source = b["source_url"]
            collection = b.get("collection_url",source)
            if not source.startswith("https://www.imperial-library.info/"):
                raise ValueError("Unexpected external source: "+source)
            doc = (
                f"# {escape_md(b['title_ko'] or b['title_en'])}\n\n"
                "**번역 상태:** 미번역\n\n"
                f"**시리즈:** {SHELVES[game]}\n\n"
                f"**원문 제목:** {escape_md(b['title_en'])}\n\n"
                f"**서지 식별자:** {uid}\n\n"
                f"**원문 출처:** [Imperial Library {'개별 서적' if b.get('direct_link') else '게임별 색인'}]({source})\n\n"
                f"**출처 분류:** [게임별 목록]({collection})\n\n"
                "**원문 본문:** 미수록 (외부 출처에서 확인)\n\n"
                "## 한국어 번역\n\n"
                "_미번역. 원문을 검토한 뒤 번역문을 작성하세요. 공개 게시 전 권리·출처를 확인해야 합니다._\n\n"
                "## 검수 메모\n\n"
                "- [ ] 원문 및 해당 권 확인\n"
                "- [ ] 다른 작품의 동일 서적과 중복 대조\n"
                "- [ ] 용어 사전 적용\n"
                "- [ ] 문맥 및 고유명사 검수\n"
                "- [ ] 공개 재배포 조건 확인\n"
            )
            if not target.exists():  # Never overwrite human translation work.
                target.write_text(doc, encoding="utf-8")
                created += 1
            index.append(f"- [{escape_md(b['title_ko'] or b['title_en'])}]({quote(rel.as_posix(),safe='/')})"
                         + (" · 개별 출처" if b.get("direct_link") else " · 게임별 원문 색인"))
        folder = root / game
        folder.mkdir(parents=True,exist_ok=True)
        (folder/"index.md").write_text("\n".join(index)+"\n",encoding="utf-8")
        manifest["games"][game] = {"books":len(books),"new_workbooks":created}
        manifest["total"] += len(books)
    if manifest["total"] != catalog["total"]:
        raise ValueError(f"Unexpected total: {manifest['total']} != {catalog['total']}")
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog",type=Path,default=Path("docs/books/imperial_game_books_catalog.json"))
    parser.add_argument("--root",type=Path,default=Path("docs/untranslated"))
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    print(json.dumps(create_workbooks(catalog,args.root),ensure_ascii=False))

if __name__=="__main__":
    main()
