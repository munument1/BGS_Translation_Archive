"""Restore complete game record bodies instead of translating a wiki transcription.

English titles and distinctive text shingles identify existing records. Once a
record is identified, every Korean response/menu field is read in stored order.
EPUB prose is retained as a reference version, not a translation-completion test.
"""
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

from build_starfield_archive import fields

from read_xtranslator_sst import parse_sst
from reconcile_fallout_epub import clean,norm
from link_fallout_translations import PLUGINS

ROOT=Path(__file__).resolve().parents[1]
BODY={'NOTE':{'TNAM'},'BOOK':{'DESC'},'INFO':{'NAM1'}}
def title_key(s):
    s=re.sub(r'^(?:article|holotape|note)\s*:\s*','',s,flags=re.I)
    s=re.sub(r'<[^>]+>','',s)
    s=re.sub(r'&[A-Za-z_]+;','',s)
    return re.sub(r'[^a-z0-9]','',s.casefold())
def shingles(s):
    ts=norm(s).split()
    return {tuple(ts[i:i+4]) for i in range(len(ts)-3)}

def read_korean_game_fields(game,plugins):
    base=Path(r'D:\Codex_Trans\비바\release-v108-20261026\Output\mods')
    folder=base/('[NoDelete] [INF] [DB] - Tale of Two Wastelands (TTW)' if game=='fo3' else 'Nuclear Sunset Korean - Base Masters')
    out=defaultdict(dict)
    for name in plugins:
        p=folder/(name+'.esm')
        if not p.exists():continue
        with p.open('rb') as f:
            h=f.read(24);header=struct.unpack('<4s5I',h);meta=f.read(header[1])
            masters=[v.rstrip(b'\0').decode('ascii').casefold() for k,v in fields(meta) if k=='MAST']
            while h:=f.read(24):
                sig,size,flags,fid,_,_=struct.unpack('<4s5I',h)
                if sig==b'GRUP':continue
                if sig not in (b'TERM',b'NOTE',b'BOOK',b'INFO') or flags&0x20:f.seek(size,1);continue
                blob=f.read(size)
                if flags&0x40000:blob=zlib.decompress(blob[4:])
                owner=masters[fid>>24] if fid>>24<len(masters) else p.name.casefold()
                if game=='fo3' and owner=='falloutnv.esm':owner='fallout3.esm'
                gid=(owner,fid&0xffffff,sig.decode());counts=Counter()
                for tag,raw in fields(blob):
                    i=counts[tag];counts[tag]+=1
                    if tag not in ('FULL','DESC','ITXT','RNAM','TNAM','NAM1'):continue
                    if b'\0' in raw[:-1]:continue
                    try:ko=clean(raw.rstrip(b'\0').decode('utf-8'))
                    except UnicodeDecodeError:
                        try:ko=clean(raw.rstrip(b'\0').decode('cp949'))
                        except UnicodeDecodeError:continue
                    if not re.search('[가-힣]',ko):continue
                    out[gid][tag,i]=dict(ko=ko,game_plugin=p.name,field=tag,sub_index=i,form_id=f'{fid:08X}',source='installed_korean_ESM')
    return out

