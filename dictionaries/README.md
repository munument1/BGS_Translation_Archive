# Dictionaries

게임 전체 또는 개별 작품에서 반복되는 용어와 표기 결정을 관리합니다.

예정 형식:

```text
dictionaries/
  common_terms.tsv
  names.tsv
  locations.tsv
  oblivion/
  fallout/
  skyrim/
```

권장 TSV 열:

```text
source	translation	scope	status	note
```

게임별 공식 번역이나 기존 프로젝트의 표기가 충돌할 수 있으므로 `scope`와 `note`를 함께 기록합니다.

## xTranslator 사전 데이터 조사 (2026-10-28)

기존 개인 `UserDictionaries`를 읽기 전용 분석한 결과,
Fallout 4 / Fallout: New Vegas / Starfield의 SST 파일은
`SSU9` (일부 `SSU8`) 바이너리 사전이었습니다.
`*.sst`를 JSONL로 재사용할 때에는 바이너리의 원문·번역문뿐 아니라
마스터 플러그인 이름, 레코드/필드, FormID, 문자열 ID, 순번,
원문 해시, 원본 사전 파일 SHA-256을 보존해야 합니다.

| 게임 | 분석 대상(백업 제외) | 한국어 매핑 초안 |
| --- | ---: | ---: |
| Fallout 4 | 1,561 SST | 1,241,764 |
| Fallout: New Vegas | 314 SST | 431,692 |
| Starfield | 143 SST | 274,365 |
| **합계** | **2,018 SST** | **1,947,821** |

위 수치는 **원본 SST의 기계적 구조 추출량**이며 인적
검수 완료나 서로 중복이 없는 고유 영어 문장 수가 아닙니다.
SST 일부는 MCM의 `$키`나 `Translations` 텍스트용
사전이므로, `****` 레코드 유형만 보고 실제 런타임
배치 경로를 결정하지 않습니다. 게임별 파일·문맥을
확인해 plugin/translation_file을 구별해야 합니다.

SST 한국어 JSONL의 로컬 임시 변환본은 총 용량이 매우 크고,
다른 제작자 번역의 공개 재배포 조건이 일괄 확인되지 않아
**이번 공개 저장소 반영에서는 제외**했습니다. 원본은
`F:\번역\프로그램\xTranslator\UserDictionaries`에
그대로 있으며, 로컬 정규화 JSONL/해시 인벤토리만 생성한 상태입니다.
일부 구형 SST의 포맷 변형은 변환 도구 검증이 필요할 수 있습니다.

## SimpleMcmJsonTranslator

Fallout 4 MCM 한국어 사용자 사전 `149`개 `.mcmdb`를
안전한 **바이트 레벨 .NET NRBF 구조 파서**로 전부 읽었으며,
`11,119`개 기록 중 한글이 존재하는 재사용 초안
`10,893`개를 정규화했습니다.

파일:
`Fallout4/MCM/SimpleMcmJsonTranslator/translation.jsonl`

이 데이터의 `mcmdb_status_code_raw`는 원본 DB의 정수
상태값을 그대로 기록한 것이며 인간 검수 완료 표시가 아닙니다.
원문 전체 대신 `source_hash`와 한국어 `ko`를
보존합니다. 별도 모드 사이에서 같은 원문에 다른 번역이
있을 수 있으므로 무조건 한 문장으로 합치면 안 됩니다.

서로 다른 제작자 및 번역 기여자의 저작권은 별도로 유지하며,
외부 번역을 재배포할 때는 출처별 권리 검토가 필요합니다.
