# xTranslator SST 한국어 번역 메모리 (압축 보관)

원본 `F:\번역\프로그램\xTranslator\UserDictionaries`의
**SST 2,018개**를 바이너리 형식 SSU8/SSU9에서 안전하게 읽어
한국어 번역 엔트리 **1,974,796개**를 보존했습니다.

| 게임 | SST 원본 수 | 한국어 번역 엔트리 | 저장 위치 |
| --- | ---: | ---: | --- |
| Fallout 4 | 1,561 | 1,268,739 | `Fallout4/Dictionaries/xTranslator/archive/` |
| Fallout: New Vegas | 314 | 431,692 | `FalloutNewVegas/Dictionaries/xTranslator/archive/` |
| Starfield | 143 | 274,365 | `Starfield/Dictionaries/xTranslator/archive/` |
| **합계** | **2,018** | **1,974,796** | |

원래 변환본은 **약 936.4MiB**였으나 표준 `gzip`으로
**약 148.8MiB**로 압축했습니다(약 84% 절약).
큰 파일을 그대로 GitHub에 올리지 않도록 17개 `tm_*.jsonl.gz`
조각으로 분리했고, **최대 조각은 13MiB 미만**입니다.
별도의 Git LFS나 외부 압축 라이브러리가 필요하지 않습니다.

## 자료 의미

- `tm_*.jsonl.gz`: UTF-8 JSONL의 **무손실 gzip**.
  `source_hash`는 원래 SST 영어 텍스트의 SHA-256이며
  해당 영어 텍스트는 **수록하지 않았습니다**.
- `source_dictionary`와 `dictionary_record_index`, 레코드 종류,
  필드, FormID·StringID, 번역 상태 원시값, `ko`를 그대로 보존합니다.
- `source_metadata.json.gz`: 기존 SST 파일별 이름·SHA·레코드 수,
  마스터 파일과 원시 속성 등 출처 증거를 압축했습니다.
- `manifest.json`: 각 gzip 조각의 SHA-256, 원래 JSONL 바이트 해시,
  보관 행 수, 원본 조각 목록/해시를 기록했습니다.

항목 수는 번역 사전에서 추출된 **발견 건수**이지
중복 제거된 고유 영문 수나 전체 인간 검수 완료량이 아닙니다.
같은 원문에도 화자·모드별로 다른 번역이 존재할 수 있으므로,
레코드 간 중복을 임의로 제거하거나 모두 하나의 문장으로 합치지
않았습니다. 게임에 적용할 때 원문 해시·플러그인 컨텍스트를
대조해야 합니다.

개인 작업 사전이라도 외부 기여자가 포함된 번역일 수 있으니
사전별 출처와 재배포 조건을 별도로 보존·확인해야 합니다.
이 보관소는 번역 데이터 참고용이며, 게임 파일이나
타사의 ESM/ESP/SST 바이너리를 직접 배포하지 않습니다.

## 다시 열기·검색·전수 검증

```powershell
# 저장소 루트에서 실행
python tools/sst_tm.py verify

# 특정 원문 SHA가 일치하는 한국어 번역문 확인
python tools/sst_tm.py find --game Fallout4 --hash <원문_sha256>

# 특정 사전의 번역문 확인
python tools/sst_tm.py find --game Starfield --dictionary SomeMod_en_ko.sst

# 한글 문구로 부분 검색
python tools/sst_tm.py find --game FalloutNewVegas --korean "볼트" --limit 10
```

압축을 풀어 원문 JSONL을 복원하려면 Python 표준 라이브러리만 사용합니다.

```python
import gzip, json

path = "Fallout4/Dictionaries/xTranslator/archive/tm_0000.jsonl.gz"
with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        print(record["source_dictionary"], record["source_hash"], record["ko"])
        break
```

원래 SST 바이너리는 로컬에서 보존합니다. 생성/검증 스크립트는
`tools/sst_tm.py`이며 `pack`, `verify`, `find`를 지원합니다.
