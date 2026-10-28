"""Import official Fallout 76 reading records from a read-only Steam install.

Uses exact localized string IDs, TERM submenu edges and NOTE -> SCEN ->
DIAL -> INFO references. Does not publish binaries, gameplay dialogue outside
holotape links, or inventory descriptions without reading text.
"""
import argparse
from collections import Counter,defaultdict
import hashlib,html,json,re,struct,zlib
from pathlib import Path
from build_starfield_archive import fields
from extract_fallout_esm import string_table
from group_fallout_series import group_series
ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def ba2_index(path):
    with path.open('rb') as f:
        magic,version,kind,count,names=struct.unpack('<4sI4sIQ',f.read(24))
        if (magic,version,kind)!=(b'BTDX',1,b'GNRL'):raise ValueError('Unsupported BA2')
        records=[struct.unpack('<I4sIIQIII',f.read(36)) for _ in range(count)]
        f.seek(names);out={}
        for row in records:
            length=struct.unpack('<H',f.read(2))[0];name=f.read(length).decode('utf-8')
            out[name.lower()]=row[4:7]
    return out

def extract_strings(archive,work):
    index=ba2_index(archive);tables={};provenance={}
    with archive.open('rb') as f:
        for language in ('ko','en'):
            for kind in ('strings','dlstrings','ilstrings'):
                name=f'strings/seventysix_{language}.{kind}'
                offset,packed,size=index[name];f.seek(offset);data=f.read(packed or size)
                if packed:data=zlib.decompress(data)
                if len(data)!=size:raise ValueError('Invalid archive member size')
                path=work/Path(name).name;path.write_bytes(data)
                tables[language,kind]=string_table(path,'utf-8' if language=='ko' else 'cp1252')
                provenance[name]=hashlib.sha256(data).hexdigest()
    return tables,provenance

def read_records(path):
    raw={};parents={};stack=[]
    with path.open('rb') as f:
        while head:=f.read(24):
            if len(head)!=24:raise ValueError('Truncated record header')
            pos=f.tell()-24
            while stack and pos>=stack[-1][0]:stack.pop()
            sig,size,flags,fid,_,_=struct.unpack('<4s5I',head)
            if sig==b'GRUP':
                if size<24:raise ValueError('Invalid group size')
                stack.append((pos+size,flags,fid));continue
            if sig not in (b'BOOK',b'NOTE',b'TERM',b'SCEN',b'INFO',b'DIAL') or flags&0x20:f.seek(size,1);continue
            blob=f.read(size)
            if len(blob)!=size:raise ValueError('Truncated record')
            if flags&0x40000:
                expected=struct.unpack_from('<I',blob)[0];blob=zlib.decompress(blob[4:])
                if len(blob)!=expected:raise ValueError('Invalid compressed record')
            raw[fid]=(sig.decode(),list(fields(blob)))
            if sig==b'INFO':parents[fid]=next((label for end,label,kind in reversed(stack) if kind==7),None)
    return raw,parents

def plain(text):
    text=re.sub(r'<img\b[^>]*>','[게임 내 이미지]',text,flags=re.I)
    text=re.sub(r'<br\s*/?>|\[pagebreak\]','\n',text,flags=re.I)
    text=re.sub(r'</(?:p|div)>','\n\n',text,flags=re.I)
    text=re.sub(r'</?(?:font|p|div|b|i|u|textformat|body|html|span)\b[^>]*>','',text,flags=re.I)
    return re.sub(r'\n{4,}','\n\n\n',html.unescape(text).replace('\r\n','\n')).strip()

def readable(text):
    prose=re.sub(r'<[^>]*>|\[게임 내 이미지\]','',text)
    return bool(re.search(r'[가-힣A-Za-z0-9]',prose))

def scene_actions(fs):
    actions=[];current=None
    for key,value in fs:
        if key=='ANAM':
            if current is not None:actions.append(current);current=None
            if len(value)==2:current={'type':int.from_bytes(value,'little'),'phase':0,'index':0,'topics':[],'scenes':[]}
        elif current is not None:
            if key in ('SNAM','INAM') and len(value)==4:current['phase' if key=='SNAM' else 'index']=int.from_bytes(value,'little')
            if key=='DATA' and len(value)==4 and current['type'] in (0,6):current['topics'].append(int.from_bytes(value,'little'))
            if key=='LCEP' and len(value)==4 and current['type']==4:current['scenes'].append(int.from_bytes(value,'little'))
    if current is not None:actions.append(current)
    return sorted(actions,key=lambda a:(a['phase'],a['index']))

