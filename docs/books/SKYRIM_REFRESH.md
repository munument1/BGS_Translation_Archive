# 스카이림 서적 번역 갱신 — 2026-11-01

## 반영 상태

2026-11-01에 [PR #1](https://github.com/munument1/BGS_Translation_Archive/pull/1)이 `main`에 병합되었다. 압축 사전에서 식별자가 일치하는 서적의 한국어 제목·본문을 원자료에 반영하고 서고의 개별 Markdown, 합본, 색인과 카탈로그를 재생성했다.

**공개 GitHub Pages의 스카이림 서적 목록에 1,072건이 표시되는 것까지 확인했다.** 다만 별도 사람 검수나 인게임 전수 검증을 마쳤다는 뜻은 아니다. 사전에서 갱신된 레코드의 `status: review_required`는 후속 언어·내용 검수가 남았다는 뜻으로 유지한다.

- 공개 서고: https://munument1.github.io/BGS_Translation_Archive/
- 공개 스카이림 서적 목록: https://munument1.github.io/BGS_Translation_Archive/books/skyrim/index.md

| 항목 | 건수 | 처리 |
|---|---:|---|
| 기존 `sources/skyrim_books/` 원자료 | 1,128 | 전부 식별자 유지 |
| 사전과 대응된 BOOK 본문(DESC) | 977 | 974건 제목/본문 변경, 3건 동일 |
| 압축 사전과 대응하지 않은 기존 항목 | 151 | 원문 유지 |
| 새 BOOK 식별자 후보 | 4 | 전체 FormID·EditorID 미확보로 추가 보류 |
| 기존 공개 서고 | 977 | 이전 카탈로그 기준 |
| 갱신된 한국어 서고 | 1,072 | 생성된 개별 Markdown·합본·검색 색인에 반영 |
| 현재 게시 목록에서 제외된 원자료 | 56 | 한글 본문이 없는 항목(빌더 필터) |

이전의 **977권**은 갱신 전 생성 서고의 수록 건수이고, 압축 사전의 **977개 DESC 대응 건수**와 우연히 같은 숫자다. 원자료 자체는 갱신 전에도 1,128건이었다. 새 목록의 1,072건은 1,128건에서 빌더가 제외하는 56건을 뺀 결과다. 새 후보 4개는 그 수치에 포함하지 않았다.

## 갱신 출처와 대응 방법

- 번역기: https://github.com/servaltullius/Skyrim_Translator_v6
- 출처 커밋: `dc1796e26f5b3d1db0e1116c5a0b04a13759dba9`
- 내장 압축 사전: `src/XTranslatorAi.App/Assets/GameStrings/game-strings-skyrim.gz`
- 형식: `XTranslatorAi-GameStrings-v2`
- 코드·검수: `tools/refresh_skyrim_book_translation.py`, `tests/test_refresh_skyrim_book_translation.py`
- 사전 추출 검증: https://github.com/munument1/BGS_Translation_Archive/actions/runs/41283278478
- 한국어 패치 참고: `Skyrim_Latest_Kor/읽어보기.txt` (26.10.16 베타 6)

사전 `F` 행에는 BOOK 레코드·필드 식별자, 영어 원문 SHA-256 지문 앞 128비트, 한국어 번역과 출처 플러그인이 있다. 예를 들어 `BOOK/owner.esm:001234/0/DESC/0`를 기존 아카이브의 플러그인 및 FormID 하위 24비트에 대응한다. 같은 식별자에 여러 후보가 있거나 동적 태그가 다르면 자동 교체를 보류한다. 영어 원문 **전문은 사전에 없다**.

## 재현 방법

~~~powershell
git clone https://github.com/servaltullius/Skyrim_Translator_v6.git ..\Skyrim_Translator_v6
git -C ..\Skyrim_Translator_v6 checkout dc1796e26f5b3d1db0e1116c5a0b04a13759dba9

python tools/refresh_skyrim_book_translation.py `
  --dictionary "..\Skyrim_Translator_v6\src\XTranslatorAi.App\Assets\GameStrings\game-strings-skyrim.gz" `
  --source-revision dc1796e26f5b3d1db0e1116c5a0b04a13759dba9 `
  --output ".local\skyrim-book-refresh"
~~~

출력된 `.local/skyrim-book-refresh/review_report.json`에서 후보 수량·보류 기록을 확인한다. 이 명령 자체는 기존 원자료나 사이트를 덮어쓰지 않는다.

## 다음 작업

1. 변경된 974건의 실제 문장·서식·용어 차이를 검수하고, 필요 시 명확한 수정 근거와 함께 교정한다.
2. 151건의 미대응 자료와 한글 본문이 없는 56건의 중복·미번역·출처를 구분한다.
3. 새 BOOK 4개는 실제 ESM/ESL에서 전체 FormID 및 EditorID를 확인한 뒤 추가 여부를 정한다.
4. 영어 원문 전문은 사용자가 보유한 ESM/ESL·영문 STRINGS에서 확보해 번역과 연결한다. 원본 게임 바이너리와 전문의 공개 재배포 여부는 별도 저작권·배포 조건을 검토한다.
5. 스카이림 번역 원문-번역 쌍을 정리한 후 모로윈드 KR12.4, 오블리비언 v1.2.0, 대거폴 등과 엘더스크롤 공통 용어를 대조한다.

GitHub Pages에서 **1,072건 목록의 공개 접근은 확인**했다. 서적별 실제 번역 내용과 링크의 전수 검수는 별도 작업이다.
