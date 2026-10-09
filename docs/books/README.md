# 엘더 스크롤 한국어 서적 아카이브

각 작품의 한국어 서적 본문을 합본 Markdown과 JSONL로 정리합니다.

| 게임 | 수록 | 열람 |
|---|---:|---|
| II. Daggerfall | 93권 | [열기](daggerfall/index.md) |
| III. Morrowind | 632권 | [열기](morrowind/index.md) |
| IV. Oblivion | 927권 | [열기](oblivion/index.md) |
| V. Skyrim | 977권 | [열기](skyrim/index.md) |

[검색과 서적 읽기 기능이 있는 GitHub Pages](../index.html)
각 게임의 books/ 폴더에 번역된 서적 제목만 사용한 Markdown 파일 1개씩 보관합니다.
complete.md가 전체 합본이고, part-XX.md는 40권 단위 분할본입니다.
스카이림 한국어 STRINGS는 로컬에서 확인했지만 해당 문자열을 BOOK FormID와 연결할 게임 플러그인(ESM/ESL)은 아직 확보되지 않았습니다.
tools/extract_skyrim_books.py로 게임 플러그인과 번역 STRINGS를 대조해 sources/skyrim_books에 BOOK JSONL을 가져오면 자동 반영됩니다.

번역 데이터의 원본 출처와 재배포 조건을 존중해야 합니다. 영어 서적 본문 전문은 포함하지 않습니다.
