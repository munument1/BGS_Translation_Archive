# 스카이림 한국어 서적 추출 안내

## 현재 확보된 자료

WWG 허용 폴더의 스카이림 번역파일/strings 안에 한국어 문자열 테이블 240개(STRINGS, DLSTRINGS, ILSTRINGS)가 있습니다.
본편, Update, Dawnguard, HearthFires, Dragonborn 및 Creation Club 언어 파일을 확인했습니다.

중요: STRINGS 데이터는 문자열 ID와 한국어 내용을 보관하지만 BOOK 레코드에 연결된 ID인지 알려주지 않습니다.
정확한 추출을 위해 원본 플러그인(.esm, .esl)에서 BOOK → FULL/DESC 매핑을 읽어야 합니다.

## 필요한 게임 파일

- Skyrim.esm
- Update.esm
- Dawnguard.esm
- HearthFires.esm
- Dragonborn.esm
- Creation Club 서적까지 추출하려면 보유 중인 cc*.esl 등

**원본 게임 ESM/ESL 파일은 GitHub에 업로드하지 마세요.** 이 스크립트가 로컬에서 읽기만 합니다.

## 자동 추출

tools/extract_skyrim_books.py는 Python 표준 라이브러리로 실행됩니다.

방법 A: 원본 게임 플러그인을 번역 폴더에 복사한 경우:

    python tools/extract_skyrim_books.py "D:\Codex_Trans\Better Cities 한국어 번역\스카이림 번역파일" --output sources/skyrim_books/skyrim_book_records.jsonl

방법 B: 원본 플러그인을 게임 Data 폴더에서 직접 읽을 경우:

    python tools/extract_skyrim_books.py "D:\Codex_Trans\Better Cities 한국어 번역\스카이림 번역파일" --plugins-dir "스카이림 게임 설치폴더\Data" --output sources/skyrim_books/skyrim_book_records.jsonl

추출기는 원본 플러그인을 수정하지 않고 번역된 BOOK 레코드만 JSONL로 기록합니다.
JSONL에 FormID, EditorID, 제목, 본문 및 출처를 기록하고 별도의 .report.json에 수량과 예외를 남깁니다.

## GitHub 통합

검증된 JSONL만 sources/skyrim_books/에 올리면 GitHub Actions가 자동으로 다음을 생성합니다.

- docs/books/skyrim/books/: 책 한 권당 Markdown 한 파일
- docs/books/skyrim/index.md: 제목별 링크 색인
- docs/books/skyrim/complete.md: 전권 합본
- docs/books/skyrim/part-XX.md: 40권 단위 합본
- docs/books/skyrim/books.jsonl: 정규화된 서적 데이터

원본 ESM/ESL을 확보하기 전까지는 스카이림 서적을 임의 추정하지 않고 0건으로 보류합니다.
