#!/usr/bin/env python3
"""Import user-provided HTTrack files without making network requests.

Keep bibliography stable; publish English in a separate reader dataset and keep
editable source/translation pairs under ignored work/. Ambiguous titles are not
guessed. Librarian commentary is separated from the source text.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urljoin, urlsplit
from zipfile import ZipFile

from bs4 import BeautifulSoup

SITE = 'https://www.imperial-library.info'
INDEXES = {
    'battlespire': 'tesl-battlespire-books',
    'redguard': 'tesa-redguard-books',
    'shadowkey': 'tes-travels-shadowkey-books',
    'eso': 'elder-scrolls-online-books',
    'eso_journals': 'elder-scrolls-online-books-journals-notes-and-letters',
}

def normalize(title):
    title = unicodedata.normalize('NFKC', title).casefold()
    title = title.translate(str.maketrans({'’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-'}))
    return re.sub(r'\s+', ' ', title).strip()

def urlkey(url):
    return unquote(urlsplit(url).path).rstrip('/').removesuffix('.html')

def extract(html, fragment=False):
    if not fragment:
        # HTTrack cache pages can contain nearly 1 MB of unrelated header scripts.
        article = re.search(r'<article\b[^>]*>[\s\S]*?</article>', html, re.I)
        if article:
            html = article.group(0)
    soup = BeautifulSoup(html, 'html.parser')
    area = soup if fragment else soup.select_one('article .entry-content')
    if area is None:
        return '', ''
    notes = '\n\n'.join(x.get_text(' ', strip=True) for x in area.select('.librarian-comment'))
    for node in area.select('script,style,iframe,form,nav,aside,.librarian-comment,.wp-block-rank-math-toc-block'):
        node.decompose()
    for br in area.select('br'):
        br.replace_with('\n')
    for node in area.select('p,h1,h2,h3,h4,h5,h6,li,blockquote,pre,tr,div'):
        node.insert_before('\n\n')
        node.insert_after('\n\n')
    for node in area.select('td,th'):
        node.insert_after(' | ')
    text = area.get_text('')
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip(), notes

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def run(mirror, root):
    if (mirror / 'www.imperial-library.info').is_dir():
        mirror = mirror / 'www.imperial-library.info'
    if not (mirror / 'game-books').is_dir():
        raise ValueError('Expected HTTrack mirror containing game-books/')
    catalog = json.loads((root / 'docs/books/imperial_game_books_catalog.json').read_text(encoding='utf-8'))
    pages, titles, unreadable = {}, defaultdict(set), set()
    # Prefer API content: it retains original HTML and authoritative source URLs.
    for folder in ('posts', 'pages'):
        for path in sorted((mirror / 'wp-json/wp/v2' / folder).glob('*.json')):
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                url = data.get('link', '')
                if urlkey(url).startswith('/content/'):
                    body, notes = extract(data.get('content', {}).get('rendered', ''), True)
                    if body:
                        pages[urlkey(url)] = (body, notes, url, path)
            except (ValueError, AttributeError):
                continue
    for path in sorted((mirror / 'content').rglob('*.html')):
        html = path.read_text(encoding='utf-8')
        match = re.search(r'Mirrored from (https?://\S+) by HTTrack', html[:1500])
        url = match.group(1) if match else SITE + '/' + path.relative_to(mirror).as_posix().removesuffix('.html')
        key = urlkey(url)
        if key in pages:
            continue
        body, notes = extract(html)
        if body:
            pages[key] = (body, notes, url, path)
    for game, name in INDEXES.items():
        path = mirror / 'game-books' / (name + '.html')
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        area = soup.select_one('.entry-content')
        if area is None:
            continue
        for link in area.select('a[href]'):
            url = urljoin(SITE + '/game-books/' + name, link['href'])
            if urlkey(url).startswith('/content/'):
                titles[(game, normalize(link.get_text(' ', strip=True)))].add(urlkey(url))
    required = set()
    for book in catalog['entries']:
        keys = {urlkey(book['source_url'])} if book.get('direct_link') else titles.get((book['game'], normalize(book['title_en'])), set())
        if len(keys) == 1:
            required.update(keys)
    cache = mirror.parent / 'hts-cache/new.zip'
    restored = 0
    if cache.is_file():
        with ZipFile(cache) as archive:
            for info in archive.infolist():
                key = urlkey(info.filename)
                if key not in required or key in pages or not info.file_size:
                    continue
                body, notes = extract(archive.read(info).decode('utf-8', errors='replace'))
                if body:
                    pages[key] = (body, notes, SITE+key, 'hts-cache/new.zip#'+info.filename)
                    restored += 1
                    if restored % 500 == 0:
                        print(f'Restored {restored} source pages from HTTrack cache', flush=True)
                else:
                    unreadable.add(key)
    entries, missing, ambiguous = [], [], []
    counts = {game: Counter() for game in INDEXES}
    work = root / 'work/imperial_library_translation'
    for book in catalog['entries']:
        game, uid = book['game'], book['uid']
        counts[game]['total'] += 1
        keys = {urlkey(book['source_url'])} if book.get('direct_link') else titles.get((game, normalize(book['title_en'])), set())
        if len(keys) != 1:
            status = 'ambiguous_title' if len(keys) > 1 else 'no_individual_link'
            row = dict(uid=uid, game=game, title_en=book['title_en'], status=status, candidate_paths=sorted(keys))
            (ambiguous if len(keys) > 1 else missing).append(row)
            counts[game][status] += 1
            continue
        key = next(iter(keys))
        if key not in pages:
            status = 'source_page_without_extractable_text' if key in unreadable else 'not_downloaded'
            missing.append(dict(uid=uid, game=game, title_en=book['title_en'], source_url=SITE+key, status=status))
            counts[game][status] += 1
            continue
        body, notes, url, path = pages[key]
        item = dict(uid=uid, game=game, title_en=book['title_en'], source_url=url,
                    body_en=body, source_notes_en=notes, translation_status='untranslated',
                    source_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest(),
                    source_file=path if isinstance(path, str) else path.relative_to(mirror).as_posix(),
                    coverage='downloaded_page', needs_source_review=True)
        entries.append(item)
        counts[game]['imported'] += 1
        target = work / game / (uid + '.md')
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"# {book['title_en']}\n\n**UID:** {uid}\n\n**출처:** {url}\n\n"
                              f"## 영어 원문\n\n{body}\n\n## 출처 편집자 주석\n\n{notes or '(없음)'}\n\n"
                              '## 한국어 번역\n\n\n## 검수 메모\n\n- [ ] 해당 게임 판본·발췌 여부 확인\n- [ ] 용어 및 고유명사 대조\n', encoding='utf-8')
    output = root / 'docs/books/external_english_texts.json'
    write_json(output, dict(schema_version=1, description='English source pages from user-provided local mirror; game edition and excerpt coverage require review.', entries=entries))
    report = dict(schema_version=1, indexed_total=len(catalog['entries']), imported=len(entries),
                  unavailable=len(missing), ambiguous=len(ambiguous), source_pages=len(pages),
                  games={g: dict(c) for g, c in counts.items()}, missing=missing, ambiguous_matches=ambiguous)
    write_json(root / 'docs/books/english_import_report.json', report)
    write_json(work / 'import_report.json', report)
    with (work / 'sources.jsonl').open('w', encoding='utf-8') as stream:
        for item in entries:
            stream.write(json.dumps(item, ensure_ascii=False) + '\n')
    summary = ['# 영문 원문 준비 현황', '', '| 게임 | 색인 | 확보 | 미확보·확인 필요 |', '|---|---:|---:|---:|']
    for game, count in counts.items():
        summary.append(f"| {game} | {count['total']} | {count['imported']} | {count['total']-count['imported']} |")
    summary += ['', '본문은 내려받은 개별 페이지 기준입니다. 판본 차이·발췌 여부는 번역 전에 확인하세요.',
                '출처 편집자 주석은 본문과 분리했습니다. 기존 번역 작업 파일은 다시 실행해도 덮어쓰지 않습니다.',
                '미확보 및 중복 제목 목록: `import_report.json` · 전체 원문: `sources.jsonl`', '']
    (work / 'README.md').write_text('\n'.join(summary), encoding='utf-8')
    return {k: v for k, v in report.items() if k not in ('missing', 'ambiguous_matches')}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mirror', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(run(args.mirror, args.root), ensure_ascii=False, indent=2))
