import feedparser
import requests
import time
import calendar
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
    article_ts = calendar.timegm(parsed_time)  # UTC struct_time -> UTC timestamp
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