def build(install):
    source=install/'Data';work=ROOT/'work/fo76/strings';work.mkdir(parents=True,exist_ok=True)
    tables,table_hashes=extract_strings(source/'SeventySix - Localization.ba2',work)
    raw,parents=read_records(source/'SeventySix.esm');topics=defaultdict(list)
    for info,topic in parents.items():topics[topic].append(info)
    missed=Counter();excluded=[]
    # String IDs are globally disjoint in this installed set; never use a FormID
    # as a string key. Only explicitly localized fields call this resolver.
    lookup={}
    for (language,kind),table in tables.items():
        for sid,text in table.items():
            if (language,sid) in lookup:raise ValueError('Ambiguous string namespace')
            lookup[language,sid]=(text,kind)
    def text(fid,key,value,index,language='ko'):
        if len(value)!=4:raise ValueError('Expected localized string ID')
        sid=int.from_bytes(value,'little')
        if not sid:return None
        match=lookup.get((language,sid))
        if not match:
            if language=='ko':missed[raw[fid][0]+'.'+key]+=1
            return None
        value,kind=match;body=plain(value)
        return dict(text=body,source=dict(dictionary='SeventySix - Localization.ba2 / strings/seventysix_ko.'+kind,plugin='SeventySix.esm',record=raw[fid][0],form_id=f'{fid:08X}',field=key,sub_index=index,string_id=sid,korean_sha256=hashlib.sha256(value.encode()).hexdigest(),translation_origin='official_ko'))
    localized={};titles={};edids={}
    for fid,(sig,fs) in raw.items():
        edids[fid]=next((v.rstrip(b'\0').decode('utf-8') for k,v in fs if k=='EDID'),'')
        allowed={'BOOK':{'FULL','DESC'},'TERM':{'FULL','NAM0','WNAM','BTXT','ITXT','RNAM','UNAM'},'NOTE':{'FULL'},'INFO':{'NAM1'}}.get(sig,set())
        items=[];counts=Counter()
        for key,value in fs:
            index=counts[key];counts[key]+=1
            if key in allowed:
                item=text(fid,key,value,index)
                if item and item['text']:items.append((key,index,item))
        localized[fid]=items
        title=next((r['text'] for k,i,r in items if k=='FULL'),None) or next((r['text'] for k,i,r in items if k=='NAM0'),None) or edids[fid] or f'{sig} {fid:08X}'
        en=next((text(fid,k,v,0,'en') for k,v in fs if k=='FULL'),None) if sig in ('BOOK','TERM','NOTE') else None
        titles[fid]=(title,en['text'] if en else edids[fid])
    def base(fid,kind,parts,links):
        body='\n\n'.join(p['body_ko'] for p in parts)
        return dict(id=f'fo76-{raw[fid][0].lower()}-{fid:08x}',game='fo76',type=kind,level='entry',title_ko=titles[fid][0],title_en=titles[fid][1],body_ko=body,body_version='official_game_localization',status='official_translation',official_localization=True,description='폴아웃 76 공식 한국어 · '+('터미널' if kind=='terminal' else '홀로테이프' if kind=='holotape' else '메모·문서'),plugin='SeventySix.esm',record_type=raw[fid][0],form_id=f'{fid:08X}',editor_id=edids[fid],source_name='Fallout 76 설치본 · 공식 한국어',source_url='',usage_status='game_record_present; placement and conditions not exhaustively reviewed',translation_sources=[src for p in parts for src in p['sources']],canonical_record_links=links,has_runtime_parameters=bool(re.search(r'<(?:Alias|Global|Token|Text|Actor|Quest)[^>]*>',body,re.I)),has_embedded_art='[게임 내 이미지]' in body)
    entries=[];excluded_roots=set()
    def excluded_root(fid):
        if re.match(r'(?:zzz|cut[_-]|test|debug|dummy|unused|delete|deprecated)',edids[fid],re.I) or edids[fid]=='Template_MultiPageNote':
            if fid not in excluded_roots:excluded.append(dict(form_id=f'{fid:08X}',record=raw[fid][0],editor_id=edids[fid],reason='explicit_test_debug_cut_or_unused_editor_ID'))
            excluded_roots.add(fid)
            return True
        return False
    def item_parts(fid,fields):
        return [dict(body_ko=r['text'],sources=[r['source']],field=k,index=i) for k,i,r in localized[fid] if k in fields and readable(r['text'])]
    for fid,(sig,fs) in raw.items():
        if sig!='BOOK':continue
        if excluded_root(fid):continue
        parts=item_parts(fid,{'DESC'})
        if parts:entries.append(base(fid,'document',parts,[dict(plugin='SeventySix.esm',record='BOOK',form_id=f'{fid:08X}')]))
        else:excluded.append(dict(form_id=f'{fid:08X}',record=sig,reason='no_reading_body; recipe, inventory item or image-only record'))
    terminals={fid for fid,(sig,fs) in raw.items() if sig=='TERM'}
    edges={fid:[int.from_bytes(v,'little') for k,v in raw[fid][1] if k=='TNAM' and len(v)==4 and int.from_bytes(v,'little') in terminals] for fid in terminals}
    note_terminals={int.from_bytes(v,'little') for sig,fs in raw.values() if sig=='NOTE' and any(k=='DNAM' and v==b'\3' for k,v in fs) for k,v in fs if k=='SNAM'}
    referenced={v for values in edges.values() for v in values};covered=set()
    def terminal_parts(root):
        parts=[];seen=set()
        def visit(fid):
            if fid in seen or fid not in terminals:return
            seen.add(fid)
            for key,index,item in localized[fid]:
                if key not in ('WNAM','BTXT','UNAM','RNAM') or not readable(item['text']):continue
                caption=titles[fid][0]
                if key in ('UNAM','RNAM'):
                    # Use the closest preceding ITXT from the actual menu block,
                    # not a guessed offset between independently indexed fields.
                    current='';seen_counts=Counter()
                    for k,v in raw[fid][1]:
                        idx=seen_counts[k];seen_counts[k]+=1
                        if k=='ITXT':current=next((r['text'] for a,b,r in localized[fid] if a=='ITXT' and b==idx),'')
                        if k==key and idx==index:break
                    caption=current or caption
                parts.append(dict(body_ko='【'+caption+'】\n'+item['text'],sources=[item['source']],form_id=f'{fid:08X}',title_ko=caption,field=key,sub_index=index))
            for child in edges[fid]:visit(child)
        visit(root);return parts,seen
    def info_parts(fid,seen=None):
        seen=set() if seen is None else seen
        if fid in seen or fid not in raw or raw[fid][0]!='INFO':return []
        seen.add(fid);parts=item_parts(fid,{'NAM1'})
        if parts:return parts
        for key,value in raw[fid][1]:
            if key in ('DNAM','GNAM') and len(value)==4:parts.extend(info_parts(int.from_bytes(value,'little'),seen))
        return parts
    def voice_parts(scene,seen=None):
        seen=set() if seen is None else seen
        if scene in seen or scene not in raw or raw[scene][0]!='SCEN':return []
        seen.add(scene);parts=[]
        for action in scene_actions(raw[scene][1]):
            for topic in action['topics']:
                for info in topics.get(topic,[]):
                    for part in info_parts(info):
                        part.update(scene_form_id=f'{scene:08X}',topic_form_id=f'{topic:08X}',phase=action['phase'],action_index=action['index'],info_form_id=f'{info:08X}',conditional_variants=len(topics.get(topic,[]))>1)
                        parts.append(part)
            for child in action['scenes']:parts.extend(voice_parts(child,seen))
        if not parts:
            for key,value in raw[scene][1]:
                if key=='TNAM' and len(value)==4:parts.extend(voice_parts(int.from_bytes(value,'little'),seen))
        return parts
    for fid,(sig,fs) in raw.items():
        if sig!='NOTE':continue
        if excluded_root(fid):continue
        kind=next((v[0] for k,v in fs if k=='DNAM'),-1);target=next((int.from_bytes(v,'little') for k,v in fs if k=='SNAM'),0)
        if kind==1:parts=voice_parts(target);links=[dict(plugin='SeventySix.esm',record='NOTE',form_id=f'{fid:08X}',scene_form_id=f'{target:08X}')]
        elif kind==3:
            parts,seen=terminal_parts(target);covered.update(seen);links=[dict(plugin='SeventySix.esm',record='NOTE',form_id=f'{fid:08X}',terminal_form_ids=[f'{x:08X}' for x in sorted(seen)])]
        else:parts=[];links=[]
        if parts:
            entry=base(fid,'holotape',parts,links)
            entry['transcript_sections']=[{k:v for k,v in p.items() if k!='body_ko'} for p in parts]
            entries.append(entry)
        else:excluded.append(dict(form_id=f'{fid:08X}',record=sig,note_type=kind,reason='no_linked_reading_text; sound-only, program-only or unresolved transcript',target_form_id=f'{target:08X}'))
    roots=sorted(terminals-referenced-note_terminals)
    for root in roots+sorted(terminals-set(roots)):
        if root in covered:continue
        if excluded_root(root):continue
        parts,seen=terminal_parts(root);covered.update(seen)
        if not parts:continue
        entry=base(root,'terminal',parts,[dict(plugin='SeventySix.esm',record='TERM',form_id=f'{fid:08X}') for fid in sorted(seen)])
        entry['terminal_page_count']=len(parts);entry['terminal_record_ids']=[f'{x:08X}' for x in sorted(seen)];entries.append(entry)
    families={"Overseer's Log":'감독관의 기록','Survivor Story':'생존자의 이야기',"Ella's Log":'엘라의 기록'}
    filtered=[]
    neutral_ids={'fo76-book-0081dd74','fo76-book-006dee63','fo76-book-0063e341','fo76-note-003b9840'}
    for r in entries:
        r['conditional_variants']=any(p.get('conditional_variants') for p in r.get('transcript_sections',[]))
        if not re.search('[가-힣]',r['body_ko']):
            if r['id'] in neutral_ids or len(r['body_ko'])<30:r['language_neutral_payload']=True
            else:
                excluded.append(dict(form_id=r['form_id'],record=r['record_type'],editor_id=r['editor_id'],reason='official_Korean_table_retains_English_prose; no_Korean_reading_body_published'))
                continue
        filtered.append(r)
    entries=filtered
    for r in entries:
        if r['type']!='holotape':continue
        title=r['title_en']
        for prefix,ko in families.items():
            if re.match(re.escape(prefix)+r'\s*[-:]',title):
                r.update(series_group_key=prefix.casefold(),series_group_title=prefix,series_group_title_ko=ko,series_group_order=sorted(x['title_en'] for x in entries if x['type']=='holotape' and x['title_en'].startswith(prefix)).index(title))
        numbered=re.match(r'^(.*(?:Log|Tape))\s*#?(\d{1,3}):\s+.+$',title,re.I)
        if numbered:
            r.update(series_group_key=numbered[1].casefold(),series_group_title=numbered[1],series_group_order=int(numbered[2]))
    entries,series=group_series(entries)
    for r in entries:
        if not r.get('series_entries'):continue
        children=r.pop('series_entries');r['reference_series_members']=[{k:c[k] for k in ('id','title_en','title_ko','form_id','editor_id') if k in c} for c in children];r['series_member_count']=len(children)
        if r.get('series_group_title_ko'):r['title_ko']=r['series_group_title_ko']
        elif r.get('series_group_key'):r['title_ko']=re.split(r'\s*#?\d{1,3}\s*[:：]',children[0]['title_ko'])[0].strip()
        r['canonical_record_links']=[link for c in children for link in c['canonical_record_links']]
        r['translation_sources']=[src for c in children for src in c['translation_sources']]
        r['has_runtime_parameters']=any(c.get('has_runtime_parameters') for c in children);r['has_embedded_art']=any(c.get('has_embedded_art') for c in children)
        r['conditional_variants']=any(c.get('conditional_variants') for c in children)
        r['status']='official_translation';r.pop('transcript_sections',None)
    catalog=ROOT/'docs/fallout/catalog.json';c=json.loads(catalog.read_text(encoding='utf-8'));previous=[r for r in c['entries'] if r['game']!='fo76'];c['entries']=previous+entries
    assert all(r['body_ko'].strip() for r in entries)
    assert len(c['entries'])==len({r['id'] for r in c['entries']})
    catalog.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(source_plugin='SeventySix.esm',source_plugin_sha256=sha(source/'SeventySix.esm'),source_archive='SeventySix - Localization.ba2',table_sha256=table_hashes,raw_reading_record_counts=dict(Counter(sig for sig,fs in raw.values() if sig in ('BOOK','TERM','NOTE'))),published_records=len(entries),categories=dict(Counter(r['type'] for r in entries)),terminal_subrecords_covered=len(covered),series=series,missing_localized_string_ids=dict(missed),excluded=excluded,scope='Installed SeventySix.esm reading records and linked official Korean subtitles. NW.esm is a separate sBabylonMasters game-mode master and is not overlaid onto the standard archive. Placement, conditional alternatives and current server availability are not exhaustively verified.')
    (catalog.parent/'fo76-import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    all_rows=c['entries']
    cleanup=dict(records=len(all_rows),categories=dict(Counter(r['type'] for r in all_rows)),korean_records=sum(bool(r.get('body_ko')) for r in all_rows),english_only=sum(not r.get('body_ko') for r in all_rows),epub_partly_translated=sum(r.get('status')=='partial_translation' for r in all_rows),holotapes_with_korean=sum(r['type']=='holotape' and bool(r.get('body_ko')) for r in all_rows),official_fo76_records=len(entries),audit=['completion-audit-report.json','fo76-import-report.json'],scope='Current published readable records, not a census of all game records')
    (catalog.parent/'cleanup-report.json').write_text(json.dumps(cleanup,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('excluded','table_sha256','series')},ensure_ascii=True))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',type=Path,required=True);a=p.parse_args();build(a.install)
