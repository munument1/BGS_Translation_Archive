"""Extract EPUB documents into the reader without changing Korean translations."""
import hashlib
import json
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

def main():
    epub = ROOT/'work/fallout_codex/Fallout.epub'
    target = ROOT/'docs/fallout/catalog.json'
    catalog = json.loads(target.read_text(encoding='utf-8'))
    from group_fallout_terminals import expand, group
    from group_fallout_series import group_series
    catalog['entries'] = expand(catalog['entries'])
    counts = {}
    with zipfile.ZipFile(epub) as archive:
        for r in catalog['entries']:
            if not r['id'].startswith('codex-'):
                continue
            soup = BeautifulSoup(archive.read(r['source_member']), 'html.parser')
            for tag in soup.select('head, h1, .author, script, style'):
                tag.decompose()
            if not soup.body:
                raise ValueError(r['source_member'])
            r['body_en'] = soup.body.get_text('\n', strip=True)
            r['status'] = 'epub_original' if not r.get('body_ko') else r['status']
            r['epub_sha256'] = hashlib.sha256(epub.read_bytes()).hexdigest()
            counts[r['game']] = counts.get(r['game'],0)+1
    catalog['entries'] = group_series(group(catalog['entries']))[0]
    target.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (target.parent/'epub-body-report.json').write_text(json.dumps(dict(documents=counts, language='en', source_sha256=hashlib.sha256(epub.read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')
    print(counts)

if __name__ == '__main__':
    main()
