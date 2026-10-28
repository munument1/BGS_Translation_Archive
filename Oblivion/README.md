# Oblivion

The Elder Scrolls IV: Oblivion 번역 데이터 아카이브입니다.

권장 하위 구조:

```text
BaseGame/   본편 번역
DLC/        공식 DLC 및 공식 추가 콘텐츠
Mods/       모드 번역
```

실제 데이터가 추가되는 범주부터 하위 폴더를 생성합니다.

## 기존 오블리비언 번역 이관

로컬 `canonical_translation_v2.csv` 및
`canonical_locations_v2.csv`의 한국어를 보존했습니다.
영문 원문은 재게시하지 않고, 원문 텍스트의 SHA-256으로 원본 변경을
대조합니다. 현재 저장된 자료는 본편 **46,225개**, DLC **1,734개**,
기타 패치·모드 **3,185개**의 정규화 JSONL입니다.

- `BaseGame/Oblivion.esm/canonical_v2.jsonl`
- `DLC/canonical_v2.jsonl`
- `Mods/canonical_v2.jsonl`

개별 항목의 `status=imported`는 기존 CSV의 한국어 자료를
추출했다는 뜻이며 인게임 사용성이나 수작업 최종 검증을 의미하지 않습니다.
`source_encoding_check=verified`도 OBCJK 인코딩 변환 상태로만 해석해야
합니다. FormID의 로드 순서와 플러그인 정합성은 별도 확인이 필요합니다.
