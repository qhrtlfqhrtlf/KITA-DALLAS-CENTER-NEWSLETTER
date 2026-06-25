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
