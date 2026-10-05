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
