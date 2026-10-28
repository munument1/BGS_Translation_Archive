"""Restore source-backed Fallout document typography without changing catalog text.

Input: raw-source-audit.json produced by audit_fallout_document_sources.py.
Only exact whitespace-insensitive source matches are accepted; no fuzzy matching.
Unknown runtime tags (Alias/Token) remain literal text. Short source-styled blocks
are headings; inline emphasis and long centered prose are not promoted.
"""
import argparse,hashlib,html,json,re
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def compact(s):return re.sub(r'\s','',s)
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
KNOWN=r'font|p|div|b|strong|i|u|img|textformat|body|html|span'
TOKEN=re.compile(r'</?(?:'+KNOWN+r')\b[^>]*>|<br\s*/?>|\[pagebreak\]',re.I)
def attr(tag,name):
 m=re.search(r'\b'+name+r'\s*=\s*[\x22\x27]?([^\x22\x27\s>]+)',tag,re.I)
 return m[1].lower() if m else ''
def raw_layout(raw):
 # Each run carries source character offsets plus source style evidence.
 text='';runs=[];stack={'font':[],'p':[],'div':[],'b':[],'strong':[],'u':[]};end=0
 def emit(value):
  nonlocal text
  value=html.unescape(value).replace('\r\n','\n').replace('\r','\n')
  start=len(text);text+=value
  if value:runs.append((start,len(text),value,{k:list(v) for k,v in stack.items()}))
 for m in TOKEN.finditer(raw):
  emit(raw[end:m.start()]);tag=m[0];end=m.end();name=re.match(r'</?([a-z]+)',tag,re.I)
  if not name or name[1].lower()=='br':emit('\n');continue
  name=name[1].lower();closing=tag.startswith('</')
  if name=='img':emit('[게임 내 이미지]');continue
  if name in ('p','div'):emit('\n\n')
  if name in stack:
   if closing:
    if stack[name]:stack[name].pop()
   else:
    if name in ('p','div'):stack[name]=[tag]
    else:stack[name].append(tag)
 emit(raw[end:]);norm=compact(text);positions=[i for i,c in enumerate(text) if not c.isspace()]
 def offset(i):return len(compact(text[:i]))
 headings=[]
 sizes=[int(attr(t,'size')) for t in TOKEN.findall(raw) if t.lower().startswith('<font') and attr(t,'size').isdigit()]
 size_counts=Counter()
 for run in runs:
  size=next((attr(t,'size') for t in reversed(run[3]['font']) if attr(t,'size')),'')
  if size.isdigit():size_counts[int(size)]+=len(compact(run[2]))
 baseline=size_counts.most_common(1)[0][0] if size_counts else 18
 emphasized=set()
 for m in re.finditer(r'<(b|u|strong)\b[^>]*>(.*?)</\1>',raw,re.I|re.S):
  val=TOKEN.sub('',m[2]);lines=[compact(t) for t in html.unescape(val).splitlines() if compact(t)]
  if len(compact(val))<=120 and len(lines)<=3:emphasized.update(lines)
 has_left=bool(re.search(r'<(?:p|div)\b[^>]*align\s*=\s*[\x22\x27]?left',raw,re.I))
 # Line-based style evaluation requires a whole standalone line, never just
 # an inline emphasized word in a longer sentence.
 for line in re.finditer(r'[^\n]+',text):
  val=line[0].strip()
  if not val or len(val)>140:continue
  relevant=[r for r in runs if r[0]<line.end() and r[1]>line.start() and r[2].strip()]
  if not relevant:continue
  def style(run):
   st=run[3];fonts=st['font'];size=next((attr(t,'size') for t in reversed(fonts) if attr(t,'size')),'')
   face=next((attr(t,'face') for t in reversed(fonts) if attr(t,'face')),'')
   sized=size.isdigit() and int(size)>baseline and int(size)>=16 and not re.search(r'handwrit|brody',face,re.I)
   paragraphs=st['p'] or st['div']
   centered=bool(paragraphs and attr(paragraphs[-1],'align')=='center')
   emphasis=compact(val) in emphasized
   return sized,centered,emphasis
  styles=[style(r) for r in relevant]
  # A source centered block is heading evidence only when the entire paragraph
  # is short; this avoids turning centered letters/poems into dozens of titles.
  pstart=text.rfind('\n\n',0,line.start())+2
  if pstart==1:pstart=0
  pend=text.find('\n\n',line.end());pend=len(text) if pend<0 else pend
  centered_short=has_left and len(compact(text[pstart:pend]))<=120 and len([t for t in text[pstart:pend].splitlines() if t.strip()])<=4
  if all(s[0] or s[1] and centered_short or s[2] for s in styles):
   if len(val)<2 or len(val)>90 or not re.search(r'[가-힣A-Za-z0-9]',val) or re.match(r'[-*•]|\d+[.)]',val):continue
   if len(val)>20 and re.search(r'[가-힣][.!]$',val):continue
   headings.append((offset(line.start()),offset(line.end()),3 if not headings else 4,'source typography'))
 breaks={offset(m.end()) for m in re.finditer(r'\n[ \t]*\n',text)}
 return text,norm,headings,breaks

