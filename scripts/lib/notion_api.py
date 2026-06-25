import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_ID = "ca96d34a-eaea-8223-803f-8787a5a9f369"
VALID_KEYWORDS = ["관세", "공급망", "한미무역", "반도체", "에너지", "환율", "텍사스", "중국"]
VALID_SOURCES = ["Bloomberg", "FT", "WSJ", "Politico", "USTR", "Reuters", "기타"]


def _map_keywords_to_notion(keywords: list) -> list:
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
    print(f"노션 DB 등록 완료 (ID: {page_id})")
    return True
