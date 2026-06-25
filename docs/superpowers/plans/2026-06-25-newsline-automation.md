# NEWSLINE 자동화 파이프라인 구현 계획서

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 일일단편뉴스(NEWSLINE) 포스트 제작 워크플로우를 two-phase 스크립트로 자동화 — 뉴스 수집/랭킹/캡션 초안(Phase 1), 완성본 생성/태그/스토리 게시/노션 등록(Phase 2)

**Architecture:** Python 라이브러리 4개(`news_collector`, `ai_processor`, `instagram_api`, `notion_api`)를 PowerShell 진입점 2개(`new-post.ps1`, `publish-post.ps1`)가 호출. Phase 1이 `state/current-draft.json`에 상태를 저장하고 Phase 2가 이를 읽어 이어서 실행.

**Tech Stack:** Python 3.11+, `feedparser`, `requests`, `beautifulsoup4`, `anthropic`, `python-dotenv`, `pytest`; Meta Graph API v19; Notion API v1

## Global Constraints

- Python 파일은 모두 `scripts/lib/` 아래 위치
- PowerShell 진입점은 `scripts/` 바로 아래
- API 키는 반드시 `scripts/.env`에서 읽음 — 코드에 하드코딩 금지
- 캡션 제목 형식: `📌[제목]` (대괄호 포함, 공백 없이)
- 출처 날짜 형식: `(MM/DD)`
- 고정 태그: `@kitasns` `@kita_dallas_center`
- Phase 1에서 영문 캡션 생성 금지 — 한국어만
- Notion DB ID: `ca96d34a-eaea-8223-803f-8787a5a9f369`

---

## 파일 구조

```
C:\Users\KITA03\Desktop\업무\scripts\
├── .env                        # API 키 (gitignore 대상)
├── .env.example                # 키 이름 템플릿
├── requirements.txt
├── new-post.ps1                # Phase 1 진입점
├── publish-post.ps1            # Phase 2 진입점
├── state\
│   └── current-draft.json      # Phase 1→2 상태 전달
└── lib\
    ├── news_collector.py       # RSS 수집 + 웹 크롤링
    ├── ai_processor.py         # Claude API 호출
    ├── tag_mapper.py           # 언론사/기관 계정 매핑
    ├── instagram_api.py        # Graph API (스토리 게시)
    └── notion_api.py           # Notion DB 등록
tests\
├── test_news_collector.py
├── test_ai_processor.py
├── test_tag_mapper.py
├── test_instagram_api.py
└── test_notion_api.py
```

---

## Task 1: 프로젝트 셋업

**Files:**
- Create: `scripts/requirements.txt`
- Create: `scripts/.env.example`
- Create: `scripts/state/.gitkeep`
- Create: `scripts/lib/__init__.py`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: 설치 가능한 Python 환경, API 키 로딩 패턴

- [ ] **Step 1: 디렉토리 생성**

```powershell
cd "C:\Users\KITA03\Desktop\업무"
New-Item -ItemType Directory -Force scripts\lib, scripts\state, tests
New-Item -ItemType File -Force scripts\lib\__init__.py, tests\__init__.py, scripts\state\.gitkeep
```

- [ ] **Step 2: requirements.txt 작성**

`scripts/requirements.txt`:
```
feedparser==6.0.11
requests==2.32.3
beautifulsoup4==4.12.3
anthropic==0.40.0
python-dotenv==1.0.1
pytest==8.3.3
pytest-mock==3.14.0
```

- [ ] **Step 3: .env.example 작성**

`scripts/.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-...
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_USER_ID=...
NOTION_API_KEY=secret_...
```

- [ ] **Step 4: .env 파일 생성 (실제 키 입력)**

```powershell
Copy-Item scripts\.env.example scripts\.env
# .env 파일 열어서 실제 API 키 입력
notepad scripts\.env
```

- [ ] **Step 5: 패키지 설치**

```powershell
cd scripts
pip install -r requirements.txt
```

Expected output: `Successfully installed feedparser-6.0.11 ...`

- [ ] **Step 6: 설치 확인**

