# Translation Data Format

## 기준 형식

아카이브의 기준 형식은 UTF-8 JSON Lines(JSONL)입니다. 한 줄은 하나의 번역 가능한 필드 또는 응답 단위를 나타냅니다.

중요: **번역 내용의 언어와 게임 런타임이 요구하는 로케일 슬롯은 별개로 기록합니다.**

예를 들어 한국어 번역이라도 영문판 베이스에서 동작시키기 위해 `*_en.txt`, `*_en.STRINGS` 이름으로 배치해야 할 수 있습니다.

예시:

```json
{"game":"oblivion","type":"plugin","plugin":"Oblivion.esm","source_language":"en","content_language":"ko","form_id":"0001A334","record":"NPC_","field":"FULL","ko":"마틴 셉팀","status":"verified"}
{"game":"fallout4","type":"translation_file","mod":"ExampleMod","source_language":"en","content_language":"ko","runtime_locale":"en","deployed_path":"Interface/Translations/Example_en.txt","key":"$Example_Enable","ko":"활성화","status":"verified"}
{"game":"fallout4","type":"string_table","source_language":"en","content_language":"ko","runtime_locale":"en","deployed_path":"Strings/Fallout4_en.STRINGS","status":"verified"}
```

## 언어와 런타임 로케일

다음 개념을 구분합니다.

- `source_language`: 번역 전 원문의 언어. 보통 `en`
- `content_language`: 실제 번역 내용의 언어. 한국어 번역은 `ko`
- `runtime_locale`: 게임/모드가 실제로 읽도록 파일명에 사용해야 하는 로케일 슬롯

Bethesda 게임에 공식 한국어 로케일이 없고 영문판 베이스로 구동하는 경우:

```text
source_language = en
content_language = ko
runtime_locale = en
```

따라서 한국어 내용이라도 실제 배치 파일은 다음처럼 유지할 수 있습니다.

```text
Interface/Translations/Example_en.txt
Strings/Fallout4_en.STRINGS
Strings/Fallout4_en.DLSTRINGS
Strings/Fallout4_en.ILSTRINGS
```

**파일명 접미사 `_en`은 내용이 영어라는 뜻으로 해석하지 않습니다.** 이 경우에는 게임이 읽는 런타임 슬롯을 의미합니다.

xTranslator의 `*_en_ko.sst` 같은 이름은 번역 작업의 source/target 언어 쌍을 나타내는 작업 사전 이름이며, 실제 게임에 배치되는 파일명의 로케일과는 별개입니다.

## 데이터 유형

### plugin
ESP/ESM/ESL 레코드에 적용되는 번역입니다.

### translation_file
게임 또는 확장 플러그인이 런타임에 직접 읽는 Translations 계열 파일입니다.

예:
- `Interface/Translations/*.txt`
- `F4SE/Plugins/<plugin>/translations/*.json`
- 기타 모드 고유 `Translations` 경로

Translations 계열은 파일명의 언어 접미사만으로 실제 언어를 판단하지 않습니다. 예를 들어 `*_en.txt` 파일 자체가 한국어 값으로 교체되어 사용될 수 있습니다.

이 유형은 **최종 배치 파일의 실제 상대 경로와 파일명을 보존**하는 것을 원칙으로 합니다. xTranslator SST가 존재하면 SST는 작업 사전/출처로 연결하되, SST 파일명만으로 plugin 번역과 translation_file 번역을 구분하지 않습니다.

### string_table
Bethesda 외부 문자열 테이블입니다.

예:
- `*.STRINGS`
- `*.DLSTRINGS`
- `*.ILSTRINGS`

한국어 내용이라도 영문판의 문자열 슬롯을 대체하여 사용하는 경우 실제 배치 이름은 `*_en.*STRINGS`를 유지합니다.

### mcm_json
SimpleMcmJsonTranslator 등 JSON 기반 MCM 설정 번역 데이터입니다.

## 권장 필드

| 필드 | 설명 |
|---|---|
| `game` | 게임 식별자 |
| `type` | plugin, translation_file, string_table, mcm_json 등 |
| `source_language` | 원문 언어 |
| `content_language` | 실제 번역 내용의 언어 |
| `runtime_locale` | 실제 배치 파일에서 게임이 읽는 로케일 슬롯 |
| `mod` | 모드명. 모드 데이터인 경우 |
| `plugin` | 원본 플러그인 파일명 |
| `deployed_path` | 실제 게임/모드에서 사용하는 상대 경로와 파일명 |
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

플러그인 번역은 FormID 하나만으로 항목을 식별하지 않습니다.

```text
game + plugin + form_id + record + field + sub_index
```

Translations 계열은 가능한 경우 다음 조합을 사용합니다.

```text
game + mod + deployed_path + key
```

외부 문자열 테이블은 실제 배치 파일 경로를 반드시 보존합니다.

```text
game + deployed_path + string_id
```

## 원문

원문 전체 문자열은 기본적으로 필수 필드가 아닙니다. 장기 보존과 변경 감지를 위해 `source_hash` 사용을 권장합니다.

원문 저장이 필요한 데이터셋은 출처, 재배포 조건, 목적을 별도로 명시해야 합니다.

## SST/XML

SST/XML은 교환 형식 또는 작업 사전으로 취급합니다.

```text
Plugin SST/XML -> Importer -> normalized JSONL -> Archive
Archive JSONL -> Exporter -> SST/XML -> ESP-ESM Translator
```

Translations 파일을 xTranslator로 번역해 SST를 저장한 경우:

```text
Translations 원본/배치 파일
        ↕
xTranslator SST (예: en -> ko 작업 사전)
        ↓
translation_file JSONL
        ↓
runtime_locale 규칙에 따라 *_en 파일로 재생성 가능
```

STRINGS 계열도 같은 원칙을 사용합니다.

```text
한국어 내용
  + content_language=ko
  + runtime_locale=en
        ↓
*_en.STRINGS / *_en.DLSTRINGS / *_en.ILSTRINGS
```

SST 내부 구조를 영구 저장 규격으로 그대로 고정하지 않는 이유는 Git diff, 자동 검증, 병합, 다른 도구와의 재사용성을 확보하기 위해서입니다.
