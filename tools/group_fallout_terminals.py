"""One searchable record per game/plugin/FormID; preserve old links and fields."""
from collections import defaultdict
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def expand(entries):
    from group_fallout_series import flatten_series
    return [child for r in flatten_series(entries) for child in r.get('terminal_sections', [r])]

def group(entries):
    result=[]
    groups=defaultdict(list)
    for r in expand(entries):
        if r.get('record_type')=='TERM' and r.get('plugin') and r.get('form_id'):
            groups[r['game'],r['plugin'].lower(),r['form_id']].append(r)
        else:
            result.append(r)
    for (game,plugin,form), sections in groups.items():
        sections.sort(key=lambda r: (0 if (r.get('translation_source',{}).get('field') in ('DESC','BTXT') or r['field'].startswith('welcome')) else 1,r.get('translation_source',{}).get('sub_index',int(r['field'].split('-')[-1]) if r['field'].split('-')[-1].isdigit() else 0), r['id']))
        first=sections[0]
        entry={k:v for k,v in first.items() if k not in ('body_ko','translation_source','field')}
        entry.update(id=f'terminal-{game}-{plugin[:-4]}-{form.lower()}', terminal_sections=sections, aliases=[r['id'] for r in sections], field='terminal', level='entry')
        # The parent title is the ESM terminal title, not its first menu caption.
        welcome=next((r for r in sections if r['field'].startswith('welcome')),None)
        title=(welcome or first).get('title_en') or first.get('editor_id') or f'Terminal {form}'
        entry['title_en']=title
        entry['title_ko']=next((r['terminal_title_ko'] for r in sections if r.get('terminal_title_ko')), '') or (welcome or {}).get('title_ko','')
        if not entry['title_ko']:
            entry['title_ko']=first.get('editor_id') or title
        entry['body_ko']='\n\n'.join((('【'+(r.get('title_ko') or r.get('title_en') or r['field'])+'】\n')+r['body_ko']) for r in sections if r.get('body_ko')) or None
        entry['status']='imported_translation' if entry['body_ko'] else 'extracted_untranslated'
        entry['description']=f"{first['plugin']} · 터미널 · {sum(bool(r.get('body_ko')) for r in sections)}개 번역 본문"
        result.append(entry)
    return result

def main():
    path=ROOT/'docs/fallout/catalog.json'
    c=json.loads(path.read_text(encoding='utf-8'))
    c['entries']=group(c['entries'])
    path.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('terminal records:',sum(bool(r.get('terminal_sections')) for r in c['entries']))

if __name__=='__main__':main()
