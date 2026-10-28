"""Build the Korean Starfield reading archive from local ESM + archived SST.

Only exact FormID/field/occurrence/string-ID matches are accepted. Game binaries
and untranslated English prose are never copied to docs.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import zlib

ROOT=Path(__file__).resolve().parents[1]

def fields(blob):
    offset=0;extended=0
    while offset+6<=len(blob):
        sig,size=struct.unpack_from('<4sH',blob,offset);offset+=6
        if sig==b'XXXX':
            extended=struct.unpack_from('<I',blob,offset)[0];offset+=size;continue
        size=extended or size;extended=0
        if offset+size>len(blob):raise ValueError('Truncated subrecord')
        yield sig.decode('ascii'),blob[offset:offset+size]
        offset+=size

def records(path):
    with path.open('rb') as f:
        while head:=f.read(24):
            sig,size,flags,fid,_,_=struct.unpack('<4s5I',head)
            if sig==b'GRUP':continue
            if sig not in (b'BOOK',b'TERM',b'TMLM') or flags&0x20:
                f.seek(size,1);continue
            blob=f.read(size)
            if flags&0x40000:
                expected=struct.unpack_from('<I',blob)[0];blob=zlib.decompress(blob[4:])
                if len(blob)!=expected:raise ValueError('Invalid compressed record')
            yield sig.decode(),fid,list(fields(blob))

def plain(text):
    text=re.sub(r'<br\s*/?>|\[pagebreak\]', '\n',text,flags=re.I)
    text=re.sub(r'</(?:p|div)>','\n\n',text,flags=re.I)
    text=re.sub(r'</?(?:font|p|div|b|i|u|img|textformat)\b[^>]*>','',text,flags=re.I)
    return html.unescape(text).strip()

def build(path):
    dictionary={};ambiguous=set();variants=defaultdict(list)
    for shard in sorted((ROOT/'Starfield/Dictionaries').rglob('tm_*.jsonl.gz')):
        with gzip.open(shard,'rt',encoding='utf-8') as f:
            for line in f:
                r=json.loads(line)
                if r.get('source_dictionary')!='starfield_en_ko.sst' or r['record'] not in ('BOOK','TERM','TMLM'):continue
                key=(r['record'],int(r['form_id'],16),r['field'],r['sub_index'],r['string_id'])
                row=dict(r,archive=shard.relative_to(ROOT).as_posix())
                variants[key].append(row)
                if key in dictionary and dictionary[key]['ko']!=r['ko']:ambiguous.add(key)
                dictionary[key]=row
    base=defaultdict(set)
    for shard in (ROOT/'Starfield/BaseGame').rglob('*strings.ko.jsonl.gz'):
        with gzip.open(shard,'rt',encoding='utf-8') as f:
            for line in f:
                r=json.loads(line);base[r['string_id']].add(r['ko'])
    resolved=0
    for key in ambiguous:
        choices={r['ko']:r for r in variants[key] if r['ko'] in base[key[-1]]}
        if len(choices)==1:
            dictionary[key]=next(iter(choices.values()));resolved+=1
        else:dictionary.pop(key,None)
    raw={fid:(sig,fs) for sig,fid,fs in records(path)}
    skipped=Counter();matched=Counter()
    def text(fid,field,index,value):
        if len(value)!=4:return None
        sig=raw[fid][0];sid=int.from_bytes(value,'little')
        r=dictionary.get((sig,fid,field,index,sid))
        if not r:
            skipped[sig+':'+field]+=1;return None
        if not re.search('[가-힣]',r['ko']) or '\ufffd' in r['ko']:return None
        matched[sig+':'+field]+=1
        return dict(text=plain(r['ko']),source=dict(archive=r['archive'],dictionary=r['source_dictionary'],record_index=r['dictionary_record_index'],field=field,sub_index=index,string_id=sid,source_hash=r['source_hash'],review_status='unreviewed'))
    data={};terms={}
    for fid,(sig,fs) in raw.items():
        edid=next((v.rstrip(b'\0').decode('utf-8') for k,v in fs if k=='EDID'),'')
        counts=Counter();translations={};links=[]
        for field,value in fs:
            index=counts[field];counts[field]+=1
            if field in ('FULL','DESC','BTXT','ITXT','UNAM'):
                item=text(fid,field,index,value)
                if item:translations[field,index]=item
            if sig=='TMLM' and field=='TNAM' and len(value)==4:links.append(int.from_bytes(value,'little'))
            if sig=='TERM' and field=='DNAM' and len(value)==4:terms[fid]=int.from_bytes(value,'little')
        data[fid]=dict(sig=sig,edid=edid,t=translations,links=links,audio_scene=next((int.from_bytes(v,'little') for k,v in fs if k=='GNAM' and len(v)==4),0),model=next((v.decode('utf-8','replace') for k,v in fs if k=='MODL'),''))
    def title(fid):
        d=data[fid];return d['t'].get(('FULL',0),{}).get('text') or d['edid'] or f'{fid:08X}'
    entries=[]
    for fid,d in data.items():
        if d['sig']!='BOOK':continue
        # A slate linked to a playback scene has a description, not a transcript.
        if d['audio_scene']:
            skipped['BOOK:audio_scene_description']+=1;continue
        body=d['t'].get(('DESC',0))
        if not body:continue
        kind='slate' if 'dataslate' in d['model'].lower() or 'slate' in d['edid'].lower() else 'book'
        entries.append(dict(id=f'sf-book-{fid:08x}',game='sf',type=kind,level='entry',title_ko=title(fid),title_en=d['edid'],body_ko=body['text'],description='데이터 슬레이트' if kind=='slate' else '서적·문서',plugin=path.name,record_type='BOOK',form_id=f'{fid:08X}',editor_id=d['edid'],status='imported_translation',source_name='기존 스타필드 한글 번역 사전',source_url='',translation_source=body['source']))
    menus={fid for fid,d in data.items() if d['sig']=='TMLM'}
    referenced={link for fid in menus for link in data[fid]['links'] if link in menus}
    roots=set(terms.values())&menus | (menus-referenced)
    covered=set();groups=[]
    def walk(root):
        seen=set();queue=[root];order=[]
        while queue:
            fid=queue.pop()
            if fid in seen or fid not in menus:continue
            seen.add(fid);order.append(fid);queue.extend(reversed(data[fid]['links']))
        return order
    for root in sorted(roots):
        order=walk(root);covered.update(order);groups.append((root,order))
    for root in sorted(menus-covered):
        if root not in covered:
            order=walk(root);covered.update(order);groups.append((root,order))
    for root,order in groups:
        sections=[]
        for fid in order:
            d=data[fid]
            for (field,index),item in d['t'].items():
                if field not in ('BTXT','UNAM'):continue
                caption=d['t'].get(('ITXT',index),{}).get('text') if field=='UNAM' else None
                sections.append(dict(id=f'sf-menu-{fid:08x}-{field.lower()}-{index}',title_ko=caption or title(fid),title_en=d['edid'],body_ko=item['text'],form_id=f'{fid:08X}',editor_id=d['edid'],translation_source=item['source']))
        if not sections:continue
        physical=[f'{fid:08X}' for fid,menu in terms.items() if menu==root]
        entries.append(dict(id=f'sf-terminal-{root:08x}',game='sf',type='terminal',level='entry',title_ko=title(root),title_en=data[root]['edid'],body_ko='\n\n'.join('【'+r['title_ko']+'】\n'+r['body_ko'] for r in sections),description=f'{len(sections)}개 기록 · 하위 메뉴 포함',plugin=path.name,record_type='TMLM',form_id=f'{root:08X}',editor_id=data[root]['edid'],status='imported_translation',source_name='게임 터미널 메뉴 구조 + 기존 한글 번역 사전',source_url='',terminal_sections=sections,aliases=[r['id'] for r in sections],physical_terminal_ids=physical,menu_ids=[f'{fid:08X}' for fid in order]))
    # Keep explicitly numbered slate series together; retain every source member.
    series=[];buckets=defaultdict(list);retained=[]
    for r in entries:
        m=re.match(r'^(.*?)\s*#?(\d{1,2})(?:호|편)?$',r['title_ko']) if r['type'] in ('book','slate') else None
        # Numbered titles need a shared EditorID stem as an independent check.
        stem=re.sub(r'(?:\d+[a-z]?|[A-Z])$','',r.get('editor_id',''))
        if m and re.search('[가-힣]',m[1]) and len(m[1].strip())>=3:
            buckets[r['type'],m[1].strip(),stem].append((int(m[2]),r))
        else:retained.append(r)
    for (kind,name,stem),items in buckets.items():
        if len(items)<2:retained.extend(r for _,r in items);continue
        items.sort(key=lambda x:(x[0],x[1]['id']));members=[r for _,r in items]
        uid='sf-series-'+hashlib.sha256((kind+name+stem).encode()).hexdigest()[:12]
        r=dict(members[0]);r.update(id=uid,title_ko=name,title_en=stem,level='series',series_entries=members,aliases=[x['id'] for x in members],description=f'{len(members)}편의 연속 기록',body_ko='\n\n'.join('【'+x['title_ko']+'】\n'+x['body_ko'] for x in members))
        retained.append(r);series.append(dict(id=uid,members=len(members),title=name))
    entries=retained
    entries.sort(key=lambda r:(r['type'],r['title_ko'],r['id']))
    out=ROOT/'docs/starfield';out.mkdir(exist_ok=True)
    (out/'catalog.json').write_text(json.dumps(dict(schema_version=1,project='성계의 기록',updated='2026-10-28',entries=entries),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(source_plugin=path.name,source_plugin_bytes=path.stat().st_size,source_plugin_sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),records=len(entries),by_type=dict(Counter(r['type'] for r in entries)),verified_field_matches=dict(matched),unmatched_fields=dict(skipped),ambiguous_dictionary_keys=len(ambiguous),resolved_by_exact_base_patch_text=resolved,series=series,scope='Installed Starfield.esm only; DLC and audio-only recordings not covered',verification='Exact ESM record type/FormID/field occurrence/string-ID matched to archived SST; conflicting SST variants accepted only when exactly one matches archived base-patch text. Imported translation, not editorial review')
    (out/'import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--esm',type=Path,required=True);build(p.parse_args().esm)
