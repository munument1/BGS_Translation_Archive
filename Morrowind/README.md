# Morrowind

The Elder Scrolls III: Morrowind 번역 데이터 아카이브입니다.

권장 하위 구조:

```text
BaseGame/   본편 번역
DLC/        공식 DLC 및 공식 추가 콘텐츠
Mods/       모드 번역
```

실제 데이터가 추가되는 범주부터 하위 폴더를 생성합니다.

## 현재 본편 번역 데이터

`BaseGame/Morrowind_Korean_ReTranslation.esp/kr6_utf8_localized.jsonl`은
로컬 KR6 한국어 ESP에서 UTF-8 한글 표시 문자열을 추출한 기록
**45,781개**입니다. 영문 원문, ESP 바이너리, 게임 리소스를 포함하지
않으며 원본 플러그인 SHA-256을 별도 메타데이터로 보존합니다.

- 수록: 한국어 객체·아이템 이름, 주요 화면 문구, 대화·저널, 책 등
- 상태: `imported` (원본 한국어 데이터 추출, 개별 문장의 최종 검수 보증 아님)
- `localized_subrecord_hash`는 **한국어 바이너리의 해시**이고 영문
  원문 해시가 아닙니다.
- 바닐라 영문 `Morrowind.esm`과의 필드 정합성 및 레코드 비교는
  별도 수행해야 합니다. 원본 ESP에 이 JSONL을 자동 주입하지 않습니다.

출처/권리 및 세부 제약은
`BaseGame/Morrowind_Korean_ReTranslation.esp/metadata.json`을 참조하세요.
