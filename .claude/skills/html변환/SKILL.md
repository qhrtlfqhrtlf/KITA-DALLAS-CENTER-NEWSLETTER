---
name: html변환
description: >
  Trade Newsline 뉴스레터 발송용 이미지맵 HTML 자동 생성 스킬.
  커버 PDF와 호별 정보(발행일, Constant Contact PDF URL, 섹션별 페이지 번호)를 받아
  이메일용 스티칭 JPG + 발송용 euc-kr HTML + 검수용 미리보기 HTML을 생성한다.
  "/html변환", "뉴스레터 HTML 만들어줘", "HTML 변환" 요청 시 반드시 이 스킬을 사용한다.
---

# /html변환 — Trade Newsline 발송용 HTML 자동 생성

## 필요 입력 (없으면 사용자에게 요청)

1. **커버 PDF 경로** — 예: `001. 뉴스레터\001.아카이브\2026년\14호(07-16)\14호 커버.pdf`
2. **발행일** — `YYYYMMDD` (이미지 파일명 `edm_YYYYMMDD.jpg`에 사용; IT SR 요청 시 이 파일명 명시)
3. **CC PDF URL** — 이너 PDF를 Constant Contact에 업로드한 뒤 받은 `https://files.constantcontact.com/...pdf`
4. **섹션별 페이지 번호** — 이너 PDF에서 각 섹션의 시작 페이지. 이너 PDF를 직접 읽어 제안하고 사용자 확인을 받는다.

## 워크플로우

### 1단계: 스티칭 이미지 생성
```
python scripts/newsletter_html.py render --pdf "<커버 PDF 경로>" --out "<호 폴더>\edm_YYYYMMDD.jpg"
```
- 출력 JSON의 `pages`(예상 5), `height` 확인. 폭 기본 700px.
- 경로에 한글·공백 있으므로 항상 따옴표.

### 2단계: 좌표 검증 (하이브리드)
1. `scripts/templates/newsletter_map.json`의 기준 좌표를 1차값으로 사용
2. 생성된 스티칭 JPG를 Read 도구로 직접 보고, 각 버튼("»자세히 보기", "전체보기", 배너, SNS 아이콘)의 실제 위치와 기준 좌표를 대조
3. y좌표가 다르면 감지값으로 보정. 단 **편차가 80px를 초과하면 기준값을 유지하고 해당 영역에 `"warn": true`** 를 붙인다
4. 섹션 개수 자체가 다르면(코너 신설/폐지) 사용자에게 알리고 영역을 추가/삭제

### 3단계: 이슈 설정 JSON 생성
- 템플릿을 복사해 호 폴더에 `<N호> issue.json` 저장:
  - `image_url`: `https://www.kita.net/mailclub/NeDM/edm_YYYYMMDD.jpg`
  - `pdf_url`: CC PDF URL
  - `areas[].page`: 확인된 페이지 번호 (1페이지는 `#page` 프래그먼트가 자동 생략됨)
  - `areas[].coords`: 보정된 좌표

### 4단계: HTML 생성
```
python scripts/newsletter_html.py build --config "<호 폴더>\<N호> issue.json" --out "<호 폴더>\<N호> html.html"
```
- euc-kr로 저장됨. 내용은 13호 발송본과 동일한 구조.

### 5단계: 미리보기 검수
```
python scripts/newsletter_html.py preview --config "<호 폴더>\<N호> issue.json" --image "edm_YYYYMMDD.jpg" --out "<호 폴더>\preview.html"
```
- `--image`는 preview.html 기준 상대경로(같은 폴더면 파일명만).
- PowerShell `Invoke-Item`으로 preview.html을 열어 사용자에게 검수 요청.
- 파란 영역 = 정상, **빨간 영역 = 편차 경고(warn)** — 반드시 육안 확인 후 수정.
- 수정 요청이 있으면 issue.json 좌표를 고치고 4~5단계 반복.

### 6단계: 마무리
1. 검수 통과 후, 확정 좌표가 템플릿과 달라졌으면 `scripts/templates/newsletter_map.json`에 반영 (다음 호 기준값)
2. 사용자에게 안내: 완성된 `edm_YYYYMMDD.jpg`는 IT 운영센터 SR로 업로드 요청(파일명 명시), HTML은 발송 시스템에 사용

## 주의사항
- 업무 자료 폴더(001~999)의 산출물은 git에 커밋하지 않는다 (템플릿 갱신만 커밋)
- 유튜브 고정 링크의 후행 공백은 발송본 원본 그대로 유지한다
- CC PDF URL 미확보 상태로 HTML을 만들지 않는다 (플레이스홀더 금지)