```powershell
python -c "import feedparser, anthropic, bs4; print('OK')"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add scripts/requirements.txt scripts/.env.example scripts/lib/__init__.py scripts/state/.gitkeep tests/__init__.py
git commit -m "feat: newsline automation project scaffold"
```

---

## Task 2: 뉴스 수집기 (`news_collector.py`)

**Files:**
- Create: `scripts/lib/news_collector.py`
- Create: `tests/test_news_collector.py`

**Interfaces:**
- Produces: `collect_articles() -> list[dict]`
  - 각 dict: `{"title": str, "url": str, "source": str, "published": str, "summary": str}`

- [ ] **Step 1: 테스트 작성**

`tests/test_news_collector.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from lib.news_collector import collect_articles, _parse_rss, _is_within_24h, _deduplicate

def test_parse_rss_returns_articles():
    mock_feed = MagicMock()
    mock_entry = MagicMock()
    mock_entry.title = "Trade War Escalates"
    mock_entry.link = "https://reuters.com/article/1"
    mock_entry.summary = "US tariffs increase..."
    mock_entry.published_parsed = (2026, 6, 25, 10, 0, 0, 0, 0, 0)
    mock_feed.entries = [mock_entry]

    with patch('feedparser.parse', return_value=mock_feed):
        result = _parse_rss("https://reuters.com/rss", "Reuters")

    assert len(result) == 1
    assert result[0]["title"] == "Trade War Escalates"
    assert result[0]["source"] == "Reuters"

def test_deduplicate_removes_same_url():
    articles = [
        {"url": "https://example.com/1", "title": "A"},
        {"url": "https://example.com/1", "title": "A duplicate"},
        {"url": "https://example.com/2", "title": "B"},
    ]
    result = _deduplicate(articles)
    assert len(result) == 2

def test_is_within_24h_recent():
    import time
    recent = time.gmtime(time.time() - 3600)  # 1시간 전
    assert _is_within_24h(recent) is True

def test_is_within_24h_old():
    import time
    old = time.gmtime(time.time() - 90000)  # 25시간 전
    assert _is_within_24h(old) is False
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
cd "C:\Users\KITA03\Desktop\업무"
python -m pytest tests/test_news_collector.py -v
```

Expected: FAIL (ImportError)

- [ ] **Step 3: news_collector.py 구현**

`scripts/lib/news_collector.py`:
```python
import feedparser
import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup

RSS_SOURCES = [
    ("https://feeds.reuters.com/reuters/businessNews", "Reuters"),
    ("https://feeds.a.dj.com/rss/RSSWorldNews.xml", "WSJ"),
    ("https://www.ft.com/?format=rss", "FT"),
    ("https://www.politico.com/rss/politicopicks.xml", "Politico"),
    ("https://ustr.gov/rss.xml", "USTR"),
    # Bloomberg: Google News RSS 프록시 사용
    ("https://news.google.com/rss/search?q=bloomberg+trade+tariff&hl=en-US&gl=US&ceid=US:en", "Bloomberg"),
]

KEYWORDS = ["관세", "tariff", "supply chain", "semiconductor", "trade", "korea", "texas",
            "energy", "currency", "china", "한미", "반도체"]

def _is_within_24h(parsed_time) -> bool:
    if parsed_time is None:
        return True  # 날짜 없으면 포함
    article_ts = time.mktime(parsed_time)
    return (time.time() - article_ts) < 86400

def _parse_rss(url: str, source: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    articles = []
    for entry in feed.entries:
        if not _is_within_24h(getattr(entry, 'published_parsed', None)):
            continue
        articles.append({
            "title": getattr(entry, 'title', ''),
            "url": getattr(entry, 'link', ''),
            "source": source,
            "published": getattr(entry, 'published', ''),
            "summary": getattr(entry, 'summary', '')[:300],
        })
    return articles

def _scrape_tradingeconomics() -> list[dict]:
    try:
        resp = requests.get("https://tradingeconomics.com/united-states/news",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        articles = []
        for item in soup.select("a.te-news-item")[:10]:
            title = item.get_text(strip=True)
            href = item.get('href', '')
            if href and not href.startswith('http'):
                href = "https://tradingeconomics.com" + href
            if title:
                articles.append({"title": title, "url": href,
                                  "source": "기타", "published": "", "summary": ""})
        return articles
    except Exception:
        return []

def _deduplicate(articles: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            result.append(a)
    return result

def _keyword_match(article: dict) -> bool:
    text = (article["title"] + " " + article["summary"]).lower()
    return any(kw.lower() in text for kw in KEYWORDS)

def collect_articles() -> list[dict]:
    all_articles = []
    for url, source in RSS_SOURCES:
        all_articles.extend(_parse_rss(url, source))
    all_articles.extend(_scrape_tradingeconomics())
    all_articles = _deduplicate(all_articles)
    # 키워드 매칭 우선 정렬
    matched = [a for a in all_articles if _keyword_match(a)]
    unmatched = [a for a in all_articles if not _keyword_match(a)]
    return matched + unmatched
```

