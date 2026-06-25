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
