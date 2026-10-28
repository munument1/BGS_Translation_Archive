"""Read ESO .lang book records and bind unique original titles to archive IDs.

No fuzzy matching, translation generation or network writes. The source .lang
and third-party lookup stay local; published imports retain hashes and IDs.
"""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
TITLE_GROUP=51188213
BODY_GROUP=21337012

def read_books(path):
    data=Path(path).read_bytes()
    if len(data)<8:raise ValueError('Truncated lang header')
    version,count=struct.unpack_from('>II',data)
    if version!=2:raise ValueError('Unsupported lang version')
    base=8+count*16
    if base>len(data):raise ValueError('Truncated lang index')
    records={}
    for pos in range(8,base,16):
        group,variant,index,offset=struct.unpack_from('>4I',data,pos)
        if group not in (TITLE_GROUP,BODY_GROUP) or variant!=0:continue
        start=base+offset
        if start>=len(data):raise ValueError('Invalid string offset')
        end=data.find(b'\0',start)
        if end<0:raise ValueError('Unterminated string')
        key=(group,index)
        if key in records:raise ValueError('Duplicate book string key')
        records[key]=data[start:end].decode('utf-8')
    return records,dict(file_name=Path(path).name,file_sha256=hashlib.sha256(data).hexdigest(),version=version,total_strings=count)

def title_key(text):
    text=re.sub(r'\s*\[ESO\]\s*$','',text,flags=re.I)
    return re.sub(r'[^\w]','',unicodedata.normalize('NFKC',text).casefold())

def plain_text(text):
    text=re.sub(r'\|t[^|]*\|t','[게임 내 삽화]',text)
    text=re.sub(r'\|a\d+:\d+:[^|\n]*\|a','[게임 내 도안]',text)
    text=re.sub(r'\|L[^|]*\|l','',text)
    text=re.sub(r'\|c[0-9a-fA-F]{6}','',text)
    text=re.sub(r'\|[Dd][a-zA-Z]','',text)
    text=re.sub(r'\|[Aa][cClLrRsS]|\|[rl]','',text)
    return re.sub(r'\n{4,}','\n\n\n',text.replace('\r\n','\n')).strip()

def read_title_map(path):
    text=Path(path).read_text(encoding='utf-8')
    blocks=re.findall(r'^  \[(\d+)\] = \{\n(.*?)(?=^  \[\d+\] = \{|^})',text,re.M|re.S)
    books={}
    for index,block in blocks:
        match=re.search(r'\["n"\] = "((?:\\.|[^"\\])*)"',block)
        if match:
            title=match[1].replace('\\"','"').replace("\\'","'").replace('\\n','\n')
            books[int(index)]=title
    return books,hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main(lang,title_map,map_url):
    strings,source=read_books(lang);names,map_sha=read_title_map(title_map)
    index=defaultdict(list)
    for book_id,name in names.items():index[title_key(name)].append(book_id)
    folder=ROOT/'docs/books'
    references=json.loads((folder/'imperial_game_books_catalog.json').read_text(encoding='utf-8'))['entries']
    english={r['uid']:r for r in json.loads((folder/'external_english_texts.json').read_text(encoding='utf-8'))['entries']}
    preserved={r['uid'] for r in json.loads((folder/'external_korean_texts.json').read_text(encoding='utf-8'))['entries'] if r.get('coverage')=='full'}
    out=[];deferred=[]
    for ref in references:
        if ref['game'] not in ('eso','eso_journals'):continue
        ids=index.get(title_key(ref['title_en']),[])
        valid=[i for i in ids if strings.get((TITLE_GROUP,i),'').strip() and re.search('[가-힣]',strings.get((BODY_GROUP,i),''))]
        if not valid:reason='no_unique_original_title_match'
        elif len({strings[BODY_GROUP,i] for i in valid})>1:reason='same_title_multiple_distinct_game_bodies'
        elif ref['uid'] in preserved:reason='preserve_existing_full_translation'
        else:
            book_id=valid[0];raw=strings[BODY_GROUP,book_id];body=plain_text(raw)
            out.append(dict(uid=ref['uid'],game=ref['game'],title_en=ref['title_en'],title_ko=plain_text(strings[TITLE_GROUP,book_id]),body_ko=body,coverage='existing_game_record',source_sha256=english.get(ref['uid'],{}).get('source_sha256'),source_url=english.get(ref['uid'],ref)['source_url'],translation_source='User-supplied ESO Korean language patch (kr.lang)',translation_source_url='https://esokr.org/',eso_book_id=book_id,equivalent_book_ids=valid,body_group=BODY_GROUP,title_group=TITLE_GROUP,raw_body_sha256=hashlib.sha256(raw.encode()).hexdigest(),raw_title_sha256=hashlib.sha256(strings[TITLE_GROUP,book_id].encode()).hexdigest(),has_runtime_parameters='<<' in raw,has_embedded_art=bool(re.search(r'\|t|\|a\d+:',raw)),match_method='unique_original_title_to_game_book_ID; identical-body variants allowed',needs_translation_review=True))
            continue
        deferred.append(dict(uid=ref['uid'],title_en=ref['title_en'],reason=reason,candidate_book_ids=valid))
    source.update(title_map_url=map_url,title_map_sha256=map_sha)
    result=dict(schema_version=1,source=source,scope='Existing ESO reading entries matched by original title and game book ID; not all language strings or all ESO books',entries=out)
    (folder/'eso_korean_imports.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(source=source,unique_game_book_ids=len({r['eso_book_id'] for r in out}),book_titles=sum(g==TITLE_GROUP for g,i in strings),book_bodies=sum(g==BODY_GROUP for g,i in strings),imported=len(out),by_shelf=dict(Counter(r['game'] for r in out)),deferred_counts=dict(Counter(r['reason'] for r in deferred)),deferred=deferred,method='No fuzzy title matching; different bodies with the same title remain unlinked. Imported Korean is the game record version, not a claim of an exact translation of the editorial English compilation.')
    (folder/'eso_korean_import_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source','deferred')},ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--lang',type=Path,required=True);p.add_argument('--title-map',type=Path,required=True);p.add_argument('--map-url',required=True);a=p.parse_args();main(a.lang,a.title_map,a.map_url)