- [ ] **Step 4: 테스트 통과 확인**

```powershell
python -m pytest tests/test_news_collector.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/news_collector.py tests/test_news_collector.py
git commit -m "feat: add news_collector with RSS + web scraping"
```

---

## Task 3: AI 처리기 (`ai_processor.py`)

**Files:**
- Create: `scripts/lib/ai_processor.py`
- Create: `tests/test_ai_processor.py`

**Interfaces:**
- Consumes: `collect_articles() -> list[dict]` (Task 2)
- Produces:
  - `rank_articles(articles: list[dict]) -> list[dict]` — 상위 5개, `ranking_reason` 필드 추가
  - `generate_korean_draft(article: dict) -> dict` — `{"title": str, "body": str, "source_line": str, "summary": str, "keywords": list[str]}`
  - `generate_full_caption(draft: dict) -> str` — 한국어+영어+해시태그 완성본

- [ ] **Step 1: 테스트 작성**

`tests/test_ai_processor.py`:
```python
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from unittest.mock import patch, MagicMock
from lib.ai_processor import rank_articles, generate_korean_draft, generate_full_caption

SAMPLE_ARTICLES = [
    {"title": "US Tariffs on Korean Steel Rise 25%", "url": "https://reuters.com/1",
     "source": "Reuters", "published": "6/25", "summary": "The US announced new tariffs..."},
    {"title": "Fed Holds Rates Steady", "url": "https://wsj.com/2",
     "source": "WSJ", "published": "6/25", "summary": "Federal Reserve kept rates..."},
]

SAMPLE_DRAFT = {
    "title": "미국, 한국산 철강에 25% 관세 부과",
    "body": "미국 정부가 한국산 철강 제품에 대해 25%의 추가 관세를 부과한다고 발표했다.",
    "source_line": "Reuters(6/25)",
    "summary": "미-한 철강 관세 분쟁 확대",
    "keywords": ["관세", "한미무역"],
}

def test_rank_articles_returns_top5(mocker):
    mock_response = MagicMock()
    mock_response.content[0].text = '''[
        {"index": 0, "reason": "한국 기업 직접 영향"},
        {"index": 1, "reason": "간접 영향"}
    ]'''
    mocker.patch('anthropic.Anthropic').return_value.messages.create.return_value = mock_response
    result = rank_articles(SAMPLE_ARTICLES)
    assert isinstance(result, list)
    assert len(result) <= 5

def test_generate_korean_draft_returns_required_fields(mocker):
    mock_response = MagicMock()
    mock_response.content[0].text = '''{
        "title": "미국, 한국산 철강에 25% 관세",
        "body": "본문 내용입니다.",
        "source_line": "Reuters(6/25)",
        "summary": "한 줄 요약",
        "keywords": ["관세", "한미무역"]
    }'''
    mocker.patch('anthropic.Anthropic').return_value.messages.create.return_value = mock_response
    result = generate_korean_draft(SAMPLE_ARTICLES[0])
    assert "title" in result
    assert "body" in result
    assert "keywords" in result

def test_generate_full_caption_contains_required_blocks(mocker):
    mock_response = MagicMock()
    mock_response.content[0].text = "📌[제목]\n\n본문\n\n📖 Reuters(6/25)\n📷 사용된 모든...\n⚠️ 본 게시물...\n\n--------------------\n\nEnglish title\nEnglish body"
    mocker.patch('anthropic.Anthropic').return_value.messages.create.return_value = mock_response
    result = generate_full_caption(SAMPLE_DRAFT)
    assert "📌[" in result
    assert "--------------------" in result
    assert "📷" in result
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
python -m pytest tests/test_ai_processor.py -v
```

