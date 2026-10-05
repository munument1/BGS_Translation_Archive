# BGS Translation Archive

베데스다 게임의 **번역 데이터 자체를 장기 보존하고 재사용하기 위한 아카이브**입니다.

이 저장소는 ESP/ESM 플러그인이나 완성형 한글패치를 직접 배포하는 것을 주목적으로 하지 않습니다.  
게임 및 플러그인 버전이 바뀌어도 기존 번역을 다시 적용·검수·이식할 수 있도록, 번역 데이터를 정규화된 형태로 보관하는 것이 목적입니다.

## 기본 원칙

- **ESP/ESM**: 최종 적용 결과물
- **SST/XML**: ESP-ESM Translator와의 교환·가져오기/내보내기 형식
- **JSONL**: 아카이브의 기준 번역 데이터 형식
- **GitHub**: 변경 이력, 검수, 용어 통일 및 장기 보존

## 게임별 구조

게임은 저장소 최상위에서 분리합니다.

```text
BGS_Translation_Archive/
├─ Morrowind/
├─ Oblivion/
│  ├─ BaseGame/
│  │  └─ Oblivion.esm/
│  ├─ DLC/
│  └─ Mods/
├─ Fallout3/
├─ FalloutNewVegas/
├─ Skyrim/
├─ Fallout4/
├─ Starfield/
├─ dictionaries/
├─ docs/
├─ exports/
└─ tools/
```

게임 폴더 내부는 기본적으로 다음 범주를 사용합니다.

- `BaseGame/` — 본편
- `DLC/` — 공식 DLC 및 공식 추가 콘텐츠
- `Mods/` — 모드 번역 데이터

실제 폴더는 데이터가 존재할 때 생성합니다.

## 저장 데이터

가능한 경우 각 번역 항목은 다음 식별 정보를 함께 보관합니다.

- 게임
- 플러그인 이름
- FormID 또는 Local FormID
- EditorID(존재하는 경우)
- 레코드 타입
- 필드명
- 하위 인덱스/순번
- 한국어 번역
- 번역 상태
- 원문 해시
- 출처 및 검수 메모

베데스다 원본 문자열 전체를 불필요하게 복제하지 않는 것을 기본 원칙으로 합니다. 원문 대조가 필요할 때는 식별자와 해시를 우선 사용합니다.

## SST와 아카이브의 관계

```text
SST/XML
  ↓
Importer
  ↓
정규화 JSONL
  ↓
BGS Translation Archive
  ↓
Exporter
  ↓
SST/XML
```

SST/XML은 실사용 교환 형식으로 유지하고, JSONL을 장기 보존용 기준 데이터로 사용합니다.

자세한 데이터 규격은 [docs/FORMAT.md](docs/FORMAT.md)를 참고하세요.
