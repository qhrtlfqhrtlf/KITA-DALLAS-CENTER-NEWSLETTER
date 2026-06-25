import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'current-draft.json')

def save_draft(data: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_draft() -> dict:
    if not os.path.exists(STATE_PATH):
        raise FileNotFoundError("current-draft.json 없음. new-post를 먼저 실행하세요.")
    with open(STATE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
