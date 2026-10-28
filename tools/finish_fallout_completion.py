"""Finish the audited record-link repair and handle non-text source entries."""
from pathlib import Path
import hashlib
import json
import re
import struct
import zlib
from collections import Counter
from build_starfield_archive import fields

ROOT=Path(__file__).resolve().parents[1]
def linked_voice(path,topic):
    stack=[];rows=[]
    with path.open('rb') as f:
        while h:=f.read(24):
            start=f.tell()-24
            while stack and start>=stack[-1][0]:stack.pop()
            sig,size,flags,fid,_,_=struct.unpack('<4s5I',h)
            if sig==b'GRUP':stack.append((start+size,flags,fid));continue
            if sig!=b'INFO' or not any(label==topic for end,label,kind in stack):f.seek(size,1);continue
            b=f.read(size)
            if flags&0x40000:b=zlib.decompress(b[4:])
            for tag,raw in fields(b):
                if tag=='NAM1':rows.append((f'{fid:08X}',raw.rstrip(b'\0').decode('utf-8')))
    assert rows and all(re.search('[가-힣]',s) for _,s in rows)
    return rows

def main():
    path=ROOT/'docs/fallout/catalog.json';c=json.loads(path.read_text(encoding='utf-8'));entries=c['entries']
    byid={r['id']:r for r in entries}
    # The apparent gap was a missing NOTE -> DIAL -> INFO relationship.
    p=Path(r'D:\Codex_Trans\비바\release-v108-20261026\Output\mods\[NoDelete] [INF] [DB] - Tale of Two Wastelands (TTW)\BrokenSteel.esm')
    voice=linked_voice(p,0x09007D94)
    r=byid['codex-907071b3f7f4fab4']
    r.update(title_ko='엔클레이브 병사 기록 #1',type='holotape',body_ko='\n\n'.join(s for _,s in voice),status='canonical_game_translation',body_version='existing_game_translation',translation_coverage=dict(complete=True,method='NOTE.TNAM -> DIAL child GRUP -> INFO.NAM1',resolved_fields=len(voice),total_fields=len(voice)),canonical_record_links=[dict(plugin='BrokenSteel.esm',note_form_id='09007D9D',dialogue_form_id='09007D94',info_form_ids=sorted({fid for fid,s in voice}))],translation_sources=[dict(dictionary='설치된 한국어 BrokenSteel.esm',record='INFO',field='NAM1',form_id=fid,sub_index=i,korean_sha256=hashlib.sha256(s.encode()).hexdigest()) for i,(fid,s) in enumerate(voice)])
    completions=json.loads((path.parent/'editorial-completions.json').read_text(encoding='utf-8'))
    for id,translation in completions.items():
        r=byid[id]
        r.update(body_ko=translation['body_ko'],title_ko=translation['title_ko'],status='editorial_translation',translation_coverage=dict(complete=True,method='new_editorial_translation'),editorial_translation=dict(basis=translation['basis'],source_english_sha256=hashlib.sha256(r['body_en'].encode()).hexdigest(),review_status='archive translation; independent editorial review pending'))
        if translation.get('dlc_group'):r['dlc_group']=translation['dlc_group'];r['content_scope']='creation_club'
    # Alphabetic puzzle symbols must remain the original symbols, not be
    # "translated" into Hangul. Their surrounding item labels are localized.
    r=byid['codex-210b550f558d48c6'];r['language_neutral_payload']=True
    # These are inventory descriptions or a music track, not absent text pages.
    excluded={
      'codex-963d22743296be2f':'item_description_only; no readable economic-data text',
      'codex-f7c5dd6276e9744b':'item_description_only; no readable reactor-data text',
      'codex-63bd7b027aec40d2':'music playback; EPUB supplies a fan transcription of lyrics rather than a localized game text record',
    }
    teachings=next(r for r in entries if r.get('title_en')=='Hubologist teachings')
    hub_id='codex-3d8d3956f77c9e68'
    teachings.setdefault('aliases',[]).append(hub_id);teachings['aliases']=list(dict.fromkeys(teachings['aliases']))
    excluded[hub_id]='inventory-description duplicate; reading body is Hubologist teachings'
    c['entries']=[r for r in entries if r['id'] not in excluded]
    for r in c['entries']:
        if r.get('canonical_record_links') and r.get('series_entries'):
            r['reference_series_members']=[{k:x[k] for k in ('id','title_en','title_ko','source_member','editor_id','form_id') if k in x} for x in r.pop('series_entries')]
            r['series_member_count']=len(r['reference_series_members'])
    path.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(records=len(c['entries']),unresolved_translation_links=sum(not r.get('body_ko') or r.get('status')=='partial_translation' for r in c['entries']),editorial_completions=list(completions),non_reading_entries_excluded=excluded,method='Existing game translations restored by source records and voice-topic linkage; no machine-generated substitute for FO3/FNV/FO4 base-game/DLC translations')
    resolved={i for r in c['entries'] for i in (r['id'],*r.get('aliases',[]))}
    report['merged_description_aliases']={i:excluded.pop(i) for i in list(excluded) if i in resolved}
    target_path=path.parent/'completion-targets.json'
    if target_path.exists():
        targets=json.loads(target_path.read_text(encoding='utf-8'))['target_ids']
        assert set(targets)-resolved==set(excluded)
        report.update(original_target_records=len(targets),resolved_target_records=sum(i in resolved for i in targets),existing_translation_targets=sum(i in resolved for i in targets)-len(completions),excluded_non_reading_targets=len(excluded))
    report.update(categories=dict(Counter(r['type'] for r in c['entries'])),game_records=dict(Counter(r['game'] for r in c['entries'])))
    (path.parent/'completion-audit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert report['unresolved_translation_links']==0
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':main()
