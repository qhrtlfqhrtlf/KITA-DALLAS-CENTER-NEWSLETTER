# NEWSLINE 자동화 파이프라인 설계

**작성일**: 2026-06-25  
**프로젝트**: KITA Dallas Center — 일일단편뉴스(NEWSLINE) 인스타그램 포스트 자동화  
**목표**: 뉴스 발굴 → 캡션 생성 → 인스타그램 게시까지의 반복 수작업 최소화

---

## 1. 전체 구조

워크플로우를 두 개의 독립 스크립트로 분리한다.  
승인(과장님)이 두 페이즈 사이에 위치하며, 디지털 트리거가 없으므로 사람이 직접 Phase 2를 실행한다.

```
Phase 1: new-post
  뉴스 수집 → AI 필터링 → 사용자 선택 → 한국어 캡션 초안

      [ 과장님 승인 — 수동 ]

Phase 2: publish-post
  한국어 캡션 확정 → 영문 포함 완성본 생성 → 태그 목록 출력
  → (캔바 디자인 + Instagram 공유 — 수동)
  → 스토리 자동 게시 (Graph API)
  → 노션 DB 자동 등록
```

---

## 2. Phase 1 — `new-post`

### 2-1. 뉴스 수집

대상 소스:

| 소스 | 방법 |
|------|------|
| Reuters | RSS 피드 |
| Bloomberg | RSS 피드 |
| WSJ | RSS 피드 |
| FT | RSS 피드 |
| Politico | RSS 피드 |
| USTR | RSS 피드 |
| tradingeconomics.com | 웹 크롤링 |
| insidetrade.com | 웹 크롤링 (구독 필요 — 로그인 세션 또는 공개 페이지만 수집) |

- 최근 24시간 기사만 수집
- 중복 제거 (URL 기준)
- 노션 DB 키워드(관세·공급망·한미무역·반도체·에너지·환율·텍사스·중국)와 매칭되는 기사 우선

### 2-2. AI 필터링 및 랭킹

Claude API로 수집된 기사를 분석하여 KITA Dallas Center 팔로워 관점에서 중요도 순 후보 3~5개 추출.  
각 후보에 한 줄 요약, 출처, 추천 키워드 포함.

### 2-3. 사용자 선택 및 초안 생성

터미널에서 번호 선택 → 선택된 기사 기반으로 한국어 캡션 초안 생성.  
출력: 제목 + 본문 + 출처 (날짜 형식: MM/DD).  
**영문본은 이 단계에서 생성하지 않는다.**

---

## 3. Phase 2 — `publish-post`

### 3-1. 캡션 완성본 생성

Phase 1에서 생성된 한국어 초안을 불러온다.  
사용자가 수정 사항을 입력하거나 그대로 확정.  
확정 후 영문 번역 포함 전체 완성본(한국어 블록 + 영어 블록 + 해시태그) 생성.  
기존 `kita-dallas-newsline-caption` 스킬의 포맷 및 고정 문구 준수.

### 3-2. 태그 목록 자동 생성

아래를 자동으로 조합하여 복사 가능한 태그 목록 출력:

- 고정: `@kitasns` `@kita_dallas_center`
- 인용 언론사 인스타그램 계정 (Reuters→@reuters, Bloomberg→@bloomberg 등)
- 기사에 등장하는 주요 기관/기업 계정 (AI가 추출 + 알려진 계정 매핑)

### 3-3. 사진 등록 및 게시 (수동)

캔바 "000. 일일 뉴스" 폴더에서 해당 호차 디자인 완성 후  
캔바 공유 → Instagram 옵션으로 게시. (자동화 범위 외)

### 3-4. 스토리 자동 게시

Instagram Graph API를 사용하여 피드 게시물을 스토리에 자동 공유.  
사용자가 캔바에서 피드 게시 완료 후 `publish-post.ps1`에서 "게시 완료(y)" 입력 시 실행.  
위치는 Dallas, TX (위치 ID 사전 설정)로 고정.

### 3-5. 노션 DB 자동 등록

게시 완료 후 `📰 일일 카드뉴스 이력 DB`에 자동 생성:

| 필드 | 값 |
|------|----|
| 뉴스 제목 | 캡션 제목 |
| 발행여부 | ✅ |
| 발행일 | 오늘 날짜 |
| 출처 | 선택된 언론사 |
| 키워드 | AI 추출 키워드 |
| 한 줄 요약 | Phase 1 AI 요약 |

---

## 4. 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| 뉴스 수집 | Python — `feedparser`, `requests`, `BeautifulSoup` |
| AI 처리 | Claude API (`claude-sonnet-4-6`) |
| Instagram 게시/스토리 | Meta Graph API |
| 노션 연동 | Notion API |
| 실행 환경 | PowerShell + Python (Windows) |
| 설정 관리 | `.env` 파일 (API 키) |

---

## 5. 파일 구조

```
C:\Users\KITA03\Desktop\업무\
└── scripts\
    ├── new-post.ps1         # Phase 1
    ├── publish-post.ps1     # Phase 2
    ├── .env                 # API 키 (Claude, Instagram, Notion)
    └── lib\
        ├── news_collector.py
        ├── ai_processor.py
        ├── instagram_api.py
        └── notion_api.py
```

---

## 6. 제외 범위

- 셔터스톡 키워드 제안 — 사진 선정은 사용자가 직접 수행
- 캔바 디자인 자동화 — 디자인은 사용자가 직접 수행
- 승인 자동화 — 과장님 승인은 사내 메신저/구두로 수행

---

## 7. 성공 기준

- Phase 1 실행 후 3분 이내에 후보 목록 + 한국어 캡션 초안 출력
- Phase 2 실행 후 완성본 캡션 + 태그 목록 즉시 출력
- 스토리 게시 및 노션 DB 등록이 사람 개입 없이 자동 완료