Expected: FAIL

- [ ] **Step 3: ai_processor.py 구현**

`scripts/lib/ai_processor.py`:
```python
import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

KITA_CONTEXT = """KITA Dallas Center는 한국무역협회 달라스 지부로, 
주요 팔로워는 한국 기업 및 미국에서 사업하는 한국 무역 관계자입니다.
관심 키워드: 관세, 공급망, 한미무역, 반도체, 에너지, 환율, 텍사스, 중국."""

def rank_articles(articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    articles_text = "\n".join(
        f"[{i}] {a['title']} ({a['source']}) — {a['summary'][:150]}"
        for i, a in enumerate(articles[:20])
    )
    prompt = f"""{KITA_CONTEXT}

아래 기사 목록에서 KITA Dallas Center 인스타그램 포스트로 가장 적합한 기사 최대 5개를 선정하라.
한국 기업 및 무역 관계자에게 중요한 내용 우선. JSON 배열로 반환:
[{{"index": 숫자, "reason": "선정 이유 한 줄"}}]

기사 목록:
{articles_text}"""

    resp = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        ranked_indices = json.loads(resp.content[0].text)
        result = []
        for item in ranked_indices[:5]:
            idx = item["index"]
            if 0 <= idx < len(articles):
                a = dict(articles[idx])
                a["ranking_reason"] = item.get("reason", "")
                result.append(a)
        return result
    except Exception:
        return articles[:5]

def generate_korean_draft(article: dict) -> dict:
    prompt = f"""다음 기사를 KITA Dallas Center 인스타그램 일일단편뉴스 포스트로 작성하라.

기사 제목: {article['title']}
출처: {article['source']}
내용: {article['summary']}

요구사항:
- 제목: 한국어로 번역, 핵심 내용 담기 (30자 이내)
- 본문: 3~5문장, 사실 중심, 한국 기업 관련성 포함
- source_line: "{article['source']}(MM/DD)" 형식
- summary: 한 줄 요약 (20자 이내)
- keywords: 해당하는 것만 선택 ["관세","공급망","한미무역","반도체","에너지","환율","텍사스","중국"]

JSON으로만 반환:
{{"title": "...", "body": "...", "source_line": "...", "summary": "...", "keywords": [...]}}"""

    resp = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

def generate_full_caption(draft: dict) -> str:
    prompt = f"""다음 한국어 캡션 초안을 기반으로 NEWSLINE 완성본을 작성하라.

제목: {draft['title']}
본문: {draft['body']}
출처: {draft['source_line']}

완성본 형식 (정확히 준수):

📌[제목]

[본문]

📖 [출처]
📷 사용된 모든 이미지는 적법한 라이선스를 보유하고 있습니다.
⚠️ 본 게시물은 공개된 보도 자료를 기반으로 작성된 정보성 콘텐츠로, 협회의 공식 견해가 아님을 밝힙니다.

--------------------

[영어 제목 번역 — 보도자료 문체]
[영어 본문 번역]

📖 [출처 영문]
📷 All images used herein are covered by valid licenses.
⚠️ This post constitutes informational content compiled based on publicly available press materials and does not represent the official views of the KITA Dallas Center.

[해시태그: #통상뉴스 #한국무역협회 #KITA 포함, 주제 태그 추가, 공백 구분, 8~10개]"""

    resp = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text.strip()
```

- [ ] **Step 4: 테스트 통과 확인**

```powershell
python -m pytest tests/test_ai_processor.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/ai_processor.py tests/test_ai_processor.py
git commit -m "feat: add ai_processor with Claude API ranking and caption generation"
```

---

## Task 4: 태그 매퍼 (`tag_mapper.py`)

**Files:**
- Create: `scripts/lib/tag_mapper.py`
- Create: `tests/test_tag_mapper.py`

