# 미번역 서적 번역 작업실

외전 및 ESO 서적의 **작품별·책별 번역 작업 파일**을 모아 두었습니다.

- [배틀스파이어](battlespire/index.md): 50건
- [레드가드](redguard/index.md): 16건
- [섀도키](shadowkey/index.md): 5건
- [ESO 일반 서적](eso/index.md): 2,533건
- [ESO 일지·편지·쪽지](eso_journals/index.md): 2,233건 (공개 목록 확인)

총 **4,837개의 개별 Markdown 작업 파일**이 있습니다. 기존 한국어 번역 완료 서적 2,629건과는 별개입니다.

## 파일 구성

각 파일에는 원문 영문 제목, 게임 시리즈, 외부 원문 출처, 한국어 번역 입력란, 검수 체크리스트가 있습니다. 일부 개별 원문 링크가 확보되지 않은 책은 게임별 원문 색인 링크를 사용합니다. **원문 전문은 들어 있지 않습니다.**

파일명은 책 제목만 사용하고, 동일한 제목의 다른 책만 동명서적 폴더로 구분합니다. 한국어 제목이 확정되지 않은 책은 원제 파일명을 유지합니다.

## 번역 시작하기

1. 해당 게임의 `index.md`에서 작업할 책을 선택합니다.
2. 파일 속 **원문 출처**에서 원문을 직접 확인합니다.
3. `## 한국어 번역` 아래의 미번역 안내를 검수된 번역문으로 교체합니다.
4. 고유명사와 문맥을 기존 아카이브 용어에 맞추고 검수 체크리스트를 업데이트합니다.
5. 공개 재배포 조건을 확인한 후에만 전문 게시 대상으로 승격합니다.

번역 작업 원문을 개인적으로 참고하는 경우 저장소의 `work/` 폴더를 사용하면 해당 폴더는 `.gitignore`에 의해 공개 커밋 대상에서 제외됩니다. 그러나 개인 보관 가능 범위도 원본의 이용조건을 준수해야 하며, 이 저장소에는 외부 서적 전문을 자동 다운로드하거나 업로드하는 기능이 없습니다.

## 자동 갱신 정책

- 참고 서적 제목과 출처 데이터: `docs/books/imperial_game_books_catalog.json`
- 개별 작업 파일 생성: `tools/build_translation_workbooks.py`
- GitHub Actions: `.github/workflows/build-translation-workbooks.yml`
- 웹용 작업 파일 위치 색인: `docs/untranslated/lookup.json`
- **이미 있는 작업 파일은 빌드 스크립트가 덮어쓰지 않습니다.** 수동으로 입력한 번역문을 보호합니다.

관련 참고: [외부 서적 색인](../imperial-library.html) · [서적 이용 및 검수 기준](../books/EXTERNAL_SOURCES.md)

## 로컬 영문 원문 준비 (ESP/ESM 미필요)

사용 권한이 있는 ESO 참고 EPUB을 준비했다면 저장소 최상위에서 Node.js로 실행할 수 있습니다.

```powershell
node tools/extract_eso_epub_local.cjs --epub "C:\\path\\to\\ElderScrollsOnline_Tomes.epub"
```

참고 원문이 `work/imperial_library_originals/eso/ext-<서적UID>.txt`로 저장됩니다. 이 로컬 `work/` 폴더는 Git에서 제외되며 원문 전문은 공개 웹페이지에 표시하거나 GitHub에 커밋하지 않습니다. 명시적 권한이 없는 외부 저작물의 재배포는 피해야 합니다.

자세한 내용: [외부 서적 출처·공식 소개·이용 기준](../books/EXTERNAL_SOURCES.md)
