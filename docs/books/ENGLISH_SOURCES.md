# 영문 원문과 번역 작업 자료

사용자가 제공한 Imperial Library의 HTTrack 다운로드를 기존 4,837건의 서적 색인과 대조했습니다.
네트워크 재수집 없이 로컬 HTML, WordPress JSON, HTTrack의 `hts-cache/new.zip`에서 본문을 추출했습니다.

| 게임 | 색인 | 영문 확보 |
|---|---:|---:|
| 배틀스파이어 | 50 | 50 |
| 레드가드 | 16 | 14 |
| 섀도키 | 5 | 5 |
| ESO 일반 서적 | 2,533 | 2,482 |
| ESO 일지·편지·쪽지 | 2,233 | 2,231 |
| 합계 | 4,837 | 4,782 |

[웹에서 읽기](../index.html) · [영문 원자료](external_english_texts.json) · [미확보·중복 제목 보고서](english_import_report.json)

기존 시리즈와 같은 서가·읽기 화면을 사용합니다. 별도 영문 읽기 버튼이나 전용 뷰어는 사용하지 않습니다.
각 게임 폴더에 제목만 사용한 개별 Markdown, `complete.md`, 40권 단위 `part-XX.md`, `books.jsonl`, `index.md`를 생성합니다.
책 본문은 기존 형식인 제목 → ID/저자 → 본문 → 출처 순서를 따릅니다.
미번역 서적은 `en`·`content_language: en`으로 저장하며, 한국어 번역문인 것처럼 `ko`에 넣지 않습니다.
기존 외전 한국어 전문 2건은 해당 서적의 기본 본문으로 유지합니다. 발췌·설명 자료는 기존 `external_korean_texts.json`에 보존합니다.

캐시에서 일반 폴더에 저장되지 않은 페이지도 복원했습니다. 55건은 확인이 더 필요합니다.
22건은 같은 제목으로 여러 출처가 연결되어 있어 자동 선택하지 않았고, 26건은 개별 링크를 확정하지 못했습니다.
나머지 7건은 페이지가 있지만 이미지 서적, 빈 페이지 또는 손상된 HTML 때문에 텍스트를 추출하지 못했습니다.
본문은 내려받은 개별 페이지 기준이며 게임별 판본·발췌 여부는 번역 전 검수가 필요합니다.
출처 편집자 주석은 `source_notes_en`에 분리했으며, 한국어 번역 상태와 기존 번역 자료는 유지했습니다.

## 로컬 번역 작업 폴더

`work/imperial_library_translation/`에 다음 자료를 생성합니다.

- `sources.jsonl`: UID, 게임, 제목, 출처, 원문, 원문 해시를 포함한 전체 자료
- `<game>/<uid>.md`: 서적별 영문 원문, 출처 주석, 한국어 번역 입력란, 검수 메모
- `import_report.json`: 미확보 및 제목 중복 목록

기존 Markdown 작업 파일은 다시 실행해도 덮어쓰지 않습니다. 이 폴더는 Git에서 제외됩니다.
다운로드를 이어받은 뒤 아래 명령을 다시 실행하면 웹용 데이터와 확보 현황을 갱신할 수 있습니다.

```powershell
python tools/import_til_mirror.py --mirror "C:\My Web Sites\imperial Library"
```

Python과 `beautifulsoup4`가 필요합니다. 영어 본문은 별도 데이터로 관리하므로 기존 서지 색인 생성과 번역 작업실 생성이 원문을 지우지 않습니다.

원문 재추출 없이 서적 양식과 웹 색인만 다시 생성하려면 `python tools/build_external_book_collection.py`를 실행합니다.
기존 네 시리즈의 카탈로그와 추가 시리즈의 카탈로그는 웹에서 합쳐 표시하며, 본문은 읽을 때 서적별 Markdown 1개만 불러옵니다.
