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
