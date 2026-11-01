# 탐리엘 서고 — 데이드릭 문자 표시

웹 서적 뷰어는 **명시적으로** 데이드릭 글꼴로 지정된 구간만 데이드릭 문자로 출력한다. 다른 한국어·영문 문장은 기존 글꼴로 유지한다.

- 웹 서적 Markdown 원문: `[daedric]AYEMBD[/daedric]`처럼 범위를 표시한다.
- 책 원자료: `<font face="Daedric">AYEMBD</font>` 또는 `DemonicLetters`, `Ayembedt`로 지정된 폰트 구간은 서적 생성 시 위 마커로 변환한다. 중첩된 크기 태그도 지원한다.
- 출처에 데이드릭 글꼴 정보가 없다면 **임의로** 영어 알파벳을 데이드릭으로 바꾸지 않는다. 게임에서 별도의 스크롤 폰트를 적용한 경우는 원본 메타데이터 조사 후 수동으로 표시 범위를 지정해야 한다.
- HTML 태그를 직접 삽입하는 방식 대신 브라우저의 텍스트 노드를 이용해 렌더링하며, 번역 데이터의 내용을 실행 가능한 HTML로 해석하지 않는다.
- `[daedric]` 안의 영어 알파벳은 문자 모양만 데이드릭으로 바뀌며 한국어 번역이나 음역은 수행하지 않는다.

## 폰트 출처와 라이선스

`docs/assets/fonts/DemonicLetters.ttf`는 [OpenMW](https://github.com/OpenMW/openmw/blob/master/files/data/fonts/DemonicLetters.ttf) 프로젝트에서 배포하는 데이드릭 글꼴이다. 저작권자와 배포 조건은 [OFL-DemonicLetters.txt](../assets/fonts/OFL-DemonicLetters.txt)에 원문으로 동봉했다. SIL Open Font License 1.1 및 Reserved Font Name 조건을 준수한다.

이 지원은 **탐리엘 서고 웹사이트용**이다. Morrowind-OpenMW-KR 게임 엔진의 스크롤 글꼴 설정을 수정하지 않는다.
