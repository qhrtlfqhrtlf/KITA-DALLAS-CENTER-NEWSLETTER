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
