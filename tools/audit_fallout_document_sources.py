"""Read source dictionaries and localized strings; never modify game files."""
import argparse,json,sys,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from read_xtranslator_sst import parse_sst
from extract_fallout_esm import string_table
parser=argparse.ArgumentParser(description='Recover exact game translation source strings for layout auditing. Raw source output stays local.')
parser.add_argument('--dictionary-root',type=Path,required=True)
parser.add_argument('--fo76-strings',type=Path,required=True)
parser.add_argument('--output',type=Path,default=ROOT/'work/document-layout-audit')
args=parser.parse_args()
root=args.output;root.mkdir(parents=True,exist_ok=True)
rows=[r for r in json.loads((ROOT/'docs/fallout/catalog.json').read_text(encoding='utf-8'))['entries'] if r['type']=='document'];needed=collections.defaultdict(set)
for r in rows:
 for t in ([r['translation_source']] if r.get('translation_source') else r.get('translation_sources',[])):
  name=t.get('dictionary','').lower();idx=t.get('record_index',t.get('dictionary_record_index'))
  if name.endswith('.sst') and idx is not None:needed[name].add(idx)
files={p.name.lower():p for folder in ['FalloutNV','Fallout4'] for p in (args.dictionary_root/folder).glob('*.sst') if p.name.lower() in needed}
source={}
for name,indices in needed.items():
 if name not in files:continue
 d=parse_sst(files[name],max_file_bytes=96*1024*1024)
 for idx in indices:
  if idx<len(d['records']):source[name,idx]=d['records'][idx]
ko76={k:string_table(args.fo76_strings/('seventysix_ko.'+k),'utf-8') for k in ['strings','dlstrings','ilstrings']}
en76={k:string_table(args.fo76_strings/('seventysix_en.'+k)) for k in ['strings','dlstrings','ilstrings']}
out=[]
for r in rows:
 ts=([r['translation_source']] if r.get('translation_source') else r.get('translation_sources',[]));parts=[]
 for t in ts:
  name=t.get('dictionary','').lower();idx=t.get('record_index',t.get('dictionary_record_index'))
  if (name,idx) in source:
   s=source[name,idx];parts.append(dict(en=s['source'],ko=s['korean'],source=t))
  elif r['game']=='fo76':
   kind=name.rsplit('.',1)[-1];sid=t['string_id'];parts.append(dict(en=en76[kind].get(sid,''),ko=ko76[kind].get(sid,''),source=t))
 out.append(dict(id=r['id'],game=r['game'],title=r.get('title_ko'),title_en=r.get('title_en'),body=r['body_ko'],parts=parts))
(root/'raw-source-audit.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
print('audited',len(out),'with source',sum(bool(r['parts']) for r in out),'raw HTML sources',sum(any('<' in p['ko'] and '>' in p['ko'] for p in r['parts']) for r in out))
print('markup stats',collections.Counter(tag for r in out for p in r['parts'] for tag in re.findall(r'<([A-Za-z]+)',p['ko'])).most_common(15))
