# 황무지의 기록 — Wasteland Archive

녹색 터미널 화면에서 작품·기록 종류·본문을 검색할 수 있습니다. 읽기 설정의 `화면에 맞춤`은 문단 안의 고정 줄바꿈을 화면 폭에 맞춰 표시하며, `원본 유지`로 되돌릴 수 있습니다. 글자 크기·넓게 보기를 지원하고 원본 본문은 변경하지 않습니다. 메모·문서는 원문에 명시된 소제목을 제목 요소로 구분하며, 여러 구획은 계층형 목차를 눌러 이동할 수 있습니다.

폴아웃 시리즈의 **인게임 읽을거리**를 정리하기 위한 한국어 팬 아카이브입니다.

- 웹사이트: [황무지의 기록](./index.html)
- 현재 단계: 기존 한국어 번역 본문 검색·읽기 및 외부 링크 색인
- 게임: Fallout 1, 2, 3, New Vegas, 4, 76
- 기록 종류: 터미널 기록, 홀로테이프, 홀로디스크, 메모

## 현재 공개 목록 (2026-10-28 최종 대조)

공개 읽기 자료 **7,238개 모두 한국어 본문**이 있습니다. 분류는 터미널 2,938개 / 홀로테이프·홀로디스크 733개 / 메모·문서 3,567개입니다. 같은 터미널의 페이지와 연속 홀로테이프는 한 기록 안에서 읽으며, 기존 개별 주소는 `aliases`로 유지합니다. 이 수치는 현재 수록 자료 수이며 게임 전체 기록의 완전 수집을 뜻하지 않습니다.

폴아웃 76 설치본의 공식 한국어 읽기 자료 **2,957개**를 추가했습니다. 메모·문서 1,615개, 홀로테이프 477개, 터미널 865개이며 하위 메뉴를 함께 읽고 40개 연속 기록을 묶었습니다. 암호·기호는 게임 원본대로 보존합니다. [출처와 수록 범위](FO76_SOURCES.md).

이전에 표시한 일부 번역 412개·미번역 158개는 게임 번역의 결손 수가 아니라 **서고의 번역 연결 실패 수**였습니다. EPUB 편집본과 게임 레코드의 문장 차이, 서식 태그, 터미널의 NOTE 필드, 음성 홀로테이프의 NOTE → DIAL → INFO 참조를 놓친 것이 원인이었습니다. 폴아웃 3·뉴 베가스·4 본편과 공식 DLC는 기존 한국어 게임 레코드·문자열을 연결했으며 새 기계 번역으로 대체하지 않았습니다. 한국어는 게임 본문을 기준으로 하고 EPUB 영문은 별도 참조 자료로 표시합니다.

기존 대상 570개 중 563개는 기존 번역 연결·중복 통합으로 해결했고, 택틱스 3개와 Creation Club의 Horse Power Armor 일기 1개는 별도 서고 번역으로 표시했습니다(독립 검수 전). 읽기 본문이 없는 겍코 디스크 2개와 음악 트랙 1개는 제외했습니다. 허볼로지 디스크의 소지품 설명은 이미 수록한 가르침 본문의 별칭으로 통합했습니다. 폴아웃 1의 17개와 2의 20개는 기존 MSG 한국어 번역을 연결했습니다.

[완료 대조 보고서](completion-audit-report.json), [기존 570개 대상 ID](completion-targets.json), [현재 집계](cleanup-report.json)로 확인할 수 있습니다. `canonical_record_links`, `translation_sources`, `classic_translation_source`에 플러그인·FormID·필드·원문 해시·MSG ID 등의 근거를 보존합니다. 묶음의 이전 EPUB 구성은 `reference_series_members`에 제목과 식별자로 남깁니다. 영문 알파벳을 사용하는 퍼즐 단서는 원래 기호를 보존합니다.

최종 공개 검증은 `python tools/validate_fallout_catalog.py`입니다. 재수집 작업에서는 `reconcile_fallout_epub.py` → `restore_classic_fallout_translations.py` → `restore_fallout_record_bodies.py` → `finish_fallout_completion.py` 순서의 원본 연결과 `finalize_fallout_catalog.py` 정리 후 다시 검증합니다. 복원 도구는 로컬 게임·사전·감사 자료를 읽으므로 해당 원본이 필요합니다. 앞 단계만 재실행한 결과로 현재 공개본을 덮어쓰지 않습니다.

