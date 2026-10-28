"""Group explicit numbered recording series within the same game and source.

Only short sequence numbers and recording-related titles qualify. Do not strip
arbitrary digits from locations, patient IDs, dates or EditorIDs.
"""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NUMBER=re.compile(r'^(.*?)[\s_]*(?:#|No\.?\s*)?(\d{1,3})(?:\s*(?:of|/)\s*\d+)?[).]?$',re.I)
WORDS=re.compile(r'tape|disk|disc|transcript|record|log|journal|diary|entry|entries|test|experiment|interview|message|letter|report|note|logbook|audio|speech',re.I)

def flatten_series(entries):
    return [s for r in entries for s in ([r] if r.get('canonical_record_links') else r.get('series_entries',[r]))]

def candidate(r):
    if r.get('type') not in ('holotape','holodisk','holodisk_note','note','document'):
        return None
    title=r.get('title_en') or ''
    diary=re.match(r'^(Diary)\s+(\d{1,3}):\s+.+$',title,re.I)
    if diary:
        scope=r.get('plugin') or r.get('dlc_group') or r.get('source_name')
        return (r['game'],scope,'diary'),diary[1],int(diary[2])
    m=NUMBER.match(title)
    if not m or not WORDS.search(m[1]) or len(m[1].strip())<6:
        return None
    stem=m[1].strip(' _#(.-')
    if not stem or stem[-1].isdigit() or '/' in stem or re.search(r'\d[.]$',m[1]):
        return None
    # Same plugin (or EPUB group) prevents unrelated DLC/source records merging.
    scope=r.get('plugin') or r.get('dlc_group') or r.get('source_name')
    return (r['game'],scope,stem.casefold()),stem,int(m[2])

def group_series(entries):
    result=[]
    groups=defaultdict(list)
    for r in flatten_series(entries):
        c=candidate(r)
        if c:groups[c[0]].append((c[2],c[1],r))
        else:result.append(r)
    report=[]
    for key,items in groups.items():
        # Repeated edition titles without distinct sequence numbers are not a series.
        if len({i[0] for i in items})<2:
            result.extend(i[2] for i in items)
            continue
        items.sort(key=lambda i:(i[0],i[2]['id']))
        sections=[i[2] for i in items]
        first=sections[0]
        entry={k:v for k,v in first.items() if k not in ('body_ko','body_en','translation_source','form_id','editor_id','source_member','field')}
        uid='series-'+hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        en=items[0][1]
        ko=first.get('title_ko','')
        ko=re.sub(r'\s*\(?\d{1,3}(?:\s*[/]\s*\d+)?\)?(?:장|편)?\s*$','',ko).strip()
        entry.update(id=uid,title_en=en,title_ko=ko,series_entries=sections,aliases=[r['id'] for r in sections],level='series',description=f'{len(sections)}편의 연속 기록')
        for lang in ('ko','en'):
            entry['body_'+lang]='\n\n'.join('【'+(r.get('title_'+lang) or r.get('title_en') or r['id'])+'】\n'+r['body_'+lang] for r in sections if r.get('body_'+lang)) or None
        entry['status']='imported_translation' if entry['body_ko'] else 'epub_original' if entry['body_en'] else first.get('status')
        result.append(entry)
        report.append(dict(id=uid,game=first['game'],title=en,members=[r['id'] for r in sections]))
    return result,report

def main():
    target=ROOT/'docs/fallout/catalog.json'
    c=json.loads(target.read_text(encoding='utf-8'))
    c['entries'],report=group_series(c['entries'])
    target.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (target.parent/'series-group-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([dict(title=r['title'],game=r['game'],parts=len(r['members'])) for r in report],ensure_ascii=True))

if __name__=='__main__':main()
