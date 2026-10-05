# Translation Data Format

## 기준 형식

아카이브의 기준 형식은 UTF-8 JSON Lines(JSONL)입니다. 한 줄은 하나의 번역 가능한 필드 또는 응답 단위를 나타냅니다.

예시:

```json
{"game":"oblivion","plugin":"Oblivion.esm","form_id":"0001A334","record":"NPC_","field":"FULL","ko":"마틴 셉팀","status":"verified"}
{"game":"oblivion","plugin":"Oblivion.esm","form_id":"0002531C","record":"INFO","field":"NAM1","sub_index":0,"ko":"무슨 일이 있었던 거지?","status":"reviewed"}
```

## 권장 필드

| 필드 | 설명 |
|---|---|
| `game` | 게임 식별자 |
| `plugin` | 원본 플러그인 파일명 |
| `form_id` | FormID 또는 정규화된 로컬 FormID |
| `editor_id` | EditorID. 없는 경우 생략 가능 |
| `record` | INFO, BOOK, QUST, NPC_, WEAP 등 레코드 타입 |
| `field` | FULL, DESC, NAM1 등 번역 대상 필드 |
| `sub_index` | 같은 필드가 복수일 때 순번 |
| `ko` | 한국어 번역 |
| `status` | raw, ai, reviewed, verified 등 |
| `source_hash` | 원문 문자열의 해시 |
| `source_ref` | 번역 출처 또는 원본 데이터셋 참조 |
| `note` | 검수·용어·문맥 메모 |

## 식별 규칙

FormID 하나만으로 항목을 식별하지 않습니다. 가능한 경우 다음 조합을 사용합니다.

```text
game + plugin + form_id + record + field + sub_index
```

EditorID가 존재하면 보조 식별자로 저장합니다.

## 원문

원문 전체 문자열은 기본적으로 필수 필드가 아닙니다. 장기 보존과 변경 감지를 위해 `source_hash` 사용을 권장합니다.

원문 저장이 필요한 데이터셋은 출처, 재배포 조건, 목적을 별도로 명시해야 합니다.

## SST/XML

SST/XML은 교환 형식으로 취급합니다.

```text
SST/XML -> Importer -> normalized JSONL -> Archive
Archive JSONL -> Exporter -> SST/XML -> ESP-ESM Translator
```

SST 내부 구조를 영구 저장 규격으로 그대로 고정하지 않는 이유는 Git diff, 자동 검증, 병합, 다른 도구와의 재사용성을 확보하기 위해서입니다.
