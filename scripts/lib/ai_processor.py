import json
import os
import re
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

KITA_CONTEXT = """KITA Dallas Center는 한국무역협회 달라스 지부로,
주요 팔로워는 한국 기업 및 미국에서 사업하는 한국 무역 관계자입니다.
관심 키워드: 관세, 공급망, 한미무역, 반도체, 에너지, 환율, 텍사스, 중국."""


def _get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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

    client = _get_client()
    resp = client.messages.create(
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

    client = _get_client()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.content[0].text.strip()
    if "```" in text:
        # Extract content between first and last code fence
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1)
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

    client = _get_client()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text.strip()
