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
