# 스카이림 서적 번역 갱신 — 2026-11-01

## 자료 확인 및 정정

**번역기에는 레코드 식별자가 포함된 압축 사전이 있다.**
`src/XTranslatorAi.App/Assets/GameStrings/game-strings-skyrim.gz`은
`XTranslatorAi-GameStrings-v2` 형식의 gzip 텍스트이며, `F` 행은
레코드 필드 identity, 영어 원문 128비트 SHA-256 지문, 한국어 번역,
번역 출처 플러그인을 보존한다. `BOOK/owner.esm:001234/0/DESC/0`
형태의 identity에서 기존 서적의 플러그인과 FormID 하위 24비트를
대응할 수 있다. 원본 게임 ESM 없이 **기존 BOOK 977권 갱신 후보를
추출하는 것은 가능하다.** 이전의 '원본 ESM 필수' 주장은 과도했다.

- 번역기: https://github.com/servaltullius/Skyrim_Translator_v6
- 내장 사전 및 대응 코드: `GameStringDictionary.cs`
- 번역기 커밋 고정: `dc1796e26f5b3d1db0e1116c5a0b04a13759dba9`
- 최신 한국어 패치 근거: `Skyrim_Latest_Kor/읽어보기.txt`, 26.10.16 베타 6
- 기존 서고: `sources/skyrim_books/skyrim_books_*.jsonl` (977건)
- 번역기 검수 기록의 서적 1,032권은 별도 검수 범위이므로
  정확히 55권 누락이라고 단정하지 않는다.

## 올바른 작업 순서

1. 내장 gzip 사전의 `BOOK:DESC`, `BOOK:FULL`과 기존 서고
   레코드 identity를 대응하여 서적 갱신 후보 생성.
2. 변경·유지·불일치·신규 identity를 검사.
3. 같은 BOOK에 서로 다른 번역 후보가 있거나 동적 태그가 바뀌면 자동
   교체하지 않음. 새 BOOK의 경우 압축 사전에 완전한 8자리 FormID,
   EDID가 없으므로 실제 ESM/ESL로 별도 확인.
4. 후보를 검수한 뒤 `sources/skyrim_books/`를 교체하고 기존
   `build-book-collection.yml`로 웹 서고 재생성.
5. 이후 영문 원문 전문 + 한국어를 모든 스카이림 레코드에 대응시키는
   정규화 작업에 착수. **내장 사전에는 영어 해시만 있고 본문은 없음**;
   영문 원문 전문을 확보할 때에는 사용자 게임 파일·영문 STRINGS가
   필요하며 게임 원본 바이너리와 전문을 무단 공개 업로드하지 않음.
6. 마지막으로 모로윈드 KR12.4, 오블리비언 v1.2.0, 대거폴 등과
   시리즈 공통 용어를 검수.

## 실행 예시

~~~powershell
git clone https://github.com/servaltullius/Skyrim_Translator_v6.git ..\Skyrim_Translator_v6
git -C ..\Skyrim_Translator_v6 checkout dc1796e26f5b3d1db0e1116c5a0b04a13759dba9

python tools/refresh_skyrim_book_translation.py `
  --dictionary "..\Skyrim_Translator_v6\src\XTranslatorAi.App\Assets\GameStrings\game-strings-skyrim.gz" `
  --source-revision dc1796e26f5b3d1db0e1116c5a0b04a13759dba9 `
  --output ".local\skyrim-book-refresh"
~~~

후보: `.local/skyrim-book-refresh/sources_skyrim_books/*.jsonl`

보고서: `.local/skyrim-book-refresh/review_report.json`

기존 서고·웹사이트는 직접 변경하지 않는다. 검토 후에만 새 번역을
출처와 함께 배포한다. 소스 번역자의 출처 및 수정·재배포 조건을
존중한다.

**현재 상태: 사전 기반 대응 도구와 테스트를 PR에 준비했으며, 갱신
후보의 실제 수량 및 내용은 압축 사전 처리 결과로 확정한다.**
