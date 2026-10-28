# Fallout 4 MCM 한국어 사전

`SimpleMcmJsonTranslator/translation.jsonl`은 로컬
SimpleMcmJsonTranslator의 `.mcmdb` 149개를 읽어
확인한 **10,893개** 한국어 번역 후보입니다.

- 기준 문자열: 원본 영어 텍스트의 SHA-256
- 결과: 한국어 `ko`
- 원본 식별: `source_dictionary` 및 항목 순번
- 번역 상태: `imported`, 원본 프로그램의 정수 상태값은
  `mcmdb_status_code_raw`에 별도 유지
- 잘못된 UTF-8/U+FFFD 또는 한글이 없는 항목 제외
- 실제 모드의 설치 경로나 최종 검수 여부는 이 파일만으로
  입증되지 않으므로, 무분별한 자동 적용은 하지 않습니다.

원본 `.mcmdb`, 실행 파일, 외부 원문 전문은 수록하지 않았습니다.
Bin​aryFormatter를 그대로 역직렬화하지 않고 제한된
바이트 파서로 값만 추출했습니다.
