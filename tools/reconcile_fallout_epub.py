"""Align EPUB prose to existing Korean translations by exact English word sequence.

Typography and whitespace are normalized. No fuzzy/similarity matching. Original
SST text stays local; public records retain translation hashes and provenance.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import html
import json
from pathlib import Path
import re
import zipfile
from bs4 import BeautifulSoup
from read_xtranslator_sst import parse_sst
from link_fallout_translations import PLUGINS
from group_fallout_terminals import expand,group
from group_fallout_series import group_series

ROOT=Path(__file__).resolve().parents[1]
def clean(s):
    s=re.sub(r'<br\s*/?>|\[pagebreak\]','\n',s,flags=re.I)
    s=re.sub(r'</(?:p|div)>','\n\n',s,flags=re.I)
    s=re.sub(r'</?(?:font|p|div|b|strong|i|u|img|textformat)\b[^>]*>','',s,flags=re.I)
    return html.unescape(s).strip()
def words(s):return re.findall(r'[a-z0-9]+',clean(s).casefold())
def norm(s):return ' '.join(words(s))

def main(root,source=None):
    corpus=defaultdict(list);titles=defaultdict(list)
    override_path=ROOT/'docs/fallout/translation-alignment-overrides.json'
    overrides=json.loads(override_path.read_text(encoding='utf-8')) if override_path.exists() else {}
    override_rows={}
    for game,plugins in PLUGINS.items():
        folder=root/('Fallout4' if game=='fo4' else 'FalloutNV')
        # FO3 translations also exist in TTW dictionaries; require identical prose.
        files=[folder/(p.lower()+'_en_ko.sst') for p in plugins]
        if game=='fo3':files.append(folder/'falloutnv_en_ko.sst')
        if game in ('fo3','fnv'):
            files.extend(folder/name for name in ('fallout nv kr_en_ko.sst','taleoftwowastelands_en_ko.sst'))
        for file in files:
            if not file.exists():continue
            parsed=parse_sst(file,max_file_bytes=96*1024*1024)
            for index,r in enumerate(parsed['records']):
                en=r['source'];ko=clean(r['korean']);key=norm(en)
                if not re.search('[가-힣]',ko) or '\ufffd' in ko or not key:continue
                src=dict(dictionary=file.name,record_index=index,record=r['record_name'],field=r['field_name'],form_id=r['form_id'],source_hash=hashlib.sha256(en.encode()).hexdigest(),ko_hash=hashlib.sha256(ko.encode()).hexdigest())
                for doc_id,override in overrides.items():
                    if file.name==override['dictionary'] and index==override['record_index'] and src['source_hash']==override['source_sha256']:
                        override_rows[doc_id]=(ko,src)
                if r['field_name']=='FULL':titles[game,key].append((ko,src))
                if r['record_name'] in ('INFO','NOTE','BOOK','TERM') and len(words(en))>=4:
                    corpus[game,key].append((ko,src))
    base_texts=set()
    import gzip
    for p in (ROOT/'Fallout4/BaseGame').rglob('*.jsonl.gz'):
        with gzip.open(p,'rt',encoding='utf-8') as f:
            for line in f:
                row=json.loads(line)
                if row.get('ko'):base_texts.add(clean(row['ko']))
    resolved={};prefix=defaultdict(list)
    for (game,key),values in corpus.items():
        preferred={'fo3':'fallout3_en_ko.sst','fnv':'falloutnv_en_ko.sst','fo4':'fallout4_en_ko.sst'}[game]
        preferred_values=[x for x in values if x[1]['dictionary']==preferred]
        if preferred_values:values=preferred_values
        prose=[x for x in values if x[1]['record'] in ('NOTE','BOOK')]
        if prose:values=prose
        unique={ko for ko,_ in values}
        if len(unique)>1 and game=='fo4':
            canonical=[x for x in values if x[0] in base_texts]
            if canonical:values=canonical;unique={ko for ko,_ in values}
        if len(unique)!=1:continue
        resolved[game,key]=values[0]
        prefix[game,tuple(key.split()[:3])].append(key)
    for v in prefix.values():v.sort(key=len,reverse=True)
    target=ROOT/'docs/fallout/catalog.json'
    catalog=json.loads((source or target).read_text(encoding='utf-8'))
    entries=expand(catalog['entries'])
    stats=Counter();examples=[]
    with zipfile.ZipFile(ROOT/'work/fallout_codex/Fallout.epub') as z:
        for r in entries:
            if not r.get('source_member') or r['game'] not in PLUGINS:continue
            r['body_ko']=None
            for key in ('translation_coverage','translation_sources','editorial_supplements'):r.pop(key,None)
            r['type']='terminal' if 'Terminal' in r.get('dlc_group','') else 'holodisk_note'
            r['status']='epub_original'
            soup=BeautifulSoup(z.read(r['source_member']),'html.parser')
            for tag in soup.select('head,h1,.author,script,style'):tag.decompose()
            blocks=soup.body.find_all(['p','h2','h3','h4','li'],recursive=True)
            merged=[];pending=[]
            for block in blocks:
                text=block.get_text(' ',strip=True)
                bold=block.find(['b','strong'])
                heading=block.name.startswith('h') or (bold and text==bold.get_text(' ',strip=True)) or bool(re.fullmatch(r'Message to .+\.?',text))
                if heading:
                    if pending:merged.append(('\n\n'.join(pending),False));pending=[]
                    merged.append((text,True))
                elif text:pending.append(text)
            if pending:merged.append(('\n\n'.join(pending),False))
            translated=[];sources=[];matched_words=total_words=0;unmatched=[]
            title_options=titles.get((r['game'],norm(r.get('title_en',''))),[])
            if len({x[0] for x in title_options})==1:r['title_ko']=title_options[0][0]
            if r['id'] in override_rows and hashlib.sha256(r['body_en'].encode()).hexdigest()==overrides[r['id']]['epub_sha256']:
                ko,src=override_rows[r['id']]
                n=len(words(r['body_en']))
                r.update(body_ko=ko,translation_sources=[src],status='linked_translation',type='document',translation_coverage=dict(matched_words=n,total_words=n,complete=True,method='explicit_hash_checked_alignment; '+overrides[r['id']]['alignment_check']))
                r['body_version']=overrides[r['id']].get('body_version','existing_game_translation')
                if re.search(r'holo(?:tape|disk|message)|audio',r.get('title_en',''),re.I):r['type']='holotape'
                stats['linked_documents']+=1;stats['complete']+=1
                continue
            # A NOTE/BOOK can contain its own date headings. Match the whole
            # document before splitting at EPUB headings, which are only layout.
            full_key=norm(soup.body.get_text(' ',strip=True))
            full=resolved.get((r['game'],full_key))
            if full and full[1]['record'] in ('NOTE','BOOK'):
                ko,src=full
                r.update(body_ko=ko,translation_sources=[src],status='linked_translation',type='terminal' if r['type']=='terminal' else 'document',translation_coverage=dict(matched_words=len(full_key.split()),total_words=len(full_key.split()),complete=True,method='whole_document_exact_words; formatting_tags_removed'))
                stats['linked_documents']+=1;stats['complete']+=1
                continue
            for text,heading in merged:
                if not text:continue
                token_matches=list(re.finditer(r'[a-z0-9]+',text,re.I))
                tokens=[m.group().casefold() for m in token_matches]
                if heading:
                    h=titles.get((r['game'],norm(text)),[])
                    label=h[0][0] if len({x[0] for x in h})==1 else text
                    label=re.sub(r'^(\d+) of (\d+)$',r'\2개 중 \1',label)
                    label=re.sub(r'^Message to (.+?)\.?$',r'\1에게 보내는 메시지',label)
                    label=re.sub(r'^Eddie Winter Holotape (\d+)$',r'에디 윈터 홀로테이프 \1',label)
                    translated.append('【'+label+'】');continue
                if not tokens:continue
                total_words+=len(tokens);i=0;pieces=[];gaps=[]
                while i<len(tokens):
                    found=None
                    for key in prefix.get((r['game'],tuple(tokens[i:i+3])),[]):
                        candidate=key.split();n=len(candidate)
                        if tokens[i:i+n]==candidate:
                            if n<8 and not (i==0 and n==len(tokens)):
                                before=text[:token_matches[i].start()].rstrip()
                                after=text[token_matches[i+n-1].end():].lstrip()
                                if (before and before[-1] not in '.!?:') or (after and after[0] not in '.!?'):continue
                            found=(key,n);break
                    if found:
                        if gaps:pieces.append('[미번역 원문] '+text[token_matches[i-len(gaps)].start():token_matches[i].start()]);unmatched.extend(gaps);gaps=[]
                        key,n=found;ko,src=resolved[r['game'],key];pieces.append(ko);sources.append(src);matched_words+=n;i+=n
                    else:gaps.append(tokens[i]);i+=1
                if gaps:
                    original=text[token_matches[i-len(gaps)].start():]
                    directions={'static':'잡음','sigh':'한숨','sighs':'한숨','laughs':'웃음','laughing':'웃음','gunshot':'총성','gunshots':'총성'}
                    if len(gaps)==1 and gaps[0] in directions:pieces.append('['+directions[gaps[0]]+']');matched_words+=1
                    else:pieces.append('[미번역 원문] '+original);unmatched.extend(gaps)
                translated.append('\n'.join(pieces))
            if matched_words:
                r['body_ko']='\n\n'.join(translated)
                r['translation_sources']=sources
                r['translation_coverage']=dict(matched_words=matched_words,total_words=total_words,complete=not unmatched,method='exact_english_word_sequence; typography_normalized')
                r['status']='linked_translation' if not unmatched else 'partial_translation'
                if r['type']=='terminal':pass
                elif any(s['record']=='INFO' for s in sources) and not any(s['record'] in ('NOTE','BOOK') for s in sources) and matched_words/max(total_words,1)>=.5:r['type']='holotape'
                elif r['type']!='terminal':r['type']='document'
                stats['linked_documents']+=1;stats['complete' if not unmatched else 'partial']+=1
                if 'Keller Family' in r.get('title_en','') or 'Eddie Winter Holotapes' in r.get('title_en',''):examples.append(dict(title=r['title_en'],coverage=r['translation_coverage'],gaps=unmatched[:80]))
    catalog['entries']=group_series(group(entries))[0]
    target.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(counts=dict(stats),examples=examples)
    (target.parent/'epub-translation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dictionaries',type=Path,required=True);p.add_argument('--source',type=Path);args=p.parse_args();main(args.dictionaries,args.source)