**Interfaces:**
- Produces: `get_tags(source: str, caption_text: str) -> list[str]`
  - 반환: `["@kitasns", "@kita_dallas_center", "@reuters", ...]`

- [ ] **Step 1: 테스트 작성**

`tests/test_tag_mapper.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from lib.tag_mapper import get_tags, OUTLET_MAP

def test_always_includes_fixed_tags():
    tags = get_tags("Reuters", "임의 본문")
    assert "@kitasns" in tags
    assert "@kita_dallas_center" in tags

def test_maps_reuters_to_account():
    tags = get_tags("Reuters", "임의 본문")
    assert "@reuters" in tags

def test_maps_bloomberg_to_account():
    tags = get_tags("Bloomberg", "임의 본문")
    assert "@bloombergbusiness" in tags

def test_no_duplicate_tags():
    tags = get_tags("Reuters", "Reuters mentioned again")
    assert tags.count("@reuters") == 1

def test_outlet_map_covers_all_sources():
    sources = ["Reuters", "Bloomberg", "WSJ", "FT", "Politico", "USTR"]
    for s in sources:
        assert s in OUTLET_MAP
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
python -m pytest tests/test_tag_mapper.py -v
```

Expected: FAIL

- [ ] **Step 3: tag_mapper.py 구현**

`scripts/lib/tag_mapper.py`:
```python
OUTLET_MAP = {
    "Reuters":   "@reuters",
    "Bloomberg": "@bloombergbusiness",
    "WSJ":       "@wsj",
    "FT":        "@financialtimes",
    "Politico":  "@politico",
    "USTR":      "@usambassador",  # USTR 공식 계정
    "기타":      None,
}

FIXED_TAGS = ["@kitasns", "@kita_dallas_center"]

def get_tags(source: str, caption_text: str) -> list[str]:
    tags = list(FIXED_TAGS)
    outlet_tag = OUTLET_MAP.get(source)
    if outlet_tag and outlet_tag not in tags:
        tags.append(outlet_tag)
    return tags
```

- [ ] **Step 4: 테스트 통과 확인**

```powershell
python -m pytest tests/test_tag_mapper.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/tag_mapper.py tests/test_tag_mapper.py
git commit -m "feat: add tag_mapper with outlet account mappings"
```

---

## Task 5: Phase 1 스크립트 — `new-post`

**Files:**
- Create: `scripts/lib/state.py`
- Create: `scripts/new-post.ps1`
- Create: `scripts/new_post.py` (PS1이 호출하는 Python 진입점)

**Interfaces:**
- Consumes: `collect_articles()`, `rank_articles()`, `generate_korean_draft()`
- Produces: `scripts/state/current-draft.json`

- [ ] **Step 1: state.py 작성**

`scripts/lib/state.py`:
```python
import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'current-draft.json')

def save_draft(data: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_draft() -> dict:
    if not os.path.exists(STATE_PATH):
        raise FileNotFoundError("current-draft.json 없음. new-post를 먼저 실행하세요.")
    with open(STATE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
```

- [ ] **Step 2: new_post.py 작성**

`scripts/new_post.py`:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from news_collector import collect_articles
from ai_processor import rank_articles, generate_korean_draft
from state import save_draft