아래는 이전 단계의 이력입니다.

## 데이터 구조 및 이전 작업 이력

### 이전 단계: 읽기 단위와 EPUB 원문

- 터미널은 게임·플러그인·FormID당 한 항목입니다. 2,280개 터미널의 메뉴·환영 문구는 소제목과 함께 한 화면에 표시합니다. `terminal_sections`에 원래 필드와 번역 출처를 보존합니다.
- 제목의 순번이 확인된 연속 녹음·일지·메모는 같은 게임과 출처 안에서 56개 묶음으로 정리했습니다. 외계인 포로 녹음 25편 등이 포함됩니다. `series_entries`와 [묶음 목록](series-group-report.json)에 구성 기록을 보존합니다.
- `aliases`로 예전 개별 기록 링크를 유지합니다. 개별 편의 제목·EditorID·FormID와 본문도 검색 대상입니다.
- EPUB의 폴아웃 1 17문서, 2 23문서, 택틱스 3문서도 본문을 수록했습니다. EPUB은 **영어 원문**이며 한국어 번역 수에 포함하지 않습니다. 읽기 화면에서 바로 표시하며 EPUB 파일 링크에는 **원본 EPUB 다운로드**라고 명시합니다.
- 현재 전체 목록은 묶음 처리 후 **6,144개 항목**, 한국어를 읽을 수 있는 항목은 **3,659개**입니다. 기존에 연결한 한국어 **7,863개는 묶음 내부의 본문 필드 수**입니다.
- 재생성: `python tools/link_fallout_translations.py` 다음 `python tools/import_fallout_epub_bodies.py`. EPUB 경로는 `work/fallout_codex/Fallout.epub`입니다. EPUB 추출에 BeautifulSoup4가 필요합니다. 두 도구 모두 기존 묶음을 풀어 처리한 다음 다시 묶습니다.

### 2026-10-28 기존 번역 연결

공식 본편·DLC 이름과 일치하는 xTranslator 사전에서 한국어 본문 **7,863개**를 연결했습니다. 폴아웃 3은 1,646개, 뉴 베가스는 2,654개, 폴아웃 4는 3,563개입니다. 제목·본문·FormID 검색과 작품·종류 필터를 제공하며, 기본 목록은 한국어 본문이 있는 기록만 표시합니다. 기록 주소의 해시로 읽기 화면을 직접 열 수 있습니다.

- 재생성: `python tools/link_fallout_translations.py` (표준 라이브러리만 필요).
- 공식 사전 파일명, 레코드 유형, 전체 FormID, 필드 및 하위 인덱스를 사용합니다. 모드 사전과 유사 문자열은 연결하지 않습니다.
- FO3/FNV의 기존 `menu-N`에는 환영 페이지가 포함되므로 해당 오프셋을 적용합니다. 대응하는 기존 색인이 없으면 사전 필드 식별자를 가진 `sst-` 항목을 추가합니다.
- 폴아웃 4 터미널은 기존 추출기가 놓친 `BTXT` 및 `UNAM` 본문을 별도 항목으로 추가합니다. 기존 메타데이터 항목과 중복되는 시설·레코드가 있을 수 있으며, 전체 목록 수는 고유 문서 수가 아닙니다.
- `translation_source`에 압축 사전 경로, 원래 사전명, 레코드 순서, 영어 해시, 필드와 인덱스를 보존합니다. 상태는 `imported_translation`이며 문장 검수·게임 내 사용 여부 확인을 의미하지 않습니다.
- [연결 결과](translation-link-report.json). FO3 사전은 `FalloutNewVegas/Dictionaries`에 보관된 공식 마스터 이름의 사전을 사용합니다. 폴아웃 4는 FormID·필드를 가진 사전으로 연결하며, 문자열 ID만 가진 별도 본편 패키지와 임의로 결합하지 않습니다.

아래의 10월 11일·12일 기록은 본문 연결 이전 단계의 이력입니다.

`catalog.json`에서 각 자료에 다음 필드를 유지합니다.

