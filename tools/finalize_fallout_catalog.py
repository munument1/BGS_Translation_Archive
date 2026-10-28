"""Publish only readable entries in three mutually exclusive categories."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
def main():
    target=ROOT/'docs/fallout/catalog.json'
    c=json.loads(target.read_text(encoding='utf-8'))
    from group_fallout_series import group_series
    c['entries']=group_series(c['entries'])[0]
    supplements=json.loads((target.parent/'translation-supplements.json').read_text(encoding='utf-8'))
    kept=[];removed=[]
    for r in c['entries']:
        if not (r.get('body_ko','') or r.get('body_en','')):
            removed.append(r);continue
        if r.get('series_entries') and any(s.get('translation_coverage') for s in r['series_entries']):
            children=r['series_entries']
            total=sum(s.get('translation_coverage',{}).get('total_words',len(re.findall(r'[a-z0-9]+',s.get('body_en',''),re.I))) for s in children)
            matched=sum(s.get('translation_coverage',{}).get('matched_words',0) for s in children)
            complete=all(s.get('translation_coverage',{}).get('complete',False) for s in children)
            r['translation_coverage']=dict(total_words=total,matched_words=matched,complete=complete,method='aggregate_series_members')
            r['translation_sources']=[src for s in children for src in s.get('translation_sources',[])]
            r['body_ko']='\n\n'.join('【'+(s.get('title_ko') or s.get('title_en') or s['id'])+'】\n'+(s.get('body_ko') or '[미번역 원문]\n'+s.get('body_en','')) for s in children)
        supplement=supplements.get(r.get('title_en',''))
        if supplement:
            r['title_ko']=supplement['title_ko']
            for en,ko in supplement['paragraphs']:
                needle='[미번역 원문] '+en
                if needle in (r.get('body_ko') or ''):
                    r['body_ko']=r['body_ko'].replace(needle,ko)
                    r.setdefault('editorial_supplements',[]).append(dict(source_sha256=hashlib.sha256(en.encode()).hexdigest(),ko_sha256=hashlib.sha256(ko.encode()).hexdigest(),basis='EPUB wording supplement; archive translation, not in-game reviewed'))
            if r.get('translation_coverage') and '[미번역 원문]' not in r.get('body_ko',''):
                r['translation_coverage']['complete']=True
                r['translation_coverage']['matched_words']=r['translation_coverage']['total_words']
                r['status']='linked_translation'
        # Keep a single category; historical holodisk/holotape names are synonyms.
        previous=r['type'];r.setdefault('original_type',previous)
        r['type']='terminal' if previous=='terminal' else 'holotape' if previous in ('holotape','holodisk') else 'document'
        if r.get('translation_coverage'):
            cv=r['translation_coverage']
            r['status']='linked_translation' if cv['complete'] else 'partial_translation'
        kept.append(r)
    # The same English body matched to a single source NOTE/BOOK is the same
    # document already represented by the ESM item. Prefer the bilingual entry.
    hashes={}
    for r in kept:
        if r.get('source_member') and r.get('translation_coverage',{}).get('complete'):
            sources=r.get('translation_sources',[])
            if len(sources)==1 and sources[0]['record'] in ('NOTE','BOOK'):
                hashes[r['game'],sources[0]['source_hash']]=r
    output=[];merged=0
    for r in kept:
        key=(r['game'],r.get('translation_source',{}).get('source_hash'))
        dest=hashes.get(key)
        if dest and dest is not r and r['type']!='terminal':
            dest.setdefault('aliases',[]).append(r['id']);merged+=1
        else:output.append(r)
    c['entries']=output
    c['public_policy']='readable_entries_only; terminal / holotape / document'
    target.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    work=ROOT/'work/fallout_cleanup';work.mkdir(parents=True,exist_ok=True)
    if removed:(work/'excluded-no-body.json').write_text(json.dumps(removed,ensure_ascii=False,indent=2),encoding='utf-8')
    previous=json.loads((target.parent/'cleanup-report.json').read_text(encoding='utf-8')) if (target.parent/'cleanup-report.json').exists() else {}
    report=dict(removed_no_body=len(removed) or previous.get('removed_no_body',0),merged_duplicate_documents=merged or previous.get('merged_duplicate_documents',0),records=len(output),categories=dict(Counter(r['type'] for r in output)),korean_records=sum(bool(r.get('body_ko')) for r in output),english_only=sum(bool(r.get('body_en')) and not r.get('body_ko') for r in output),epub_fully_translated=sum(r.get('translation_coverage',{}).get('complete',False) for r in output),epub_partly_translated=sum(r.get('status')=='partial_translation' for r in output),holotapes_with_korean=sum(r['type']=='holotape' and bool(r.get('body_ko')) for r in output))
    (target.parent/'cleanup-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
