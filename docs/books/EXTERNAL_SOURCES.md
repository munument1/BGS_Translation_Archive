# The Imperial Library — Game Books 확장 조사

## 범위 및 현재 상태

- 기존 한국어 서고: 대거폴 93건, 모로윈드 632건, 오블리비언 927건, 스카이림 977건, 총 2,629건
- 외부 원문 색인: [The Imperial Library · Game Books](https://www.imperial-library.info/game-books)
- 현재 수록: ESO 일반 서적 **2,533개 제목**(공개 EPUB의 NCX 목차 추출), Battlespire **54개**, Redguard **13개**, Shadowkey **8개**, ESO 일지·쪽지·편지 **11개**(후자의 네 범주는 외부 서지 자료 기반 선별 목록). 총 **2,619개** 참조 항목이며 **번역 전문 0건**
- 웹 색인: [외부 서적 찾아보기](../imperial-library.html)
- 통합 색인 데이터: [imperial_game_books_catalog.json](imperial_game_books_catalog.json)
- 한국어 제목을 시범 검토한 ESO 7종: [external_candidates.json](external_candidates.json)
- 출처 및 재생성: [build_external_game_book_index.py](../../tools/build_external_game_book_index.py), [build-external-book-index.yml](../../.github/workflows/build-external-book-index.yml)

**이 문서는 아직 네 작품의 전체 영문 서적명을 전수 대조한 결과가 아닙니다.** 원문 사이트 Game Books 목록에 대한 자동 접근이 403으로 제한됩니다. 대량 ESO 항목은 [HorrorPills/epub-imperial-library](https://github.com/HorrorPills/epub-imperial-library)의 EPUB 목차(NCX)에 기재된 **제목만** 추출했습니다. 나머지 항목은 공개 위키 목록 등을 참고하여 선별했습니다. ESO 일지·편지 전체를 전수 확보한 것은 아닙니다.

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

## 저작권과 원문 재배포

The Imperial Library의 원문 페이지 공개 자체는 번역 전문을 복제·재배포할 허락을 뜻하지 않습니다. 게임 내 서적은 베데스다 등 권리자가 소유한 저작물일 수 있으며, 웹사이트에 보존된 다른 저작물도 별도의 권리가 존재할 수 있습니다.

따라서 현재는 원문 **서지 메타데이터·직접 링크·독자적인 짧은 한국어 설명**만 제공합니다. 외부 사이트의 원문을 자동으로 대량 복제하거나 번역 전문을 공개하지 않습니다. 추후 공개 번역을 추가하려면 해당 자료의 이용 허용 범위와 권리자 조건을 확인해야 합니다.

## 추가 가능한 다음 범위

- ESO 전용 문헌: EPUB 기반 참고 색인 **2,533종** 확보. 본문·개별 URL·한국어 제목은 검수 및 권리 확인 필요
- ESO 일지·편지: 선별 11종만 확보. 지정 목록의 전체 수록 건수는 확인되지 않았습니다.
- TES: Battlespire, Redguard 등 외전 자료: Imperial Library 원문 목록 및 데이터 확보 후 별도 분류
- 네 작품의 누락: 외부 영어 제목을 원본 게임 BOOK 레코드와 식별자 기준으로 비교

원본의 **권리 조건 확인 및 사람 검수 없이 '번역 완료'로 표시하지 않습니다.**