def main():
    path=ROOT/'docs/fallout/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
    entries=catalog['entries'];reports=[];unresolved=[]
    dictionary_root=Path(r'F:\번역\프로그램\xTranslator\UserDictionaries')
    # FO4 patch string IDs are namespaced by the actual plugin.
    patch=defaultdict(set)
    for p in (ROOT/'Fallout4/BaseGame').rglob('*STRINGS.ko.jsonl.gz'):
        plugin=p.name.split('_en.')[0].casefold()+'.esm'
        for line in gzip.open(p,'rt',encoding='utf-8'):
            r=json.loads(line);patch[plugin,r['string_id']].add(clean(r['ko']))
    for game,plugins in PLUGINS.items():
        direct=read_korean_game_fields(game,plugins) if game in ('fo3','fnv') else {}
        groups=defaultdict(dict);full_titles=defaultdict(set);byhash=defaultdict(set);labels=defaultdict(set)
        folder=dictionary_root/('Fallout4' if game=='fo4' else 'FalloutNV')
        names=[p.lower()+'_en_ko.sst' for p in plugins]
        if game in ('fo3','fnv'):names+=['falloutnv_en_ko.sst','fallout nv kr_en_ko.sst','taleoftwowastelands_en_ko.sst']
        allowed={p.casefold()+'.esm' for p in plugins}
        for name in dict.fromkeys(names):
            p=folder/name
            if not p.exists():continue
            parsed=parse_sst(p,max_file_bytes=96*1024*1024)
            masters=parsed['master_files']
            for number,r in enumerate(parsed['records']):
                rec=r['record_name'];field=r['field_name']
                if field=='FULL' and re.search('[가-힣]',r['korean']):labels[title_key(clean(r['source']))].add(clean(r['korean']))
                if rec not in ('INFO','TERM','NOTE','BOOK'):continue
                fid=int(r['form_id'],16);load=fid>>24
                owner=masters[load].casefold() if load<len(masters) else name.removesuffix('_en_ko.sst')+'.esm'
                if game=='fo3' and owner=='falloutnv.esm':owner='fallout3.esm'
                if owner not in allowed:continue
                gid=(owner,fid&0xFFFFFF,rec)
                en=clean(r['source']);ko=clean(r['korean'])
                if game=='fo4':
                    candidates=patch.get((owner,r['string_id']),set())
                    if len(candidates)==1:ko=next(iter(candidates))
                priority=0 if name==owner.removesuffix('.esm')+'_en_ko.sst' else 10
                if not ko or '\ufffd' in ko:priority+=100
                slot=(field,r['index'])
                data=dict(en=en,ko=ko,priority=priority,dictionary=name,record=rec,record_index=number,field=field,sub_index=r['index'],form_id=r['form_id'],plugin=owner,source_hash=hashlib.sha256(r['source'].encode()).hexdigest(),string_id=r['string_id'])
                old=groups[gid].get(slot)
                if old is None or priority<old['priority']:groups[gid][slot]=data
                byhash[data['source_hash']].add(gid)
                if field=='FULL' and en:full_titles[title_key(en)].add(gid)
        for gid,slots in groups.items():
            for slot,d in slots.items():
                actual=direct.get(gid,{}).get(slot)
                if actual:d['ko']=actual['ko'];d['korean_evidence']=actual
        bodies={};index=defaultdict(set);source_grams={};group_signatures={}
        for gid,slots in groups.items():
            fields=({'BTXT','UNAM'} if game=='fo4' else {'DESC','RNAM'}) if gid[2]=='TERM' else BODY[gid[2]]
            body=[d for (f,i),d in slots.items() if f in fields and d['en'] and norm(d['en']) not in ('text','test','todo','unused')]
            if not body:continue
            bodies[gid]=body
            group_signatures[gid]=norm(' '.join(d['en'] for d in sorted(body,key=lambda x:(x['field'],x['sub_index']))))
            for d in body:
                key=(gid,d['field'],d['sub_index']);grams=shingles(d['en']);source_grams[key]=grams
                for gram in grams:index[gram].add(key)
        print('records indexed',game,len(bodies),flush=True)
        for r in entries:
            if r['game']!=game or (r.get('body_ko') and r.get('status') not in ('partial_translation','canonical_game_translation')):continue
            reference=r.get('body_en','');docgrams=shingles(reference)
            if not re.search('[가-힣]',r.get('title_ko','')):
                location=re.sub(r'\s+terminal entries$|\s+terminal$|\s+logs$','',r.get('title_en',''),flags=re.I)
                location=re.sub(r"['’]s$",'',location)
                names=labels.get(title_key(location),set())
                if len(names)==1:r['title_ko']=next(iter(names))+(' 터미널 기록' if r['type']=='terminal' else '')
            scores=Counter();all_scores=Counter();positions={}
            # Unique source passages identify the asset, not merely its subject.
            for gram in docgrams:
                candidates=index.get(gram,set())
                if len(candidates)<300:
                    for key in candidates:all_scores[key]+=1
                gids={key[0] for key in candidates}
                if len(gids)==1 or len({group_signatures[g] for g in gids})==1:
                    for key in candidates:scores[key]+=1
            selected=set();proof=[]
            for previous in r.get('translation_sources',[]):
                if previous.get('field') not in ('TNAM','DESC','RNAM','BTXT','UNAM','NAM1'):continue
                known={g for g in byhash.get(previous.get('source_hash'),set()) if g in bodies}
                if len(known)==1:
                    g=next(iter(known));selected.add(g)
                    proof.append(dict(method='existing_exact_source_hash',source_hash=previous['source_hash'],plugin=g[0],record=g[2],form_id=f'{g[1]:08X}'))
            for key,count in scores.items():
                source_count=len(source_grams[key])
                if count>=8 and count/max(1,source_count)>=.55:
                    selected.add(key[0]);proof.append(dict(plugin=key[0][0],record=key[0][2],form_id=f'{key[0][1]:08X}',field=key[1],sub_index=key[2],distinctive_matches=count,source_shingles=source_count))
            candidate_groups={key[0] for key in all_scores}
            for g in candidate_groups:
                total=sum(len(source_grams[g,d['field'],d['sub_index']]) for d in bodies[g])
                hits=sum(all_scores[g,d['field'],d['sub_index']] for d in bodies[g])
                if total>=12 and hits/max(1,total)>=.90:
                    selected.add(g);proof.append(dict(method='whole_record_reference_containment',plugin=g[0],record=g[2],form_id=f'{g[1]:08X}',matches=hits,total=total))
            # A unique original item name binds a NOTE/BOOK despite wiki typos,
            # handwritten formatting, substituted player names or summaries.
            key=title_key(r.get('title_en',''))
            title_candidates=full_titles.get(key,set()) or (full_titles.get(key[:-1],set()) if key.endswith('s') else set())
            named={g for g in title_candidates if g in bodies and g[2] in ('NOTE','BOOK')}
            if named and len(title_key(r.get('title_en','')))>10:
                selected=named;proof=[dict(method='unique_original_FULL_title',plugin=next(iter(named))[0],form_id=f'{next(iter(named))[1]:08X}')]
            if not selected:continue
            # Only use records consistent with the kind of document.
            if r['type']=='terminal':selected={g for g in selected if g[2] in ('TERM','NOTE','BOOK')}
            elif r['type']=='holotape':selected={g for g in selected if g[2] in ('INFO','NOTE','BOOK')}
            else:
                typed={g for g in selected if g[2] in ('NOTE','BOOK')}
                if typed:selected=typed
            if not selected:continue
            for g in list(selected):
                if g not in direct:continue
                allowed_fields=({'DESC','RNAM'} if g[2]=='TERM' else BODY[g[2]])
                actual_body=[]
                for (tag,i),actual in direct[g].items():
                    if tag not in allowed_fields:continue
                    old=groups[g].get((tag,i),{})
                    data=dict(old,en=old.get('en',''),ko=actual['ko'],dictionary=old.get('dictionary','installed_korean_ESM'),record=g[2],record_index=old.get('record_index'),field=tag,sub_index=i,form_id=actual['form_id'],plugin=g[0],source_hash=old.get('source_hash'),korean_evidence=actual)
                    actual_body.append(data)
                if actual_body:bodies[g]=actual_body
            incomplete=[g for g in selected if any(not d['ko'] for d in bodies[g])]
            if incomplete:
                unresolved.append(dict(id=r['id'],title=r.get('title_en'),reason='unresolved_source_fields',missing=[dict(plugin=g[0],form_id=f'{g[1]:08X}',record=g[2],field=d['field'],index=d['sub_index'],en=d['en'][:160]) for g in incomplete for d in bodies[g] if not d['ko']]))
                continue
            tokens=norm(reference).split()
            doc_positions={}
            for i in range(len(tokens)-3):doc_positions.setdefault(tuple(tokens[i:i+4]),i)
            def order(g):
                anchors=[]
                for d in bodies[g]:
                    ts=norm(d['en']).split()
                    for i in range(max(0,len(ts)-3)):
                        gram=tuple(ts[i:i+4])
                        if gram not in docgrams:continue
                        anchors.append(doc_positions[gram])
                return min(anchors,default=10**9),g
            selected=sorted(selected,key=order)
            chapters=[];provenance=[]
            for n,g in enumerate(selected,1):
                slots=groups[g];name=slots.get(('FULL',0),{}).get('ko') or r.get('title_ko') or r.get('title_en') or f'{g[1]:08X}'
                if not re.search('[가-힣]',name):name=f'기록 {n}'
                lines=[]
                for d in sorted(bodies[g],key=lambda x:(0 if x['field'] in ('DESC','BTXT') else 1,x['sub_index'])):
                    caption=slots.get(('ITXT',d['sub_index']),{}).get('ko') if d['field'] in ('RNAM','UNAM') else None
                    lines.append(('【'+caption+'】\n' if caption else '')+d['ko'])
                    provenance.append({k:v for k,v in d.items() if k not in ('en','ko','priority')})
                chapters.append(('【'+name+'】\n' if len(selected)>1 or r['type']=='terminal' else '')+'\n\n'.join(lines))
            if not chapters:continue
            old_coverage=r.pop('translation_coverage',None)
            r.setdefault('reference_alignment',old_coverage)
            r.update(body_ko='\n\n'.join(chapters),status='canonical_game_translation',body_version='existing_game_translation',translation_sources=provenance,canonical_record_links=proof,translation_coverage=dict(complete=True,method='canonical_game_record_fields',resolved_fields=len(provenance),total_fields=len(provenance)))
            if all(g[2]=='INFO' for g in selected):r['type']='holotape'
            if named:
                g=sorted(named)[0];label=groups[g].get(('FULL',0),{}).get('ko')
                if label and not re.search('[가-힣]',r.get('title_ko','')):r['title_ko']=label
            reports.append(dict(id=r['id'],title=r.get('title_en'),game=game,records=len(selected),fields=len(provenance),body_version=r['body_version']))
        del groups,index,source_grams,bodies
    path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (path.parent/'canonical-record-restore-report.json').write_text(json.dumps(dict(restored=len(reports),entries=reports),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'work/fallout-audit/unresolved-canonical-fields.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2),encoding='utf-8')
    print('restored canonical records',len(reports))

if __name__=='__main__':main()
