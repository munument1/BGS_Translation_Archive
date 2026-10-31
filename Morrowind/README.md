# Morrowind

The Elder Scrolls III: Morrowind 한국어 번역 데이터 아카이브입니다.

## 본편 버전별 원자료

- **KR12.4 (현행, OpenMW 0.51.0)**: `BaseGame/KR12.4/translation.jsonl` — 공식 한국어 릴리스에서 추출한 53,902건(ESP 45,779, CEL/JRN/MRK/TOP 7,669, YAML 454).
- **KR9 (역사적 스냅샷)**: `BaseGame/KR9/translation.jsonl` — 기존 한국어 원자료 53,896건. 삭제·덮어쓰기 하지 않았습니다.
- 각 버전의 `metadata.json`에 배포 ZIP/ESP 해시와 수록 범위를 기록했습니다. KR6의 이전 임시 자료는 활성 소스에서 제외합니다.
- `../dictionaries/analysis/tamriel_morrowind_kr9_to_kr124_diff_20261101.json` 대신 저장소 루트의 `dictionaries/analysis/tamriel_morrowind_kr9_to_kr124_diff_20261101.json`에서 버전별 차이를 확인할 수 있습니다.

### 검수 결과 (2026-11-01)

정확한 물리 레코드/필드 위치와 텍스트 맵 키, YAML 키 기준으로 대조한 결과, 기존 대응 항목의 **570건**(ESP 567, 텍스트 맵 3)에서 한국어 값이 달라졌고 텍스트 맵에 **6건**이 추가됐습니다. KR9 항목의 삭제는 없습니다. KR9의 일부 레코드 ID에는 인코딩 흔적이 있어 두 버전을 단순 병합하지 않습니다.

한국어 원문 해시는 영어 원문 SHA가 아니며, 이 작업 자체가 인게임 실사용 검증을 뜻하지 않습니다. 이후 용어 비교와 번역 재사용의 기본 출처는 **KR12.4**로 지정하되 KR9은 이력 확인용으로 남깁니다.

## 모드 자료

- `Mods/Morrowind-Rebirth/`: 모로윈드 리버스 번역 자료를 본편과 분리 보관합니다.
- `Mods/Patch-for-Purists/`: PFP 5.0.7 / KR12.4 작업은 별도 모드로 관리합니다. 비공개 초안·원본 ESM은 공개 아카이브로 자동 이관하지 않습니다.