def main():
    print("\n📡 뉴스 수집 중...")
    articles = collect_articles()
    if not articles:
        print("❌ 수집된 기사가 없습니다.")
        sys.exit(1)

    print(f"✅ {len(articles)}개 기사 수집 완료. AI 분석 중...\n")
    ranked = rank_articles(articles)

    print("=" * 60)
    print("📰 오늘의 포스트 후보")
    print("=" * 60)
    for i, a in enumerate(ranked, 1):
        print(f"\n[{i}] {a['title']}")
        print(f"    출처: {a['source']} | 이유: {a.get('ranking_reason', '')}")
        print(f"    {a['summary'][:100]}...")

    print("\n" + "=" * 60)
    while True:
        choice = input("번호 선택 (1-5): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(ranked):
            selected = ranked[int(choice) - 1]
            break
        print("올바른 번호를 입력하세요.")

    print(f"\n✍️  '{selected['title']}' 기반 한국어 캡션 초안 생성 중...")
    draft = generate_korean_draft(selected)

    print("\n" + "=" * 60)
    print("📋 한국어 캡션 초안")
    print("=" * 60)
    print(f"\n📌[{draft['title']}]\n")
    print(draft['body'])
    print(f"\n📖 {draft['source_line']}")
    print("📷 사용된 모든 이미지는 적법한 라이선스를 보유하고 있습니다.")
    print("⚠️ 본 게시물은 공개된 보도 자료를 기반으로 작성된 정보성 콘텐츠로, 협회의 공식 견해가 아님을 밝힙니다.")

    state = {
        "article_title": selected["title"],
        "article_url": selected["url"],
        "source": selected["source"],
        "korean_draft": draft,
    }
    save_draft(state)
    print("\n✅ 초안 저장 완료. 과장님 승인 후 publish-post.ps1을 실행하세요.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: new-post.ps1 작성**

`scripts/new-post.ps1`:
```powershell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\new_post.py"
```

- [ ] **Step 4: 실제 실행 테스트**

```powershell
cd "C:\Users\KITA03\Desktop\업무\scripts"
.\new-post.ps1
```

Expected: 뉴스 후보 목록 출력 → 번호 선택 → 한국어 캡션 초안 출력 → `state/current-draft.json` 생성

- [ ] **Step 5: state 파일 확인**

```powershell
Get-Content "C:\Users\KITA03\Desktop\업무\scripts\state\current-draft.json"
```

Expected: JSON with `korean_draft`, `source`, `article_url` 필드 존재

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/state.py scripts/new_post.py scripts/new-post.ps1
git commit -m "feat: Phase 1 new-post script with news collection and Korean draft"
```

---

## Task 6: Instagram API (`instagram_api.py`)

**Files:**
- Create: `scripts/lib/instagram_api.py`
- Create: `tests/test_instagram_api.py`

**Interfaces:**
- Produces: `post_story_from_latest_feed() -> bool`

- [ ] **Step 1: 테스트 작성**

`tests/test_instagram_api.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from unittest.mock import patch, MagicMock
from lib.instagram_api import _get_latest_media_url, post_story_from_latest_feed

def test_get_latest_media_url_returns_url(mocker):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"id": "123", "media_url": "https://cdn.instagram.com/img.jpg", "timestamp": "2026-06-25T10:00:00+0000"}]
    }
    mock_resp.raise_for_status = MagicMock()
    mocker.patch('requests.get', return_value=mock_resp)
    url = _get_latest_media_url("TOKEN", "USER_ID")
    assert url == "https://cdn.instagram.com/img.jpg"

def test_post_story_returns_true_on_success(mocker):
    mock_media_resp = MagicMock()
    mock_media_resp.json.return_value = {"data": [{"id": "123", "media_url": "https://cdn.instagram.com/img.jpg", "timestamp": "2026-06-25"}]}
    mock_media_resp.raise_for_status = MagicMock()

    mock_container_resp = MagicMock()
    mock_container_resp.json.return_value = {"id": "container_456"}
    mock_container_resp.raise_for_status = MagicMock()

    mock_publish_resp = MagicMock()
    mock_publish_resp.json.return_value = {"id": "story_789"}
    mock_publish_resp.raise_for_status = MagicMock()

    mocker.patch('requests.get', return_value=mock_media_resp)
    mocker.patch('requests.post', side_effect=[mock_container_resp, mock_publish_resp])

    result = post_story_from_latest_feed("TOKEN", "USER_ID")
    assert result is True
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
python -m pytest tests/test_instagram_api.py -v
```

Expected: FAIL

- [ ] **Step 3: instagram_api.py 구현**

`scripts/lib/instagram_api.py`:
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

GRAPH_BASE = "https://graph.facebook.com/v19.0"

def _get_latest_media_url(token: str, user_id: str) -> str:
    resp = requests.get(
        f"{GRAPH_BASE}/{user_id}/media",
        params={"fields": "id,media_url,timestamp", "access_token": token, "limit": 1}
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if not data:
        raise ValueError("피드에 게시물이 없습니다.")
    return data[0]["media_url"]

def post_story_from_latest_feed() -> bool:
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    user_id = os.getenv("INSTAGRAM_USER_ID")

    media_url = _get_latest_media_url(token, user_id)

    # 스토리 컨테이너 생성
    container_resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/media",
        params={
            "image_url": media_url,
            "media_type": "STORIES",
            "access_token": token,
        }
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    # 스토리 게시
    publish_resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/media_publish",
        params={"creation_id": container_id, "access_token": token}
    )
    publish_resp.raise_for_status()
    story_id = publish_resp.json().get("id")
    print(f"✅ 스토리 게시 완료 (ID: {story_id})")
    return True
```

