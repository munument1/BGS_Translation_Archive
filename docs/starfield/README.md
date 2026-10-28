# 성계의 기록

나사펑크 계기판과 기술 문서 스타일의 검색·읽기 화면을 제공합니다. 화면 맞춤/원본 줄바꿈, 글자 크기, 넓게 보기 설정을 지원하며 원본 본문은 변경하지 않습니다.

스타필드 본편의 데이터 슬레이트·서적·터미널을 한국어로 검색하고 읽는 비공식 팬 서고입니다.

- [웹 서고](./index.html): 795개 읽기 항목. 데이터 슬레이트 389개, 서적·문서 115개, 터미널 291개. 연속 기록 17묶음은 이 수에 포함됩니다.
- [추출 결과](./import-report.json): 설치된 `Starfield.esm`의 SHA-256, 실제 연결 필드 수, 제외 사유, 시리즈 구성.
- 터미널은 `TERM.DNAM`이 가리키는 `TMLM`과 `TMLM.TNAM` 하위 메뉴를 순회해 한 화면에 묶습니다. 같은 루트 메뉴를 사용하는 물리적 터미널은 한 항목으로 표시합니다. 공유된 하위 메뉴는 해당 루트의 읽기 화면에 함께 포함합니다. 순환 참조는 방문 집합으로 차단합니다.
- 연속 슬레이트·서적은 한국어 제목의 순번과 공통 EditorID 접두부가 함께 일치할 때만 합칩니다. 각 편의 원래 제목·FormID·출처를 `series_entries`에 보존합니다.

## 출처 및 대조

기존 `Starfield/Dictionaries/xTranslator/archive/`의 `starfield_en_ko.sst` 자료를 사용합니다. 게임 레코드의 유형·FormID·필드·필드 출현 순서·실제 StringID가 모두 일치하는 본문만 채택합니다. 사전 내 번역 충돌은 `Starfield/BaseGame/KoreanPatch-260914/archive/`에 보관된 본편 번역문과 정확히 일치하는 후보가 하나일 때만 해소합니다. 해결되지 않은 충돌과 식별자 불일치는 건너뛰며 유사 문장으로 대체하지 않습니다.

원문·번역의 권리는 각 권리자에게 있습니다. 본편 한글패치의 출처 및 권리 관련 기록은 `Starfield/BaseGame/import_metadata.json`을 따릅니다. 개별 항목은 기존 번역을 연결한 상태이며 새 문장 검수나 게임 내 사용 여부 확인을 뜻하지 않습니다. 미사용 레코드가 포함될 수 있습니다.

이번 범위는 설치된 본편 마스터 하나입니다. DLC·Creation은 포함하지 않습니다. 재생 장면(GNAM)이 연결된 음성 슬레이트의 DESC는 녹취록이 아니라 설명이므로 제외합니다. 게임 진행에 따라 치환되는 이름·수치 토큰은 원래 상태로 유지합니다. 따라서 현재 목록은 전체 게임 읽을거리의 완전한 목록이 아닙니다.

## 재생성

Python 표준 라이브러리만 사용합니다. 공개 저장소에는 게임 바이너리를 포함하지 않습니다.

```powershell
python tools/build_starfield_archive.py --esm 'D:\SteamLibrary\steamapps\common\Starfield\Data\Starfield.esm'
```

## ASMR과 BGM

상단 `ASMR·BGM`에서 환경음 켜기·끄기·음량 조절과 YouTube BGM을 이용할 수 있습니다. ASMR은 사용자가 제공한 `freesound_community-spaceship-ambient-27988.mp3`를 재생합니다. 자동 재생하지 않으며 `모두 끄기`로 두 소리를 종료할 수 있습니다. BGM은 YouTube 원본 링크도 제공합니다. [음원·영상 출처](../assets/archive-audio-sources.json).
