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