- [ ] **Step 4: 테스트 통과 확인**

```powershell
python -m pytest tests/test_instagram_api.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/instagram_api.py tests/test_instagram_api.py
git commit -m "feat: add instagram_api with story posting via Graph API"
```

---

## Task 7: Notion API (`notion_api.py`)

**Files:**
- Create: `scripts/lib/notion_api.py`
- Create: `tests/test_notion_api.py`

**Interfaces:**
- Consumes: `load_draft() -> dict` (Task 5의 state)
- Produces: `register_published_post(draft: dict) -> bool`

- [ ] **Step 1: 테스트 작성**

`tests/test_notion_api.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from unittest.mock import patch, MagicMock
from lib.notion_api import register_published_post, _map_keywords_to_notion

SAMPLE_DRAFT = {
    "article_title": "US Tariffs on Korean Steel",
    "source": "Reuters",
    "korean_draft": {
        "title": "미국, 한국산 철강에 25% 관세",
        "summary": "미-한 철강 관세 분쟁",
        "keywords": ["관세", "한미무역"],
    }
}

def test_map_keywords_filters_valid():
    result = _map_keywords_to_notion(["관세", "반도체", "존재안함"])
    assert "관세" in result
    assert "반도체" in result
    assert "존재안함" not in result

def test_register_published_post_calls_notion_api(mocker):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"id": "new-page-id"}
    mocker.patch('requests.post', return_value=mock_resp)
    result = register_published_post(SAMPLE_DRAFT)
    assert result is True
```

- [ ] **Step 2: 테스트 실패 확인**

```powershell
python -m pytest tests/test_notion_api.py -v
```

Expected: FAIL

- [ ] **Step 3: notion_api.py 구현**

`scripts/lib/notion_api.py`:
```python
import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_ID = "ca96d34a-eaea-8223-803f-8787a5a9f369"
VALID_KEYWORDS = ["관세", "공급망", "한미무역", "반도체", "에너지", "환율", "텍사스", "중국"]
VALID_SOURCES = ["Bloomberg", "FT", "WSJ", "Politico", "USTR", "Reuters", "기타"]

def _map_keywords_to_notion(keywords: list[str]) -> list[str]:
    return [k for k in keywords if k in VALID_KEYWORDS]

def register_published_post(state: dict) -> bool:
    token = os.getenv("NOTION_API_KEY")
    draft = state.get("korean_draft", {})
    source = state.get("source", "기타")
    if source not in VALID_SOURCES:
        source = "기타"

    payload = {
        "parent": {"database_id": DB_ID},
        "properties": {
            "뉴스 제목": {"title": [{"text": {"content": draft.get("title", state.get("article_title", ""))}}]},
            "발행여부": {"checkbox": True},
            "발행일": {"date": {"start": date.today().isoformat()}},
            "출처": {"select": {"name": source}},
            "키워드": {"multi_select": [{"name": k} for k in _map_keywords_to_notion(draft.get("keywords", []))]},
            "한 줄 요약": {"rich_text": [{"text": {"content": draft.get("summary", "")}}]},
        }
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        json=payload
    )
    resp.raise_for_status()
    page_id = resp.json().get("id")
    print(f"✅ 노션 DB 등록 완료 (ID: {page_id})")
    return True
```

- [ ] **Step 4: 테스트 통과 확인**

```powershell
python -m pytest tests/test_notion_api.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/notion_api.py tests/test_notion_api.py
git commit -m "feat: add notion_api for post-publish DB registration"
```

---

## Task 8: Phase 2 스크립트 — `publish-post`

