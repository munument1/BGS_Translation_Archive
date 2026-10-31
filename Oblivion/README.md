# Oblivion

The Elder Scrolls IV: Oblivion 한국어 번역 데이터 아카이브입니다.

## 공식 본편 및 DLC

`canonical_translation_v2.csv` 및 `canonical_locations_v2.csv`에서 번역을 정규화했습니다. 영어 원문 전문은 재게시하지 않고 원문 SHA-256을 보존합니다.

- `BaseGame/Oblivion.esm/canonical_v2.jsonl`: 본편 46,225건
- `DLC/canonical_v2.jsonl`: 공식 DLC 1,734건
- `Mods/canonical_v2.jsonl`: 기존 기타 플러그인 3,185건

**2026-11-01 동기화:** 한글패치 v1.2.0 canonical CSV와 레코드 식별자·영어 원문 SHA가 정확히 일치하는 47,215건을 검사해 기존 1,197건(본편 908 / DLC 286 / 기타 3)의 한국어 값을 갱신했습니다. 최신 CSV에서 대응하지 않는 12건은 `review_candidates_v1.2.0_20261101.jsonl`에 별도 보관했습니다. 나머지 기존 49,947건을 유지했습니다. 자세한 결과는 `dictionaries/analysis/tamriel_oblivion_sync_20261101.json`을 참고하세요.

## 언오피셜 패치 번역

`Mods/UnofficialPatches/canonical_unofficial_v1.2.0.jsonl`에는 UOP/USIP/UODP 등 언오피셜 플러그인의 번역 메모리 **8,818건**을 본편과 별도 보관합니다. 원본 CSV의 영문 필드에서 생성한 영어 SHA-256을 `source_hash`로 사용하며, 원본 CSV의 `source_sha256` 열과 혼동하지 않습니다. 상세 출처·버전·플러그인별 건수는 같은 폴더의 `metadata.json`을 참고하세요.

`status=imported`는 자료 이관을 뜻하며 최종 수작업 검수나 실게임 테스트 완료를 의미하지 않습니다. `source_encoding_check=verified` 역시 OBCJK 인코딩 검증에 관한 상태입니다.
