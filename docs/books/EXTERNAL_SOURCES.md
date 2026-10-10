# The Imperial Library — Game Books 확장 조사

## 범위 및 현재 상태

- 기존 한국어 서고: 대거폴 93건, 모로윈드 632건, 오블리비언 927건, 스카이림 977건, 총 2,629건
- 외부 원문 색인: [The Imperial Library · Game Books](https://www.imperial-library.info/game-books)
- 현재 수록: ESO 일반 서적 **2,533개 제목**(공개 EPUB의 NCX 목차 추출), Battlespire **50개**, Redguard **16개**, Shadowkey **5개**, ESO 일지·쪽지·편지 **2,233개**(이 네 범주는 Imperial Library 원문 색인에서 직접 추출한 제목·개별 URL). 총 **4,837개** 참조 항목이며 **번역 전문 0건**
- 웹 색인: [외부 서적 찾아보기](../imperial-library.html)
- 통합 색인 데이터: [imperial_game_books_catalog.json](imperial_game_books_catalog.json)
- 한국어 제목 1차 작업(2026-10-10): 외전 3종 **71건 전부 제목 번역**, 이 중 **5건 한국어 내용 소개**를 [external_korean_previews.json](external_korean_previews.json)으로 추가함. 한국어 전문 공개는 0건이며, 검수·권리 검토 완료 전까지 원문·본문을 공개 색인에 병합하지 않음.
- 개인 원문 참조 보관소의 `metadata/side_games_ko_drafts_20261010.md`에는 **본문 전체 2건과 본문 발췌·설명 3건**의 한국어 작업 초안을 저장함(공개 저장소에는 포함하지 않음).
- 한국어 제목을 시범 검토한 ESO 7종: [external_candidates.json](external_candidates.json)
- 출처 및 재생성: [build_external_game_book_index.py](../../tools/build_external_game_book_index.py), [build-external-book-index.yml](../../.github/workflows/build-external-book-index.yml)

**이 문서는 아직 네 작품의 전체 영문 서적명을 전수 대조한 결과가 아닙니다.** 기존 웹 검색 환경에서는 Game Books 페이지가 403으로 차단됐지만, 2026-10-10 연결된 사용자 PC에서는 동일 페이지가 HTTP 200으로 열렸습니다. 대량 ESO 항목은 [HorrorPills/epub-imperial-library](https://github.com/HorrorPills/epub-imperial-library)의 EPUB 목차(NCX)에 기재된 **제목만** 추출했습니다. PC에서 해당 페이지가 정상 열려 외전 3종 및 ESO 일지 페이지의 전체 목록과 개별 링크를 직접 추출했습니다. 다만 원문 전체 사이트를 망라한 결과는 아닙니다.

## 원문 게임별 카탈로그

| 게임 | 외부 색인 |
|---|---|
| TES II: Daggerfall | https://www.imperial-library.info/game-books/tes2-daggerfall-books |
| TES III: Morrowind | https://www.imperial-library.info/game-books/tes3-morrowind-books |
| TES IV: Oblivion | https://www.imperial-library.info/game-books/tes4-oblivion-books |
| TES V: Skyrim | https://www.imperial-library.info/game-books/tes5-skyrim-books |
| The Elder Scrolls Online | https://www.imperial-library.info/game-books/elder-scrolls-online-books |

위 게임별 색인 URL은 공개된 [The Elder Scrolls Tomes 프로젝트의 수집기](https://github.com/HorrorPills/epub-imperial-library/blob/main/scrape_elder_scrolls.py)에도 기록되어 있습니다.

해당 프로젝트의 분류 수량은 **대거폴 63, 모로윈드 233, 오블리비언 225, 스카이림 384, ESO 2,533종**이지만, 일지·편지·쪽지 등을 제외한 분류이며 현재 아카이브의 BOOK 레코드 단위 집계와 직접 비교하면 안 됩니다. 특히 36 Lessons와 권별 서적, DLC/확장팩, 동일 작품의 재등장 기록으로 단위가 다릅니다.

## 누락 여부 판정 규칙

1. 영문 표제와 게임·확장팩·서적 묶음·권 번호, 가능한 경우 게임 내부 FormID/EditorID를 확인합니다.
2. 기존 한국어 본문과 같은 작품인지 대조합니다. **한글 제목만 다른 책을 새 책으로 처리하지 않습니다.**
3. 원문 책을 여러 게임이 공유하면 재등장 작품으로 연결하고 무조건 중복 저장하지 않습니다.
4. 이전에 없던 항목은 '참고 링크 / 번역 검토 / 재배포 조건 확인 / 번역 검수 / 수록' 상태로 나누어 관리합니다.
5. 수록 허가와 출처가 확인된 텍스트에 한해 기존 `books/<번역 제목>.md` 형식으로 추가합니다. 동명 책은 폴더로 구분합니다.


## 미번역 서적 본문 필드

시리즈 색인에 등록한 항목은 번역 완료 항목과 섞지 않습니다. 각 레코드의 주요 필드:

- `game`: 작품 및 하위 문서 유형
- `title_en`: 공개 서지 자료에 있는 원문 제목
- `title_ko`: 번역 제목(미검수 항목은 빈 문자열)
- `translation_status: untranslated`
- `body_en: null` — 원문 전문 미수록
- `body_ko: null` — 한국어 전문 미수록
- `source_url`, `collection_url`: 원문 서적 또는 카테고리 링크
- `rights_reviewed: false` — 전문 게재 권리 확인 전
- `source_text_access: external_link_only`

본문을 넣을 자리를 미리 예약했지만 현재 공개 저장소에는 원문 전체를 복사하지 않았습니다. 나중에 권리 검토가 끝나고 번역문이 확보되면 같은 서지 식별자로 수록할 수 있습니다.

## 공식 소개 기록 및 보존 목적

The Imperial Library는 엘더 스크롤 게임 내 서적·대화·기타 설정 자료를 장기간 아카이빙해 온 팬 관리 사이트입니다.

- [Bethesda Support — 세계관 참고 사이트](https://help.bethesda.net/app/answers/detail/a_id/1421): The Imperial Library를 참고 사이트로 안내합니다.
- [ESO 공식 Community Spotlight (2021년 5월 20일)](https://www.elderscrollsonline.com/en-us/news/post/60117): 독립 팬 아카이브 활동을 공식적으로 소개합니다.

본 한국어 프로젝트는 그 보존 정신을 참고하지만, The Imperial Library나 Bethesda의 공식 번역판이 아닙니다. 공식 소개는 번역 및 재배포에 관한 포괄적인 이용허락으로 해석하지 않습니다.

## 로컬 원문 추출 도구

원문 확보에 필요한 기술적 경로는 마련했습니다. [`tools/extract_eso_epub_local.cjs`](../../tools/extract_eso_epub_local.cjs)는 **사용자가 적법하게 확보한 EPUB 파일**에서 영어 서적 본문을 추출하며, Node.js만 사용합니다.

```powershell
node tools/extract_eso_epub_local.cjs --epub "C:\\path\\to\\ElderScrollsOnline_Tomes.epub"
```

- 출력 폴더: `work/imperial_library_originals/eso/` (Git에서 제외)
- 결과: 각 `ext-*.txt` 원문 참조 파일과 `_extraction_manifest.json` (출처·원제·해시)
- 공개 자료: 제목·링크·서지 메타데이터, 한국어 번역 작업 틀만 유지
- 자동 다운로드·사이트 접속·403 우회·공개 저장소에 원문 전문 업로드 기능은 없습니다.
- ESO 일반 서적 이외 네 분류의 원문 전문은 아직 확보되지 않았습니다.
- 테스트 결과(2026-10-10): 참고 EPUB의 ESO 2,533개 항목 중 **2,530개의 텍스트 추출을 확인**했습니다. `Daedric Text`, `Snapdragon’s Burnt Notes`, `Summoning Rituals of the Arch-Mage` 3개는 EPUB 본문 HTML에서 추출 가능한 텍스트가 없어 예외로 기록됩니다. 이 시험 추출물은 공개 저장소에 커밋하지 않고 일회성 실행 환경에서 삭제했습니다.

## Imperial Library 직접 확인한 원문 목록의 로컬 추출

- 원문 공식 Game Books 페이지에서 직접 확인한 항목: 배틀스파이어 50건, 레드가드 16건, 섀도키 5건, ESO 일지·편지 2,233건 (합계 2,304건)
- ESO 일반 서적은 EPUB 목차 2,533건, 그중 로컬 추출 가능한 영문 텍스트 2,530건
- 연결된 PC에서 외전·ESO 일지 7건의 본문 추가 추출을 검증함
- 최신 로컬 원문 추출 도구: [`tools/import_til_originals_local.py`](../../tools/import_til_originals_local.py)
- `robots.txt`에 기재된 10초 간격을 존중하며 최소 10.5초 간격으로 요청. 원문 결과는 Git에서 제외되는 `work/`에만 저장

## 저작권과 원문 재배포

The Imperial Library의 원문 페이지 공개 자체는 번역 전문을 복제·재배포할 허락을 뜻하지 않습니다. 게임 내 서적은 베데스다 등 권리자가 소유한 저작물일 수 있으며, 웹사이트에 보존된 다른 저작물도 별도의 권리가 존재할 수 있습니다.

따라서 현재는 원문 **서지 메타데이터·직접 링크·독자적인 짧은 한국어 설명**만 제공합니다. 외부 사이트의 원문을 자동으로 대량 복제하거나 번역 전문을 공개하지 않습니다. 추후 공개 번역을 추가하려면 해당 자료의 이용 허용 범위와 권리자 조건을 확인해야 합니다.

## 추가 가능한 다음 범위

- ESO 전용 문헌: EPUB 기반 참고 색인 **2,533종** 확보. 본문·개별 URL·한국어 제목은 검수 및 권리 확인 필요
- ESO 일지·편지: 원문 페이지 2,233건의 제목·개별 URL을 확보. 일부 서적은 시험적으로 로컬 작업 폴더에만 원문을 추출했습니다.
- TES: Battlespire(50건), Redguard(16건), Shadowkey(5건) — 실제 원문 색인 및 개별 서적 URL 확보. 개별 본문 일부만 로컬 검증.
- 네 작품의 누락: 외부 영어 제목을 원본 게임 BOOK 레코드와 식별자 기준으로 비교

원본의 **권리 조건 확인 및 사람 검수 없이 '번역 완료'로 표시하지 않습니다.**
