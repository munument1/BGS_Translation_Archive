"""Download the public EPUB; keep bodies local and publish its document index.

Requires requests and beautifulsoup4. Run from the repository root.
"""
import collections
import hashlib
import json
import pathlib
import xml.etree.ElementTree as ET
import zipfile
from datetime import date

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / 'work/fallout_codex'
URL = 'https://libraryofcodexes.com/ebooks/Fallout.epub'


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    epub = WORK / 'Fallout.epub'
    if not epub.exists():
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        epub.write_bytes(response.content)
    records, local, groups = [], [], collections.Counter()
    with zipfile.ZipFile(epub) as archive:
        opf = ET.fromstring(archive.read('content.opf'))
        ns = {'o': 'http://www.idpf.org/2007/opf'}
        manifest = {x.attrib['id']: x.attrib['href'] for x in opf.findall('o:manifest/o:item', ns)}
        toc = BeautifulSoup(archive.read('toc.xhtml'), 'html.parser')
        headings = {a['href']: a.get_text(' ', strip=True) for a in toc.select('a[href]')}
        group = None
        for item in opf.findall('o:spine/o:itemref', ns):
            filename = manifest[item.attrib['idref']]
            if filename in headings:
                group = headings[filename]
                continue
            if not group or not group.startswith('Fallout') or filename in ('Afterword.html', 'Copyright.html', 'Support.html'):
                continue
            soup = BeautifulSoup(archive.read(filename), 'html.parser')
            body = soup.body
            title = soup.find('h1')
            if not body or not title:
                continue
            title_text = title.get_text(' ', strip=True)
            title.decompose()
            text = body.get_text('\n', strip=True)
            if not text:
                continue
            game = next((g for label, g in [('Fallout Tactics', 'fot'), ('Fallout: New Vegas', 'fnv'), ('Fallout New Vegas', 'fnv'), ('Fallout 4', 'fo4'), ('Fallout 3', 'fo3'), ('Fallout 2', 'fo2')] if group.startswith(label)), 'fo1')
            kind = 'terminal' if 'Terminal' in group else ('holodisk_note' if 'Holodisk' in group or 'Notes' in group else 'holodisk')
            uid = 'codex-' + hashlib.sha256((game + ':' + filename).encode()).hexdigest()[:16]
            record = dict(id=uid, game=game, type=kind, level='document', title_ko='', title_en=title_text,
                          description=group, dlc_group=group, source_url=URL, source_name='Library of Codexes — Fallout EPUB',
                          source_member=filename, status='source_index', body_ko=None,
                          checked_at=date.today().isoformat(), verification='epub_member_verified',
                          editor_id=None, form_id=None, usage_status='unknown')
            records.append(record)
            local.append({**record, 'body_en': text})
            groups[group] += 1
            folder = WORK / game
            folder.mkdir(exist_ok=True)
            target = folder / (uid + '.md')
            if not target.exists():
                target.write_text(f'# {title_text}\n\nID: {uid}\n\n{text}\n\n[출처]({URL})\n\n## 한국어 번역\n\n', encoding='utf-8')
    assert len({r['id'] for r in records}) == len(records)
    (WORK / 'sources.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in local), encoding='utf-8')
    catalog_path = ROOT / 'docs/fallout/catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    catalog['entries'] = [r for r in catalog['entries'] if not r['id'].startswith('codex-')] + records
    catalog['updated'] = date.today().isoformat()
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = dict(source_url=URL, sha256=hashlib.sha256(epub.read_bytes()).hexdigest(), bytes=epub.stat().st_size,
                  documents=len(records), games=dict(collections.Counter(r['game'] for r in records)), groups=dict(groups),
                  korean_bodies=0, completeness='EPUB spine documents only; not a complete game record census',
                  limitations=['Terminal pages can contain multiple entries; document counts are not entry counts.',
                               'Mixed holodisk/note groups are not individually classified.',
                               'Fallout 76 absent; wiki links and game identifiers not yet independently verified.'])
    (ROOT / 'docs/fallout/import-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
