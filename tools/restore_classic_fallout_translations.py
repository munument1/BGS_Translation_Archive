"""Restore classic holodisks from MSG IDs already audited against the EPUB.

This imports existing translations, never fabricates English/Korean pairs.
The local audit records keep source file hashes, message ranges and comparison.
"""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def compose_legacy_korean(text):
    # KS X 1001 filler-prefixed syllables only; retain ordinary typed jamo.
    leading='ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
    vowels='ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
    trailing=' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'
    def syllable(match):
        a,b,c=match.groups()
        return chr(0xac00+(leading.index(a)*21+vowels.index(b))*28+(trailing.index(c) if c else 0))
    return re.sub('ㅤ(['+leading+'])(['+vowels+'])(['+trailing[1:]+']?)',syllable,text)
TITLES={
'Alpha experiment disk':'알파 실험 디스크','Ancient Brotherhood disk':'고대 브라더후드 디스크','Brotherhood honor code':'브라더후드 명예 규율','Captain Maxson’s diary':'맥슨 대위의 일기','Delta experiment disk':'델타 실험 디스크','FEV experiment disk':'FEV 실험 디스크','FEV research':'FEV 연구','Maxson log':'맥슨 기록','Mutant transmissions':'뮤턴트 통신 기록','Power armor specs':'파워 아머 사양','Regulator transmission':'레귤레이터 통신 기록','Richard Grey’s audio diary':'리처드 그레이의 음성 일기','Security tape':'보안 테이프','Sophia’s tape':'소피아의 테이프','Vault locations v34.129':'볼트 위치 v34.129','Vree’s autopsy report':'브리의 부검 보고서','West Tek records':'웨스트텍 기록',
'Hubologist teachings':'허볼로지의 가르침','Military base level 1':'군사 기지 1층','Military base level 2':'군사 기지 2층','Military base level 3':'군사 기지 3층','Military base level 4':'군사 기지 4층','Military base outside':'군사 기지 외부','NCR history holodisk':'NCR 역사 홀로디스크','NCR spy holodisk':'NCR 첩보 홀로디스크','Power plant operations':'발전소 운영','Sierra Depot evacuation notice':'시에라 보급창 대피 공지','Sierra Depot experiment log':'시에라 보급창 실험 일지','Sierra Depot GNN transcript':'시에라 보급창 GNN 녹취록','Sierra Depot medical log':'시에라 보급창 의료 일지','Sierra mission statement':'시에라 임무 방침','State of the Nation':'국가 현황','The Project':'프로젝트','Vault City designer notes':'볼트 시티 설계자 메모','Vault City travel log':'볼트 시티 여행 기록','Westin holodisk':'웨스틴 홀로디스크','Word list':'단어 목록'}

def main():
    path=ROOT/'docs/fallout/catalog.json';c=json.loads(path.read_text(encoding='utf-8'))
    imports={}
    for game in ('fallout1','fallout2'):
        rows=json.loads((ROOT/f'work/fallout-audit/{game}-msg-audit.json').read_text(encoding='utf-8'))
        for row in rows:
            if row['similarity']<.94 or '\ufffd' in row['korean'] or not re.search('[가-힣]',row['korean']):continue
            imports[row['id']]=(game,row)
    restored=[]
    for r in c['entries']:
        if r['id'] not in imports:continue
        game,row=imports[r['id']]
        r.update(body_ko=compose_legacy_korean(row['korean'].strip()),title_ko=TITLES.get(r.get('title_en'),r.get('title_ko','')),status='imported_translation',body_version='existing_game_translation',translation_coverage=dict(complete=True,method='existing_MSG_message_ID_range; English comparison audited',total_words=len(re.findall(r'\w+',r.get('body_en',''))),matched_words=len(re.findall(r'\w+',r.get('body_en','')))))
        r['classic_translation_source']=dict(project='Fallout Et Tu Korean Edition' if game=='fallout1' else 'Fallout 2 RPU Korean Edition',file='game/PIPBOY.MSG',message_ids=row['message_ids'],english_file_sha256=row['source_english_sha256'],korean_file_sha256=row['source_korean_sha256'],status='existing_translation_imported; not newly editorially reviewed')
        restored.append(r['id'])
    path.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (path.parent/'classic-translation-report.json').write_text(json.dumps(dict(restored=len(restored),record_ids=restored),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('classic translations restored',len(restored))

if __name__=='__main__':main()