**Files:**
- Create: `scripts/publish_post.py`
- Create: `scripts/publish-post.ps1`

**Interfaces:**
- Consumes: `load_draft()`, `generate_full_caption()`, `get_tags()`, `post_story_from_latest_feed()`, `register_published_post()`

- [ ] **Step 1: publish_post.py 작성**

`scripts/publish_post.py`:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from state import load_draft
from ai_processor import generate_full_caption
from tag_mapper import get_tags
from instagram_api import post_story_from_latest_feed
from notion_api import register_published_post

def main():
    # 1. 저장된 초안 불러오기
    try:
        state = load_draft()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    draft = state["korean_draft"]

    print("\n" + "=" * 60)
    print("📋 저장된 한국어 초안")
    print("=" * 60)
    print(f"\n📌[{draft['title']}]\n")
    print(draft['body'])
    print(f"\n📖 {draft['source_line']}")

    # 2. 수정 여부 확인
    print("\n수정 사항이 있으면 입력하세요. 없으면 Enter를 누르세요.")
    revision = input("수정 내용: ").strip()
    if revision:
        print("수정 사항 반영 중...")
        draft["body"] = draft["body"] + f"\n[수정: {revision}]"

    # 3. 완성본 캡션 생성 (KO + EN)
    print("\n✍️  완성본 캡션 생성 중 (한국어 + 영어)...")
    full_caption = generate_full_caption(draft)

    print("\n" + "=" * 60)
    print("✅ 완성본 캡션")
    print("=" * 60)
    print(full_caption)

    # 4. 태그 목록 출력
    tags = get_tags(state["source"], full_caption)
    print("\n" + "=" * 60)
    print("🏷️  태그 목록 (복사해서 사용)")
    print("=" * 60)
    print("  ".join(tags))

    # 5. 캔바 게시 대기
    print("\n" + "=" * 60)
    print("📸 캔바에서 디자인 완성 후 Instagram에 게시하세요.")
    print("   게시 완료 후 y를 눌러주세요.")
    print("=" * 60)
    while True:
        confirm = input("게시 완료 (y): ").strip().lower()
        if confirm == 'y':
            break

    # 6. 스토리 자동 게시
    print("\n📖 스토리 게시 중...")
    try:
        post_story_from_latest_feed()
    except Exception as e:
        print(f"⚠️  스토리 게시 실패: {e}")

    # 7. 노션 DB 등록
    print("📝 노션 DB 등록 중...")
    try:
        register_published_post(state)
    except Exception as e:
        print(f"⚠️  노션 등록 실패: {e}")

    print("\n🎉 완료! 오늘의 NEWSLINE 포스트가 게시되었습니다.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: publish-post.ps1 작성**

`scripts/publish-post.ps1`:
```powershell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\publish_post.py"
```

- [ ] **Step 3: 전체 테스트 실행**

```powershell
cd "C:\Users\KITA03\Desktop\업무"
python -m pytest tests/ -v
```

Expected: 모든 테스트 PASSED

- [ ] **Step 4: Phase 1 → Phase 2 엔드투엔드 테스트**

```powershell
cd scripts
# Phase 1
.\new-post.ps1
# (기사 선택 후 초안 확인)

# Phase 2
.\publish-post.ps1
# (완성본 확인 → 태그 확인 → y 입력 → 스토리+노션 자동 처리)
```

- [ ] **Step 5: Commit**

```bash
git add scripts/publish_post.py scripts/publish-post.ps1
git commit -m "feat: Phase 2 publish-post script — full caption, tags, story, notion"
```

---

## 실행 가이드 요약

```powershell
# 매일 아침: Phase 1
cd "C:\Users\KITA03\Desktop\업무\scripts"
.\new-post.ps1

# 과장님 승인 후: Phase 2
.\publish-post.ps1
```

**필요한 API 키** (`scripts/.env`):
- `ANTHROPIC_API_KEY` — Anthropic Console
- `INSTAGRAM_ACCESS_TOKEN` — Meta Developer (장기 토큰)
- `INSTAGRAM_USER_ID` — Instagram 계정 숫자 ID
- `NOTION_API_KEY` — Notion Integrations
