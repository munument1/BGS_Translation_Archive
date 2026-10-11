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
