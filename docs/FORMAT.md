# Translation Data Format

## 기준 형식

아카이브의 기준 형식은 UTF-8 JSON Lines(JSONL)입니다. 한 줄은 하나의 번역 가능한 필드 또는 응답 단위를 나타냅니다.

예시:

```json
{"game":"oblivion","type":"plugin","plugin":"Oblivion.esm","form_id":"0001A334","record":"NPC_","field":"FULL","ko":"마틴 셉팀","status":"verified"}
{"game":"oblivion","type":"plugin","plugin":"Oblivion.esm","form_id":"0002531C","record":"INFO","field":"NAM1","sub_index":0,"ko":"무슨 일이 있었던 거지?","status":"reviewed"}
{"game":"fallout4","type":"translation_file","mod":"ExampleMod","deployed_path":"Interface/Translations/Example_en.txt","key":"$Example_Enable","ko":"활성화","status":"verified"}
```

## 데이터 유형

### plugin
ESP/ESM/ESL 레코드에 적용되는 번역입니다.

### translation_file
게임 또는 확장 플러그인이 런타임에 직접 읽는 Translations 계열 파일입니다.

예:
- `Interface/Translations/*.txt`
- `F4SE/Plugins/<plugin>/translations/*.json`
- 기타 모드 고유 `Translations` 경로

Translations 계열은 파일명의 언어 접미사만으로 실제 언어를 판단하지 않습니다. 예를 들어 `*_en.txt` 파일 자체가 한국어 값으로 교체되어 사용되는 모드도 있습니다.

이 유형은 **최종 배치 파일의 실제 상대 경로와 파일명을 보존**하는 것을 원칙으로 합니다. xTranslator SST가 존재하면 SST는 작업 사전/출처로 연결하되, SST 파일명만으로 plugin 번역과 translation_file 번역을 구분하지 않습니다.

### mcm_json
SimpleMcmJsonTranslator 등 JSON 기반 MCM 설정 번역 데이터입니다.

## 권장 필드

| 필드 | 설명 |
|---|---|
| `game` | 게임 식별자 |
| `type` | plugin, translation_file, mcm_json 등 |
| `mod` | 모드명. 모드 데이터인 경우 |
| `plugin` | 원본 플러그인 파일명 |
| `deployed_path` | 실제 게임/모드에서 사용하는 상대 경로 |
| `source_dictionary` | SST, MCMDB 등 작업 사전 참조 |
| `form_id` | FormID 또는 정규화된 로컬 FormID |
| `editor_id` | EditorID. 없는 경우 생략 가능 |
| `record` | INFO, BOOK, QUST, NPC_, WEAP 등 레코드 타입 |
| `field` | FULL, DESC, NAM1 등 번역 대상 필드 |
| `sub_index` | 같은 필드가 복수일 때 순번 |
| `key` | Translations/MCM 문자열 키 |
| `ko` | 한국어 번역 |
| `status` | raw, ai, reviewed, verified 등 |
| `source_hash` | 원문 문자열의 해시 |
| `source_ref` | 번역 출처 또는 원본 데이터셋 참조 |
| `note` | 검수·용어·문맥 메모 |

## 식별 규칙

플러그인 번역은 FormID 하나만으로 항목을 식별하지 않습니다. 가능한 경우 다음 조합을 사용합니다.

```text
game + plugin + form_id + record + field + sub_index
```

Translations 계열은 가능한 경우 다음 조합을 사용합니다.

```text
game + mod + deployed_path + key
```

EditorID가 존재하면 보조 식별자로 저장합니다.

## 원문

원문 전체 문자열은 기본적으로 필수 필드가 아닙니다. 장기 보존과 변경 감지를 위해 `source_hash` 사용을 권장합니다.

원문 저장이 필요한 데이터셋은 출처, 재배포 조건, 목적을 별도로 명시해야 합니다.

## SST/XML

SST/XML은 교환 형식 또는 작업 사전으로 취급합니다.

```text
Plugin SST/XML -> Importer -> normalized JSONL -> Archive
Archive JSONL -> Exporter -> SST/XML -> ESP-ESM Translator
```

Translations 파일을 xTranslator로 번역해 SST를 저장한 경우에는 다음 관계로 취급합니다.

```text
Translations 원본/배치 파일
        ↕
xTranslator SST (작업 사전)
        ↓
translation_file JSONL
```

SST 내부 구조를 영구 저장 규격으로 그대로 고정하지 않는 이유는 Git diff, 자동 검증, 병합, 다른 도구와의 재사용성을 확보하기 위해서입니다.