| 필드 | 뜻 |
| --- | --- |
| `id` | 바뀌지 않는 고유 식별자 |
| `game` | `fo1`, `fo2`, `fo3`, `fnv`, `fo4`, `fo76` |
| `type` | `terminal`, `holotape`, `holodisk`, `note` |
| `level` | `collection` = 원문 목차, `entry` = 개별 기록 |
| `title_ko`, `title_en` | 표시 제목과 영어 원명 |
| `description` | 직접 작성한 한국어 안내 문구 |
| `source_url`, `source_name` | 원문 출처와 링크 |
| `status` | `external_index`, 향후 `reviewed_translation` 등 |
| `body_ko` | 저작권 및 공개 가능 여부를 확인한 뒤 추가하는 한국어 본문. 기본 `null` |

작품과 유형 필터, 검색, 세부 기록 보기, 출처로 이동 기능이 있습니다. JSON을 확장하면 추가 개발 없이 개별 기록과 한국어 본문을 표시할 수 있습니다.

## 수집 및 번역 원칙

1. 인게임 기록은 가능하면 **게임 데이터에서 직접 추출한 식별자**(플러그인, FormID, EditorID, 레코드 유형)를 별도로 관리합니다.
2. 출처 목록으로 외부 위키를 참조하지만, **위키의 원문 전문을 자동 복사하거나 저장소에 일괄 복제하지 않습니다.**
3. 위키 편집 콘텐츠의 라이선스와 게임 원본 텍스트의 권리는 별개입니다. 게임에서 추출한 텍스트라 해도 공개·번역·재배포에 제한이 있을 수 있습니다.
4. 공개 가능한 번역 자료는 출처, 번역 상태, 근거와 검수 상태를 붙입니다. 허락되지 않은 원문은 메타데이터와 외부 링크로 유지합니다.
5. 영문 추출/번역의 중간 생성물은 로컬 `work/` 폴더에 보관하고 무심코 GitHub에 업로드하지 않습니다.

## 참조 사이트