def main(source_audit):
 rows=json.loads(source_audit.read_text(encoding='utf-8'))
 dest=ROOT/'docs/fallout/document-layout-overrides.json'
 # Preserve the two fully audited examples, including exact letter paragraphs.
 previous=json.loads(dest.read_text(encoding='utf-8'))['entries'] if dest.exists() else {}
 pinned={k:v for k,v in previous.items() if k in ['sst-fo3-fallout3-note-060758a0-tnam-0','sst-fo3-fallout3-note-060c339c-tnam-0']}
 rules=json.loads((ROOT/'tools/data/fallout-document-heading-rules.json').read_text(encoding='utf-8'))['rules']
 layouts={};stats=Counter();misses=[];example=[]
 # Exact source identity also applies the two carefully audited layouts to
 # canonical EPUB records and duplicates with the same Korean text.
 pinned_by_body={compact(next(r['body'] for r in rows if r['id']==k)):v for k,v in pinned.items()}
 for r in rows:
  body=r['body'];norm=compact(body);positions=[i for i,c in enumerate(body) if not c.isspace()];headings=[];breaks=set();provenance=[];methods=set();flatten=False
  if norm in pinned_by_body:
   layout=dict(pinned_by_body[norm]);layout['body_sha256']=sha(body);layouts[r['id']]=layout;stats['audited_examples']+=1;continue
  for part in r['parts']:
   raw=part['ko'];visible,pnorm,hs,bs=raw_layout(raw)
   if not pnorm:continue
   start=norm.find(pnorm)
   if start<0:
    # FO3/4 historically dropped source image tags while FO76 retains a label.
    visible=visible.replace('[게임 내 이미지]','');pnorm=compact(visible);hs=[];bs=set();start=norm.find(pnorm)
   if start<0:stats['source_parts_not_exact']+=1;continue
   provenance.append(dict(**part['source'],raw_korean_sha256=sha(raw),raw_english_sha256=sha(part['en'])))
   if hs:
    headings.extend((start+a,start+b,level,basis) for a,b,level,basis in hs);methods.add('source typography')
   breaks.update(start+b for b in bs)
   for rule in rules:
    en=part['en'].replace('\r\n','\n').strip()
    if not en.startswith(rule['english_header'].strip()):continue
    prefix=''.join(compact(h) for h in rule['korean_header_lines'])
    if not pnorm.startswith(prefix):continue
    pos=start
    for i,title in enumerate(rule['korean_header_lines']):
     finish=pos+len(compact(title));headings.append((pos,finish,3 if i==0 else 4,'audited bilingual header'));pos=finish
    methods.add('audited bilingual header')
    # Structured fields use the exact corresponding English field labels as
    # evidence; insert paragraph boundaries without rewording any values.
    labels={'Position:':'보직:', 'Age:':'나이:', 'Term of Contract:':'계약 기간:', 'Merits/Demerits:':'상점/벌점:', 'Pay:':'보수:', 'Status:':'상태:', 'Description:':'설명:', 'Repair Log:':'수리 기록:', 'Incident:':'사고 내용:', 'Diagnosis:':'진단:', 'Symptoms:':'증상:', 'Attendees:':'참석자:', 'Summary:':'요약:', 'Projected Income:':'예상 수입:', 'Acquired Income:':'얻은 수입:'}
    for english,korean in labels.items():
     if english.lower() in en.lower():
      at=pnorm.find(compact(korean),len(prefix))
      if at>=0:breaks.add(start+at)
    for m in re.finditer(r'(?:^|\n)[ \t]*[-*•](?=[^\n])',visible):
     breaks.add(start+len(compact(visible[:m.start()])))
    # Remove forced mid-word game display wraps only for confirmed collapsed
    # FO3 records, where source English has title + paragraph separators.
    first=rule['korean_header_lines'][0]
    raw_first=raw.replace('\r\n','\n').split('\n')[0]
    if r['game']=='fo3' and not re.search(r'\n\s*\n',raw.replace('\r\n','\n')) and not raw_first.strip()==first.strip():flatten=True
   # A standalone short label followed by a source list is a section boundary.
   for match in re.finditer(r'(?:^|\n\s*\n)([^\n]{2,36})\n(?=[ \t]*[-*•])',visible):
    title=match[1].strip()
    if not title or re.search(r'[.!?。！？]$',title) or re.match(r'[-*•]|\d+[.)]',title):continue
    a=len(compact(visible[:match.start(1)]));b=a+len(compact(title))
    headings.append((start+a,start+b,4,'source list section'));methods.add('source list section')
  if not headings:continue
  # Preserve already explicit series/document section markers alongside source headings.
  for m in re.finditer(r'^[ \t]*(?:【[^\r\n】]+】|={2,}[^\r\n]+?={2,}|#{1,3}[ \t]+[^\r\n]+)[ \t]*\r?$',body,re.M):
   if not re.search(r'[가-힣A-Za-z0-9]',m[0]):continue
   a=len(compact(body[:m.start()]));b=len(compact(body[:m.end()]))
   headings.append((a,b,3,'explicit archive heading'))
  accepted=[]
  for a,b,level,basis in sorted(set(headings),key=lambda h:(h[0],-(h[1]-h[0]))):
   if a>=b or a<0 or b>len(norm) or accepted and a<accepted[-1][1]:continue
   accepted.append((a,b,level,basis))
  def original(a,b):
   if a==b:return ''
   s=body[positions[a]:positions[b-1]+1].strip()
   return s.replace('\r\n','').replace('\n','').replace('\r','') if flatten else s.replace('\r\n','\n').replace('\r','\n')
  blocks=[];cursor=0
  def prose(a,b):
   cuts=[a]+sorted(p for p in breaks if a<p<b)+[b]
   for lo,hi in zip(cuts,cuts[1:]):
    s=original(lo,hi)
    if s:blocks.append(dict(type='text',text=s))
  for a,b,level,basis in accepted:
   prose(cursor,a);s=original(a,b);title=re.sub(r'\s+',' ',s)
   blocks.append(dict(type='heading',text=s,title=title,level=level));cursor=b
  prose(cursor,len(norm))
  assert compact(''.join(b['text'] for b in blocks))==norm,r['id']
  layouts[r['id']]=dict(body_sha256=sha(body),basis='; '.join(sorted(methods)),sources=provenance,blocks=blocks)
  stats.update(methods)
  if len(example)<30:example.append(dict(id=r['id'],title=r['title'],headings=[b['title'] for b in blocks if b['type']=='heading']))
 output=dict(schema_version=1,entries=dict(sorted(layouts.items())))
 dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report=dict(documents_scanned=len(rows),documents_with_recovered_source=sum(bool(r['parts']) for r in rows),documents_with_restored_layout=len(layouts),headings=sum(sum(b['type']=='heading' for b in l['blocks']) for l in layouts.values()),methods=dict(stats),wording_preservation='Every layout matches its catalog body SHA-256 and the complete non-whitespace character sequence.',examples=example)
 (ROOT/'docs/fallout/document-layout-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='examples'},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-audit',type=Path,default=ROOT/'work/document-layout-audit/raw-source-audit.json');a=p.parse_args();main(a.source_audit)
