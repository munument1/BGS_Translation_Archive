#!/usr/bin/env python3
"""Private, resumable source-text fetcher for The Imperial Library.

- Only URLs from the checked-in bibliographic index are fetched.
- Obeys the site's robots.txt and >=10.5-second request spacing.
- Never uploads source texts; files are written to Git-ignored work/.
- Run manually in small batches for translation reference, with permitted uses.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

SITE = "https://www.imperial-library.info"
UA = "TamrielArchive-TranslationResearch/1.0 (noncommercial personal study)"
GAMES = ("battlespire", "redguard", "shadowkey", "eso_journals")

def read_robots(session: requests.Session) -> tuple[RobotFileParser, float]:
    r = session.get(SITE + "/robots.txt", timeout=30)
    r.raise_for_status()
    robot = RobotFileParser()
    robot.parse(r.text.splitlines())
    return robot, max(10.5, float(robot.crawl_delay(UA) or 0))

def content_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    area = soup.select_one("article .entry-content") or soup.select_one(".entry-content")
    if area is None:
        return ""
    for child in area.select("script,style,iframe,form,nav,aside"):
        child.decompose()
    return "\n".join(
        line for line in (x.strip() for x in area.get_text("\n", strip=True).splitlines()) if line
    ).strip()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path,
                        default=Path("sources/imperial_library/live_indexes.json"))
    parser.add_argument("--out", type=Path,
                        default=Path("work/imperial_library_originals"))
    parser.add_argument("--game", choices=GAMES + ("all",), default="all")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max new pages to fetch in this invocation (1–50)")
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("--limit must be 1 to 50; run again to resume the next batch")
    source = json.loads(args.catalog.read_text(encoding="utf-8"))
    output = args.out.resolve()
    private = Path("work").resolve()
    if not output.is_relative_to(private):
        parser.error("Output must be under Git-ignored work/ directory")
    session = requests.Session()
    session.headers["User-Agent"] = UA
    session.headers["Accept-Language"] = "en-US,en;q=0.9"
    robots, delay = read_robots(session)
    print("Robots.txt checked; delay between requests:", delay, "seconds", flush=True)
    targets = []
    for game in GAMES:
        if args.game not in ("all", game):
            continue
        for record in source["groups"][game]["items"]:
            url = record["url"]
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.netloc != "www.imperial-library.info" or not parsed.path.startswith("/content/"):
                raise ValueError("Unexpected source URL: " + url)
            filename = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16] + ".txt"
            target = output / game / filename
            if target.exists():
                continue
            if not robots.can_fetch(UA, url):
                print("Blocked by robots.txt:", url, flush=True)
                continue
            targets.append((game, record["title_en"], url, target))
    fetched = saved = failed = 0
    report_path = output / "_crawl_progress.jsonl"
    output.mkdir(parents=True, exist_ok=True)
    for game, title, url, target in targets:
        if fetched >= args.limit:
            break
        if fetched:
            time.sleep(delay)
        fetched += 1
        status, body = "error", ""
        try:
            response = session.get(url, timeout=45)
            response.raise_for_status()
            body = content_from_html(response.content.decode("utf-8", errors="replace"))
            if len(body) < 30:
                status = "no_readable_body"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Never replace a translator's existing source notes.
                with target.open("x", encoding="utf-8") as f:
                    f.write("TITLE: " + title + "\nSOURCE: " + url + "\n\n" + body + "\n")
                status = "saved"
                saved += 1
        except Exception as exc:
            status = "error: " + type(exc).__name__ + ": " + str(exc)[:120]
            failed += 1
        with report_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"game":game,"title":title,"url":url,"status":status,
                                "chars":len(body)},ensure_ascii=False)+"\n")
        print(game, "attempt", fetched, "of", args.limit, status, title[:75], flush=True)
        if status.startswith("error") and ("429" in status or "403" in status):
            print("Stopping on rate limit/access denial", flush=True)
            break
    print(json.dumps({"new_requests":fetched,"saved":saved,"failed":failed,
                      "output":str(output),"remaining_candidates_before_run":len(targets)},
                     ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