- [Fallout Wiki — Source text](https://fallout.fandom.com/wiki/Source_text)
- [Fallout Wiki — Content policy](https://fallout.fandom.com/wiki/Fallout_Wiki:Content_policy)
- [Fallout Wiki — Copyrights](https://fallout.fandom.com/wiki/Fallout_Wiki:Copyrights)

본 사이트는 비공식 팬 프로젝트이며 Bethesda, Microsoft, Interplay, Obsidian, Fallout Wiki와 공식 관계가 없습니다.

## 2026-10-11 EPUB 수집 진행

Library of Codexes의 공개 다운로드를 실제로 확인하고 EPUB 문서 1,113개를 색인에 추가했습니다. 기존 상위 목차 16개는 유지합니다. 영문 본문과 번역 작업 Markdown은 Git에서 제외되는 `work/fallout_codex/`에 보관합니다.

- 폴아웃 1: 17문서, 2: 23문서, 3: 293문서, 뉴 베가스: 204문서, 4: 573문서, 택틱스: 3문서.
- 터미널 문서는 여러 개별 기록을 포함할 수 있습니다. 문서 수를 개별 기록 수로 계산하지 않습니다.
- DLC 구분은 전자책 목차 그대로 보존하며, 홀로디스크·메모 혼합 분류는 추가 대조가 필요합니다.
- 한국어 본문: 0개. 폴아웃 76: 미수집. 게임 전체 목록과의 일치, 개별 위키 URL, EditorID/FormID, 미사용 여부는 아직 검증하지 않았습니다.
- `import-report.json`에 작품·DLC별 문서 수와 원본 SHA256을 기록했습니다.
- 재실행: `python tools/import_fallout_codex.py` (requests, beautifulsoup4 필요). 기존 번역 작업 Markdown은 덮어쓰지 않습니다.
- 다음 단계: 위키 목차 및 볼트 106/22 구조 확인, 터미널 하위 기록 분리, 혼합 유형 세분화, 출처와 게임 식별자 검증, 폴아웃 76 조사.

공개 색인의 `level=document`는 전자책 문서 단위이며 `verification=epub_member_verified`는 EPUB 내부 파일 확인만을 의미합니다. 원문 링크는 추측한 위키 주소 대신 실제 다운로드 파일을 가리키고, `source_member`에 내부 파일명을 보존합니다.

## 2026-10-12 게임 ESM 직접 추출

`Fallout3.esm`, `FalloutNV.esm`, `Fallout4.esm` 및 함께 제공된 공식 DLC ESM을 직접 스캔하여 `TERM`, `NOTE`, `BOOK` 레코드의 **실제 텍스트가 존재하는 필드**를 색인으로 만들었습니다.

- **폴아웃 3: 2,334개**, **뉴 베가스: 2,680개**, **폴아웃 4: 1,165개**. 합계 6,179개 텍스트 항목을 신규 등록해 기존 색인 1,129개 포함 **총 7,308개**가 되었습니다.
- 레코드에는 파일명, FormID, EditorID, 레코드 타입, 텍스트 필드 위치를 보존합니다. `TERM`의 환영 문구와 하위 메뉴 본문은 각각 한 항목으로 색인합니다.
- `docs/fallout/esm-import-report.json`에서 플러그인별 추출 건수를 확인할 수 있습니다. `verification=esm_direct`는 ESM 안의 텍스트 필드를 직접 읽었다는 뜻이며, 해당 기록이 실제 게임 플레이 중 사용되는지 또는 번역 검수가 완료되었는지를 뜻하지 않습니다.
- **영문/한국어 추출 본문은 공개 JSON에 포함하지 않습니다.** `work/fallout_esm/records.jsonl` 로컬 파일에 `body_lang` 및 `body_local`로 저장하며, 확인된 한국어 번역만 나중에 `body_ko`로 공개할 수 있습니다. 폴아웃 4의 현지화된 `*_en.STRINGS`에는 한국어가 들어 있을 수 있어 인코딩을 유니코드/CP949로 처리합니다.
- 게임 내 음성으로만 재생되는 홀로테이프, 스크립트가 동적으로 생성하는 문구, 다른 레코드의 참조만 있는 항목은 포함되지 않습니다. 한 터미널에 여러 페이지가 있다면 각 페이지가 별도 항목이므로 전체 레코드 개수와 추출 건수는 다릅니다.

재실행 방법 (`Python 3.10+`, 외부 라이브러리 불필요):

```powershell
python tools/extract_fallout_esm.py --input 'D:\Codex_Trans\그냥 번역\폴아웃' --probe
python tools/extract_fallout_esm.py --input 'D:\Codex_Trans\그냥 번역\폴아웃'
```

재실행 시 기존 `codex-` 및 외부 목차 항목을 보존하고 `esm-` 항목만 갱신합니다. 이 입력 경로는 작업자의 예시로서 사이트 실행에는 필요하지 않습니다.

## ASMR과 BGM

상단 `ASMR·BGM`에서 환경음 켜기·끄기·음량 조절과 YouTube BGM을 이용할 수 있습니다. ASMR은 사용자가 제공한 `dragon-studio-creepy-industrial-sounds-ambience-482892.mp3`를 재생합니다. 자동 재생하지 않으며 `모두 끄기`로 두 소리를 종료할 수 있습니다. BGM은 YouTube 원본 링크도 제공합니다. [음원·영상 출처](../assets/archive-audio-sources.json).

원래 번역에서 제목·문단 경계가 소실된 문서는 [표시 구획 보정](document-layout-overrides.json)에 원문 레코드 대조 근거와 본문 해시를 보존합니다. 이 보정은 한국어 문구를 바꾸지 않고 제목·문단·목록 경계만 복원합니다.

문서 3,567개를 점검하고 원본 서식·동일 레코드의 영문 머리말을 대조해 696개 문서에 1,306개 구획을 복원했습니다. [점검 결과](document-layout-report.json). 글자 크기만 큰 손글씨 본문, 문장 속 강조, 목록 항목은 제목으로 간주하지 않습니다.

재검사: `python tools/audit_fallout_document_sources.py --dictionary-root <xTranslator UserDictionaries 경로> --fo76-strings <추출한 공식 문자열 폴더>` 후 `python tools/restore_fallout_document_layouts.py`. 원시 대조 자료는 `work/document-layout-audit/`에만 저장됩니다.
