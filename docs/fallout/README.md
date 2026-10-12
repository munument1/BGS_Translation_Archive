# 황무지의 기록 — Wasteland Archive

폴아웃 시리즈의 **인게임 읽을거리**를 정리하기 위한 한국어 팬 아카이브입니다.

- 웹사이트: [황무지의 기록](./index.html)
- 현재 단계: 원문 목차에 대한 **외부 링크 색인** (본문 미수록)
- 게임: Fallout 1, 2, 3, New Vegas, 4, 76
- 기록 종류: 터미널 기록, 홀로테이프, 홀로디스크, 메모

## 데이터 구조

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
