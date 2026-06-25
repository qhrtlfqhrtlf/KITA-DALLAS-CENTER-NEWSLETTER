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


def post_story_from_latest_feed(token: str = None, user_id: str = None) -> bool:
    """최신 피드 이미지를 가져와 스토리로 게시합니다.

    Args:
        token: Instagram Graph API 액세스 토큰. None이면 환경변수 INSTAGRAM_ACCESS_TOKEN을 사용.
        user_id: Instagram 사용자 ID. None이면 환경변수 INSTAGRAM_USER_ID를 사용.

    Returns:
        True if successful.
    """
    if token is None:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if user_id is None:
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
    print(f"스토리 게시 완료 (ID: {story_id})")
    return True
