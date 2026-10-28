# 베데스다 통합 번역 메모리 / 중복·표기 충돌 검토

2026-10-28 기준. 기존 원본을 수정·병합하거나 구버전 번역문으로
덮어쓰지 않고, **GitHub에 이미 보관된 사전만 읽어** 로컬
SQLite 검색 색인을 생성하는 구조입니다.

## 사용 방법

저장소 루트에서:

```powershell
# 최초 1회: 현재 아카이브만 읽어 로컬 검색용 DB를 생성
python tools/translation_memory.py build

# 영어를 정확히 입력해 영문 SHA가 일치하는 기존 번역을 확인
python tools/translation_memory.py lookup --english "Slaughterfish"
python tools/translation_memory.py lookup --english "Slaughterfish" --game oblivion

# 모로윈드 KR9는 영문 SHA가 없으므로 KR9 레코드 ID로 검색
python tools/translation_memory.py lookup --game morrowind --record-id BookSkill_Enchant1

# 한국어 검색: 작품을 지정하고 결과를 제한
python tools/translation_memory.py lookup --game fallout4 --korean "볼트" --limit 10

# 같은 숫자 ID가 여러 문자열 테이블에서 나타날 때 구분
python tools/translation_memory.py lookup --game fallout4 --dataset base --record-id 224439

# 모로윈드 KR9의 빈 레코드 ID도 타입/필드/정확한 identity로 조회 가능
python tools/translation_memory.py lookup --game morrowind --dataset kr9 --record-id "" --record-type MGEF --field DESC --limit 5

# 책 등 긴 원문을 줄이지 않고 출력
python tools/translation_memory.py lookup --game morrowind --record-id BookSkill_Enchant1 --full

# 중복과 충돌 규모 집계
python tools/translation_memory.py report

# 충돌이 잦은 영어 해시 150개와 한국어 변형의 검토 큐 재생성
python tools/export_conflict_review.py --limit 150
```

로컬 DB는 `work/translation_memory.sqlite3`에 만들어집니다.
**Git 관리 대상이 아니며** 크기는 약 1.28GiB입니다. 필요한
경우 이 파일만 삭제한 뒤 언제든 다시 생성할 수 있습니다.
자료 원본(압축 JSONL, SST 바이너리, ESP, 사용자 사전)은
읽기 전용으로 취급하며 변경하지 않습니다.

## 집계 및 주의사항

`translation_memory_summary.json`에 집계 결과가 있습니다.

| 구분 | 건수 |
| --- | ---: |
| 색인한 한국어 레코드 전체 | 2,437,378 |
| 실제 원본 영어의 SHA-256을 보유한 레코드 | 2,036,833 |
| 영어 출처 SHA-256을 확인할 수 있는 고유 키 | 1,114,263 |
| 같은 영어 해시 아래 한국어 변형이 2개 이상 있는 키 | 48,773 |
| 동일 게임 내 영어 해시·한국어 값이 반복 등장한 추가 행 | 837,310 |
| 한국어·레코드 ID 기준이지만 영어 SHA는 없는 행 | 400,545 |

**중요: 충돌 48,773건은 오역 48,773건이 아닙니다.**
문장 주체, NPC 말투, 아이템 유형, 단어의 중의성,
변수/대명사·문법 차이로 같은 영어 문자열을 다르게
번역하는 것이 자연스러운 경우도 있습니다. 단순 다수결로
최빈 한국어를 하나 선택해 기존 번역을 덮어쓰지 않습니다.
`conflicts_to_review.jsonl`은 **발생 빈도가 높은 상위 150개의
우선 검토 후보 목록**이며, 모든 48,773개 갈등의 자동
해결을 주장하지 않습니다.

별도 SST 전수 감사에서 게임별 영어 해시 기준 복수 한국어
번역 후보는 **43,080개 키**(폴아웃 4 31,934,
뉴 베가스 8,477, 스타필드 2,669)로 확인됐습니다.
원본 모드별 문맥 식별자가 겹치면서 번역문이 다른 경우도
있지만, 버전 차이·사용 상황·동일 키 재활용 가능성이
있으므로 단순한 오류나 삭제 대상으로 판단하지 않습니다.

### 검증된 영문 기준과 ID 전용 자료의 차이

- xTranslator SST, 오블리비언 canonical_v2, 폴아웃 4 MCMDB:
  `source_hash`는 실제 **기존 영어 문장에 대한 SHA-256**입니다.
  정확하게 같은 원문 문자열을 입력할 때에만 후보를 찾습니다.
- Fallout 4·Starfield 본편: `string_id` 또는 UI 키와 한국어
  문자열만 있습니다. 같은 버전의 영문 원본을 따로 확보해
  대조하기 전에는 **영어 해시를 추측하지 않습니다.**
  특히 Fallout 4는 동일 StringID가 `STRINGS`와
  `DLSTRINGS` 등 다른 테이블에 공존하므로,
  **게임·플러그인·파일/테이블·StringID 복합키**로만
  연결합니다. 같은 UI 키도 대소문자와 출현 순번에 따라
  구별합니다. JSONL의 `plugin_hint`는 파일명에서 추정한
  값이므로 ESM 원본 대조로 확정한 FormID라고 해석하지
  않습니다. Fallout 4 본편 추출값에는 Unicode 대체 문자
  `U+FFFD`가 포함된 한국어 항목이 **2개** 있어 향후
  별도 교정이 필요합니다. 원본 재현성을 위해 이
  단계에서는 임의 복구하거나 삭제하지 않았습니다.
- 모로윈드: 2026-10-27 공식 **KR9 릴리스**의 ESP·OpenMW
  파일에서 한국어를 가져왔습니다. 해당 파일 안의
  `localized_subrecord_hash`는 **한국어 바이트의 해시**이지
  영어 문장 해시가 아닙니다. 레코드 ID/필드로 검색합니다.
  이전 KR6 자료는 색인에 사용하지 않습니다.
- 원문 해시·ID가 같아도 문맥이 다르면 적용 전 검토가 필요합니다.
  Skyrim 등 외부 번역 프로젝트의 전문은 이 통합 DB에
  포함됐다고 주장하지 않습니다.

### 검수·우선순위

사전 검색 결과는 항상 `imported` 또는 `extracted_unreviewed`
출처의 **참고 후보**입니다. 게임/모드 본편 한국어 기존 표기를
우선 존중하고, 사용자가 직접 확정한 예외가 있다면 별도로
보존해야 합니다. 스카이림·오블리비언·모로윈드 표기를
비교할 때도 무조건 전역 치환하지 않으며, **모로윈드
표기 원전은 KR9만 사용**합니다.

이 인덱스는 번역 데이터 수집·검토 도구입니다. 단순 일치
검출을 근거로 ESP/ESM/게임 설치 파일에 자동 반영하지 않습니다.
